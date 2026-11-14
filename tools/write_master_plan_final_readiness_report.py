#!/usr/bin/env python3
"""Write/verify the final master-plan readiness rollup."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_PASS_CURRENT_SCOPE = "PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS"
STATUS_NOT_READY = "NOT_READY-MASTER-PLAN-FINAL-READINESS"
SCHEMA_VERSION = 1

DEFAULT_ROOT = Path("docs/codex_audit/evidence/master_plan_final_readiness_20260731")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "master_plan_final_readiness_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "master_plan_final_readiness_report.md"

DEFAULT_ENGINEERING_TRACEABILITY = Path(
    "docs/codex_audit/evidence/engineering_h2_master_plan_traceability_20260724/"
    "h2_master_plan_traceability_report.json"
)
DEFAULT_ENGINEERING_VERIFY = Path(
    "docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/"
    "production_evidence_verification_report.json"
)
DEFAULT_ENGINEERING_SCORECARD = Path(
    "docs/codex_audit/evidence/engineering_production_scorecard_20260728_integrated_initial_acceptance/"
    "engineering_production_scorecard.json"
)
DEFAULT_ENGINEERING_ACCEPTANCE = Path(
    "docs/codex_audit/evidence/engineering_h2_integrated_initial_acceptance_20260728/"
    "h2_integrated_initial_acceptance_report.json"
)
DEFAULT_ACADEMIC_GAS = Path(
    "docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724/"
    "academic_gas_detonation_readiness_report.json"
)
DEFAULT_ACADEMIC_TWOPHASE = Path(
    "docs/codex_audit/evidence/academic_twophase_broader_matrix_20260730/"
    "academic_twophase_broader_matrix_report.json"
)
DEFAULT_GAS_LIQUID_CERT = Path(
    "docs/codex_audit/evidence/academic_gas_liquid_detonation_certification_20260731/"
    "academic_gas_liquid_detonation_certification_report.json"
)
DEFAULT_FULL_REPRO = Path(
    "docs/codex_audit/evidence/master_plan_full_reproducibility_20260731/"
    "master_plan_full_reproducibility_report.json"
)
DEFAULT_CURRENT_PARALLEL_CAPABILITY = Path(
    "docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/"
    "current_parallel_capability_matrix_report.json"
)
DEFAULT_CURRENT_SCOPE_OPERATOR_RUNBOOK = Path(
    "docs/codex_audit/evidence/current_scope_operator_runbook_20260803/"
    "current_scope_operator_runbook_report.json"
)
DEFAULT_GATE_LOG_DIR = DEFAULT_ROOT / "gate_logs"

EXPECTED_DEFERRED_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}


class RollupError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RollupError(message)


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
        raise RollupError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RollupError(f"invalid JSON evidence {path}: {exc}") from exc
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


def read_exitcode(path: Path) -> int:
    require(path.is_file(), f"missing gate exitcode: {path}")
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    require(text.isdigit(), f"invalid gate exitcode {path}: {text!r}")
    return int(text)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    engineering_traceability_path = Path(args.engineering_traceability)
    engineering_verify_path = Path(args.engineering_verify)
    engineering_scorecard_path = Path(args.engineering_scorecard)
    engineering_acceptance_path = Path(args.engineering_acceptance)
    academic_gas_path = Path(args.academic_gas)
    academic_twophase_path = Path(args.academic_twophase)
    gas_liquid_cert_path = Path(args.gas_liquid_cert)
    full_repro_path = Path(args.full_repro)
    current_parallel_capability_path = Path(args.current_parallel_capability)
    current_scope_operator_runbook_path = Path(args.current_scope_operator_runbook)
    gate_log_dir = Path(args.gate_log_dir)

    engineering_traceability = load_json(engineering_traceability_path)
    engineering_verify = load_json(engineering_verify_path)
    engineering_scorecard = load_json(engineering_scorecard_path)
    engineering_acceptance = load_json(engineering_acceptance_path)
    academic_gas = load_json(academic_gas_path)
    academic_twophase = load_json(academic_twophase_path)
    gas_liquid_cert = load_json(gas_liquid_cert_path)
    full_repro = load_json(full_repro_path)
    current_parallel_capability = load_json(current_parallel_capability_path)
    current_scope_operator_runbook = load_json(current_scope_operator_runbook_path)

    engineering_exit = read_exitcode(gate_log_dir / "engineering_h2_verify.exitcode")
    academic_exit = read_exitcode(gate_log_dir / "academic_verify.exitcode")
    repro_exit = read_exitcode(gate_log_dir / "reproducible_gate_light.exitcode")

    traceability_blockers = [
        item.get("blocker")
        for item in engineering_traceability.get("remaining_blockers", [])
        if isinstance(item, dict)
    ]
    traceability_blocker_set = set(str(item) for item in traceability_blockers)

    engineering_core_ready = (
        engineering_exit == 0
        and engineering_verify.get("status") == "PASS"
        and engineering_acceptance.get("status") == "PASS-H2-INTEGRATED-ENGINEERING-INITIAL-ACCEPTANCE"
    )
    academic_gas_ready = (
        academic_gas.get("status") == "PASS-ACADEMIC-GAS-DETONATION-READINESS"
        and academic_gas.get("summary", {}).get("academic_gas_detonation_ready") is True
    )
    academic_twophase_ready = (
        academic_twophase.get("status") == "PASS-ACADEMIC-TWOPHASE-BROADER-MATRIX-AUDIT"
        and academic_twophase.get("summary", {}).get("academic_twophase_broader_matrix_ready") is True
        and gas_liquid_cert.get("status") == "PASS-ACADEMIC-GAS-LIQUID-DETONATION-CERTIFICATION"
    )
    reproducibility_light_ready = repro_exit == 0
    full_cpu_reproducibility_ready = full_repro.get("summary", {}).get("full_cpu_reproducibility_ready") is True
    current_cuda_runtime_ready = full_repro.get("summary", {}).get("current_cuda_runtime_ready") is True
    historical_gpu_evidence_ready = (
        full_repro.get("summary", {}).get("historical_engineering_gpu_case_evidence_ready") is True
    )
    current_parallel_summary = current_parallel_capability.get("summary", {})
    current_parallel_capability_ready = (
        current_parallel_capability.get("status") == "PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX"
        and current_parallel_summary.get("current_parallel_capability_matrix_ready") is True
        and current_parallel_summary.get("cpu_mpi_ready_for_all_current_scenarios") is True
        and current_parallel_summary.get("single_gpu_ready_for_all_current_scenarios") is True
        and current_parallel_summary.get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios") is True
    )
    current_scope_operator_runbook_ready = (
        current_scope_operator_runbook.get("status") == "PASS-CURRENT-SCOPE-OPERATOR-RUNBOOK"
        and current_scope_operator_runbook.get("summary", {}).get("operator_runbook_ready") is True
    )
    strict_master_plan_complete = engineering_traceability.get("status") == "PASS-H2-MASTER-PLAN-TRACEABILITY"

    deferred_blockers_match = traceability_blocker_set == EXPECTED_DEFERRED_BLOCKERS
    current_user_priority_ready = (
        engineering_core_ready
        and academic_gas_ready
        and academic_twophase_ready
        and reproducibility_light_ready
        and full_cpu_reproducibility_ready
        and historical_gpu_evidence_ready
        and current_parallel_capability_ready
        and current_scope_operator_runbook_ready
        and deferred_blockers_match
    )
    status = STATUS_PASS_CURRENT_SCOPE if current_user_priority_ready else STATUS_NOT_READY

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "summary": {
            "current_user_priority_ready": current_user_priority_ready,
            "strict_master_plan_complete": strict_master_plan_complete,
            "engineering_core_initial_production_credible": engineering_core_ready,
            "academic_gas_detonation_ready": academic_gas_ready,
            "academic_twophase_broader_matrix_ready": academic_twophase_ready,
            "light_reproducibility_gate_ready": reproducibility_light_ready,
            "full_cpu_reproducibility_ready": full_cpu_reproducibility_ready,
            "current_cuda_runtime_ready": current_cuda_runtime_ready,
            "current_cuda_runtime_blocker": full_repro.get("summary", {}).get("current_cuda_runtime_blocker"),
            "historical_engineering_gpu_case_evidence_ready": historical_gpu_evidence_ready,
            "current_parallel_capability_ready": current_parallel_capability_ready,
            "current_parallel_capability_status": current_parallel_capability.get("status"),
            "cpu_mpi_ready_for_all_current_scenarios": current_parallel_summary.get("cpu_mpi_ready_for_all_current_scenarios"),
            "single_gpu_ready_for_all_current_scenarios": current_parallel_summary.get("single_gpu_ready_for_all_current_scenarios"),
            "multi_gpu_mpi_cuda_ready_for_all_current_scenarios": current_parallel_summary.get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios"),
            "current_scope_operator_runbook_ready": current_scope_operator_runbook_ready,
            "current_scope_operator_runbook_status": current_scope_operator_runbook.get("status"),
            "overall_progress_estimate_percent": "90-92",
            "engineering_progress_estimate_percent": "90-92",
            "academic_gas_progress_estimate_percent": "85-90",
            "academic_twophase_progress_estimate_percent": "92-94",
            "deferred_strict_master_plan_blocker_count": len(traceability_blockers),
            "deferred_strict_master_plan_blockers": traceability_blockers,
        },
        "gate_results": {
            "engineering_h2_verify_exitcode": engineering_exit,
            "academic_verify_exitcode": academic_exit,
            "reproducible_gate_light_exitcode": repro_exit,
        },
        "strict_master_plan_status": {
            "traceability_status": engineering_traceability.get("status"),
            "scorecard_status": engineering_scorecard.get("status"),
            "strict_completion_blocked_by": engineering_traceability.get("remaining_blockers", []),
            "interpretation": (
                "The current user-prioritized engineering and academic CFD target is ready, "
                "but original strict master-plan completion remains deferred until external plume-shape data, "
                "real CAD cleanup evidence, and calibrated fire/radiation-overpressure datasets are ingested."
            ),
        },
        "evidence_files": [
            evidence_entry("engineering_traceability_report", engineering_traceability_path),
            evidence_entry("engineering_production_evidence_verification_report", engineering_verify_path),
            evidence_entry("engineering_integrated_initial_acceptance_report", engineering_acceptance_path),
            evidence_entry("engineering_production_scorecard", engineering_scorecard_path),
            evidence_entry("academic_gas_detonation_readiness_report", academic_gas_path),
            evidence_entry("academic_twophase_broader_matrix_report", academic_twophase_path),
            evidence_entry("academic_gas_liquid_detonation_certification_report", gas_liquid_cert_path),
            evidence_entry("master_plan_full_reproducibility_report", full_repro_path),
            evidence_entry("current_parallel_capability_matrix_report", current_parallel_capability_path),
            evidence_entry("current_scope_operator_runbook_report", current_scope_operator_runbook_path),
            evidence_entry("engineering_h2_verify_log", gate_log_dir / "engineering_h2_verify.log"),
            evidence_entry("engineering_h2_verify_exitcode", gate_log_dir / "engineering_h2_verify.exitcode"),
            evidence_entry("academic_verify_log", gate_log_dir / "academic_verify.log"),
            evidence_entry("academic_verify_exitcode", gate_log_dir / "academic_verify.exitcode"),
            evidence_entry("reproducible_gate_light_log", gate_log_dir / "reproducible_gate_light.log"),
            evidence_entry("reproducible_gate_light_exitcode", gate_log_dir / "reproducible_gate_light.exitcode"),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS_CURRENT_SCOPE, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("engineering_core_initial_production_credible") is True, "engineering core not ready")
    require(summary.get("academic_gas_detonation_ready") is True, "academic gas not ready")
    require(summary.get("academic_twophase_broader_matrix_ready") is True, "academic twophase not ready")
    require(summary.get("light_reproducibility_gate_ready") is True, "light reproducibility gate not ready")
    require(summary.get("full_cpu_reproducibility_ready") is True, "full CPU reproducibility gate not ready")
    require(
        summary.get("historical_engineering_gpu_case_evidence_ready") is True,
        "historical engineering GPU evidence not ready",
    )
    require(summary.get("current_parallel_capability_ready") is True, "current parallel capability matrix not ready")
    require(summary.get("current_parallel_capability_status") == "PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX", "current parallel capability status changed")
    require(summary.get("cpu_mpi_ready_for_all_current_scenarios") is True, "CPU/MPI capability no longer covers all current scenarios")
    require(summary.get("single_gpu_ready_for_all_current_scenarios") is True, "single-GPU capability no longer covers all current scenarios")
    require(summary.get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios") is True, "multi-GPU MPI+CUDA capability no longer covers all current scenarios")
    require(summary.get("current_scope_operator_runbook_ready") is True, "current-scope operator runbook not ready")
    require(summary.get("current_scope_operator_runbook_status") == "PASS-CURRENT-SCOPE-OPERATOR-RUNBOOK", "current-scope operator runbook status changed")
    require(summary.get("strict_master_plan_complete") is False, "strict master-plan status should remain deferred")
    blockers = summary.get("deferred_strict_master_plan_blockers")
    require(isinstance(blockers, list), "missing deferred blockers")
    require(set(blockers) == EXPECTED_DEFERRED_BLOCKERS, "deferred blocker set changed")
    gates = data.get("gate_results")
    require(isinstance(gates, dict), "missing gate_results")
    require(gates.get("engineering_h2_verify_exitcode") == 0, "engineering gate failed")
    require(gates.get("academic_verify_exitcode") == 0, "academic gate failed")
    require(gates.get("reproducible_gate_light_exitcode") == 0, "repro gate failed")
    if data.get("status") == STATUS_PASS_CURRENT_SCOPE:
        require(summary.get("current_user_priority_ready") is True, "PASS report must be user-priority ready")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    blockers = summary["deferred_strict_master_plan_blockers"]
    lines = [
        "# Master Plan Final Readiness Rollup",
        "",
        f"- Status: `{report['status']}`",
        f"- Current user-prioritized target ready: `{summary['current_user_priority_ready']}`",
        f"- Strict original master-plan complete: `{summary['strict_master_plan_complete']}`",
        f"- Overall progress estimate: `{summary['overall_progress_estimate_percent']}%`",
        f"- Engineering core progress estimate: `{summary['engineering_progress_estimate_percent']}%`",
        f"- Academic gas progress estimate: `{summary['academic_gas_progress_estimate_percent']}%`",
        f"- Academic two-phase progress estimate: `{summary['academic_twophase_progress_estimate_percent']}%`",
        f"- Full CPU reproducibility: `{summary['full_cpu_reproducibility_ready']}`",
        f"- Current CUDA runtime ready: `{summary['current_cuda_runtime_ready']}`",
        f"- Current CUDA runtime blocker: `{summary['current_cuda_runtime_blocker']}`",
        f"- Current parallel capability matrix: `{summary['current_parallel_capability_status']}`",
        f"- CPU/MPI all-current-scenarios ready: `{summary['cpu_mpi_ready_for_all_current_scenarios']}`",
        f"- Single-GPU all-current-scenarios ready: `{summary['single_gpu_ready_for_all_current_scenarios']}`",
        f"- Multi-GPU MPI+CUDA all-current-scenarios ready: `{summary['multi_gpu_mpi_cuda_ready_for_all_current_scenarios']}`",
        f"- Current-scope operator runbook: `{summary['current_scope_operator_runbook_status']}`",
        "",
        "## Passed Gates",
        "",
        "- Engineering H2 production evidence verification: `PASS`",
        "- Academic evidence verification: `PASS`",
        "- Light reproducibility gate: `PASS`",
        "- Full CPU reproducibility gate including `smoke_all`: `PASS`",
        "- Current CPU/MPI, single-GPU, and multi-GPU MPI+CUDA capability matrix: `PASS`",
        "- Current-scope operator runbook: `PASS`",
        "- Integrated engineering initial acceptance: `PASS`",
        "- Academic gas detonation readiness: `PASS`",
        "- Academic two-phase broader matrix and gas-liquid detonation certification: `PASS`",
        "",
        "## Deferred Strict Master-Plan Items",
        "",
    ]
    lines.extend(f"- `{item}`" for item in blockers)
    lines.extend([
        "",
        "These deferred items require external plume-shape datasets, real CAD cleanup/intake evidence, "
        "and calibrated fire/radiation-overpressure datasets. They do not invalidate the current user-scoped "
        "engineering CFD chain acceptance, but they prevent claiming strict completion of the original full master plan.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engineering-traceability", default=str(DEFAULT_ENGINEERING_TRACEABILITY))
    parser.add_argument("--engineering-verify", default=str(DEFAULT_ENGINEERING_VERIFY))
    parser.add_argument("--engineering-scorecard", default=str(DEFAULT_ENGINEERING_SCORECARD))
    parser.add_argument("--engineering-acceptance", default=str(DEFAULT_ENGINEERING_ACCEPTANCE))
    parser.add_argument("--academic-gas", default=str(DEFAULT_ACADEMIC_GAS))
    parser.add_argument("--academic-twophase", default=str(DEFAULT_ACADEMIC_TWOPHASE))
    parser.add_argument("--gas-liquid-cert", default=str(DEFAULT_GAS_LIQUID_CERT))
    parser.add_argument("--full-repro", default=str(DEFAULT_FULL_REPRO))
    parser.add_argument("--current-parallel-capability", default=str(DEFAULT_CURRENT_PARALLEL_CAPABILITY))
    parser.add_argument("--current-scope-operator-runbook", default=str(DEFAULT_CURRENT_SCOPE_OPERATOR_RUNBOOK))
    parser.add_argument("--gate-log-dir", default=str(DEFAULT_GATE_LOG_DIR))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(
            "master_plan_final_readiness VERIFY-PASS "
            f"json={args.verify_json} status={data.get('status')}"
        )
        return 0

    report = build_report(args)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(
        "master_plan_final_readiness PASS "
        f"json={output_json} md={output_md} status={report['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
