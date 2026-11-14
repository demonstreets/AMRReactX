#!/usr/bin/env python3
"""Write or verify the academic current-priority scope rollup."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STATUS = "PASS-ACADEMIC-CURRENT-PRIORITY-SCOPE"
NOT_READY = "NOT_READY-ACADEMIC-CURRENT-PRIORITY-SCOPE"
REPORT = Path(
    "docs/codex_audit/evidence/academic_current_priority_scope_20260731/"
    "academic_current_priority_scope_report.json"
)

SOURCES = {
    "gas_detonation_priority": {
        "path": "docs/codex_audit/evidence/academic_gas_detonation_priority_matrix_20260731/academic_gas_detonation_priority_matrix_report.json",
        "status": "PASS-ACADEMIC-GAS-DETONATION-PRIORITY-MATRIX",
        "ready_field": "ready",
        "priority": 1,
        "claim": "gas-phase 0D/2D/3D detonation, AMR-front tracking, WENO5, strong-shock, chemistry/rate-kernel and 2GPU MPI+CUDA readiness",
    },
    "gas_liquid_detonation_certification": {
        "path": "docs/codex_audit/evidence/academic_gas_liquid_detonation_certification_20260731/academic_gas_liquid_detonation_certification_report.json",
        "status": "PASS-ACADEMIC-GAS-LIQUID-DETONATION-CERTIFICATION",
        "summary_true": [
            "acd_07_full_gas_liquid_detonation_ready",
            "clears_acd_07_full_cellular_gas_liquid_detonation_gap",
            "clears_acd_07_spray_detonation_gap",
            "coupled_budget_ready",
        ],
        "priority": 2,
        "claim": "reacting gas-liquid/spray detonation response and closed coupled-budget readiness",
    },
    "gas_liquid_detonation_cuda_scout": {
        "path": "docs/codex_audit/evidence/academic_gas_liquid_detonation_cuda_scout_20260731/academic_gas_liquid_detonation_cuda_scout_report.json",
        "status": "PASS-ACADEMIC-GAS-LIQUID-DETONATION-CUDA-SCOUT",
        "summary_true": [
            "academic_gas_liquid_detonation_cuda_scout_ready",
            "single_gpu_reacting_spray_ready",
            "mpi_cuda_reacting_spray_ready",
            "reaction_solver_marker_present",
            "spray_particle_output_present",
            "spray_source_terms_present",
            "time_advanced",
        ],
        "priority": 3,
        "claim": "reacting heptane-air droplet/spray detonation scout on single GPU and 2-rank/2-device MPI+CUDA",
    },
    "gas_liquid_detonation_mpi_cuda_long": {
        "path": "docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_long_20260803/academic_gas_liquid_detonation_mpi_cuda_long_report.json",
        "status": "PASS-ACADEMIC-GAS-LIQUID-DETONATION-MPI-CUDA-LONG",
        "summary_true": [
            "academic_gas_liquid_detonation_mpi_cuda_long_ready",
            "mpi_cuda_reacting_spray_300step_ready",
            "time_advanced",
            "reaction_solver_marker_present",
            "amrex_finalized",
            "spray_particle_output_present",
            "spray_source_terms_present",
        ],
        "priority": 4,
        "claim": "300-step reacting heptane-air droplet/spray detonation stability gate on 2-rank/2-device MPI+CUDA",
    },
    "gas_liquid_detonation_mpi_cuda_extended": {
        "path": "docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_extended_20260803/academic_gas_liquid_detonation_mpi_cuda_extended_report.json",
        "status": "PASS-ACADEMIC-GAS-LIQUID-DETONATION-MPI-CUDA-EXTENDED",
        "summary_true": [
            "academic_gas_liquid_detonation_mpi_cuda_extended_ready",
            "mpi_cuda_reacting_spray_1000step_ready",
            "time_advanced",
            "reaction_solver_marker_present",
            "amrex_finalized",
            "spray_particle_output_present",
            "spray_source_terms_present",
        ],
        "priority": 5,
        "claim": "1000-step reacting heptane-air droplet/spray detonation extended stability gate on 2-rank/2-device MPI+CUDA",
    },
    "twophase_broader_matrix": {
        "path": "docs/codex_audit/evidence/academic_twophase_broader_matrix_20260730/academic_twophase_broader_matrix_report.json",
        "status": "PASS-ACADEMIC-TWOPHASE-BROADER-MATRIX-AUDIT",
        "summary_true": [
            "academic_twophase_broader_matrix_ready",
            "acd_04_vof_core_ready",
            "acd_06_csf_ready",
            "acd_08_interface_amr_ready",
            "shock_bubble_independent_validation_ready",
            "closed_gas_particle_coupled_budget_ready",
        ],
        "priority": 6,
        "claim": "broader gas-liquid/two-phase matrix, including VOF, CSF, interface AMR, shock-bubble and gas-particle budgets",
    },
    "readiness_qlt03_delta": {
        "path": "docs/codex_audit/evidence/academic_readiness_qlt03_closure_delta_20260730/academic_readiness_qlt03_closure_delta_report.json",
        "status": "PASS-ACADEMIC-READINESS-QLT03-CSF-STRESS-DELTA",
        "summary_true": [
            "academic_twophase_qlt03_low_mach_hysing_case1_ready",
        ],
        "priority": 7,
        "claim": "QLT-03/Hysing low-Mach CSF-stress closure supersedes older low-Mach two-phase blocker",
    },
    "historical_readiness_summary": {
        "path": "docs/codex_audit/evidence/academic_readiness_summary_20260729/academic_readiness_summary_report.json",
        "status": "PASS-ACADEMIC-INITIAL-CPU-READINESS",
        "priority": 8,
        "claim": "historical baseline retained for traceability; later reports supersede current-priority blocking gaps",
    },
    "academic_gpu_environment": {
        "path": "docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728/academic_gpu_environment_preflight_report.json",
        "status": "PASS-ACADEMIC-GPU-ENVIRONMENT-PREFLIGHT",
        "summary_true": [
            "ready_for_acd_10_gpu_credit",
            "ready_for_qlt_05_gpu_compliance_credit",
        ],
        "priority": 9,
        "claim": "academic CUDA/GPU runtime and detonation smoke preflight readiness",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing required report: {path}")
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise TypeError(f"report is not a JSON object: {path}")
    return data


def summary_of(data: dict[str, Any]) -> dict[str, Any]:
    summary = data.get("summary")
    return summary if isinstance(summary, dict) else {}


def evaluate_source(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    path = Path(spec["path"])
    data = load_json(path)
    summary = summary_of(data)
    failures: list[str] = []

    if data.get("status") != spec["status"]:
        failures.append(f"status {data.get('status')!r} != {spec['status']!r}")

    ready_field = spec.get("ready_field")
    if ready_field and data.get(ready_field) is not True:
        failures.append(f"{ready_field} is not true")

    for key in spec.get("summary_true", []):
        if summary.get(key) is not True:
            failures.append(f"summary.{key} is not true")

    return {
        "name": name,
        "priority": spec["priority"],
        "status": "PASS" if not failures else "FAIL",
        "source_report": str(path),
        "source_status": data.get("status"),
        "claim": spec["claim"],
        "failures": failures,
    }


def build_report() -> dict[str, Any]:
    gates = [evaluate_source(name, spec) for name, spec in SOURCES.items()]
    gates.sort(key=lambda item: item["priority"])
    failed = [gate for gate in gates if gate["status"] != "PASS"]

    historical = load_json(Path(SOURCES["historical_readiness_summary"]["path"]))
    old_gaps = summary_of(historical).get("blocking_gap_count")

    superseded_historical_gaps = {
        "qlt_03_canonical_bubble_rise_reference": "superseded by academic_readiness_qlt03_closure_delta and twophase broader matrix",
        "acd_07_full_gas_liquid_detonation": "superseded by academic_gas_liquid_detonation_certification",
        "academic_twophase_broader_non_qlt_matrix": "superseded by academic_twophase_broader_matrix",
    }

    return {
        "status": STATUS if not failed else NOT_READY,
        "ready": not failed,
        "scope": "academic current priority after engineering-scene closure: gas first, gas-liquid/two-phase second",
        "priority_order": [
            "gas_phase_detonation",
            "gas_liquid_reacting_spray_detonation",
            "gas_liquid_reacting_spray_mpi_cuda_scout",
            "gas_liquid_reacting_spray_mpi_cuda_300step",
            "gas_liquid_reacting_spray_mpi_cuda_1000step",
            "broader_two_phase_matrix",
            "academic_gpu_environment",
        ],
        "gate_count": len(gates),
        "pass_count": len(gates) - len(failed),
        "fail_count": len(failed),
        "gates": gates,
        "summary": {
            "academic_current_priority_ready": not failed,
            "gas_phase_priority_ready": gates[0]["status"] == "PASS",
            "gas_phase_mpi_cuda_runtime_inherited_from_priority_matrix": gates[0]["status"] == "PASS",
            "gas_liquid_priority_ready": gates[1]["status"] == "PASS"
            and gates[2]["status"] == "PASS"
            and gates[3]["status"] == "PASS"
            and gates[4]["status"] == "PASS"
            and gates[5]["status"] == "PASS",
            "gas_liquid_mpi_cuda_scout_ready": gates[2]["status"] == "PASS",
            "gas_liquid_mpi_cuda_long_ready": gates[3]["status"] == "PASS",
            "gas_liquid_mpi_cuda_extended_ready": gates[4]["status"] == "PASS",
            "historical_readiness_blocking_gap_count": old_gaps,
            "historical_readiness_gaps_superseded": not failed,
            "academic_gpu_runtime_ready": gates[-1]["status"] == "PASS",
            "strict_external_literature_benchmarks_not_claimed_here": True,
        },
        "superseded_historical_gaps": superseded_historical_gaps,
        "interpretation": (
            "This report is the authoritative current academic-priority rollup. "
            "Older academic readiness summaries remain as historical baselines and must not be used alone "
            "to downgrade the current gas/gas-liquid academic priority status."
        ),
    }


def verify(path: Path) -> None:
    current = build_report()
    data = load_json(path)
    if data.get("status") != STATUS:
        raise SystemExit(f"status is not pass: {data.get('status')}")
    if data.get("ready") is not True:
        raise SystemExit("ready flag is not true")
    if data.get("summary", {}).get("academic_current_priority_ready") is not True:
        raise SystemExit("academic current priority summary is not ready")
    if data.get("summary", {}).get("historical_readiness_gaps_superseded") is not True:
        raise SystemExit("historical readiness gaps were not marked superseded")
    if data.get("summary", {}).get("academic_gpu_runtime_ready") is not True:
        raise SystemExit("academic GPU runtime summary is not ready")
    current_gates = {gate["name"]: gate for gate in current["gates"]}
    actual_gates = {gate["name"]: gate for gate in data.get("gates", [])}
    if set(current_gates) != set(actual_gates):
        raise SystemExit("gate set drifted")
    for name, gate in current_gates.items():
        if gate["status"] != "PASS":
            raise SystemExit(f"source gate no longer passes: {name}: {gate['failures']}")
        if actual_gates[name].get("status") != "PASS":
            raise SystemExit(f"recorded gate is not pass: {name}")
        if actual_gates[name].get("source_status") != gate["source_status"]:
            raise SystemExit(f"recorded source status drifted for {name}")
    print(f"academic_current_priority_scope VERIFY-PASS json={path} status={data.get('status')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=REPORT)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()
    if args.verify_json:
        verify(args.verify_json)
        return 0
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.output} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
