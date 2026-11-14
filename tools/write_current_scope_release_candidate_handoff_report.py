#!/usr/bin/env python3
"""Write/verify a current-scope release-candidate handoff report."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF"
STATUS_NOT_READY = "NOT_READY-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_scope_release_candidate_handoff_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_scope_release_candidate_handoff_report.md"

FINAL_READINESS = Path(
    "docs/codex_audit/evidence/master_plan_final_readiness_20260731/"
    "master_plan_final_readiness_report.json"
)
COMPLETION_AUDIT = Path(
    "docs/codex_audit/evidence/master_plan_completion_audit_20260803/"
    "master_plan_completion_audit_report.json"
)
PARALLEL_MATRIX = Path(
    "docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/"
    "current_parallel_capability_matrix_report.json"
)
SCENARIO_MATRIX = Path(
    "docs/codex_audit/evidence/current_scenario_readiness_matrix_20260805/"
    "current_scenario_readiness_matrix_report.json"
)
MULTIFUEL_ANSWER = Path(
    "docs/codex_audit/evidence/engineering_multifuel_liquefied_user_answer_20260811/"
    "engineering_multifuel_liquefied_user_answer_report.json"
)
OPERATOR_RUNBOOK = Path(
    "docs/codex_audit/evidence/current_scope_operator_runbook_20260803/"
    "current_scope_operator_runbook_report.json"
)
STRICT_BLOCKER_MATRIX = Path(
    "docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/"
    "master_plan_strict_blocker_matrix_report.json"
)
CURRENT_SCOPE_RUNBOOK_MD = Path("docs/codex_audit/current_scope_operator_runbook.md")
README = Path("README.md")

EXPECTED_STRICT_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}


class ReleaseCandidateError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseCandidateError(message)


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
        raise ReleaseCandidateError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseCandidateError(f"invalid JSON evidence {path}: {exc}") from exc
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
    final = load_json(FINAL_READINESS)
    completion = load_json(COMPLETION_AUDIT)
    parallel = load_json(PARALLEL_MATRIX)
    scenarios = load_json(SCENARIO_MATRIX)
    multifuel = load_json(MULTIFUEL_ANSWER)
    runbook = load_json(OPERATOR_RUNBOOK)
    blockers = load_json(STRICT_BLOCKER_MATRIX)

    fsum = final["summary"]
    csum = completion["summary"]
    psum = parallel["summary"]
    ssum = scenarios["summary"]
    msum = multifuel["summary"]
    rsum = runbook["summary"]
    bsum = blockers["summary"]

    open_blockers = set(csum.get("open_strict_blockers", completion.get("open_strict_blockers", [])))
    if not open_blockers:
        open_blockers = set(blockers.get("summary", {}).get("open_strict_blockers", []))

    current_scope_ready = all(
        value is True
        for value in [
            fsum.get("current_user_priority_ready"),
            fsum.get("engineering_core_initial_production_credible"),
            fsum.get("current_parallel_capability_ready"),
            psum.get("current_parallel_capability_matrix_ready"),
            psum.get("cpu_mpi_ready_for_all_current_scenarios"),
            psum.get("single_gpu_ready_for_all_current_scenarios"),
            psum.get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios"),
            ssum.get("current_user_priority_ready"),
            ssum.get("cpu_mpi_ready_for_all_current_scenarios"),
            ssum.get("single_gpu_ready_for_all_current_scenarios"),
            ssum.get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios"),
            msum.get("operator_answer_ready"),
            rsum.get("operator_runbook_ready"),
        ]
    )
    strict_boundary_explicit = (
        csum.get("goal_complete") is False
        and csum.get("strict_master_plan_complete") is False
        and bsum.get("strict_master_plan_complete") is False
        and open_blockers == EXPECTED_STRICT_BLOCKERS
        and csum.get("open_strict_blocker_count") == 3
        and bsum.get("open_strict_blocker_count") == 3
    )
    handoff_ready = current_scope_ready and strict_boundary_explicit

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if handoff_ready else STATUS_NOT_READY,
        "scope": "current user-priority release-candidate handoff without strict master-plan overclaim",
        "summary": {
            "release_candidate_handoff_ready": handoff_ready,
            "current_scope_ready": current_scope_ready,
            "current_user_priority_ready": fsum["current_user_priority_ready"],
            "engineering_core_initial_production_credible": fsum["engineering_core_initial_production_credible"],
            "engineering_progress_estimate_percent": fsum["engineering_progress_estimate_percent"],
            "overall_progress_estimate_percent": fsum["overall_progress_estimate_percent"],
            "scenario_count": ssum["scenario_count"],
            "ready_scenario_count": ssum["ready_scenario_count"],
            "cpu_mpi_ready_for_all_current_scenarios": psum["cpu_mpi_ready_for_all_current_scenarios"],
            "single_gpu_ready_for_all_current_scenarios": psum["single_gpu_ready_for_all_current_scenarios"],
            "multi_gpu_mpi_cuda_ready_for_all_current_scenarios": psum[
                "multi_gpu_mpi_cuda_ready_for_all_current_scenarios"
            ],
            "multifuel_liquefied_operator_answer_ready": msum["operator_answer_ready"],
            "gas_species_supported_in_current_templates": msum["gas_species_supported_in_current_templates"],
            "liquefied_fluids_with_screening_presets": msum["liquefied_fluids_with_screening_presets"],
            "internal_liquid_phase_change_cfd_ready": msum["internal_liquid_phase_change_cfd_ready"],
            "production_phase_change_claim_allowed": msum["production_phase_change_claim_allowed"],
            "operator_runbook_ready": rsum["operator_runbook_ready"],
            "required_operator_command_count": rsum["required_command_count"],
            "missing_operator_command_count": rsum["missing_command_count"],
            "strict_boundary_explicit": strict_boundary_explicit,
            "goal_complete": csum["goal_complete"],
            "strict_master_plan_complete": csum["strict_master_plan_complete"],
            "open_strict_blocker_count": csum["open_strict_blocker_count"],
            "open_strict_blockers": sorted(open_blockers),
            "release_candidate_can_be_used_for_current_priority_scope": handoff_ready,
            "release_candidate_is_full_strict_master_plan_completion": False,
        },
        "handoff_paths": {
            "operator_runbook": str(CURRENT_SCOPE_RUNBOOK_MD),
            "readme": str(README),
            "final_readiness_report": str(FINAL_READINESS),
            "completion_audit_report": str(COMPLETION_AUDIT),
            "scenario_matrix_report": str(SCENARIO_MATRIX),
            "parallel_matrix_report": str(PARALLEL_MATRIX),
            "multifuel_liquefied_answer_report": str(MULTIFUEL_ANSWER),
        },
        "remaining_strict_work": [
            {
                "blocker": "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
                "needed_to_close": "external plume-shape/time-series agreement data and passing CFD comparison",
            },
            {
                "blocker": "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
                "needed_to_close": "real CAD artifact intake, cleanup, boundary tagging, and mesh parity evidence",
            },
            {
                "blocker": "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
                "needed_to_close": "calibrated radiation and overpressure evidence, not only screening proxies",
            },
        ],
        "evidence_files": [
            evidence_entry("master_plan_final_readiness", FINAL_READINESS),
            evidence_entry("master_plan_completion_audit", COMPLETION_AUDIT),
            evidence_entry("current_parallel_capability_matrix", PARALLEL_MATRIX),
            evidence_entry("current_scenario_readiness_matrix", SCENARIO_MATRIX),
            evidence_entry("engineering_multifuel_liquefied_user_answer", MULTIFUEL_ANSWER),
            evidence_entry("current_scope_operator_runbook", OPERATOR_RUNBOOK),
            evidence_entry("master_plan_strict_blocker_matrix", STRICT_BLOCKER_MATRIX),
            evidence_entry("current_scope_operator_runbook_md", CURRENT_SCOPE_RUNBOOK_MD),
            evidence_entry("readme", README),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "release candidate handoff is not passing")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("release_candidate_handoff_ready") is True, "handoff is not ready")
    require(summary.get("current_scope_ready") is True, "current scope is not ready")
    require(summary.get("current_user_priority_ready") is True, "current user-priority scope is not ready")
    require(summary.get("engineering_core_initial_production_credible") is True, "engineering core is not credible")
    require(summary.get("scenario_count") == 4, "unexpected scenario count")
    require(summary.get("ready_scenario_count") == 4, "not all current scenarios are ready")
    require(summary.get("cpu_mpi_ready_for_all_current_scenarios") is True, "CPU/MPI not ready")
    require(summary.get("single_gpu_ready_for_all_current_scenarios") is True, "single GPU not ready")
    require(summary.get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios") is True, "MPI+CUDA not ready")
    require(summary.get("multifuel_liquefied_operator_answer_ready") is True, "multifuel answer not ready")
    require(set(summary.get("gas_species_supported_in_current_templates", [])) == {"C3H8", "CH4", "H2"}, "unexpected gas species")
    require(set(summary.get("liquefied_fluids_with_screening_presets", [])) == {"LNG_CH4", "LPG_C3H8"}, "unexpected liquefied fluids")
    require(summary.get("internal_liquid_phase_change_cfd_ready") is False, "internal phase-change should not be overclaimed")
    require(summary.get("production_phase_change_claim_allowed") is False, "production phase-change claim should not be allowed")
    require(summary.get("operator_runbook_ready") is True, "operator runbook is not ready")
    require(summary.get("missing_operator_command_count") == 0, "operator command inventory has missing commands")
    require(summary.get("strict_boundary_explicit") is True, "strict boundary is not explicit")
    require(summary.get("goal_complete") is False, "goal should not be overclaimed complete")
    require(summary.get("strict_master_plan_complete") is False, "strict master plan should remain incomplete")
    require(summary.get("open_strict_blocker_count") == 3, "unexpected strict blocker count")
    require(set(summary.get("open_strict_blockers", [])) == EXPECTED_STRICT_BLOCKERS, "unexpected strict blocker set")
    require(summary.get("release_candidate_can_be_used_for_current_priority_scope") is True, "current priority scope cannot be handed off")
    require(summary.get("release_candidate_is_full_strict_master_plan_completion") is False, "strict completion overclaimed")
    handoff_paths = data.get("handoff_paths")
    require(isinstance(handoff_paths, dict), "missing handoff paths")
    for label, value in handoff_paths.items():
        require(isinstance(value, str) and Path(value).exists(), f"missing handoff path: {label}={value}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current-Scope Release Candidate Handoff",
        "",
        f"- Status: `{report['status']}`",
        f"- Handoff ready: `{summary['release_candidate_handoff_ready']}`",
        f"- Current user-priority ready: `{summary['current_user_priority_ready']}`",
        f"- Engineering progress estimate: `{summary['engineering_progress_estimate_percent']}`",
        f"- Overall progress estimate: `{summary['overall_progress_estimate_percent']}`",
        f"- Scenarios ready: `{summary['ready_scenario_count']}/{summary['scenario_count']}`",
        f"- CPU/MPI: `{summary['cpu_mpi_ready_for_all_current_scenarios']}`",
        f"- Single GPU: `{summary['single_gpu_ready_for_all_current_scenarios']}`",
        f"- MPI+CUDA: `{summary['multi_gpu_mpi_cuda_ready_for_all_current_scenarios']}`",
        f"- Multifuel/liquefied answer ready: `{summary['multifuel_liquefied_operator_answer_ready']}`",
        f"- Gas species: `{', '.join(summary['gas_species_supported_in_current_templates'])}`",
        f"- Liquefied screening fluids: `{', '.join(summary['liquefied_fluids_with_screening_presets'])}`",
        f"- Internal liquid phase-change CFD ready: `{summary['internal_liquid_phase_change_cfd_ready']}`",
        f"- Goal complete: `{summary['goal_complete']}`",
        f"- Strict master-plan complete: `{summary['strict_master_plan_complete']}`",
        f"- Open strict blockers: `{summary['open_strict_blocker_count']}`",
        "",
        "## Handoff Paths",
        "",
    ]
    for label, value in report["handoff_paths"].items():
        lines.append(f"- `{label}`: `{value}`")
    lines.extend(["", "## Remaining Strict Work", ""])
    for item in report["remaining_strict_work"]:
        lines.append(f"- `{item['blocker']}`: {item['needed_to_close']}")
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
        print(f"current_scope_release_candidate_handoff VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_scope_release_candidate_handoff PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
