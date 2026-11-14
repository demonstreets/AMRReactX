#!/usr/bin/env python3
"""Generate/verify a Chinese handoff sheet for strict external artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-EXTERNAL-ARTIFACT-CN-HANDOFF"

REPO = Path.cwd().resolve()
DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_external_artifact_cn_handoff_20260818")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_external_artifact_cn_handoff_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_external_artifact_cn_handoff_report.md"
DEFAULT_GUIDE = Path("docs/user_guides/真实资料投递清单_按文件路径.md")

DROP_INDEX = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
    "strict_external_artifact_drop_index_report.json"
)
RECEIVING_PACK = Path(
    "docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812/"
    "strict_external_evidence_receiving_pack_report.json"
)

EXPECTED_COUNTS = {"external_plume": 5, "fire_calibration": 5, "real_cad": 4}
DOMAIN_CN = {
    "external_plume": "外部泄漏/扩散 plume 数据",
    "fire_calibration": "火灾、热辐射、过压标定数据",
    "real_cad": "真实 CAD、清理几何与边界标签",
}
BLOCKER_CN = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset": (
        "扩散云团仍缺少真实外部数据对照"
    ),
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup": (
        "几何证据仍是合成储罐/管廊 STL，不是真实 CAD 清理结果"
    ),
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure": (
        "火灾后果仍是筛查级，缺少热辐射/过压标定"
    ),
}


class HandoffError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HandoffError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HandoffError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HandoffError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def normalize_domains(index: dict[str, Any]) -> list[dict[str, Any]]:
    domains = []
    for domain in index.get("domain_drop_index", []):
        name = domain.get("domain")
        require(name in EXPECTED_COUNTS, f"unexpected domain: {name}")
        files = []
        for check in domain.get("checks", []):
            label = check.get("label")
            target = check.get("target_path")
            template = check.get("template_path")
            require(isinstance(label, str) and label, "artifact is missing label")
            require(isinstance(target, str) and target, f"{label} is missing target_path")
            require(isinstance(template, str) and template, f"{label} is missing template_path")
            files.append(
                {
                    "label": label,
                    "kind": check.get("kind"),
                    "required": check.get("required") is not False,
                    "currently_present": check.get("currently_present") is True,
                    "target_path": target,
                    "template_path": template,
                    "json_required_keys": check.get("json_required_keys"),
                    "csv_header": check.get("csv_header"),
                }
            )
        files = sorted(files, key=lambda item: item["label"])
        domains.append(
            {
                "domain": name,
                "domain_cn": DOMAIN_CN[name],
                "required_file_count": len(files),
                "present_file_count": sum(1 for item in files if item["currently_present"]),
                "missing_file_count": sum(1 for item in files if not item["currently_present"]),
                "files": files,
            }
        )
    return sorted(domains, key=lambda item: item["domain"])


def csv_header_text(item: dict[str, Any]) -> str:
    header = item.get("csv_header")
    if not header:
        return ""
    return ", ".join(str(value) for value in header)


def json_key_text(item: dict[str, Any]) -> str:
    keys = item.get("json_required_keys")
    if not keys:
        return ""
    return ", ".join(str(value) for value in keys)


def write_chinese_guide(
    *,
    guide_path: Path,
    domains: list[dict[str, Any]],
    blockers: list[str],
    total_required: int,
    total_present: int,
    total_missing: int,
    strict_completion_allowed: bool,
) -> None:
    lines = [
        "# 真实资料投递清单（按文件路径）",
        "",
        "这份清单由 `tools/write_strict_external_artifact_cn_handoff_report.py` 根据当前严格资料投递索引自动生成。",
        "用途是让真实 CAD、外部扩散数据、火灾标定数据到位后，可以直接按路径投递并一键复验。",
        "",
        "## 1. 当前状态",
        "",
        f"- 合同要求文件总数：`{total_required}`",
        f"- 当前已存在文件：`{total_present}`",
        f"- 当前缺失文件：`{total_missing}`",
        f"- 是否允许严格 master plan 闭合：`{strict_completion_allowed}`",
        "",
        "当前这份清单本身不代表真实资料已经到位，也不关闭严格 master plan。",
        "",
        "## 2. 仍打开的严格阻塞项",
        "",
    ]
    for blocker in blockers:
        lines.append(f"- `{blocker}`：{BLOCKER_CN.get(blocker, '待外部资料解除')}")

    lines.extend(
        [
            "",
            "## 3. 投递目录与文件",
            "",
            "操作原则：从 `template_path` 复制到 `target_path`，保留 JSON key 或 CSV 表头不改名，再把示例值替换为真实资料。",
            "",
        ]
    )
    for domain in domains:
        lines.extend(
            [
                f"### {domain['domain_cn']} (`{domain['domain']}`)",
                "",
                f"- 本类文件数：`{domain['required_file_count']}`",
                f"- 已存在：`{domain['present_file_count']}`",
                f"- 缺失：`{domain['missing_file_count']}`",
                "",
            ]
        )
        for item in domain["files"]:
            done = "已存在" if item["currently_present"] else "待投递"
            required = "必需" if item["required"] else "建议/可选但保留合同项"
            lines.extend(
                [
                    f"- `{item['label']}`：{done}，{required}，类型 `{item['kind']}`",
                    f"  - template_path：`{item['template_path']}`",
                    f"  - target_path：`{item['target_path']}`",
                ]
            )
            keys = json_key_text(item)
            header = csv_header_text(item)
            if keys:
                lines.append(f"  - JSON 必需 key：`{keys}`")
            if header:
                lines.append(f"  - CSV 表头：`{header}`")
        lines.append("")

    lines.extend(
        [
            "## 4. 投递后复验命令",
            "",
            "先运行轻量接收预检，确认真实资料路径、格式和当前状态链路都能通过；需要刷新完整当前阶段证据链时，再运行完整 release refresh。",
            "",
            "```bash",
            "cd /path/to/my-pele",
            "bash tools/run_strict_external_artifact_receiving_preflight.sh",
            "python3 tools/write_strict_external_artifact_receiving_preflight_entrypoint_report.py",
            "bash tools/verify_strict_external_artifact_receiving_preflight_entrypoint.sh",
            "",
            "# 一键入口内部会执行的关键合同检查包括：",
            "bash tools/verify_strict_artifact_drop_contract_preflight.sh",
            "",
            "# 如果需要刷新完整当前阶段证据链，再运行：",
            "python3 tools/write_strict_external_artifact_cn_handoff_report.py",
            "bash tools/verify_strict_external_artifact_cn_handoff.sh",
            "bash tools/run_current_scope_release_refresh.sh",
            "```",
            "",
            "## 5. 通过标准",
            "",
            "- `verify_strict_artifact_drop_contract_preflight.sh` 必须通过，证明目标文件存在且结构符合合同。",
            "- `run_strict_external_artifact_receiving_preflight.sh` 必须最终出现 `STRICT_EXTERNAL_ARTIFACT_RECEIVING_PREFLIGHT_RC=0`。",
            "- `run_current_scope_release_refresh.sh` 必须最终出现 `CURRENT_SCOPE_RC=0`。",
            "- 如果真实资料足以解除三个严格阻塞项，`strict_master_plan_completion_gate` 才能从等待外部资料进入可闭合状态。",
        ]
    )
    guide_path.parent.mkdir(parents=True, exist_ok=True)
    guide_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(guide_path: Path) -> dict[str, Any]:
    index = load_json(DROP_INDEX)
    receiving_pack = load_json(RECEIVING_PACK)
    index_summary = index["summary"]
    receiving_summary = receiving_pack["summary"]

    domains = normalize_domains(index)
    counts_by_domain = {domain["domain"]: domain["required_file_count"] for domain in domains}
    total_required = sum(domain["required_file_count"] for domain in domains)
    total_present = sum(domain["present_file_count"] for domain in domains)
    total_missing = sum(domain["missing_file_count"] for domain in domains)
    blockers = sorted(index_summary.get("open_strict_blockers", []))
    strict_completion_allowed = bool(index_summary.get("strict_completion_allowed"))

    ready = (
        index.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX"
        and receiving_pack.get("status") == "PASS-STRICT-EXTERNAL-EVIDENCE-RECEIVING-PACK"
        and index_summary.get("strict_external_artifact_drop_index_ready") is True
        and receiving_summary.get("strict_external_evidence_receiving_pack_ready") is True
        and counts_by_domain == EXPECTED_COUNTS
        and total_required == 14
        and total_present == receiving_summary.get("present_file_count")
        and total_missing == receiving_summary.get("missing_file_count")
        and len(blockers) == receiving_summary.get("open_strict_blocker_count")
        and set(blockers) == set(receiving_summary.get("open_strict_blockers", []))
    )
    require(ready, "strict external artifact handoff sources are inconsistent")

    write_chinese_guide(
        guide_path=guide_path,
        domains=domains,
        blockers=blockers,
        total_required=total_required,
        total_present=total_present,
        total_missing=total_missing,
        strict_completion_allowed=strict_completion_allowed,
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "Chinese operator handoff sheet for strict external CAD/plume/fire artifacts",
        "summary": {
            "strict_external_artifact_cn_handoff_ready": True,
            "domain_count": len(domains),
            "required_file_count": total_required,
            "present_file_count": total_present,
            "missing_file_count": total_missing,
            "counts_by_domain": counts_by_domain,
            "open_strict_blocker_count": len(blockers),
            "strict_completion_allowed": strict_completion_allowed,
            "guide_path": str(guide_path),
        },
        "handoff_domains": domains,
        "operator_commands": [
            "bash tools/run_strict_external_artifact_receiving_preflight.sh",
            "python3 tools/write_strict_external_artifact_receiving_preflight_entrypoint_report.py",
            "bash tools/verify_strict_external_artifact_receiving_preflight_entrypoint.sh",
            "python3 tools/write_strict_external_artifact_cn_handoff_report.py",
            "bash tools/verify_strict_external_artifact_cn_handoff.sh",
            "bash tools/run_current_scope_release_refresh.sh",
        ],
        "strict_boundary": {
            "does_not_mark_external_artifacts_complete": True,
            "does_not_allow_strict_master_plan_closure": total_missing > 0,
            "real_external_files_still_required": total_missing > 0,
        },
        "evidence_files": [
            evidence_entry("strict_external_artifact_drop_index", DROP_INDEX),
            evidence_entry("strict_external_evidence_receiving_pack", RECEIVING_PACK),
            evidence_entry("chinese_handoff_guide", guide_path),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_external_artifact_cn_handoff_ready") is True, "handoff is not ready")
    require(summary.get("domain_count") == 3, "unexpected domain count")
    require(summary.get("required_file_count") == 14, "unexpected required file count")
    require(summary.get("counts_by_domain") == EXPECTED_COUNTS, "unexpected domain counts")
    present = summary.get("present_file_count")
    missing = summary.get("missing_file_count")
    require(isinstance(present, int) and isinstance(missing, int), "present/missing counts must be integers")
    require(present + missing == 14, "present/missing counts do not add to contract total")
    blocker_count = summary.get("open_strict_blocker_count")
    require(
        isinstance(blocker_count, int) and 0 <= blocker_count <= 3,
        "open strict blocker count is outside the expected range",
    )
    guide_path = Path(str(summary.get("guide_path", "")))
    require(guide_path.is_file(), f"missing generated Chinese handoff guide: {guide_path}")
    guide_text = guide_path.read_text(encoding="utf-8")
    for required_text in [
        "## 1. 当前状态",
        "## 2. 仍打开的严格阻塞项",
        "## 3. 投递目录与文件",
        "## 4. 投递后复验命令",
        "bash tools/run_strict_external_artifact_receiving_preflight.sh",
        "bash tools/verify_strict_external_artifact_receiving_preflight_entrypoint.sh",
        "bash tools/verify_strict_artifact_drop_contract_preflight.sh",
        "bash tools/run_current_scope_release_refresh.sh",
    ]:
        require(required_text in guide_text, f"generated guide missing text: {required_text}")
    domains = data.get("handoff_domains")
    require(isinstance(domains, list) and len(domains) == 3, "invalid handoff domains")
    for domain in domains:
        require(domain.get("domain") in EXPECTED_COUNTS, "unexpected handoff domain")
        require(domain.get("required_file_count") == EXPECTED_COUNTS[domain["domain"]], "bad domain file count")
        files = domain.get("files")
        require(isinstance(files, list) and len(files) == domain.get("required_file_count"), "invalid files")
        for item in files:
            target = item.get("target_path")
            template = item.get("template_path")
            label = item.get("label")
            require(isinstance(target, str) and target in guide_text, f"guide missing target path for {label}")
            require(isinstance(template, str) and template in guide_text, f"guide missing template path for {label}")
    boundary = data.get("strict_boundary")
    require(isinstance(boundary, dict), "missing strict boundary")
    require(boundary.get("does_not_mark_external_artifacts_complete") is True, "handoff overclaims artifacts")
    if missing:
        require(boundary.get("real_external_files_still_required") is True, "missing files should keep requirement open")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence path: {path}")
            require(entry["sha256"] == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict External Artifact Chinese Handoff Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Guide: `{summary['guide_path']}`",
        f"- Domains: `{summary['domain_count']}`",
        f"- Required files: `{summary['required_file_count']}`",
        f"- Present files: `{summary['present_file_count']}`",
        f"- Missing files: `{summary['missing_file_count']}`",
        f"- Strict completion allowed: `{summary['strict_completion_allowed']}`",
        "",
        "## Commands",
        "",
        "```bash",
        *report["operator_commands"],
        "```",
        "",
        "## Domains",
        "",
    ]
    for domain in report["handoff_domains"]:
        lines.append(
            f"- `{domain['domain']}` `{domain['domain_cn']}` required={domain['required_file_count']} "
            f"present={domain['present_file_count']} missing={domain['missing_file_count']}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--guide", default=str(DEFAULT_GUIDE))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data)
        print(f"strict_external_artifact_cn_handoff VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0

    report = build_report(Path(args.guide))
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_external_artifact_cn_handoff PASS json={output_json} md={output_md} guide={args.guide}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
