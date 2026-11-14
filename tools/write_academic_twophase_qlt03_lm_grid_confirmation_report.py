#!/usr/bin/env python3
"""Write/verify QLT-03 low-Mach 32/64 grid-confirmation evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

STATUS = "NOT_READY-ACADEMIC-TWOPHASE-QLT03-LM-GRID-CONFIRMATION"
MIN_TIME_SERIES_SAMPLES = 10


def fail(message: str) -> None:
    raise RuntimeError(message)


def load(path: Path) -> dict:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        fail(f"JSON root is not an object: {path}")
    return data


def build_report(coarse_report: Path, fine_report: Path, output: Path | None = None) -> dict:
    coarse = load(coarse_report)
    fine = load(fine_report)
    center_delta = abs(float(fine["alpha_center_y_final"]) - float(coarse["alpha_center_y_final"]))
    max_v_delta = abs(float(fine["alpha_max_mean_rise_velocity_y"]) - float(coarse["alpha_max_mean_rise_velocity_y"]))
    min_c_delta = abs(float(fine["alpha_min_circularity"]) - float(coarse["alpha_min_circularity"]))
    fine_errors = fine.get("reference_errors", {})
    coarse_errors = coarse.get("reference_errors", {})
    report = {
        "status": STATUS,
        "scope": "QLT-03 low-Mach grid confirmation comparing 32x64 and 64x128 t=3 evidence under the same canonical Hysing settings.",
        "coarse_report": str(coarse_report),
        "fine_report": str(fine_report),
        "coarse_status": coarse.get("status"),
        "fine_status": fine.get("status"),
        "coarse_metrics": {
            "sample_count": coarse.get("time_series", {}).get("sample_count"),
            "center_y_final": coarse.get("alpha_center_y_final"),
            "max_mean_rise_velocity_y": coarse.get("alpha_max_mean_rise_velocity_y"),
            "min_circularity": coarse.get("alpha_min_circularity"),
            "mass_relative_drift": coarse.get("alpha_mass_relative_drift"),
        },
        "fine_metrics": {
            "sample_count": fine.get("time_series", {}).get("sample_count"),
            "center_y_final": fine.get("alpha_center_y_final"),
            "max_mean_rise_velocity_y": fine.get("alpha_max_mean_rise_velocity_y"),
            "min_circularity": fine.get("alpha_min_circularity"),
            "mass_relative_drift": fine.get("alpha_mass_relative_drift"),
        },
        "grid_differences": {
            "center_y_final_abs_delta": center_delta,
            "max_mean_rise_velocity_abs_delta": max_v_delta,
            "min_circularity_abs_delta": min_c_delta,
        },
        "reference_errors": {
            "coarse": coarse_errors,
            "fine": fine_errors,
        },
        "contracts": {
            "coarse_reaches_t3": coarse.get("contracts", {}).get("t3_final_time_reached") is True,
            "fine_reaches_t3": fine.get("contracts", {}).get("t3_final_time_reached") is True,
            "coarse_mass_conserved": coarse.get("contracts", {}).get("alpha_mass_conserved") is True,
            "fine_mass_conserved": fine.get("contracts", {}).get("alpha_mass_conserved") is True,
            "coarse_time_series_sample_count_sufficient": coarse.get("contracts", {}).get("time_series_sample_count_sufficient") is True or int(coarse.get("time_series", {}).get("sample_count", 0)) >= MIN_TIME_SERIES_SAMPLES,
            "fine_time_series_sample_count_sufficient": fine.get("contracts", {}).get("time_series_sample_count_sufficient") is True or int(fine.get("time_series", {}).get("sample_count", 0)) >= MIN_TIME_SERIES_SAMPLES,
            "center_height_grid_consistency_cleared": center_delta <= 0.02,
            "fine_center_reference_error_cleared": float(fine_errors.get("center_of_mass_y_at_t3_abs_error", 1.0)) <= 0.10,
            "velocity_grid_consistency_cleared": max_v_delta <= 0.10,
            "circularity_grid_consistency_cleared": min_c_delta <= 0.10,
            "fine_velocity_reference_error_cleared": float(fine_errors.get("maximum_mean_rise_velocity_abs_error", 1.0)) <= 0.10,
            "fine_circularity_reference_error_cleared": float(fine_errors.get("minimum_circularity_abs_error", 1.0)) <= 0.15,
            "full_grid_confirmation_cleared": False,
        },
        "cleared_gates": [
            "32x64 and 64x128 both reach t=3 without recorded NaN/Abort/Segfault",
            "alpha mass is conserved on both grids",
            "final center-of-mass height is grid-consistent and within the Hysing center-y tolerance on the fine grid",
        ],
        "remaining_gates": [
            "64x128 fine-grid time series needs at least 10 samples before shape/velocity extrema can be promoted",
            "minimum circularity is not grid-converged and remains below the Hysing Case 1 tolerance",
            "maximum mean rise velocity overshoots the Hysing Case 1 reference on the 64x128 run",
            "CSF curvature/balanced-force treatment needs improvement before claiming strict QLT-03 academic completion",
        ],
    }
    validate_report(report)
    return report


def validate_report(report: dict) -> None:
    if report.get("status") != STATUS:
        fail(f"unexpected status: {report.get('status')}")
    contracts = report.get("contracts", {})
    required_true = [
        "coarse_reaches_t3",
        "fine_reaches_t3",
        "coarse_mass_conserved",
        "fine_mass_conserved",
        "center_height_grid_consistency_cleared",
        "fine_center_reference_error_cleared",
    ]
    missing = [key for key in required_true if contracts.get(key) is not True]
    if missing:
        fail(f"grid-confirmation required contracts not proven: {missing}")
    if contracts.get("full_grid_confirmation_cleared") is True:
        fail("grid confirmation should not be fully cleared while velocity/circularity gates remain open")
    if contracts.get("fine_circularity_reference_error_cleared") is True and contracts.get("fine_velocity_reference_error_cleared") is True:
        fail("status should be promoted before all refined reference gates are true")


def verify_json(path: Path) -> int:
    report = load(path)
    validate_report(report)
    print(f"academic_twophase_qlt03_lm_grid_confirmation VERIFY-PASS json={path} status={report['status']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coarse-report", type=Path)
    parser.add_argument("--fine-report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()
    if args.verify_json is not None:
        return verify_json(args.verify_json)
    if args.coarse_report is None or args.fine_report is None or args.output is None:
        fail("--coarse-report, --fine-report, and --output are required unless --verify-json is used")
    report = build_report(args.coarse_report, args.fine_report, args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
