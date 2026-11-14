#!/usr/bin/env python3
"""Write or verify the academic gas-phase detonation priority matrix report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STATUS = "PASS-ACADEMIC-GAS-DETONATION-PRIORITY-MATRIX"
REPORT = Path(
    "docs/codex_audit/evidence/academic_gas_detonation_priority_matrix_20260731/"
    "academic_gas_detonation_priority_matrix_report.json"
)

GATES: dict[str, dict[str, Any]] = {
    "zero_d_ignition_reference": {
        "path": "docs/codex_audit/evidence/academic_gas_cantera_ignition_reference_20260724/cantera_ignition_reference_report.json",
        "expected_status": "PASS-ACADEMIC-GAS-CANTERA-IGNITION-REFERENCE",
        "summary_true": ["reference_curve_available", "delay_monotonic_decreases_with_temperature"],
        "role": "0D ignition-delay reference curve for gas chemistry sanity.",
    },
    "cantera_mechanism_comparison": {
        "path": "docs/codex_audit/evidence/academic_gas_cantera_mechanism_comparison_20260728/cantera_mechanism_comparison_report.json",
        "expected_status": "PASS-ACADEMIC-GAS-CANTERA-MECHANISM-COMPARISON",
        "summary_true": [
            "clears_cantera_mechanism_comparison_gap",
            "pelephysics_yaml_loads_in_cantera",
            "reaction_rate_samples_finite",
            "thermochemistry_samples_finite",
        ],
        "role": "Mechanism-level reference comparison against Cantera.",
    },
    "pelephysics_rate_kernel_equivalence": {
        "path": "docs/codex_audit/evidence/academic_gas_pelephysics_rate_kernel_equivalence_20260728/pelephysics_rate_kernel_equivalence_report.json",
        "expected_status": "PASS-ACADEMIC-GAS-PELEPHYSICS-RATE-KERNEL-EQUIVALENCE",
        "summary_true": ["clears_acd_02_rate_kernel_gap", "clears_full_pelephysics_source_rate_equivalence"],
        "summary_limits": {
            "max_active_wdot_relative_error": 1.0e-5,
            "max_cp_mass_relative_error": 1.0e-10,
            "max_density_relative_error": 1.0e-11,
        },
        "role": "Compiled PelePhysics rate kernel equivalence.",
    },
    "two_d_detonation_reference": {
        "path": "docs/codex_audit/evidence/academic_gas_2d_detonation_reference_20260728/academic_gas_2d_detonation_reference_report.json",
        "expected_status": "PASS-ACADEMIC-GAS-2D-DETONATION-REFERENCE",
        "min_case_count": 3,
        "summary_true": ["clears_two_d_detonation_reference_validation_gap"],
        "summary_limits": {
            "max_mass_rel": 1.0e-10,
            "max_species_closure_rel": 1.0e-3,
            "speed_rel_spread": 0.35,
            "medium_fine_speed_rel_diff": 0.25,
        },
        "role": "2D detonation propagation and resolution-consistency evidence.",
    },
    "three_d_detonation_reference": {
        "path": "docs/codex_audit/evidence/academic_gas_3d_detonation_reference_20260728/academic_gas_3d_detonation_reference_report.json",
        "expected_status": "PASS-ACADEMIC-GAS-3D-DETONATION-REFERENCE",
        "min_case_count": 3,
        "summary_true": ["clears_three_d_detonation_reference_validation_gap"],
        "summary_limits": {
            "max_mass_rel": 1.0e-9,
            "max_species_closure_rel": 1.0e-12,
            "speed_rel_spread": 0.35,
            "medium_fine_speed_rel_diff": 0.25,
        },
        "role": "3D detonation propagation and resolution-consistency evidence.",
    },
    "detonation_front_amr": {
        "path": "docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/academic_gas_detonation_front_amr_validation_report.json",
        "expected_status": "PASS-ACADEMIC-GAS-DETONATION-FRONT-AMR-VALIDATION",
        "min_case_count": 2,
        "summary_true": ["clears_detonation_front_amr_validation_gap"],
        "summary_limits": {
            "max_mass_rel": 1.0e-9,
            "max_species_closure_rel": 1.0e-12,
            "amr_uniform_speed_rel_diff": 0.3,
            "amr_refined_cell_fraction": 0.85,
        },
        "role": "AMR tracks the detonation front while matching uniform-fine propagation.",
    },
    "mpi_cuda_detonation_runtime": {
        "path": "docs/codex_audit/evidence/academic_gas_detonation_mpi_cuda_20260731/academic_gas_detonation_mpi_cuda_report.json",
        "expected_status": "PASS-ACADEMIC-GAS-DETONATION-MPI-CUDA",
        "summary_true": [
            "academic_gas_detonation_mpi_cuda_ready",
            "time_advanced",
            "reaction_solver_marker_present",
            "amrex_finalized",
            "critical_plot_variables_present",
        ],
        "summary_minimums": {
            "mpi_ranks": 2,
            "cuda_devices": 2,
            "max_step": 40,
        },
        "role": "Gas detonation reacting runtime gate on 2 MPI ranks and 2 CUDA devices.",
    },
    "weno5_convergence": {
        "path": "docs/codex_audit/evidence/academic_weno5_convergence_validation_20260729/academic_weno5_convergence_validation_report.json",
        "expected_status": "PASS-ACADEMIC-WENO5-CONVERGENCE-VALIDATION",
        "summary_true": ["clears_acd_01_weno5_order_gap", "clears_qlt_03_weno5_mms_order_subgap"],
        "summary_limits": {
            "weno_to_second_order_error_ratio": 0.02,
        },
        "summary_minimums": {
            "standalone_weno5_sine_order": 4.5,
            "pelec_weno5z_p32_64": 4.5,
            "pelec_weno5z_p64_128": 4.5,
        },
        "role": "High-order WENO foundation for gas detonation numerics.",
    },
    "double_mach_shock": {
        "path": "docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/academic_gas_double_mach_validation_report.json",
        "expected_status": "PASS-ACADEMIC-GAS-DOUBLE-MACH-VALIDATION",
        "summary_true": ["clears_qlt_03_double_mach_gap"],
        "summary_minimums": {
            "front_x": 0.278926,
        },
        "role": "Strong-shock gas dynamics sanity check adjacent to detonation use.",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing required report: {path}")
    return json.loads(path.read_text())


def get_summary(data: dict[str, Any]) -> dict[str, Any]:
    summary = data.get("summary")
    return summary if isinstance(summary, dict) else {}


def evaluate_gate(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    path = Path(spec["path"])
    data = load_json(path)
    summary = get_summary(data)
    failures: list[str] = []

    status = data.get("status")
    if status != spec["expected_status"]:
        failures.append(f"status {status!r} != {spec['expected_status']!r}")

    min_case_count = spec.get("min_case_count")
    case_count = data.get("case_count", summary.get("case_count"))
    if min_case_count is not None:
        if not isinstance(case_count, (int, float)) or case_count < min_case_count:
            failures.append(f"case_count {case_count!r} < {min_case_count}")

    for key in spec.get("summary_true", []):
        if summary.get(key) is not True:
            failures.append(f"summary.{key} is not true")

    for key, limit in spec.get("summary_limits", {}).items():
        value = summary.get(key)
        if not isinstance(value, (int, float)) or abs(value) > limit:
            failures.append(f"summary.{key} {value!r} exceeds {limit}")

    for key, minimum in spec.get("summary_minimums", {}).items():
        value = summary.get(key)
        if not isinstance(value, (int, float)) or value < minimum:
            failures.append(f"summary.{key} {value!r} below {minimum}")

    return {
        "name": name,
        "status": "PASS" if not failures else "FAIL",
        "source_report": str(path),
        "source_status": status,
        "role": spec["role"],
        "case_count": case_count,
        "failures": failures,
        "evidence_hash": data.get("evidence_hash"),
        "key_summary": {
            key: summary.get(key)
            for key in sorted(
                set(spec.get("summary_true", []))
                | set(spec.get("summary_limits", {}).keys())
                | set(spec.get("summary_minimums", {}).keys())
            )
        },
    }


def build_report() -> dict[str, Any]:
    gates = [evaluate_gate(name, spec) for name, spec in GATES.items()]
    failed = [gate for gate in gates if gate["status"] != "PASS"]
    return {
        "status": STATUS if not failed else "NOT_READY-ACADEMIC-GAS-DETONATION-PRIORITY-MATRIX",
        "scope": "academic gas-phase detonation priority after engineering-scope closure",
        "ready": not failed,
        "strict_external_literature_detonation_benchmark": "not claimed; this gate proves current in-repo 0D/2D/3D/AMR/numerics readiness only",
        "gate_count": len(gates),
        "pass_count": len(gates) - len(failed),
        "fail_count": len(failed),
        "gates": gates,
        "summary": {
            "academic_gas_priority_ready": not failed,
            "covers_zero_d_chemistry": True,
            "covers_compiled_rate_kernel": True,
            "covers_two_d_detonation": True,
            "covers_three_d_detonation": True,
            "covers_detonation_front_amr": True,
            "covers_mpi_cuda_detonation_runtime": True,
            "covers_high_order_weno": True,
            "covers_strong_shock_gas_dynamics": True,
            "remaining_strict_literature_benchmark_gap": True,
        },
    }


def verify_report(path: Path) -> None:
    expected = build_report()
    actual = load_json(path)
    if actual.get("status") != STATUS:
        raise SystemExit(f"status is not pass: {actual.get('status')}")
    if actual.get("ready") is not True:
        raise SystemExit("report ready flag is not true")
    actual_gates = {gate.get("name"): gate for gate in actual.get("gates", [])}
    expected_gates = {gate.get("name"): gate for gate in expected.get("gates", [])}
    missing = sorted(set(expected_gates) - set(actual_gates))
    if missing:
        raise SystemExit(f"missing gates: {missing}")
    for name, gate in expected_gates.items():
        actual_gate = actual_gates[name]
        if actual_gate.get("status") != "PASS":
            raise SystemExit(f"gate {name} is not pass in report")
        if gate.get("status") != "PASS":
            raise SystemExit(f"source evidence no longer passes for gate {name}: {gate.get('failures')}")
        if actual_gate.get("source_status") != gate.get("source_status"):
            raise SystemExit(f"gate {name} source status drifted")
    print(f"academic_gas_detonation_priority_matrix VERIFY-PASS json={path} status={actual.get('status')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=REPORT)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()

    if args.verify_json:
        verify_report(args.verify_json)
        return 0

    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.output} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
