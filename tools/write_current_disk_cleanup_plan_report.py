#!/usr/bin/env python3
"""Write/verify a dry-run disk cleanup decision plan."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_AUDITED = "AUDITED-CURRENT-DISK-CLEANUP-PLAN"
STATUS_NOT_READY = "NOT_READY-CURRENT-DISK-CLEANUP-PLAN"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_disk_cleanup_plan_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_disk_cleanup_plan_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_disk_cleanup_plan_report.md"

DISK_USAGE_MANIFEST = Path(
    "docs/codex_audit/evidence/current_disk_usage_manifest_20260803/"
    "current_disk_usage_manifest_report.json"
)
CASE_OUTPUT_MANIFEST = Path(
    "docs/codex_audit/evidence/current_case_output_cleanup_manifest_20260803/"
    "current_case_output_cleanup_manifest_report.json"
)

HIGH_VALUE_EXAMPLE_DIRS = (
    "examples/academic/bench_1gpu_znd",
    "examples/academic/bench_1gpu",
    "examples/academic/bench_1gpu_nn_A",
    "examples/academic/bench_cpu16",
)


class CleanupPlanError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CleanupPlanError(message)


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
        raise CleanupPlanError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CleanupPlanError(f"invalid JSON evidence {path}: {exc}") from exc
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


def candidate_kind(item: dict[str, Any]) -> str:
    path = str(item["path"])
    category = str(item["category"])
    if category == "protected_audit_evidence" or path.startswith("docs/codex_audit/evidence"):
        return "protected_evidence"
    if path in {"build-gpu2", "build-gpu-mpi"} or category == "build_artifact":
        return "rebuildable_build_tree"
    if path == "test/gpu_correctness" or category == "test_output_or_artifact":
        return "test_output_tree"
    if path in HIGH_VALUE_EXAMPLE_DIRS:
        return "plotfile_heavy_example_output"
    if category == "case_output":
        return "case_output_file_or_tree"
    if category == "case_executable":
        return "rebuildable_case_executable"
    return "review_only"


def cleanup_stage(kind: str) -> str:
    if kind == "protected_evidence":
        return "protect"
    if kind in {"rebuildable_build_tree", "test_output_tree"}:
        return "stage_1_lowest_risk_after_rebuild_checks"
    if kind in {"plotfile_heavy_example_output", "case_output_file_or_tree"}:
        return "stage_2_case_output_after_evidence_export"
    if kind == "rebuildable_case_executable":
        return "stage_3_after_rebuild_recipe_verified"
    return "review_only"


def risk_level(kind: str) -> str:
    if kind == "protected_evidence":
        return "protected_do_not_delete"
    if kind in {"rebuildable_build_tree", "test_output_tree"}:
        return "low_to_medium"
    if kind in {"plotfile_heavy_example_output", "case_output_file_or_tree"}:
        return "medium"
    if kind == "rebuildable_case_executable":
        return "medium_to_high"
    return "unknown_review_required"


def build_candidates(disk: dict[str, Any]) -> list[dict[str, Any]]:
    by_path = {item["path"]: item for item in disk["top_directories"]}
    candidates: list[dict[str, Any]] = []

    preferred_paths = [
        "test/gpu_correctness",
        "build-gpu2",
        "build-gpu-mpi",
        *HIGH_VALUE_EXAMPLE_DIRS,
        "examples/engineering/h2_leak_3d",
        "examples/academic/detonation_znd_gpu",
    ]

    for path in preferred_paths:
        item = by_path.get(path)
        if not item:
            continue
        kind = candidate_kind(item)
        candidates.append(
            {
                "path": path,
                "kind": kind,
                "size_kib": item["size_kib"],
                "size_mib": item["size_mib"],
                "cleanup_stage": cleanup_stage(kind),
                "risk_level": risk_level(kind),
                "manual_approval_required": True,
                "cleanup_performed": False,
                "preconditions": [
                    "rerun bash tools/codex_verify_current_scope.sh before cleanup",
                    "confirm no running CFD job is writing this path",
                    "preserve required logs/reports/inputs before deletion",
                ],
            }
        )

    protected = by_path.get("docs/codex_audit/evidence")
    if protected:
        candidates.append(
            {
                "path": "docs/codex_audit/evidence",
                "kind": "protected_evidence",
                "size_kib": protected["size_kib"],
                "size_mib": protected["size_mib"],
                "cleanup_stage": "protect",
                "risk_level": "protected_do_not_delete",
                "manual_approval_required": True,
                "cleanup_performed": False,
                "preconditions": [
                    "export or replace evidence chain before considering cleanup",
                    "do not include in routine disk cleanup",
                ],
            }
        )

    return candidates


def build_report() -> dict[str, Any]:
    disk = load_json(DISK_USAGE_MANIFEST)
    case_manifest = load_json(CASE_OUTPUT_MANIFEST)
    candidates = build_candidates(disk)

    actionable = [c for c in candidates if c["cleanup_stage"] != "protect"]
    stage_1 = [c for c in candidates if c["cleanup_stage"] == "stage_1_lowest_risk_after_rebuild_checks"]
    stage_2 = [c for c in candidates if c["cleanup_stage"] == "stage_2_case_output_after_evidence_export"]
    protected = [c for c in candidates if c["cleanup_stage"] == "protect"]

    estimated_reclaim_kib = sum(int(c["size_kib"]) for c in actionable)
    stage_1_reclaim_kib = sum(int(c["size_kib"]) for c in stage_1)
    stage_2_reclaim_kib = sum(int(c["size_kib"]) for c in stage_2)

    disk_ok = (
        disk.get("status") == "AUDITED-CURRENT-DISK-USAGE-MANIFEST"
        and disk.get("summary", {}).get("cleanup_performed") is False
    )
    case_ok = (
        case_manifest.get("status") == "AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST"
        and case_manifest.get("summary", {}).get("cleanup_performed") is False
    )
    ready = disk_ok and case_ok and len(candidates) > 0 and len(protected) > 0

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_AUDITED if ready else STATUS_NOT_READY,
        "summary": {
            "disk_cleanup_plan_audited": ready,
            "cleanup_performed": False,
            "cleanup_policy": "decision plan only; no files are deleted, restored, staged, or ignored",
            "candidate_count": len(candidates),
            "actionable_candidate_count": len(actionable),
            "protected_candidate_count": len(protected),
            "estimated_actionable_reclaim_kib": estimated_reclaim_kib,
            "stage_1_reclaim_kib": stage_1_reclaim_kib,
            "stage_2_reclaim_kib": stage_2_reclaim_kib,
            "disk_usage_manifest_status": disk.get("status"),
            "case_output_cleanup_manifest_status": case_manifest.get("status"),
            "repo_size_kib": disk.get("summary", {}).get("repo_size_kib"),
        },
        "cleanup_candidates": candidates,
        "required_before_any_cleanup": [
            "obtain explicit user approval for concrete paths",
            "run bash tools/codex_verify_current_scope.sh immediately before cleanup",
            "stop active CFD jobs that may write candidate paths",
            "preserve audit evidence and current input decks needed for reproducibility",
            "after cleanup, regenerate disk usage, cleanup plan, state snapshot, and PROGRESS evidence",
        ],
        "explicitly_protected": [
            "docs/codex_audit/evidence",
            "docs/codex_audit/current_scope_operator_runbook.md",
            "PROGRESS.md",
            "README.md",
        ],
        "evidence_files": [
            evidence_entry("current_disk_usage_manifest_report", DISK_USAGE_MANIFEST),
            evidence_entry("current_case_output_cleanup_manifest_report", CASE_OUTPUT_MANIFEST),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_AUDITED, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("disk_cleanup_plan_audited") is True, "disk cleanup plan was not audited")
    require(summary.get("cleanup_performed") is False, "disk cleanup plan must be non-destructive")
    require(summary.get("candidate_count", 0) > 0, "cleanup plan has no candidates")
    require(summary.get("protected_candidate_count", 0) > 0, "cleanup plan has no protected evidence candidate")
    require(summary.get("disk_usage_manifest_status") == "AUDITED-CURRENT-DISK-USAGE-MANIFEST", "disk usage manifest is not passing")
    require(summary.get("case_output_cleanup_manifest_status") == "AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST", "case-output cleanup manifest is not passing")
    for candidate in data.get("cleanup_candidates", []):
        require(candidate.get("manual_approval_required") is True, "cleanup candidate does not require manual approval")
        require(candidate.get("cleanup_performed") is False, "cleanup candidate was marked as performed")
    protected = [c for c in data.get("cleanup_candidates", []) if c.get("cleanup_stage") == "protect"]
    require(any(c.get("path") == "docs/codex_audit/evidence" for c in protected), "audit evidence is not explicitly protected")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current Disk Cleanup Plan",
        "",
        f"- Status: `{report['status']}`",
        f"- Candidate count: `{summary['candidate_count']}`",
        f"- Actionable candidates: `{summary['actionable_candidate_count']}`",
        f"- Protected candidates: `{summary['protected_candidate_count']}`",
        f"- Estimated actionable reclaim KiB: `{summary['estimated_actionable_reclaim_kib']}`",
        f"- Stage 1 reclaim KiB: `{summary['stage_1_reclaim_kib']}`",
        f"- Stage 2 reclaim KiB: `{summary['stage_2_reclaim_kib']}`",
        f"- Cleanup performed: `{summary['cleanup_performed']}`",
        "",
        "## Candidates",
        "",
    ]
    for item in report["cleanup_candidates"]:
        lines.append(
            f"- `{item['path']}` size_mib=`{item['size_mib']}` stage=`{item['cleanup_stage']}` risk=`{item['risk_level']}`"
        )
    lines.extend(["", "## Required Before Any Cleanup", ""])
    for item in report["required_before_any_cleanup"]:
        lines.append(f"- {item}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"current_disk_cleanup_plan VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_disk_cleanup_plan PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
