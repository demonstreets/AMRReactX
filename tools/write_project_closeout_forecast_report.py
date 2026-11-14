#!/usr/bin/env python3
"""Write/verify a project closeout forecast report for the active Pele CFD goal."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-PROJECT-CLOSEOUT-FORECAST"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/project_closeout_forecast_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "project_closeout_forecast_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "project_closeout_forecast_report.md"

RELEASE_CANDIDATE = Path(
    "docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812/"
    "current_scope_release_candidate_handoff_report.json"
)
FINAL_READINESS = Path(
    "docs/codex_audit/evidence/master_plan_final_readiness_20260731/"
    "master_plan_final_readiness_report.json"
)
COMPLETION_AUDIT = Path(
    "docs/codex_audit/evidence/master_plan_completion_audit_20260803/"
    "master_plan_completion_audit_report.json"
)
STRICT_BLOCKER_MATRIX = Path(
    "docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/"
    "master_plan_strict_blocker_matrix_report.json"
)
STRICT_UNBLOCK_RUNBOOK = Path(
    "docs/codex_audit/evidence/strict_master_plan_unblock_runbook_20260803/"
    "strict_master_plan_unblock_runbook_report.json"
)
ARTIFACT_INTAKE = Path(
    "docs/codex_audit/evidence/master_plan_strict_artifact_intake_manifest_20260731/"
    "master_plan_strict_artifact_intake_manifest_report.json"
)
ARTIFACT_DROP_PREFLIGHT = Path(
    "docs/codex_audit/evidence/master_plan_strict_artifact_drop_preflight_20260731/"
    "master_plan_strict_artifact_drop_preflight_report.json"
)
FIRE_RESIDUAL_BUDGET = Path(
    "docs/codex_audit/evidence/h2_fire_calibration_residual_budget_20260811/"
    "h2_fire_calibration_residual_budget_report.json"
)

EXPECTED_STRICT_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}


class CloseoutForecastError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CloseoutForecastError(message)


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
        raise CloseoutForecastError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CloseoutForecastError(f"invalid JSON evidence {path}: {exc}") from exc
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


def build_report() -> dict[str, Any]:
    release = load_json(RELEASE_CANDIDATE)
    final = load_json(FINAL_READINESS)
    completion = load_json(COMPLETION_AUDIT)
    blockers = load_json(STRICT_BLOCKER_MATRIX)
    unblock = load_json(STRICT_UNBLOCK_RUNBOOK)
    intake = load_json(ARTIFACT_INTAKE)
    drop = load_json(ARTIFACT_DROP_PREFLIGHT)
    fire = load_json(FIRE_RESIDUAL_BUDGET)

    rsum = release["summary"]
    fsum = final["summary"]
    csum = completion["summary"]
    bsum = blockers["summary"]
    usum = unblock["summary"]
    isum = intake["summary"]
    dsum = drop["summary"]
    firesum = fire["summary"]

    open_blockers = set(csum.get("open_strict_blockers", [])) or set(bsum.get("open_strict_blockers", []))
    strict_blockers_match = open_blockers == EXPECTED_STRICT_BLOCKERS
    current_release_candidate_ready = (
        release.get("status") == "PASS-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF"
        and rsum.get("release_candidate_handoff_ready") is True
        and rsum.get("release_candidate_can_be_used_for_current_priority_scope") is True
        and rsum.get("release_candidate_is_full_strict_master_plan_completion") is False
    )
    strict_artifact_intake_ready = (
        unblock.get("status") == "PASS-STRICT-MASTER-PLAN-UNBLOCK-RUNBOOK"
        and usum.get("strict_master_plan_unblock_runbook_ready") is True
        and intake.get("status") == "READY-MASTER-PLAN-STRICT-ARTIFACT-INTAKE-MANIFEST"
        and isum.get("artifact_intake_ready") is True
        and drop.get("status") == "AWAITING-MASTER-PLAN-STRICT-ARTIFACT-DROP-PREFLIGHT-EXTERNAL-ARTIFACTS"
    )
    complete_domain_count = dsum.get("complete_domain_count")
    awaiting_domain_count = dsum.get("awaiting_external_artifact_domain_count")
    strict_external_artifacts_missing = (
        isinstance(complete_domain_count, int)
        and isinstance(awaiting_domain_count, int)
        and complete_domain_count + awaiting_domain_count == 3
        and awaiting_domain_count > 0
    )
    strict_fire_external_blocked = (
        fire.get("status") == "TRIAGED-H2-FIRE-CALIBRATION-RESIDUAL-BUDGET"
        and firesum.get("production_fire_calibration_claim_allowed") is False
        and firesum.get("strict_fire_calibration_blocker_cleared") is False
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "closeout forecast for current release candidate versus strict master-plan completion",
        "summary": {
            "current_release_candidate_ready": current_release_candidate_ready,
            "current_scope_can_be_closed_now": current_release_candidate_ready,
            "current_scope_closeout_estimate": "0.5-1 day for final handoff notes and optional fresh smoke reruns",
            "strict_master_plan_complete": csum["strict_master_plan_complete"],
            "strict_goal_complete": csum["goal_complete"],
            "strict_master_plan_can_be_closed_now": False,
            "strict_closeout_requires_external_artifacts": True,
            "strict_closeout_estimate_after_artifacts": "3-7 days after real CAD/reference/fire calibration artifacts are available",
            "overall_progress_estimate_percent": fsum["overall_progress_estimate_percent"],
            "engineering_progress_estimate_percent": fsum["engineering_progress_estimate_percent"],
            "open_strict_blocker_count": csum["open_strict_blocker_count"],
            "open_strict_blockers": sorted(open_blockers),
            "strict_blocker_set_matches_expected": strict_blockers_match,
            "strict_artifact_intake_ready": strict_artifact_intake_ready,
            "strict_external_artifacts_missing": strict_external_artifacts_missing,
            "strict_external_artifact_complete_domain_count": complete_domain_count,
            "strict_external_artifact_awaiting_domain_count": awaiting_domain_count,
            "strict_fire_calibration_requires_external_case_aligned_data": strict_fire_external_blocked,
            "release_candidate_status": release["status"],
            "completion_audit_status": completion["status"],
            "strict_blocker_matrix_status": blockers["status"],
            "artifact_drop_preflight_status": drop["status"],
            "fire_residual_budget_status": fire["status"],
        },
        "closeout_decision": {
            "recommended_current_action": "close the current user-priority release candidate as usable, with strict caveats recorded",
            "do_not_claim": [
                "full strict master-plan completion",
                "production CFD-internal liquid flashing or pool evaporation",
                "calibrated fire radiation/overpressure consequence prediction",
                "validated real-CAD cleanup and boundary tagging on user-provided plant geometry",
                "external plume-shape agreement against a passing public dataset",
            ],
            "can_claim_for_current_scope": [
                "current engineering and academic priority scenarios are verified by the current-scope chain",
                "CPU/MPI, single GPU, and MPI+CUDA readiness are represented in the current parallel matrix",
                "H2, CH4, and C3H8 gas-source workflows are represented by current templates",
                "LNG_CH4 and LPG_C3H8 liquefied release workflows are screening/external-source ready",
            ],
        },
        "remaining_strict_blockers": [
            {
                "blocker": "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
                "state": "open",
                "why_open": "existing Dataverse/open-channel runs are stable but agreement attempts are quantified as not passing",
                "closure_evidence_required": "passing plume shape or sensor time-series agreement report against external reference data",
            },
            {
                "blocker": "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
                "state": "open",
                "why_open": "current geometry evidence uses synthetic tank-farm/pipe-rack STL rather than user real CAD",
                "closure_evidence_required": "real CAD intake, cleanup, boundary tags, mesh/EB parity, and negative selftests",
            },
            {
                "blocker": "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
                "state": "open",
                "why_open": "fire residual budget keeps production calibration claims disabled",
                "closure_evidence_required": "case-aligned calibrated radiation and overpressure comparisons with acceptance metrics",
            },
        ],
        "evidence_files": [
            evidence_entry("current_scope_release_candidate_handoff", RELEASE_CANDIDATE),
            evidence_entry("master_plan_final_readiness", FINAL_READINESS),
            evidence_entry("master_plan_completion_audit", COMPLETION_AUDIT),
            evidence_entry("master_plan_strict_blocker_matrix", STRICT_BLOCKER_MATRIX),
            evidence_entry("strict_master_plan_unblock_runbook", STRICT_UNBLOCK_RUNBOOK),
            evidence_entry("master_plan_strict_artifact_intake_manifest", ARTIFACT_INTAKE),
            evidence_entry("master_plan_strict_artifact_drop_preflight", ARTIFACT_DROP_PREFLIGHT),
            evidence_entry("h2_fire_calibration_residual_budget", FIRE_RESIDUAL_BUDGET),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_release_candidate_ready") is True, "current release candidate is not ready")
    require(summary.get("current_scope_can_be_closed_now") is True, "current scope should be closable")
    require(summary.get("strict_master_plan_complete") is False, "strict completion is unexpectedly true")
    require(summary.get("strict_goal_complete") is False, "goal completion is unexpectedly true")
    require(summary.get("strict_master_plan_can_be_closed_now") is False, "strict closure is overclaimed")
    require(summary.get("strict_closeout_requires_external_artifacts") is True, "external artifact requirement missing")
    require(summary.get("open_strict_blocker_count") == 3, "unexpected strict blocker count")
    require(set(summary.get("open_strict_blockers", [])) == EXPECTED_STRICT_BLOCKERS, "unexpected strict blocker set")
    require(summary.get("strict_blocker_set_matches_expected") is True, "strict blocker set mismatch")
    require(summary.get("strict_artifact_intake_ready") is True, "strict artifact intake path is not ready")
    require(summary.get("strict_external_artifacts_missing") is True, "external artifact missing state changed")
    complete_domain_count = summary.get("strict_external_artifact_complete_domain_count")
    awaiting_domain_count = summary.get("strict_external_artifact_awaiting_domain_count")
    require(isinstance(complete_domain_count, int), "complete domain count is not an integer")
    require(isinstance(awaiting_domain_count, int), "awaiting domain count is not an integer")
    require(complete_domain_count + awaiting_domain_count == 3, "strict artifact domain counts do not sum to 3")
    require(awaiting_domain_count > 0, "strict external artifacts unexpectedly complete")
    require(
        summary.get("strict_fire_calibration_requires_external_case_aligned_data") is True,
        "fire calibration boundary changed",
    )
    require(data.get("closeout_decision", {}).get("recommended_current_action"), "missing closeout recommendation")
    remaining = data.get("remaining_strict_blockers")
    require(isinstance(remaining, list) and len(remaining) == 3, "remaining strict blockers not enumerated")
    require({item.get("blocker") for item in remaining} == EXPECTED_STRICT_BLOCKERS, "remaining blocker list mismatch")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Project Closeout Forecast",
        "",
        f"- Status: `{report['status']}`",
        f"- Current release candidate ready: `{summary['current_release_candidate_ready']}`",
        f"- Current scope can be closed now: `{summary['current_scope_can_be_closed_now']}`",
        f"- Current scope closeout estimate: `{summary['current_scope_closeout_estimate']}`",
        f"- Strict master-plan complete: `{summary['strict_master_plan_complete']}`",
        f"- Strict master-plan can be closed now: `{summary['strict_master_plan_can_be_closed_now']}`",
        f"- Strict closeout requires external artifacts: `{summary['strict_closeout_requires_external_artifacts']}`",
        f"- Strict closeout estimate after artifacts: `{summary['strict_closeout_estimate_after_artifacts']}`",
        f"- Overall progress estimate: `{summary['overall_progress_estimate_percent']}`",
        f"- Engineering progress estimate: `{summary['engineering_progress_estimate_percent']}`",
        f"- Open strict blockers: `{summary['open_strict_blocker_count']}`",
        "",
        "## Closeout Decision",
        "",
        f"- Recommended current action: `{report['closeout_decision']['recommended_current_action']}`",
        "",
        "## Can Claim For Current Scope",
        "",
    ]
    for item in report["closeout_decision"]["can_claim_for_current_scope"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Do Not Claim", ""])
    for item in report["closeout_decision"]["do_not_claim"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Remaining Strict Blockers", ""])
    for item in report["remaining_strict_blockers"]:
        lines.append(f"- `{item['blocker']}`: {item['why_open']}")
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
        print(f"project_closeout_forecast VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"project_closeout_forecast PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
