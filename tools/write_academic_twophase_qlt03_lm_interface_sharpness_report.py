#!/usr/bin/env python3
"""Write/verify QLT-03 low-Mach interface-sharpness diagnosis evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

STATUS_PASS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-INTERFACE-SHARPNESS-DIAGNOSIS"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing report: {path}")
    return json.loads(path.read_text())


def rel_drop(initial: float, final: float) -> float:
    if initial == 0.0:
        fail("cannot compute relative drop from zero initial value")
    return (initial - final) / initial


def nearest_sample(samples: list[dict], key: str, target: float) -> dict:
    return min(samples, key=lambda item: abs(float(item[key]) - target))


def build_report(repo_root: Path, output: Path) -> dict:
    t3_path = repo_root / (
        "docs/codex_audit/evidence/academic_twophase_qlt03_lm_t3_scout_20260730/"
        "academic_twophase_qlt03_lm_t3_scout_report.json"
    )
    grid_path = repo_root / (
        "docs/codex_audit/evidence/academic_twophase_qlt03_lm_t3_grid_confirmation_20260730/"
        "qlt03_lm_grid_confirmation_report.json"
    )
    curvature_path = repo_root / (
        "docs/codex_audit/evidence/academic_twophase_qlt03_lm_curvature_trials_20260730/"
        "curvature_trial_report.json"
    )
    t3 = load_json(t3_path)
    grid = load_json(grid_path)
    curvature = load_json(curvature_path)
    series = t3.get("time_series", {})
    samples = series.get("samples", [])
    if len(samples) < 10:
        fail("need dense QLT-03 time series for sharpness diagnosis")

    initial = samples[0]
    final = series.get("final", samples[-1])
    min_circ = min(float(s["circularity"]) for s in samples)
    max_interface_length = max(float(s["interface_length"]) for s in samples)
    min_circ_sample = nearest_sample(samples, "circularity", min_circ)
    max_length_sample = nearest_sample(samples, "interface_length", max_interface_length)
    initial_alpha_max = float(initial["alpha_max"])
    final_alpha_max = float(final["alpha_max"])
    alpha_max_relative_drop = rel_drop(initial_alpha_max, final_alpha_max)
    min_circ_alpha_drop = rel_drop(initial_alpha_max, float(min_circ_sample["alpha_max"]))
    final_center_error = float(
        t3.get("reference_errors", {}).get("center_of_mass_y_at_t3_abs_error", 999.0)
    )
    final_velocity_error = float(
        t3.get("reference_errors", {}).get("maximum_mean_rise_velocity_abs_error", 999.0)
    )
    min_circularity_error = float(
        t3.get("reference_errors", {}).get("minimum_circularity_abs_error", 999.0)
    )

    diagnosis = {
        "initial_alpha_max": initial_alpha_max,
        "final_alpha_max": final_alpha_max,
        "alpha_max_relative_drop": alpha_max_relative_drop,
        "min_circularity": min_circ,
        "min_circularity_time": min_circ_sample["time"],
        "min_circularity_alpha_max": min_circ_sample["alpha_max"],
        "min_circularity_alpha_max_relative_drop": min_circ_alpha_drop,
        "max_interface_length": max_interface_length,
        "max_interface_length_time": max_length_sample["time"],
        "time_gap_between_min_circularity_and_max_interface_length": abs(
            float(min_circ_sample["time"]) - float(max_length_sample["time"])
        ),
        "final_center_error": final_center_error,
        "maximum_rise_velocity_error": final_velocity_error,
        "minimum_circularity_error": min_circularity_error,
    }
    grid_status = grid.get("status")
    grid_metrics = grid.get("metrics", {})
    curvature_contracts = curvature.get("contracts", {})
    contracts = {
        "dense_time_series_available": len(samples) >= 10,
        "t3_stable_and_mass_conserved": (
            t3.get("contracts", {}).get("t3_final_time_reached") is True
            and t3.get("contracts", {}).get("alpha_mass_conserved") is True
        ),
        "alpha_peak_diffuses_substantially": alpha_max_relative_drop >= 0.50,
        "minimum_circularity_occurs_near_interface_length_peak": diagnosis[
            "time_gap_between_min_circularity_and_max_interface_length"
        ]
        <= 0.15,
        "center_and_velocity_errors_are_not_primary_blockers": (
            final_center_error <= 0.10 and final_velocity_error <= 0.10
        ),
        "minimum_circularity_is_primary_baseline_blocker": min_circularity_error > 0.15,
        "simple_curvature_smoothing_rejected": (
            curvature_contracts.get("no_rejected_trial_promoted") is True
        ),
        "grid_confirmation_keeps_two_phase_not_ready": str(grid_status).startswith("NOT_READY-"),
    }
    report = {
        "status": STATUS_PASS,
        "scope": (
            "QLT-03 low-Mach Aux-alpha interface-sharpness diagnosis using dense t=3 "
            "time-series evidence. This is a diagnostic/route-selection gate, not a "
            "claim that Hysing reference agreement is cleared."
        ),
        "inputs": {
            "t3_report": str(t3_path),
            "grid_confirmation_report": str(grid_path),
            "curvature_trial_report": str(curvature_path),
        },
        "sample_count": len(samples),
        "diagnosis": diagnosis,
        "grid_status": grid_status,
        "grid_metrics": grid_metrics,
        "contracts": contracts,
        "decision": {
            "qlt03_ready": False,
            "next_physics_priority": "sharper conservative interface transport with balanced-force CSF coupling",
            "reason": (
                "baseline center-height and maximum-rise-velocity errors are already within "
                "the current tolerances, while minimum circularity fails and coincides with "
                "large interface-length growth plus strong alpha-peak diffusion; simple "
                "curvature smoothing trials were rejected."
            ),
        },
    }
    validate_report(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def validate_report(report: dict) -> None:
    if report.get("status") != STATUS_PASS:
        fail(f"unexpected status: {report.get('status')}")
    contracts = report.get("contracts", {})
    missing = [key for key, value in contracts.items() if value is not True]
    if missing:
        fail(f"interface-sharpness diagnosis contracts not proven: {missing}")
    if report.get("decision", {}).get("qlt03_ready") is not False:
        fail("diagnosis report cannot mark QLT-03 ready")


def verify_json(path: Path) -> int:
    report = load_json(path)
    validate_report(report)
    print(f"academic_twophase_qlt03_lm_interface_sharpness VERIFY-PASS json={path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()
    if args.verify_json is not None:
        return verify_json(args.verify_json)
    if args.output is None:
        fail("--output is required unless --verify-json is used")
    report = build_report(args.repo_root.resolve(), args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
