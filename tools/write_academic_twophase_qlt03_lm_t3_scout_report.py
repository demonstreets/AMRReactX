#!/usr/bin/env python3
"""Write/verify QLT-03 low-Mach t=3 final-time and reference-gap evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import amrex_reader  # noqa: E402
from validate_academic_twophase_qlt03_lm_aux_bridge import field_metrics  # noqa: E402

STATUS_PASS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT"
STATUS_NOT_READY = "NOT_READY-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT"
MIN_TIME_SERIES_SAMPLES = 10


def fail(message: str) -> None:
    raise RuntimeError(message)


def compact_inputs(path: Path) -> str:
    return " ".join(" ".join(line.split("#", 1)[0].split()) for line in path.read_text(errors="replace").splitlines())


def get_reference_values(reference_report: dict) -> dict:
    reference = reference_report.get("reference", {})
    values = reference.get("case_1_contract", {}).get("representative_reference_values")
    if not isinstance(values, dict):
        values = reference.get("case_1", {}).get("representative_reference_values")
    if not isinstance(values, dict):
        values = reference.get("representative_reference_values")
    if not isinstance(values, dict):
        fail("missing Hysing Case 1 representative reference values")
    return values


def collect_timeseries(run_dir: Path) -> dict:
    plotfiles = sorted(p for p in run_dir.glob("plt*") if p.is_dir())
    if not plotfiles:
        fail(f"missing plotfiles for QLT-03 time-series comparison: {run_dir}")
    samples = []
    for plotfile in plotfiles:
        data = amrex_reader.read_plotfile(str(plotfile))
        metrics = field_metrics(data, "alpha")
        samples.append({"plotfile": str(plotfile), **metrics})
    max_velocity = max(s["mean_rise_velocity_y"] for s in samples if s["mean_rise_velocity_y"] is not None)
    min_circularity = min(s["circularity"] for s in samples)
    final = samples[-1]
    return {
        "run_dir": str(run_dir),
        "sample_count": len(samples),
        "samples": samples,
        "max_mean_rise_velocity_y": max_velocity,
        "min_circularity": min_circularity,
        "final": final,
    }


def build_report(repo_root: Path, inputs: Path, bridge_report: Path, reference_report: Path, run_dir: Path | None) -> dict:
    bridge = json.loads(bridge_report.read_text())
    reference = json.loads(reference_report.read_text())
    values = get_reference_values(reference)
    compact = compact_inputs(inputs)
    contracts = bridge.get("bridge_contracts", {})
    if run_dir is None:
        run_dir = bridge_report.parent / "run"
    series = collect_timeseries(run_dir)
    center_ref = float(values["center_of_mass_y_at_t3"])
    circularity_ref = float(values["minimum_circularity"])
    max_velocity_ref = float(values["maximum_mean_rise_velocity"])
    final = series["final"]
    center = float(final["alpha_center_y"])
    min_circularity = float(series["min_circularity"])
    max_velocity = float(series["max_mean_rise_velocity_y"])
    center_abs_error = abs(center - center_ref)
    circularity_abs_error = abs(min_circularity - circularity_ref)
    velocity_abs_error = abs(max_velocity - max_velocity_ref)
    reference_agreement = (
        center_abs_error <= 0.10
        and circularity_abs_error <= 0.15
        and velocity_abs_error <= 0.10
        and series["sample_count"] >= MIN_TIME_SERIES_SAMPLES
    )
    status = STATUS_PASS if reference_agreement else STATUS_NOT_READY
    report = {
        "status": status,
        "scope": (
            "QLT-03 low-Mach Aux-alpha t=3 scout with uncapped canonical sigma=24.5. "
            "The reference comparison uses final center-of-mass y and time-series "
            "extrema for mean rise velocity and circularity."
        ),
        "inputs": str(inputs),
        "bridge_report": str(bridge_report),
        "reference_report": str(reference_report),
        "time": bridge.get("time"),
        "time_series": series,
        "alpha_mass_relative_drift": bridge.get("alpha_mass_relative_drift"),
        "alpha_max": bridge.get("alpha_max"),
        "alpha_center_y_initial": bridge.get("initial_alpha_metrics", {}).get("alpha_center_y"),
        "alpha_center_y_final": center,
        "alpha_center_displacement": bridge.get("alpha_center_displacement"),
        "alpha_mean_rise_velocity_y_final": bridge.get("alpha_mean_rise_velocity_y"),
        "alpha_max_mean_rise_velocity_y": max_velocity,
        "alpha_circularity_final": bridge.get("alpha_circularity"),
        "alpha_min_circularity": min_circularity,
        "alpha_interface_length": bridge.get("alpha_interface_length"),
        "reference_values": {
            "center_of_mass_y_at_t3": center_ref,
            "minimum_circularity": circularity_ref,
            "maximum_mean_rise_velocity": max_velocity_ref,
        },
        "reference_errors": {
            "center_of_mass_y_at_t3_abs_error": center_abs_error,
            "minimum_circularity_abs_error": circularity_abs_error,
            "maximum_mean_rise_velocity_abs_error": velocity_abs_error,
        },
        "contracts": {
            "sigma_is_hysing_case1_value": "prob.surface_tension_sigma = 24.5" in compact,
            "csf_force_cap_disabled": "prob.surface_tension_force_cap = 0.0" in compact,
            "t3_final_time_reached": bridge.get("time", 0.0) >= 2.99,
            "short_log_has_no_nan_abort_or_segfault": contracts.get("run_log_has_no_nan_abort_or_segfault") is True,
            "alpha_mass_conserved": contracts.get("alpha_mass_conserved") is True,
            "alpha_bounded_0_1": contracts.get("alpha_bounded_0_1") is True,
            "alpha_center_of_mass_rises": contracts.get("alpha_center_of_mass_rises") is True,
            "canonical_observables_recorded": contracts.get("canonical_observables_recorded") is True,
            "time_series_extrema_used_for_reference": True,
            "time_series_sample_count_sufficient": series["sample_count"] >= MIN_TIME_SERIES_SAMPLES,
            "hysing_reference_agreement_cleared": reference_agreement,
        },
        "cleared_gates": [
            "uncapped canonical sigma=24.5 reaches t=3 without NaN/abort/segfault",
            "alpha mass remains conserved at t=3",
            "center-of-mass, mean-rise-velocity, circularity, and interface-length diagnostics are recorded through t=3",
        ],
        "remaining_qlt03_work": [] if reference_agreement else [
            "improve CSF curvature/balanced-force treatment so minimum circularity matches Hysing Case 1",
            "tighten time-series maximum rise-velocity agreement on refined grids",
            "keep QLT-03 t=3 comparisons on sufficiently dense time-series sampling before promotion",
            "use higher-resolution/grid-convergence evidence before final academic two-phase promotion",
        ],
    }
    validate_report(report)
    return report


def validate_report(report: dict) -> None:
    status = report.get("status")
    if status not in {STATUS_PASS, STATUS_NOT_READY}:
        fail(f"unexpected status: {status}")
    contracts = report.get("contracts", {})
    required_true = [
        "sigma_is_hysing_case1_value",
        "csf_force_cap_disabled",
        "t3_final_time_reached",
        "short_log_has_no_nan_abort_or_segfault",
        "alpha_mass_conserved",
        "alpha_bounded_0_1",
        "alpha_center_of_mass_rises",
        "canonical_observables_recorded",
        "time_series_extrema_used_for_reference",
    ]
    missing = [key for key in required_true if contracts.get(key) is not True]
    if missing:
        fail(f"t=3 scout contracts not proven: {missing}")
    if status == STATUS_PASS and contracts.get("hysing_reference_agreement_cleared") is not True:
        fail("PASS report must clear Hysing reference agreement")
    if status == STATUS_PASS and contracts.get("time_series_sample_count_sufficient") is not True:
        fail("PASS report must use sufficiently dense time-series sampling")
    if status == STATUS_NOT_READY and contracts.get("hysing_reference_agreement_cleared") is True:
        fail("NOT_READY report cannot clear Hysing reference agreement")
    if abs(float(report.get("alpha_mass_relative_drift", 1.0))) > 1.0e-12:
        fail("alpha mass drift too large")
    if float(report.get("alpha_max", 2.0)) > 1.0 + 1.0e-10:
        fail("alpha max exceeds bounded range")
    if float(report.get("alpha_min_circularity", 0.0)) <= 0.0:
        fail("minimum circularity must be positive")
    if float(report.get("alpha_interface_length", 0.0)) <= 0.0:
        fail("interface length must be positive")


def verify_json(path: Path) -> int:
    report = json.loads(path.read_text())
    validate_report(report)
    print(f"academic_twophase_qlt03_lm_t3_scout VERIFY-PASS json={path} status={report['status']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--bridge-report", type=Path)
    parser.add_argument("--reference-report", type=Path)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()
    if args.verify_json is not None:
        return verify_json(args.verify_json)
    if args.inputs is None or args.bridge_report is None or args.reference_report is None or args.output is None:
        fail("--inputs, --bridge-report, --reference-report, and --output are required unless --verify-json is used")
    report = build_report(args.repo_root, args.inputs, args.bridge_report, args.reference_report, args.run_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
