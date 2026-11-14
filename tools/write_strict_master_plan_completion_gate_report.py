#!/usr/bin/env python3
"""Write a strict master-plan completion gate report.

This gate is intentionally different from the current-scope release gate.  It
passes as an audit artifact when the boundary is explicit, but it only allows
strict completion after the external CAD/reference/fire-calibration blockers
are actually cleared by their upstream evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_AWAITING = "AWAITING-STRICT-MASTER-PLAN-COMPLETION-GATE-EXTERNAL-ARTIFACTS"
STATUS_PASS = "PASS-STRICT-MASTER-PLAN-COMPLETION-GATE"
STATUS_NOT_READY = "NOT_READY-STRICT-MASTER-PLAN-COMPLETION-GATE"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_master_plan_completion_gate_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_master_plan_completion_gate_report.md"

PROJECT_CLOSEOUT = Path(
    "docs/codex_audit/evidence/project_closeout_forecast_20260812/"
    "project_closeout_forecast_report.json"
)
COMPLETION_AUDIT = Path(
    "docs/codex_audit/evidence/master_plan_completion_audit_20260803/"
    "master_plan_completion_audit_report.json"
)
STRICT_BLOCKER_MATRIX = Path(
    "docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/"
    "master_plan_strict_blocker_matrix_report.json"
)
ARTIFACT_INTAKE = Path(
    "docs/codex_audit/evidence/master_plan_strict_artifact_intake_manifest_20260731/"
    "master_plan_strict_artifact_intake_manifest_report.json"
)
ARTIFACT_DROP_PREFLIGHT = Path(
    "docs/codex_audit/evidence/master_plan_strict_artifact_drop_preflight_20260731/"
    "master_plan_strict_artifact_drop_preflight_report.json"
)
STRICT_DROP_CONTRACT = Path(
    "docs/codex_audit/evidence/strict_artifact_drop_contract_preflight_20260803/"
    "strict_artifact_drop_contract_preflight_report.json"
)
UNBLOCK_RUNBOOK = Path(
    "docs/codex_audit/evidence/strict_master_plan_unblock_runbook_20260803/"
    "strict_master_plan_unblock_runbook_report.json"
)
UNBLOCK_COMMANDS = Path(
    "docs/codex_audit/evidence/strict_unblock_command_inventory_20260803/"
    "strict_unblock_command_inventory_report.json"
)
REAL_CAD_UPDATE = Path(
    "docs/codex_audit/evidence/master_plan_strict_real_cad_update_20260731/"
    "master_plan_strict_real_cad_update_report.json"
)
EXTERNAL_SOURCE_UPDATE = Path(
    "docs/codex_audit/evidence/master_plan_strict_external_source_update_20260731/"
    "master_plan_strict_external_source_update_report.json"
)
FIRE_CALIBRATION_UPDATE = Path(
    "docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731/"
    "master_plan_strict_fire_calibration_update_report.json"
)

EXPECTED_STRICT_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}


class CompletionGateError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CompletionGateError(message)


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
        raise CompletionGateError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CompletionGateError(f"invalid JSON evidence {path}: {exc}") from exc
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


def blocker_state(label: str, path: Path, blocker: str) -> dict[str, Any]:
    data = load_json(path)
    summary = data.get("summary", {})
    open_blockers = set(summary.get("open_strict_blockers", []))
    if not open_blockers and summary.get("strict_blocker") == blocker:
        cleared = summary.get("strict_blocker_cleared") is True
    else:
        cleared = blocker not in open_blockers and summary.get("strict_master_plan_complete") is True
    return {
        "label": label,
        "blocker": blocker,
        "path": str(path),
        "status": data.get("status"),
        "cleared_by_report": cleared,
        "sha256": sha256_file(path),
    }


def build_report() -> dict[str, Any]:
    closeout = load_json(PROJECT_CLOSEOUT)
    completion = load_json(COMPLETION_AUDIT)
    matrix = load_json(STRICT_BLOCKER_MATRIX)
    intake = load_json(ARTIFACT_INTAKE)
    drop = load_json(ARTIFACT_DROP_PREFLIGHT)
    contract = load_json(STRICT_DROP_CONTRACT)
    runbook = load_json(UNBLOCK_RUNBOOK)
    commands = load_json(UNBLOCK_COMMANDS)

    closeout_summary = closeout["summary"]
    completion_summary = completion["summary"]
    matrix_summary = matrix["summary"]
    intake_summary = intake["summary"]
    drop_summary = drop["summary"]
    contract_summary = contract["summary"]
    runbook_summary = runbook["summary"]
    commands_summary = commands["summary"]

    open_blockers = set(completion_summary.get("open_strict_blockers", []))
    if not open_blockers:
        open_blockers = set(matrix_summary.get("open_strict_blockers", []))

    artifact_intake_ready = (
        intake.get("status") == "READY-MASTER-PLAN-STRICT-ARTIFACT-INTAKE-MANIFEST"
        and intake_summary.get("artifact_intake_ready") is True
        and contract.get("status") == "PASS-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT"
        and contract_summary.get("strict_artifact_drop_contract_preflight_ready") is True
        and runbook.get("status") == "PASS-STRICT-MASTER-PLAN-UNBLOCK-RUNBOOK"
        and runbook_summary.get("strict_master_plan_unblock_runbook_ready") is True
        and commands.get("status") == "PASS-STRICT-UNBLOCK-COMMAND-INVENTORY"
        and commands_summary.get("strict_unblock_command_inventory_ready") is True
    )
    complete_domain_count = drop_summary.get("complete_domain_count")
    awaiting_domain_count = drop_summary.get("awaiting_external_artifact_domain_count")
    external_artifacts_missing = (
        drop.get("status") == "AWAITING-MASTER-PLAN-STRICT-ARTIFACT-DROP-PREFLIGHT-EXTERNAL-ARTIFACTS"
        and isinstance(complete_domain_count, int)
        and isinstance(awaiting_domain_count, int)
        and complete_domain_count + awaiting_domain_count == 3
        and awaiting_domain_count > 0
    )
    current_scope_closable = (
        closeout.get("status") == "PASS-PROJECT-CLOSEOUT-FORECAST"
        and closeout_summary.get("current_scope_can_be_closed_now") is True
    )
    strict_complete = (
        completion_summary.get("strict_master_plan_complete") is True
        and completion_summary.get("goal_complete") is True
        and completion_summary.get("open_strict_blocker_count") == 0
        and not open_blockers
    )
    expected_current_awaiting = (
        current_scope_closable
        and artifact_intake_ready
        and external_artifacts_missing
        and open_blockers == EXPECTED_STRICT_BLOCKERS
        and closeout_summary.get("strict_master_plan_can_be_closed_now") is False
        and closeout_summary.get("strict_closeout_requires_external_artifacts") is True
    )

    status = STATUS_PASS if strict_complete else STATUS_AWAITING if expected_current_awaiting else STATUS_NOT_READY
    gate_ready = status in {STATUS_PASS, STATUS_AWAITING}

    blocker_reports = [
        blocker_state(
            "external_plume_reference_agreement",
            EXTERNAL_SOURCE_UPDATE,
            "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
        ),
        blocker_state(
            "real_cad_cleanup_and_boundary_tags",
            REAL_CAD_UPDATE,
            "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
        ),
        blocker_state(
            "fire_radiation_overpressure_calibration",
            FIRE_CALIBRATION_UPDATE,
            "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
        ),
    ]

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "scope": "strict master-plan completion gate and current release closeout boundary",
        "summary": {
            "strict_master_plan_completion_gate_ready": gate_ready,
            "current_scope_closure_allowed": current_scope_closable,
            "strict_master_plan_completion_allowed": strict_complete,
            "strict_master_plan_complete": completion_summary.get("strict_master_plan_complete"),
            "strict_goal_complete": completion_summary.get("goal_complete"),
            "strict_external_artifact_intake_ready": artifact_intake_ready,
            "strict_external_artifacts_missing": external_artifacts_missing,
            "strict_external_artifact_complete_domain_count": complete_domain_count,
            "strict_external_artifact_awaiting_domain_count": awaiting_domain_count,
            "open_strict_blocker_count": len(open_blockers),
            "open_strict_blockers": sorted(open_blockers),
            "expected_current_awaiting_state": expected_current_awaiting,
            "expected_strict_blocker_set": sorted(EXPECTED_STRICT_BLOCKERS),
            "strict_blocker_set_matches_expected": open_blockers == EXPECTED_STRICT_BLOCKERS,
            "artifact_drop_preflight_status": drop.get("status"),
            "artifact_contract_status": contract.get("status"),
            "closeout_forecast_status": closeout.get("status"),
            "completion_audit_status": completion.get("status"),
            "strict_blocker_matrix_status": matrix.get("status"),
        },
        "completion_decision": {
            "current_release_candidate": "closable" if current_scope_closable else "not_closable",
            "strict_master_plan": "complete" if strict_complete else "blocked_by_external_artifacts",
            "operator_action": (
                "Use the current release candidate for the verified priority scope; keep strict master-plan "
                "completion open until the three external artifact blockers are cleared."
            ),
        },
        "strict_blocker_reports": blocker_reports,
        "required_to_unlock_strict_completion": [
            {
                "domain": "external plume/reference agreement",
                "required_evidence": "passing external plume shape or sensor time-series comparison report",
            },
            {
                "domain": "real CAD geometry",
                "required_evidence": "user CAD intake, cleanup, boundary tags, mesh/EB parity, and negative selftests",
            },
            {
                "domain": "fire consequence calibration",
                "required_evidence": "case-aligned radiation and overpressure calibration tables with acceptance metrics",
            },
        ],
        "evidence_files": [
            evidence_entry("project_closeout_forecast", PROJECT_CLOSEOUT),
            evidence_entry("master_plan_completion_audit", COMPLETION_AUDIT),
            evidence_entry("master_plan_strict_blocker_matrix", STRICT_BLOCKER_MATRIX),
            evidence_entry("master_plan_strict_artifact_intake_manifest", ARTIFACT_INTAKE),
            evidence_entry("master_plan_strict_artifact_drop_preflight", ARTIFACT_DROP_PREFLIGHT),
            evidence_entry("strict_artifact_drop_contract_preflight", STRICT_DROP_CONTRACT),
            evidence_entry("strict_master_plan_unblock_runbook", UNBLOCK_RUNBOOK),
            evidence_entry("strict_unblock_command_inventory", UNBLOCK_COMMANDS),
            evidence_entry("master_plan_strict_real_cad_update", REAL_CAD_UPDATE),
            evidence_entry("master_plan_strict_external_source_update", EXTERNAL_SOURCE_UPDATE),
            evidence_entry("master_plan_strict_fire_calibration_update", FIRE_CALIBRATION_UPDATE),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_AWAITING, STATUS_PASS}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_master_plan_completion_gate_ready") is True, "completion gate is not ready")
    require(summary.get("current_scope_closure_allowed") is True, "current scope closure is not allowed")
    if data.get("status") == STATUS_AWAITING:
        require(summary.get("strict_master_plan_completion_allowed") is False, "strict completion overclaimed")
        require(summary.get("strict_master_plan_complete") is False, "strict master plan unexpectedly complete")
        require(summary.get("strict_goal_complete") is False, "strict goal unexpectedly complete")
        require(summary.get("strict_external_artifact_intake_ready") is True, "strict artifact intake is not ready")
        require(summary.get("strict_external_artifacts_missing") is True, "external missing state changed")
        complete_domain_count = summary.get("strict_external_artifact_complete_domain_count")
        awaiting_domain_count = summary.get("strict_external_artifact_awaiting_domain_count")
        require(isinstance(complete_domain_count, int), "complete domain count is not an integer")
        require(isinstance(awaiting_domain_count, int), "awaiting domain count is not an integer")
        require(complete_domain_count + awaiting_domain_count == 3, "strict artifact domain counts do not sum to 3")
        require(awaiting_domain_count > 0, "strict external artifacts unexpectedly complete")
        require(summary.get("open_strict_blocker_count") == 3, "unexpected open blocker count")
        require(set(summary.get("open_strict_blockers", [])) == EXPECTED_STRICT_BLOCKERS, "unexpected blocker set")
        require(summary.get("expected_current_awaiting_state") is True, "awaiting state is not internally consistent")
    else:
        require(summary.get("strict_master_plan_completion_allowed") is True, "strict completion not allowed")
        require(summary.get("strict_master_plan_complete") is True, "strict master plan not complete")
        require(summary.get("strict_goal_complete") is True, "strict goal not complete")
        require(summary.get("open_strict_blocker_count") == 0, "strict blockers remain")

    reports = data.get("strict_blocker_reports")
    require(isinstance(reports, list) and len(reports) == 3, "invalid blocker report list")
    evidence_files = data.get("evidence_files")
    require(isinstance(evidence_files, list) and len(evidence_files) >= 11, "missing evidence file entries")
    if verify_hashes:
        for entry in evidence_files:
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence path: {path}")
            require(entry["sha256"] == sha256_file(path), f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict Master-Plan Completion Gate",
        "",
        f"- Status: `{report['status']}`",
        f"- Current scope closure allowed: `{summary['current_scope_closure_allowed']}`",
        f"- Strict completion allowed: `{summary['strict_master_plan_completion_allowed']}`",
        f"- Open strict blockers: `{summary['open_strict_blocker_count']}`",
        f"- External artifact intake ready: `{summary['strict_external_artifact_intake_ready']}`",
        f"- External artifacts missing: `{summary['strict_external_artifacts_missing']}`",
        "",
        "## Open Blockers",
        "",
    ]
    for blocker in summary["open_strict_blockers"]:
        lines.append(f"- `{blocker}`")
    lines.extend(["", "## Required To Unlock Strict Completion", ""])
    for item in report["required_to_unlock_strict_completion"]:
        lines.append(f"- `{item['domain']}`: {item['required_evidence']}")
    lines.extend(["", "## Evidence", ""])
    for entry in report["evidence_files"]:
        lines.append(f"- `{entry['label']}`: `{entry['path']}`")
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
        validate_report(data)
        print(f"strict_master_plan_completion_gate VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, output_md)
    print(
        "strict_master_plan_completion_gate PASS "
        f"json={output_json} md={output_md} status={report['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
