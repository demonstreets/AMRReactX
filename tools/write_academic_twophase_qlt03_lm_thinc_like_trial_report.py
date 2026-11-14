#!/usr/bin/env python3
"""Write/verify QLT-03 low-Mach THINC-like transport-trial rejection evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

STATUS_PASS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-THINC-LIKE-TRIAL-REJECTION"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing report: {path}")
    return json.loads(path.read_text())


def build_report(repo_root: Path, output: Path) -> dict:
    evidence = repo_root / "docs/codex_audit/evidence"
    baseline_path = evidence / (
        "academic_twophase_qlt03_lm_t3_scout_20260730/"
        "academic_twophase_qlt03_lm_t3_scout_report.json"
    )
    smoke_path = evidence / "academic_twophase_qlt03_lm_thinc_like_smoke_20260730/report.json"
    trial_path = evidence / "academic_twophase_qlt03_lm_thinc_like_t3_20260730/report.json"
    advance = repo_root / "external/PeleLMeX/Source/PeleLMeX_Advance.cpp"
    setup = repo_root / "external/PeleLMeX/Source/PeleLMeX_Setup.cpp"
    header = repo_root / "external/PeleLMeX/Source/PeleLMeX.H"

    baseline = load_json(baseline_path)
    smoke = load_json(smoke_path)
    trial = load_json(trial_path)
    baseline_errors = baseline.get("reference_errors", {})
    trial_errors = trial.get("reference_errors", {})
    source_text = "\n".join(
        path.read_text(errors="replace") for path in (advance, setup, header)
    )
    prototype_absent = all(
        token not in source_text
        for token in (
            "pelelmex_aux_thinc_like_state",
            "m_incompressible_aux_advect_scheme == 4",
            "incompressible_aux_thinc_beta",
            "THINC-like sharpening trial",
        )
    )

    report = {
        "status": STATUS_PASS,
        "scope": (
            "Reproducibility guard for the rejected QLT-03 low-Mach bounded "
            "THINC-like Aux-alpha face-state sharpening trial. The report "
            "retains evidence and verifies that the prototype was not promoted."
        ),
        "baseline": {
            "report": str(baseline_path),
            "status": baseline.get("status"),
            "center_of_mass_y_at_t3_abs_error": baseline_errors.get("center_of_mass_y_at_t3_abs_error"),
            "maximum_mean_rise_velocity_abs_error": baseline_errors.get("maximum_mean_rise_velocity_abs_error"),
            "minimum_circularity_abs_error": baseline_errors.get("minimum_circularity_abs_error"),
            "alpha_max_final": baseline.get("alpha_max"),
        },
        "thinc_like_smoke": {
            "report": str(smoke_path),
            "status": smoke.get("status"),
            "time": smoke.get("time"),
            "scheme": smoke.get("aux_transport_scheme"),
            "alpha_mass_relative_drift": smoke.get("alpha_mass_relative_drift"),
            "alpha_min": smoke.get("alpha_min"),
            "alpha_max": smoke.get("alpha_max"),
            "center_y": smoke.get("alpha_center_y"),
            "circularity": smoke.get("alpha_circularity"),
        },
        "thinc_like_t3_trial": {
            "report": str(trial_path),
            "status": trial.get("status"),
            "time": trial.get("time"),
            "sample_count": trial.get("time_series", {}).get("sample_count"),
            "alpha_mass_relative_drift": trial.get("alpha_mass_relative_drift"),
            "alpha_max_final": trial.get("alpha_max"),
            "center_of_mass_y_at_t3_abs_error": trial_errors.get("center_of_mass_y_at_t3_abs_error"),
            "maximum_mean_rise_velocity_abs_error": trial_errors.get("maximum_mean_rise_velocity_abs_error"),
            "minimum_circularity_abs_error": trial_errors.get("minimum_circularity_abs_error"),
        },
        "contracts": {
            "smoke_identified_thinc_like_scheme": smoke.get("aux_transport_scheme")
            == "finite_volume_thinc_like_bounded_using_mac_projected_face_velocities",
            "smoke_reached_short_window": float(smoke.get("time", 0.0)) >= 0.5,
            "smoke_mass_conserved": abs(float(smoke.get("alpha_mass_relative_drift", 1.0))) <= 1.0e-12,
            "smoke_bounded": float(smoke.get("alpha_min", -1.0)) >= -1.0e-10
            and float(smoke.get("alpha_max", 2.0)) <= 1.0 + 1.0e-10,
            "trial_reached_t3": float(trial.get("time", 0.0)) >= 2.99,
            "trial_time_series_sample_count_sufficient": int(trial.get("time_series", {}).get("sample_count", 0)) >= 10,
            "trial_mass_conserved": abs(float(trial.get("alpha_mass_relative_drift", 1.0))) <= 1.0e-12,
            "trial_remains_not_ready": str(trial.get("status", "")).startswith("NOT_READY-"),
            "trial_did_not_clear_center_height": float(
                trial_errors.get("center_of_mass_y_at_t3_abs_error", 0.0)
            )
            > 0.10,
            "trial_did_not_clear_minimum_circularity": float(
                trial_errors.get("minimum_circularity_abs_error", 0.0)
            )
            > 0.15,
            "trial_worse_than_baseline_center_height": float(
                trial_errors.get("center_of_mass_y_at_t3_abs_error", 0.0)
            )
            >= float(baseline_errors.get("center_of_mass_y_at_t3_abs_error", 999.0)),
            "trial_worse_than_baseline_minimum_circularity": float(
                trial_errors.get("minimum_circularity_abs_error", 0.0)
            )
            >= float(baseline_errors.get("minimum_circularity_abs_error", 999.0)),
            "thinc_like_prototype_not_retained": prototype_absent,
        },
        "decision": {
            "promote_trial": False,
            "reason": (
                "The bounded THINC-like face-state trial was numerically stable, "
                "bounded, and mass-conservative, but it degraded final center "
                "height and minimum circularity relative to the current minmod "
                "baseline; the prototype was removed from production source."
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
    missing = [
        key for key, value in report.get("contracts", {}).items() if value is not True
    ]
    if missing:
        fail(f"THINC-like rejection contracts not proven: {missing}")
    if report.get("decision", {}).get("promote_trial") is not False:
        fail("THINC-like trial rejection report cannot promote the trial")


def verify_json(path: Path) -> int:
    report = load_json(path)
    validate_report(report)
    print(f"academic_twophase_qlt03_lm_thinc_like_trial VERIFY-PASS json={path}")
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
