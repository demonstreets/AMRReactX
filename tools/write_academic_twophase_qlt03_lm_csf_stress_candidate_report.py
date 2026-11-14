#!/usr/bin/env python3
"""Write/verify QLT-03 CSF stress-divergence candidate promotion evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STATUS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-CSF-STRESS-CANDIDATE-PROMOTION"
SHORT_STATUS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-CSF-STRESS-CANDIDATE-SHORT"
T3_STATUS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT"
PRE_STRESS_BASELINE = {
    "final_center_x_drift": 0.1351832869968323,
    "center_of_mass_y_at_t3_abs_error": 0.2435548712848178,
    "maximum_mean_rise_velocity_abs_error": 0.021518844103998735,
    "minimum_circularity_abs_error": 0.22931204142949568,
    "final_alpha_max": 0.4464218681538674,
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def read_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    return json.loads(path.read_text())


def source_contracts(repo_root: Path) -> dict:
    prob_h = (repo_root / "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H").read_text(errors="replace")
    prob_cpp = (repo_root / "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.cpp").read_text(errors="replace")
    return {
        "force_form_parameter_present": "surface_tension_force_form" in prob_h and "surface_tension_force_form" in prob_cpp,
        "stress_divergence_candidate_present": "csf_stress(" in prob_h and "force_form == 3" in prob_h,
        "continuum_surface_stress_tensor_present": "1.0 - nx * nx" in prob_h and "-coeff * nx * ny" in prob_h,
        "legacy_csf_default_path_retained": "force_x = -sigma * curvature * grad_x" in prob_h,
        "candidate_default_off": "int surface_tension_force_form = 1" in prob_h,
    }


def build_report(repo_root: Path, short_summary_path: Path, t3_report_path: Path) -> dict:
    short = read_json(short_summary_path)
    t3 = read_json(t3_report_path)
    if short.get("status") != SHORT_STATUS:
        fail(f"unexpected short candidate status: {short.get('status')}")
    if t3.get("status") != T3_STATUS:
        fail(f"unexpected t3 candidate status: {t3.get('status')}")
    source = source_contracts(repo_root)
    short_contracts = short.get("contracts", {})
    t3_contracts = t3.get("contracts", {})
    errors = t3.get("reference_errors", {})
    final = t3.get("time_series", {}).get("final", {})
    final_center_x_drift = abs(float(final.get("alpha_center_x", 0.5)) - 0.5)
    report = {
        "status": STATUS,
        "scope": (
            "Promotion evidence for the default-off QLT-03 low-Mach continuum-surface-stress "
            "CSF candidate. This clears the coarse 32x64 t=3 Hysing reference gate and records "
            "that full canonical readiness still needs grid-confirmation evidence."
        ),
        "evidence": {
            "source_prob_h": "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H",
            "source_prob_cpp": "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.cpp",
            "short_summary": str(short_summary_path),
            "t3_report": str(t3_report_path),
        },
        "source_contracts": source,
        "short_metrics": short.get("cases", {}),
        "short_status": short.get("status"),
        "t3_status": t3.get("status"),
        "t3_metrics": {
            "sample_count": t3.get("time_series", {}).get("sample_count"),
            "final_center_x": final.get("alpha_center_x"),
            "final_center_x_drift": final_center_x_drift,
            "final_center_y": final.get("alpha_center_y"),
            "final_alpha_max": final.get("alpha_max"),
            "final_circularity": final.get("circularity"),
            "max_mean_rise_velocity_y": t3.get("alpha_max_mean_rise_velocity_y"),
            "min_circularity": t3.get("alpha_min_circularity"),
            "reference_errors": errors,
            "alpha_mass_relative_drift": t3.get("alpha_mass_relative_drift"),
        },
        "pre_stress_baseline": PRE_STRESS_BASELINE,
        "contracts": {
            "source_candidate_present_and_default_off": all(source.values()),
            "short_candidate_passed": all(short_contracts.get(key) is True for key in (
                "no_gravity_ran_without_bad_tokens",
                "buoyant_ran_without_bad_tokens",
                "alpha_mass_conserved",
                "alpha_bounded",
                "no_gravity_reached_short_window",
                "buoyant_reached_short_window",
                "no_gravity_lateral_drift_target_met",
                "buoyant_mean_rise_positive",
            )),
            "t3_reference_agreement_cleared": t3_contracts.get("hysing_reference_agreement_cleared") is True,
            "t3_sample_count_sufficient": t3_contracts.get("time_series_sample_count_sufficient") is True,
            "t3_mass_conserved": t3_contracts.get("alpha_mass_conserved") is True,
            "t3_reached_final_time": t3_contracts.get("t3_final_time_reached") is True,
            "t3_no_bad_log_tokens": t3_contracts.get("short_log_has_no_nan_abort_or_segfault") is True,
            "center_error_improved_vs_pre_stress_baseline": (
                float(errors.get("center_of_mass_y_at_t3_abs_error", 1.0))
                < PRE_STRESS_BASELINE["center_of_mass_y_at_t3_abs_error"]
            ),
            "velocity_error_improved_vs_pre_stress_baseline": (
                float(errors.get("maximum_mean_rise_velocity_abs_error", 1.0))
                < PRE_STRESS_BASELINE["maximum_mean_rise_velocity_abs_error"]
            ),
            "circularity_error_improved_vs_pre_stress_baseline": (
                float(errors.get("minimum_circularity_abs_error", 1.0))
                < PRE_STRESS_BASELINE["minimum_circularity_abs_error"]
            ),
            "interface_sharpness_improved_vs_pre_stress_baseline": (
                float(final.get("alpha_max", 0.0)) > PRE_STRESS_BASELINE["final_alpha_max"]
            ),
        },
        "decision": {
            "retain_csf_stress_candidate": True,
            "promote_as_preferred_qlt03_low_mach_csf_form": True,
            "promote_full_academic_twophase_readiness": False,
            "why": [
                "canonical no-gravity short-window lateral drift falls below the target threshold",
                "buoyant short-window run remains stable, mass-conserving, bounded, and rising",
                "coarse 32x64 t=3 Hysing center-height, maximum-rise-velocity, and minimum-circularity errors all clear the current tolerances",
            ],
            "remaining_work": [
                "rerun 32/64 or better grid-confirmation evidence with force_form=3",
                "decide whether QLT-03 example inputs should default to force_form=3 after grid confirmation",
                "repeat academic evidence summary/path-decision records after grid confirmation clears",
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
        "source_candidate_present_and_default_off",
        "short_candidate_passed",
        "t3_reference_agreement_cleared",
        "t3_sample_count_sufficient",
        "t3_mass_conserved",
        "t3_reached_final_time",
        "t3_no_bad_log_tokens",
        "center_error_improved_vs_pre_stress_baseline",
        "velocity_error_improved_vs_pre_stress_baseline",
        "circularity_error_improved_vs_pre_stress_baseline",
        "interface_sharpness_improved_vs_pre_stress_baseline",
    )
    missing = [key for key in required_true if contracts.get(key) is not True]
    if missing:
        fail(f"CSF stress candidate promotion contracts not true: {missing}")
    decision = report.get("decision", {})
    if decision.get("retain_csf_stress_candidate") is not True:
        fail("CSF stress candidate must be retained")
    if decision.get("promote_as_preferred_qlt03_low_mach_csf_form") is not True:
        fail("CSF stress candidate must be marked preferred for QLT-03 low-Mach")
    if decision.get("promote_full_academic_twophase_readiness") is not False:
        fail("full academic two-phase readiness must still wait for grid confirmation")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--short-summary", type=Path)
    parser.add_argument("--t3-report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()
    if args.verify_json is not None:
        verify(read_json(args.verify_json))
        return 0
    if args.short_summary is None or args.t3_report is None or args.output is None:
        fail("--short-summary, --t3-report, and --output are required unless --verify-json is used")
    report = build_report(args.repo_root, args.short_summary, args.t3_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
