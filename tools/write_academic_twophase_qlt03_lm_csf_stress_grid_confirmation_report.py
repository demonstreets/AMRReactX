#!/usr/bin/env python3
"""Write/verify QLT-03 CSF stress-divergence grid-confirmation evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STATUS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-CSF-STRESS-GRID-CONFIRMATION"
T3_STATUS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT"


def fail(message: str) -> None:
    raise RuntimeError(message)


def read_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    return json.loads(path.read_text())


def build_report(repo_root: Path, coarse_report_path: Path, fine_report_path: Path) -> dict:
    coarse = read_json(coarse_report_path)
    fine = read_json(fine_report_path)
    if coarse.get("status") != T3_STATUS:
        fail(f"unexpected coarse status: {coarse.get('status')}")
    if fine.get("status") != T3_STATUS:
        fail(f"unexpected fine status: {fine.get('status')}")
    c_errors = coarse.get("reference_errors", {})
    f_errors = fine.get("reference_errors", {})
    c_contracts = coarse.get("contracts", {})
    f_contracts = fine.get("contracts", {})
    center_delta = abs(float(fine["alpha_center_y_final"]) - float(coarse["alpha_center_y_final"]))
    max_v_delta = abs(float(fine["alpha_max_mean_rise_velocity_y"]) - float(coarse["alpha_max_mean_rise_velocity_y"]))
    min_c_delta = abs(float(fine["alpha_min_circularity"]) - float(coarse["alpha_min_circularity"]))
    inputs = (repo_root / "examples/academic/qlt03_lm_aux_bridge/inputs").read_text(errors="replace")
    report = {
        "status": STATUS,
        "scope": (
            "QLT-03 low-Mach grid confirmation for the preferred continuum-surface-stress "
            "CSF force form, comparing 32x64 and 64x128 t=3 Hysing Case 1 evidence."
        ),
        "evidence": {
            "coarse_report": str(coarse_report_path),
            "fine_report": str(fine_report_path),
            "qlt03_inputs": "examples/academic/qlt03_lm_aux_bridge/inputs",
        },
        "coarse_status": coarse.get("status"),
        "fine_status": fine.get("status"),
        "coarse_metrics": {
            "sample_count": coarse.get("time_series", {}).get("sample_count"),
            "center_y_final": coarse.get("alpha_center_y_final"),
            "max_mean_rise_velocity_y": coarse.get("alpha_max_mean_rise_velocity_y"),
            "min_circularity": coarse.get("alpha_min_circularity"),
            "mass_relative_drift": coarse.get("alpha_mass_relative_drift"),
            "reference_errors": c_errors,
        },
        "fine_metrics": {
            "sample_count": fine.get("time_series", {}).get("sample_count"),
            "center_y_final": fine.get("alpha_center_y_final"),
            "max_mean_rise_velocity_y": fine.get("alpha_max_mean_rise_velocity_y"),
            "min_circularity": fine.get("alpha_min_circularity"),
            "mass_relative_drift": fine.get("alpha_mass_relative_drift"),
            "reference_errors": f_errors,
        },
        "grid_differences": {
            "center_y_final_abs_delta": center_delta,
            "max_mean_rise_velocity_abs_delta": max_v_delta,
            "min_circularity_abs_delta": min_c_delta,
        },
        "contracts": {
            "qlt03_inputs_promote_force_form_3": "prob.surface_tension_force_form = 3" in inputs,
            "coarse_reaches_t3": c_contracts.get("t3_final_time_reached") is True,
            "fine_reaches_t3": f_contracts.get("t3_final_time_reached") is True,
            "coarse_reference_agreement_cleared": c_contracts.get("hysing_reference_agreement_cleared") is True,
            "fine_reference_agreement_cleared": f_contracts.get("hysing_reference_agreement_cleared") is True,
            "coarse_sample_count_sufficient": c_contracts.get("time_series_sample_count_sufficient") is True,
            "fine_sample_count_sufficient": f_contracts.get("time_series_sample_count_sufficient") is True,
            "coarse_mass_conserved": c_contracts.get("alpha_mass_conserved") is True,
            "fine_mass_conserved": f_contracts.get("alpha_mass_conserved") is True,
            "center_height_grid_consistency_cleared": center_delta <= 0.02,
            "max_rise_velocity_grid_consistency_cleared": max_v_delta <= 0.05,
            "minimum_circularity_grid_consistency_cleared": min_c_delta <= 0.05,
            "fine_center_reference_error_cleared": float(f_errors.get("center_of_mass_y_at_t3_abs_error", 1.0)) <= 0.10,
            "fine_velocity_reference_error_cleared": float(f_errors.get("maximum_mean_rise_velocity_abs_error", 1.0)) <= 0.10,
            "fine_circularity_reference_error_cleared": float(f_errors.get("minimum_circularity_abs_error", 1.0)) <= 0.15,
            "full_grid_confirmation_cleared": True,
        },
        "decision": {
            "promote_force_form_3_for_qlt03_example": True,
            "qlt03_low_mach_csf_stress_grid_confirmed": True,
            "promote_full_academic_twophase_readiness": False,
            "remaining_work": [
                "refresh the older QLT-03 path-decision/readiness summary records so they no longer describe the pre-stress baseline as the preferred route",
                "optionally run higher-resolution or AMR confirmation before claiming broad two-phase academic production readiness",
                "keep non-QLT two-phase cases and spray/two-way-coupling readiness gates separate",
            ],
        },
    }
    verify(report)
    return report


def verify(report: dict) -> None:
    if report.get("status") != STATUS:
        fail(f"unexpected status: {report.get('status')}")
    contracts = report.get("contracts", {})
    required_true = (
        "qlt03_inputs_promote_force_form_3",
        "coarse_reaches_t3",
        "fine_reaches_t3",
        "coarse_reference_agreement_cleared",
        "fine_reference_agreement_cleared",
        "coarse_sample_count_sufficient",
        "fine_sample_count_sufficient",
        "coarse_mass_conserved",
        "fine_mass_conserved",
        "center_height_grid_consistency_cleared",
        "max_rise_velocity_grid_consistency_cleared",
        "minimum_circularity_grid_consistency_cleared",
        "fine_center_reference_error_cleared",
        "fine_velocity_reference_error_cleared",
        "fine_circularity_reference_error_cleared",
        "full_grid_confirmation_cleared",
    )
    missing = [key for key in required_true if contracts.get(key) is not True]
    if missing:
        fail(f"CSF stress grid contracts not true: {missing}")
    decision = report.get("decision", {})
    if decision.get("promote_force_form_3_for_qlt03_example") is not True:
        fail("force_form=3 must be promoted for the QLT-03 example")
    if decision.get("promote_full_academic_twophase_readiness") is not False:
        fail("full academic two-phase readiness remains broader than QLT-03")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--coarse-report", type=Path)
    parser.add_argument("--fine-report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()
    if args.verify_json is not None:
        verify(read_json(args.verify_json))
        return 0
    if args.coarse_report is None or args.fine_report is None or args.output is None:
        fail("--coarse-report, --fine-report, and --output are required unless --verify-json is used")
    report = build_report(args.repo_root, args.coarse_report, args.fine_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
