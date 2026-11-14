#!/usr/bin/env python3
"""Write/verify a phase acceptance gate for current closeout versus strict completion."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/project_closeout_acceptance_gate_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "project_closeout_acceptance_gate_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "project_closeout_acceptance_gate_report.md"

CLOSEOUT_FORECAST = Path(
    "docs/codex_audit/evidence/project_closeout_forecast_20260812/project_closeout_forecast_report.json"
)
DELIVERY_PACKAGE = Path(
    "docs/codex_audit/evidence/current_scope_delivery_package_20260812/current_scope_delivery_package_report.json"
)
STRICT_COMPLETION_GATE = Path(
    "docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812/"
    "strict_master_plan_completion_gate_report.json"
)
STRICT_DROP_INDEX = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
    "strict_external_artifact_drop_index_report.json"
)
STRICT_DROP_CHECKLIST = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812/"
    "strict_external_artifact_drop_checklist_report.json"
)
STRICT_PROGRESS_SELFTEST = Path(
    "docs/codex_audit/evidence/strict_external_artifact_progress_selftest_20260812/"
    "strict_external_artifact_progress_selftest_report.json"
)
CURRENT_STATUS = Path("docs/codex_audit/evidence/current_status_cli_20260803/current_status_cli_report.json")


class AcceptanceGateError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AcceptanceGateError(message)


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
        raise AcceptanceGateError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AcceptanceGateError(f"invalid JSON evidence {path}: {exc}") from exc
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


def required_artifact_rows(drop_index: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for domain in drop_index.get("domain_drop_index", []):
        domain_name = domain.get("domain")
        for check in domain.get("checks", []):
            rows.append(
                {
                    "domain": domain_name,
                    "label": check.get("label"),
                    "kind": check.get("kind"),
                    "required": check.get("required"),
                    "currently_present": check.get("currently_present"),
                    "target_path": check.get("target_path"),
                    "template_path": check.get("template_path"),
                }
            )
    return rows


def build_report() -> dict[str, Any]:
    closeout = load_json(CLOSEOUT_FORECAST)
    delivery = load_json(DELIVERY_PACKAGE)
    strict_gate = load_json(STRICT_COMPLETION_GATE)
    drop_index = load_json(STRICT_DROP_INDEX)
    drop_checklist = load_json(STRICT_DROP_CHECKLIST)
    progress_selftest = load_json(STRICT_PROGRESS_SELFTEST)
    current_status = load_json(CURRENT_STATUS)

    closeout_summary = closeout["summary"]
    delivery_summary = delivery["summary"]
    strict_summary = strict_gate["summary"]
    drop_index_summary = drop_index["summary"]
    checklist_summary = drop_checklist["summary"]
    progress_summary = progress_selftest["summary"]
    status_summary = current_status["summary"]

    checklist_done = checklist_summary.get("checklist_done_count")
    checklist_missing = checklist_summary.get("missing_file_count")
    open_blockers = set(strict_summary.get("open_strict_blockers", []))
    strict_completion_allowed = strict_summary.get("strict_master_plan_completion_allowed") is True
    current_phase_acceptance_allowed = all(
        [
            closeout.get("status") == "PASS-PROJECT-CLOSEOUT-FORECAST",
            closeout_summary.get("current_scope_can_be_closed_now") is True,
            delivery.get("status") == "PASS-CURRENT-SCOPE-DELIVERY-PACKAGE",
            delivery_summary.get("current_scope_delivery_package_ready") is True,
            delivery_summary.get("last_full_current_scope_log_passed") is True,
            strict_summary.get("current_scope_closure_allowed") is True,
            progress_summary.get("strict_external_artifact_progress_selftest_ready") is True,
        ]
    )
    strict_final_acceptance_allowed = all(
        [
            strict_completion_allowed,
            checklist_done == 14,
            checklist_missing == 0,
            not open_blockers,
            drop_index_summary.get("present_contract_artifact_count") == 14,
            drop_index_summary.get("awaiting_missing_artifact_count") == 0,
        ]
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "machine-verifiable acceptance boundary for current phase closeout and strict master-plan completion",
        "summary": {
            "project_closeout_acceptance_gate_ready": True,
            "current_phase_acceptance_allowed": current_phase_acceptance_allowed,
            "current_phase_acceptance_basis": "current-scope delivery package, full verification log, and closeout forecast are passing",
            "current_scope_closeout_estimate": closeout_summary.get("current_scope_closeout_estimate"),
            "strict_final_acceptance_allowed": strict_final_acceptance_allowed,
            "strict_final_acceptance_basis": "requires strict completion gate allowed, zero open strict blockers, and all external artifacts present",
            "strict_closeout_estimate_after_artifacts": closeout_summary.get("strict_closeout_estimate_after_artifacts"),
            "strict_master_plan_completion_allowed": strict_completion_allowed,
            "strict_master_plan_completion_gate_status": strict_gate.get("status"),
            "strict_external_artifact_required_file_count": checklist_summary.get("required_file_count"),
            "strict_external_artifact_done_count": checklist_done,
            "strict_external_artifact_missing_count": checklist_missing,
            "strict_external_artifact_present_index_count": drop_index_summary.get("present_contract_artifact_count"),
            "strict_external_artifact_awaiting_index_count": drop_index_summary.get("awaiting_missing_artifact_count"),
            "strict_external_artifact_progress_selftest_ready": progress_summary.get(
                "strict_external_artifact_progress_selftest_ready"
            ),
            "open_strict_blocker_count": strict_summary.get("open_strict_blocker_count"),
            "open_strict_blockers": sorted(open_blockers),
            "current_status_cli_status": current_status.get("status"),
            "current_status_cli_seen_open_strict_blocker_count": status_summary.get("open_strict_blocker_count"),
        },
        "acceptance_decision": {
            "current_phase": "ACCEPTABLE_TO_CLOSE" if current_phase_acceptance_allowed else "DO_NOT_CLOSE",
            "strict_master_plan": "ACCEPTABLE_TO_CLOSE" if strict_final_acceptance_allowed else "AWAITING_EXTERNAL_ARTIFACTS",
            "non_overclaim_rule": "do not mark the active goal complete while strict_final_acceptance_allowed is false",
        },
        "strict_final_acceptance_requirements": [
            {
                "requirement": "all_external_artifacts_present",
                "current_state": f"{checklist_done}/14 done, {checklist_missing}/14 missing",
                "evidence": str(STRICT_DROP_CHECKLIST),
            },
            {
                "requirement": "strict_completion_gate_allowed",
                "current_state": strict_gate.get("status"),
                "evidence": str(STRICT_COMPLETION_GATE),
            },
            {
                "requirement": "zero_open_strict_blockers",
                "current_state": sorted(open_blockers),
                "evidence": str(STRICT_COMPLETION_GATE),
            },
        ],
        "required_external_artifacts": required_artifact_rows(drop_index),
        "evidence_files": [
            evidence_entry("project_closeout_forecast", CLOSEOUT_FORECAST),
            evidence_entry("current_scope_delivery_package", DELIVERY_PACKAGE),
            evidence_entry("strict_master_plan_completion_gate", STRICT_COMPLETION_GATE),
            evidence_entry("strict_external_artifact_drop_index", STRICT_DROP_INDEX),
            evidence_entry("strict_external_artifact_drop_checklist", STRICT_DROP_CHECKLIST),
            evidence_entry("strict_external_artifact_progress_selftest", STRICT_PROGRESS_SELFTEST),
            evidence_entry("current_status_cli", CURRENT_STATUS),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("project_closeout_acceptance_gate_ready") is True, "acceptance gate is not ready")
    require(summary.get("current_phase_acceptance_allowed") is True, "current phase is not acceptable to close")
    strict_final_allowed = summary.get("strict_final_acceptance_allowed")
    strict_completion_allowed = summary.get("strict_master_plan_completion_allowed")
    require(isinstance(strict_final_allowed, bool), "strict final acceptance flag is not boolean")
    require(isinstance(strict_completion_allowed, bool), "strict completion flag is not boolean")
    required = summary.get("strict_external_artifact_required_file_count")
    done = summary.get("strict_external_artifact_done_count")
    missing = summary.get("strict_external_artifact_missing_count")
    present = summary.get("strict_external_artifact_present_index_count")
    awaiting = summary.get("strict_external_artifact_awaiting_index_count")
    require(required == 14, "unexpected required artifact count")
    for label, value in [("done", done), ("missing", missing), ("present", present), ("awaiting", awaiting)]:
        require(isinstance(value, int), f"{label} artifact count is not an integer")
        require(0 <= value <= 14, f"{label} artifact count is outside contract range")
    require(done + missing == 14, "checklist done/missing counts do not sum to 14")
    require(present + awaiting == 14, "drop index present/awaiting counts do not sum to 14")
    require(summary.get("strict_external_artifact_progress_selftest_ready") is True, "progress selftest is not ready")
    blocker_count = summary.get("open_strict_blocker_count")
    blockers = summary.get("open_strict_blockers", [])
    require(isinstance(blocker_count, int), "strict blocker count is not an integer")
    require(0 <= blocker_count <= 3, "strict blocker count is outside expected closure range")
    require(isinstance(blockers, list) and len(blockers) == blocker_count, "strict blockers are not enumerated")
    decision = data.get("acceptance_decision", {})
    require(decision.get("current_phase") == "ACCEPTABLE_TO_CLOSE", "current phase decision is not acceptable")
    if strict_final_allowed:
        require(strict_completion_allowed is True, "strict final acceptance allowed without strict completion gate")
        require(done == 14 and missing == 0, "strict final acceptance allowed without all checklist files")
        require(present == 14 and awaiting == 0, "strict final acceptance allowed without all indexed files")
        require(blocker_count == 0, "strict final acceptance allowed with open blockers")
        require(decision.get("strict_master_plan") == "ACCEPTABLE_TO_CLOSE", "strict decision is not acceptable")
    else:
        require(strict_completion_allowed is False, "strict completion gate allowed while final acceptance is false")
        require(
            decision.get("strict_master_plan") == "AWAITING_EXTERNAL_ARTIFACTS",
            "strict master-plan decision is not awaiting artifacts",
        )
    artifacts = data.get("required_external_artifacts")
    require(isinstance(artifacts, list) and len(artifacts) == 14, "required external artifacts are not enumerated")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Project Closeout Acceptance Gate",
        "",
        f"- Status: `{report['status']}`",
        f"- Current phase acceptance allowed: `{summary['current_phase_acceptance_allowed']}`",
        f"- Current scope closeout estimate: `{summary['current_scope_closeout_estimate']}`",
        f"- Strict final acceptance allowed: `{summary['strict_final_acceptance_allowed']}`",
        f"- Strict closeout estimate after artifacts: `{summary['strict_closeout_estimate_after_artifacts']}`",
        f"- Strict external artifacts done: `{summary['strict_external_artifact_done_count']}/14`",
        f"- Strict external artifacts missing: `{summary['strict_external_artifact_missing_count']}/14`",
        f"- Open strict blockers: `{summary['open_strict_blocker_count']}`",
        "",
        "## Decision",
        "",
        f"- Current phase: `{report['acceptance_decision']['current_phase']}`",
        f"- Strict master-plan: `{report['acceptance_decision']['strict_master_plan']}`",
        f"- Non-overclaim rule: {report['acceptance_decision']['non_overclaim_rule']}",
        "",
        "## Required External Artifacts",
        "",
    ]
    for row in report["required_external_artifacts"]:
        mark = "x" if row["currently_present"] else " "
        lines.append(f"- [{mark}] `{row['domain']}` `{row['label']}` -> `{row['target_path']}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"project_closeout_acceptance_gate VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"project_closeout_acceptance_gate PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
