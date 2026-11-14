#!/usr/bin/env python3
"""Write/verify a concise checklist for strict external artifact handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-CHECKLIST"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_external_artifact_drop_checklist_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_external_artifact_drop_checklist_report.md"

DROP_INDEX = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
    "strict_external_artifact_drop_index_report.json"
)

EXPECTED_COUNTS = {"external_plume": 5, "fire_calibration": 5, "real_cad": 4}


class DropChecklistError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DropChecklistError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DropChecklistError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DropChecklistError(f"invalid JSON evidence {path}: {exc}") from exc
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


def checklist_items(index: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for domain in index.get("domain_drop_index", []):
        domain_name = domain.get("domain")
        require(domain_name in EXPECTED_COUNTS, f"unexpected domain: {domain_name}")
        for check in domain.get("checks", []):
            items.append(
                {
                    "domain": domain_name,
                    "label": check.get("label"),
                    "target_path": check.get("target_path"),
                    "template_path": check.get("template_path"),
                    "kind": check.get("kind"),
                    "currently_present": check.get("currently_present"),
                    "done": check.get("currently_present") is True,
                    "operator_note": (
                        "Fill from template and replace placeholder/example values with real external evidence."
                    ),
                }
            )
    return sorted(items, key=lambda item: (str(item["domain"]), str(item["label"])))


def build_report(index_path: Path = DROP_INDEX) -> dict[str, Any]:
    index = load_json(index_path)
    summary = index["summary"]
    items = checklist_items(index)
    counts_by_domain: dict[str, int] = {}
    for item in items:
        counts_by_domain[item["domain"]] = counts_by_domain.get(item["domain"], 0) + 1

    ready = (
        index.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX"
        and summary.get("strict_external_artifact_drop_index_ready") is True
        and summary.get("strict_completion_allowed") is False
        and summary.get("domain_count") == 3
        and summary.get("contract_check_count") == 14
        and isinstance(summary.get("awaiting_missing_artifact_count"), int)
        and 0 <= summary.get("awaiting_missing_artifact_count") <= 14
        and counts_by_domain == EXPECTED_COUNTS
        and len(items) == 14
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "human-readable strict external artifact checklist derived from the verified drop index",
        "summary": {
            "strict_external_artifact_drop_checklist_ready": ready,
            "source_index_status": index.get("status"),
            "strict_completion_allowed": summary.get("strict_completion_allowed"),
            "domain_count": summary.get("domain_count"),
            "required_file_count": len(items),
            "missing_file_count": summary.get("awaiting_missing_artifact_count"),
            "counts_by_domain": counts_by_domain,
            "checklist_done_count": sum(1 for item in items if item["done"]),
        },
        "checklist_items": items,
        "usage": {
            "print_checklist": "python3 tools/codex_print_strict_external_artifact_drop_index.py",
            "verify_drop_contract": "bash tools/verify_strict_artifact_drop_contract_preflight.sh",
            "refresh_all_evidence": "bash tools/run_current_scope_release_refresh.sh",
        },
        "evidence_files": [evidence_entry("strict_external_artifact_drop_index", index_path)],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_external_artifact_drop_checklist_ready") is True, "checklist is not ready")
    require(summary.get("source_index_status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX", "source index not passing")
    require(summary.get("strict_completion_allowed") is False, "strict completion unexpectedly allowed")
    require(summary.get("domain_count") == 3, "unexpected domain count")
    require(summary.get("required_file_count") == 14, "unexpected checklist item count")
    missing_count = summary.get("missing_file_count")
    done_count = summary.get("checklist_done_count")
    require(isinstance(missing_count, int), "missing file count is not an integer")
    require(isinstance(done_count, int), "checklist done count is not an integer")
    require(0 <= missing_count <= 14, "missing file count is outside the contract range")
    require(0 <= done_count <= 14, "checklist done count is outside the contract range")
    require(missing_count + done_count == 14, "done and missing checklist counts do not match contract total")
    require(summary.get("counts_by_domain") == EXPECTED_COUNTS, "unexpected per-domain counts")
    items = data.get("checklist_items")
    require(isinstance(items, list) and len(items) == 14, "invalid checklist items")
    for item in items:
        require(item.get("target_path"), "missing target path")
        require(item.get("template_path"), "missing template path")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence path: {path}")
            require(entry["sha256"] == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict External Artifact Drop Checklist",
        "",
        f"- Status: `{report['status']}`",
        f"- Source index: `{summary['source_index_status']}`",
        f"- Domains: `{summary['domain_count']}`",
        f"- Required files: `{summary['required_file_count']}`",
        f"- Missing files: `{summary['missing_file_count']}`",
        f"- Strict completion allowed: `{summary['strict_completion_allowed']}`",
        "",
        "## Checklist",
        "",
    ]
    for item in report["checklist_items"]:
        marker = "x" if item["done"] else " "
        lines.append(f"- [{marker}] `{item['domain']}` / `{item['label']}`")
        lines.append(f"  - target: `{item['target_path']}`")
        lines.append(f"  - template: `{item['template_path']}`")
    lines.extend(
        [
            "",
            "## Commands",
            "",
            "```bash",
            report["usage"]["print_checklist"],
            report["usage"]["verify_drop_contract"],
            report["usage"]["refresh_all_evidence"],
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", default=str(DROP_INDEX))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data)
        print(f"strict_external_artifact_drop_checklist VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0

    report = build_report(Path(args.index))
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_external_artifact_drop_checklist PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
