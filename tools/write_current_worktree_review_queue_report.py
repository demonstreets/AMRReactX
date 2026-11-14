#!/usr/bin/env python3
"""Write/verify a non-destructive review queue for the current dirty worktree."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-WORKTREE-REVIEW-QUEUE"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_worktree_review_queue_20260820")
DEFAULT_JSON = DEFAULT_ROOT / "current_worktree_review_queue_report.json"
DEFAULT_MD = DEFAULT_ROOT / "current_worktree_review_queue_report.md"

SOURCE_LEDGER = Path(
    "docs/codex_audit/evidence/current_worktree_source_ledger_20260803/"
    "current_worktree_source_ledger_report.json"
)
CASE_OUTPUT_MANIFEST = Path(
    "docs/codex_audit/evidence/current_case_output_cleanup_manifest_20260803/"
    "current_case_output_cleanup_manifest_report.json"
)
CURRENT_STATUS = Path(
    "docs/codex_audit/evidence/current_status_cli_20260803/"
    "current_status_cli_report.json"
)
SUNDIALS_LOCAL_LINK_AUDIT = Path(
    "docs/codex_audit/evidence/sundials_local_link_audit_20260820/"
    "sundials_local_link_audit_report.json"
)


class ReviewQueueError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReviewQueueError(message)


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
        raise ReviewQueueError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReviewQueueError(f"invalid JSON evidence {path}: {exc}") from exc
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


def review_domain(path_text: str) -> str:
    parts = Path(path_text).parts
    if not parts:
        return "other"
    if len(parts) >= 2 and parts[0] == "examples" and parts[1] == "engineering":
        return "engineering_examples"
    if len(parts) >= 2 and parts[0] == "examples" and parts[1] == "academic":
        return "academic_examples"
    if parts[0] == "tools":
        return "tooling"
    if parts[0] == "docs":
        return "documentation_or_audit"
    if parts[0] == "external":
        return "external_dependency_or_mirror"
    if parts[0] in {"README.md", "PROGRESS.md", "AGENTS.md"}:
        return "root_handoff_docs"
    return "other"


def review_priority(entry: dict[str, Any]) -> str:
    category = str(entry.get("category", ""))
    path = str(entry.get("path", ""))
    xy = str(entry.get("xy", ""))
    if "D" in xy and category != "generated_or_case_output":
        return "P0"
    if path.startswith("external/") or category in {"source_or_config", "example_source_or_config"}:
        return "P1"
    if category == "tooling":
        return "P2"
    if category == "documentation":
        return "P3"
    return "P4"


def churn(entry: dict[str, Any]) -> int:
    stats = entry.get("diff_numstat")
    if not isinstance(stats, dict):
        return 0
    added = stats.get("added")
    deleted = stats.get("deleted")
    if not isinstance(added, int) or not isinstance(deleted, int):
        return 0
    return added + deleted


def tracked_mode(path_text: str) -> str:
    result = subprocess.run(
        ["git", "ls-files", "-s", "--", path_text],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        timeout=30,
    )
    first = result.stdout.strip().split(maxsplit=1)[0] if result.stdout.strip() else ""
    return first


def replacement_kind(path_text: str) -> str:
    path = Path(path_text)
    if path.is_symlink():
        return "symlink"
    if path.is_dir():
        return "directory"
    if path.is_file():
        return "file"
    if path.exists():
        return "other_existing_path"
    return "missing"


def risk_reason(entry: dict[str, Any], priority: str, mode: str, replacement: str) -> str:
    path = str(entry.get("path", ""))
    xy = str(entry.get("xy", ""))
    category = str(entry.get("category", ""))
    if mode == "120000" and "D" in xy and replacement == "directory":
        return "tracked_symlink_deleted_but_replacement_directory_present"
    if "D" in xy and category != "generated_or_case_output":
        return "tracked_non_generated_path_deleted_or_replaced"
    if path.startswith("external/"):
        return "external_dependency_or_mirror_change"
    if category in {"source_or_config", "example_source_or_config"}:
        return "source_or_input_change_requires_review"
    if category == "tooling":
        return "tooling_change_requires_review"
    if category == "documentation":
        return "documentation_or_handoff_change"
    return f"{priority.lower()}_review_item"


def queue_entry(entry: dict[str, Any]) -> dict[str, Any]:
    path_text = str(entry.get("path", ""))
    priority = review_priority(entry)
    mode = tracked_mode(path_text)
    replacement = replacement_kind(path_text)
    item = {
        "path": entry.get("path"),
        "xy": entry.get("xy"),
        "category": entry.get("category"),
        "domain": review_domain(path_text),
        "priority": priority,
        "risk_reason": risk_reason(entry, priority, mode, replacement),
        "tracked_mode": mode,
        "replacement_kind": replacement,
        "exists": entry.get("exists"),
        "size_bytes": entry.get("size_bytes"),
        "diff_numstat": entry.get("diff_numstat"),
        "churn": churn(entry),
    }
    if entry.get("sha256"):
        item["sha256"] = entry.get("sha256")
    return item


def build_report() -> dict[str, Any]:
    ledger = load_json(SOURCE_LEDGER)
    cleanup = load_json(CASE_OUTPUT_MANIFEST)
    status = load_json(CURRENT_STATUS)
    sundials_audit = load_json(SUNDIALS_LOCAL_LINK_AUDIT)

    ledger_summary = ledger.get("summary", {})
    cleanup_summary = cleanup.get("summary", {})
    status_summary = status.get("summary", {})
    sundials_summary = sundials_audit.get("summary", {})
    require(isinstance(ledger_summary, dict), "missing source ledger summary")
    require(isinstance(cleanup_summary, dict), "missing cleanup manifest summary")
    require(isinstance(status_summary, dict), "missing status summary")
    require(isinstance(sundials_summary, dict), "missing SUNDIALS local link audit summary")

    high_attention = ledger.get("high_attention_entries")
    ledger_entries = ledger.get("ledger_entries")
    require(isinstance(high_attention, list), "missing high attention entries")
    require(isinstance(ledger_entries, list), "missing ledger entries")

    queue = [queue_entry(item) for item in high_attention]
    by_domain = Counter(str(item["domain"]) for item in queue)
    by_priority = Counter(str(item["priority"]) for item in queue)
    by_category = Counter(str(item["category"]) for item in queue)
    by_risk_reason = Counter(str(item["risk_reason"]) for item in queue)
    top_churn = sorted(queue, key=lambda item: (-int(item.get("churn", 0)), str(item.get("path", ""))))[:40]
    external_dependency_link_drift_count = by_risk_reason.get(
        "tracked_symlink_deleted_but_replacement_directory_present", 0
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS,
        "scope": "non-destructive dirty-worktree review queue",
        "summary": {
            "review_queue_ready": True,
            "review_queue_policy": "non-destructive; review classification only; no cleanup/stage/restore/ignore",
            "cleanup_performed": False,
            "source_ledger_status": ledger.get("status"),
            "case_output_cleanup_manifest_status": cleanup.get("status"),
            "current_status_cli_status": status.get("status"),
            "goal_complete": status_summary.get("goal_complete"),
            "open_strict_blocker_count": status_summary.get("open_strict_blocker_count"),
            "ledger_entry_count": ledger_summary.get("ledger_entry_count"),
            "high_attention_entry_count": ledger_summary.get("high_attention_ledger_entry_count"),
            "generated_or_case_output_excluded_count": ledger_summary.get(
                "generated_or_case_output_excluded_count"
            ),
            "case_output_cleanup_candidate_root_count": cleanup_summary.get("cleanup_candidate_root_count"),
            "case_output_existing_candidate_root_count": cleanup_summary.get("existing_candidate_root_count"),
            "review_domain_count": len(by_domain),
            "review_priority_count": len(by_priority),
            "external_dependency_link_drift_count": external_dependency_link_drift_count,
            "sundials_local_link_audit_status": sundials_audit.get("status"),
            "sundials_local_link_audit_ready": sundials_summary.get("audit_ready"),
            "sundials_local_link_drift_present": sundials_summary.get("local_link_drift_present"),
            "sundials_local_link_current_kind": sundials_summary.get("current_replacement_kind"),
            "sundials_local_link_safe_to_auto_restore": sundials_summary.get("safe_to_auto_restore"),
            "sundials_restore_requires_explicit_operator_review": sundials_summary.get(
                "restore_requires_explicit_operator_review"
            ),
            "top_churn_entry_count": len(top_churn),
            "review_required_before_packaging": len(queue) > 0,
        },
        "counts": {
            "by_domain": dict(sorted(by_domain.items())),
            "by_priority": dict(sorted(by_priority.items())),
            "by_category": dict(sorted(by_category.items())),
            "by_risk_reason": dict(sorted(by_risk_reason.items())),
        },
        "review_queue": queue,
        "top_churn_entries": top_churn,
        "operator_guidance": [
            "Review P0/P1 entries before packaging or handing off source changes.",
            "Treat generated/case-output cleanup candidates separately from source review.",
            "Do not delete, restore, stage, or ignore files from this report alone.",
            "Run the source ledger and cleanup manifest again after any manual cleanup.",
        ],
        "evidence_files": [
            evidence_entry("current_worktree_source_ledger", SOURCE_LEDGER),
            evidence_entry("current_case_output_cleanup_manifest", CASE_OUTPUT_MANIFEST),
            evidence_entry("current_status_cli", CURRENT_STATUS),
            evidence_entry("sundials_local_link_audit", SUNDIALS_LOCAL_LINK_AUDIT),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("review_queue_ready") is True, "review queue is not ready")
    require(summary.get("cleanup_performed") is False, "review queue must be non-destructive")
    require(summary.get("source_ledger_status") == "AUDITED-CURRENT-WORKTREE-SOURCE-LEDGER", "bad source ledger")
    require(
        summary.get("case_output_cleanup_manifest_status") == "AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST",
        "bad cleanup manifest",
    )
    require(summary.get("current_status_cli_status") == "PASS-CURRENT-STATUS-CLI", "bad current status")
    require(summary.get("sundials_local_link_audit_status") == "PASS-SUNDIALS-LOCAL-LINK-AUDIT", "bad SUNDIALS audit")
    require(summary.get("sundials_local_link_audit_ready") is True, "SUNDIALS audit not ready")
    require(summary.get("sundials_local_link_safe_to_auto_restore") is False, "SUNDIALS auto-restore guard missing")
    require(
        summary.get("sundials_restore_requires_explicit_operator_review") is True,
        "SUNDIALS explicit-review guard missing",
    )
    high_attention_count = summary.get("high_attention_entry_count")
    require(isinstance(high_attention_count, int) and high_attention_count > 0, "missing high attention count")
    queue = data.get("review_queue")
    require(isinstance(queue, list), "missing review queue")
    require(len(queue) == high_attention_count, "review queue count mismatch")
    require(summary.get("review_required_before_packaging") is True, "review-required flag missing")
    counts = data.get("counts")
    require(isinstance(counts, dict), "missing counts")
    by_priority = counts.get("by_priority")
    require(isinstance(by_priority, dict), "missing priority counts")
    require(any(key in by_priority for key in ("P0", "P1")), "no high-priority entries found")
    for item in queue:
        require(isinstance(item, dict), "invalid review queue item")
        require(isinstance(item.get("risk_reason"), str) and item["risk_reason"], "missing risk reason")
    if "P0" in by_priority:
        require(
            int(summary.get("external_dependency_link_drift_count", 0)) >= 1
            or any(item.get("priority") == "P0" and item.get("risk_reason") for item in queue),
            "P0 entries are not explained",
        )
    top_churn = data.get("top_churn_entries")
    require(isinstance(top_churn, list) and len(top_churn) > 0, "missing top churn entries")
    guidance = data.get("operator_guidance")
    require(isinstance(guidance, list), "missing operator guidance")
    require(any("Do not delete" in item for item in guidance), "missing non-destructive guidance")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence path: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    counts = report["counts"]
    lines = [
        "# Current Worktree Review Queue",
        "",
        f"- Status: `{report['status']}`",
        f"- Ready: `{summary['review_queue_ready']}`",
        f"- Policy: `{summary['review_queue_policy']}`",
        f"- Ledger entries: `{summary['ledger_entry_count']}`",
        f"- High-attention entries: `{summary['high_attention_entry_count']}`",
        f"- Generated/case-output entries excluded: `{summary['generated_or_case_output_excluded_count']}`",
        f"- Cleanup candidate roots: `{summary['case_output_cleanup_candidate_root_count']}`",
        f"- Existing cleanup candidate roots: `{summary['case_output_existing_candidate_root_count']}`",
        f"- External dependency link drifts: `{summary['external_dependency_link_drift_count']}`",
        f"- SUNDIALS local link audit: `{summary['sundials_local_link_audit_status']}`",
        f"- SUNDIALS local link drift present: `{summary['sundials_local_link_drift_present']}`",
        f"- SUNDIALS current link kind: `{summary['sundials_local_link_current_kind']}`",
        f"- SUNDIALS safe to auto-restore: `{summary['sundials_local_link_safe_to_auto_restore']}`",
        f"- Review required before packaging: `{summary['review_required_before_packaging']}`",
        "",
        "## Priority Counts",
        "",
    ]
    for key, value in counts["by_priority"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Domain Counts", ""])
    for key, value in counts["by_domain"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Risk Reasons", ""])
    for key, value in counts["by_risk_reason"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Top Churn Entries", ""])
    for item in report["top_churn_entries"][:25]:
        lines.append(
            f"- `{item['priority']}` `{item['domain']}` `{item['xy']}` "
            f"churn=`{item['churn']}` reason=`{item['risk_reason']}` `{item['path']}`"
        )
    lines.extend(["", "## Operator Guidance", ""])
    for item in report["operator_guidance"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"current_worktree_review_queue VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_worktree_review_queue PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
