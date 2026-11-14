#!/usr/bin/env python3
"""Write/verify QLT-03 low-Mach curvature-trial rejection evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

STATUS_PASS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-CURVATURE-TRIAL-REJECTION"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing report: {path}")
    return json.loads(path.read_text())


def trial_summary(name: str, path: Path) -> dict:
    data = load_json(path)
    contracts = data.get("contracts", {})
    errors = data.get("reference_errors", {})
    required_contracts = {
        "t3_final_time_reached": True,
        "short_log_has_no_nan_abort_or_segfault": True,
        "alpha_mass_conserved": True,
        "alpha_bounded_0_1": True,
        "canonical_observables_recorded": True,
        "time_series_extrema_used_for_reference": True,
        "hysing_reference_agreement_cleared": False,
    }
    mismatches = [
        key
        for key, expected in required_contracts.items()
        if contracts.get(key) is not expected
    ]
    if mismatches:
        fail(f"{name} contract mismatches: {mismatches}")
    if not str(data.get("status", "")).startswith("NOT_READY-"):
        fail(f"{name} trial unexpectedly promoted: {data.get('status')}")
    if float(data.get("time", 0.0)) < 2.99:
        fail(f"{name} did not reach t=3: {data.get('time')}")
    if abs(float(data.get("alpha_mass_relative_drift", 1.0))) > 1.0e-12:
        fail(f"{name} alpha mass drift too large")
    if int(data.get("time_series", {}).get("sample_count", 0)) < 1:
        fail(f"{name} missing time-series samples")
    return {
        "name": name,
        "report": str(path),
        "status": data.get("status"),
        "time": data.get("time"),
        "sample_count": data.get("time_series", {}).get("sample_count"),
        "alpha_mass_relative_drift": data.get("alpha_mass_relative_drift"),
        "alpha_min_circularity": data.get("alpha_min_circularity"),
        "alpha_center_y_final": data.get("alpha_center_y_final"),
        "alpha_max_mean_rise_velocity_y": data.get("alpha_max_mean_rise_velocity_y"),
        "reference_errors": {
            "center_of_mass_y_at_t3_abs_error": errors.get("center_of_mass_y_at_t3_abs_error"),
            "maximum_mean_rise_velocity_abs_error": errors.get("maximum_mean_rise_velocity_abs_error"),
            "minimum_circularity_abs_error": errors.get("minimum_circularity_abs_error"),
        },
    }


def build_report(repo_root: Path, output: Path) -> dict:
    evidence = repo_root / "docs/codex_audit/evidence"
    baseline_path = evidence / (
        "academic_twophase_qlt03_lm_t3_scout_20260730/"
        "academic_twophase_qlt03_lm_t3_scout_report.json"
    )
    trial_paths = {
        "scheme2_divergence_of_normal": evidence / (
            "academic_twophase_qlt03_lm_curvature_scheme2_scout_20260730/report.json"
        ),
        "scheme3_filtered_curvature_and_delta": evidence / (
            "academic_twophase_qlt03_lm_curvature_scheme3_scout_20260730/report.json"
        ),
        "scheme4_filtered_curvature_raw_delta": evidence / (
            "academic_twophase_qlt03_lm_curvature_scheme4_scout_20260730/report.json"
        ),
    }
    source = repo_root / "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H"
    inputs = repo_root / "examples/academic/qlt03_lm_aux_bridge/inputs"
    baseline = load_json(baseline_path)
    trials = [trial_summary(name, path) for name, path in trial_paths.items()]
    source_text = source.read_text(errors="replace")
    inputs_text = inputs.read_text(errors="replace")
    prototype_tokens = [
        "alpha_filtered_3x3",
        "alpha_for_csf",
        "filter_curvature",
        "filter_delta",
    ]
    prototype_tokens_absent = all(token not in source_text for token in prototype_tokens)
    default_scheme_one = re.search(
        r"prob\.surface_tension_curvature_scheme\s*=\s*1\b", inputs_text
    ) is not None
    baseline_errors = baseline.get("reference_errors", {})
    baseline_summary = {
        "report": str(baseline_path),
        "status": baseline.get("status"),
        "minimum_circularity_abs_error": baseline_errors.get("minimum_circularity_abs_error"),
        "center_of_mass_y_at_t3_abs_error": baseline_errors.get("center_of_mass_y_at_t3_abs_error"),
        "maximum_mean_rise_velocity_abs_error": baseline_errors.get("maximum_mean_rise_velocity_abs_error"),
    }
    not_promoted = prototype_tokens_absent and default_scheme_one
    all_rejected = all(t["status"].startswith("NOT_READY-") for t in trials)
    all_stable = all(float(t["time"]) >= 2.99 for t in trials)
    all_mass_conserved = all(abs(float(t["alpha_mass_relative_drift"])) <= 1.0e-12 for t in trials)
    report = {
        "status": STATUS_PASS,
        "scope": (
            "Reproducibility guard for rejected QLT-03 low-Mach curvature trials. "
            "This report proves the trials were stable and informative but did not "
            "clear Hysing reference agreement and were not promoted into the active example."
        ),
        "baseline": baseline_summary,
        "trials": trials,
        "source": str(source),
        "inputs": str(inputs),
        "contracts": {
            "all_trials_reached_t3": all_stable,
            "all_trials_mass_conserved": all_mass_conserved,
            "all_trials_remain_not_ready": all_rejected,
            "filtered_curvature_prototype_not_retained": prototype_tokens_absent,
            "default_curvature_scheme_remains_baseline": default_scheme_one,
            "no_rejected_trial_promoted": not_promoted and all_rejected,
        },
        "decision": {
            "promote_trial": False,
            "reason": (
                "scheme2, scheme3, and scheme4 do not jointly clear center-height, "
                "maximum-rise-velocity, and minimum-circularity reference gates; "
                "next work should target a more faithful balanced-force/curvature "
                "or sharper conservative interface method."
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
        fail(f"curvature-trial rejection contracts not proven: {missing}")
    if report.get("decision", {}).get("promote_trial") is not False:
        fail("rejected curvature trial report cannot promote a trial")
    trials = report.get("trials", [])
    if len(trials) != 3:
        fail("expected exactly three curvature trials")
    for trial in trials:
        if not str(trial.get("status", "")).startswith("NOT_READY-"):
            fail(f"trial unexpectedly ready: {trial.get('name')}")


def verify_json(path: Path) -> int:
    report = load_json(path)
    validate_report(report)
    print(f"academic_twophase_qlt03_lm_curvature_trials VERIFY-PASS json={path}")
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
