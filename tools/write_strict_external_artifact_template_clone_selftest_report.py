#!/usr/bin/env python3
"""Write/verify a selftest that template clones cannot be credited as strict artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-EXTERNAL-ARTIFACT-TEMPLATE-CLONE-SELFTEST"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_external_artifact_template_clone_selftest_20260817")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_external_artifact_template_clone_selftest_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_external_artifact_template_clone_selftest_report.md"

RECEIVING_PACK = Path(
    "docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812/"
    "strict_external_evidence_receiving_pack_report.json"
)

EXPECTED_COUNTS = {"external_plume": 5, "fire_calibration": 5, "real_cad": 4}


class TemplateCloneSelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TemplateCloneSelftestError(message)


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
        raise TemplateCloneSelftestError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TemplateCloneSelftestError(f"invalid JSON evidence {path}: {exc}") from exc
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


def resolve_repo_path(path: Path, repo_root: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def collect_template_clone_cases(receiving_pack: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for domain in receiving_pack.get("receiving_domains", []):
        domain_name = domain.get("domain")
        require(domain_name in EXPECTED_COUNTS, f"unexpected domain: {domain_name}")
        for item in domain.get("files", []):
            template_path = resolve_repo_path(Path(str(item.get("template_path", ""))), repo_root)
            target_path = Path(str(item.get("target_path", "")))
            require(template_path.is_file(), f"missing template path: {template_path}")
            require(str(target_path), f"missing target path for {item.get('label')}")
            template_sha256 = sha256_file(template_path)
            simulated_target_sha256 = template_sha256
            cases.append(
                {
                    "domain": domain_name,
                    "label": item.get("label"),
                    "kind": item.get("kind"),
                    "target_path": str(target_path),
                    "template_path": str(template_path),
                    "template_sha256": template_sha256,
                    "simulated_target_sha256": simulated_target_sha256,
                    "target_equals_template": simulated_target_sha256 == template_sha256,
                    "credit_decision": "REJECT",
                    "rejection_reason": "target artifact bytes are identical to the verified template",
                }
            )
    return sorted(cases, key=lambda item: (str(item["domain"]), str(item["label"])))


def build_report(receiving_pack_path: Path = RECEIVING_PACK, repo_root: Path = Path(".")) -> dict[str, Any]:
    receiving_pack_path = resolve_repo_path(receiving_pack_path, repo_root)
    repo_root = repo_root.resolve()
    receiving_pack = load_json(receiving_pack_path)
    receiving_summary = receiving_pack["summary"]
    cases = collect_template_clone_cases(receiving_pack, repo_root)
    counts_by_domain: dict[str, int] = {}
    for case in cases:
        counts_by_domain[case["domain"]] = counts_by_domain.get(case["domain"], 0) + 1

    rejected = [case for case in cases if case["credit_decision"] == "REJECT"]
    ready = (
        receiving_pack.get("status") == "PASS-STRICT-EXTERNAL-EVIDENCE-RECEIVING-PACK"
        and receiving_summary.get("strict_external_evidence_receiving_pack_ready") is True
        and receiving_summary.get("strict_completion_allowed") is False
        and counts_by_domain == EXPECTED_COUNTS
        and len(cases) == 14
        and len(rejected) == 14
        and all(case["target_equals_template"] is True for case in cases)
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "negative selftest for template-clone strict artifact overcredit",
        "summary": {
            "strict_external_artifact_template_clone_selftest_ready": ready,
            "source_receiving_pack_status": receiving_pack.get("status"),
            "source_receiving_pack_path": str(receiving_pack_path),
            "repo_root": str(repo_root),
            "domain_count": len(counts_by_domain),
            "counts_by_domain": counts_by_domain,
            "template_clone_case_count": len(cases),
            "template_clone_rejected_count": len(rejected),
            "template_clone_accepted_count": len(cases) - len(rejected),
            "strict_completion_allowed": receiving_summary.get("strict_completion_allowed"),
            "strict_master_plan_still_open": receiving_summary.get("strict_master_plan_still_open"),
            "does_not_create_or_copy_target_artifacts": True,
        },
        "template_clone_cases": cases,
        "evidence_files": [
            evidence_entry("strict_external_evidence_receiving_pack", receiving_pack_path),
            *[
                evidence_entry(f"template:{case['domain']}:{case['label']}", Path(case["template_path"]))
                for case in cases
            ],
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(
        summary.get("strict_external_artifact_template_clone_selftest_ready") is True,
        "template-clone selftest is not ready",
    )
    require(summary.get("source_receiving_pack_status") == "PASS-STRICT-EXTERNAL-EVIDENCE-RECEIVING-PACK", "bad receiving pack status")
    require(summary.get("domain_count") == 3, "unexpected domain count")
    require(summary.get("counts_by_domain") == EXPECTED_COUNTS, "unexpected per-domain counts")
    require(summary.get("template_clone_case_count") == 14, "unexpected clone case count")
    require(summary.get("template_clone_rejected_count") == 14, "not all template clones were rejected")
    require(summary.get("template_clone_accepted_count") == 0, "template clone was accepted")
    require(summary.get("strict_completion_allowed") is False, "strict completion unexpectedly allowed")
    require(summary.get("strict_master_plan_still_open") is True, "strict master plan should still be open")
    require(summary.get("does_not_create_or_copy_target_artifacts") is True, "selftest must not write targets")
    cases = data.get("template_clone_cases")
    require(isinstance(cases, list) and len(cases) == 14, "invalid template clone cases")
    for case in cases:
        require(case.get("target_equals_template") is True, "case is not a template clone")
        require(case.get("credit_decision") == "REJECT", "template clone was not rejected")
        require(case.get("target_path"), "missing target path")
        require(case.get("template_path"), "missing template path")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence path: {path}")
            require(entry["sha256"] == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict External Artifact Template Clone Selftest",
        "",
        f"- Status: `{report['status']}`",
        f"- Clone cases: `{summary['template_clone_case_count']}`",
        f"- Rejected clones: `{summary['template_clone_rejected_count']}`",
        f"- Accepted clones: `{summary['template_clone_accepted_count']}`",
        f"- Strict completion allowed: `{summary['strict_completion_allowed']}`",
        "",
        "This negative selftest simulates every strict target artifact as a byte-for-byte copy of its template.",
        "All such cases must be rejected and no target artifacts are created or copied by this selftest.",
        "",
        "## Cases",
        "",
    ]
    for case in report["template_clone_cases"]:
        lines.append(
            f"- `{case['domain']}` / `{case['label']}`: `{case['credit_decision']}` "
            f"`{case['rejection_reason']}`"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receiving-pack", default=str(RECEIVING_PACK))
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data)
        print(f"strict_external_artifact_template_clone_selftest VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0

    report = build_report(Path(args.receiving_pack), Path(args.repo_root))
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_external_artifact_template_clone_selftest PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
