#!/usr/bin/env python3
"""Write/verify QLT-03 low-Mach transport-trial rejection evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

STATUS_PASS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-TRANSPORT-TRIAL-REJECTION"


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
    mc_path = evidence / "academic_twophase_qlt03_lm_mc_limiter_scout_20260730/report.json"
    advance = repo_root / "external/PeleLMeX/Source/PeleLMeX_Advance.cpp"
    setup = repo_root / "external/PeleLMeX/Source/PeleLMeX_Setup.cpp"
    baseline = load_json(baseline_path)
    mc = load_json(mc_path)
    advance_text = advance.read_text(errors="replace")
    setup_text = setup.read_text(errors="replace")
    mc_tokens_absent = (
        "pelelmex_aux_mc_slope" not in advance_text
        and "pelelmex_aux_minmod3" not in advance_text
        and "TVD MC" not in setup_text
        and "m_incompressible_aux_advect_scheme == 3" not in setup_text
    )
    mc_errors = mc.get("reference_errors", {})
    baseline_errors = baseline.get("reference_errors", {})
    contracts = mc.get("contracts", {})
    report = {
        "status": STATUS_PASS,
        "scope": (
            "Reproducibility guard for the rejected QLT-03 low-Mach Aux-alpha "
            "MC-limiter transport trial. The report does not promote the trial."
        ),
        "baseline": {
            "report": str(baseline_path),
            "status": baseline.get("status"),
            "minimum_circularity_abs_error": baseline_errors.get("minimum_circularity_abs_error"),
            "center_of_mass_y_at_t3_abs_error": baseline_errors.get("center_of_mass_y_at_t3_abs_error"),
            "maximum_mean_rise_velocity_abs_error": baseline_errors.get("maximum_mean_rise_velocity_abs_error"),
            "alpha_max_final": baseline.get("alpha_max"),
        },
        "mc_limiter_trial": {
            "report": str(mc_path),
            "status": mc.get("status"),
            "time": mc.get("time"),
            "sample_count": mc.get("time_series", {}).get("sample_count"),
            "alpha_mass_relative_drift": mc.get("alpha_mass_relative_drift"),
            "alpha_max_final": mc.get("alpha_max"),
            "minimum_circularity_abs_error": mc_errors.get("minimum_circularity_abs_error"),
            "center_of_mass_y_at_t3_abs_error": mc_errors.get("center_of_mass_y_at_t3_abs_error"),
            "maximum_mean_rise_velocity_abs_error": mc_errors.get("maximum_mean_rise_velocity_abs_error"),
        },
        "contracts": {
            "trial_reached_t3": float(mc.get("time", 0.0)) >= 2.99,
            "trial_mass_conserved": abs(float(mc.get("alpha_mass_relative_drift", 1.0))) <= 1.0e-12,
            "trial_remains_not_ready": str(mc.get("status", "")).startswith("NOT_READY-"),
            "trial_did_not_clear_minimum_circularity": float(
                mc_errors.get("minimum_circularity_abs_error", 0.0)
            )
            > 0.15,
            "trial_did_not_improve_baseline_circularity": float(
                mc_errors.get("minimum_circularity_abs_error", 0.0)
            )
            >= float(baseline_errors.get("minimum_circularity_abs_error", 999.0)),
            "mc_limiter_prototype_not_retained": mc_tokens_absent,
        },
        "decision": {
            "promote_trial": False,
            "reason": (
                "The MC limiter trial reached t=3 and conserved mass, but minimum "
                "circularity error increased relative to the minmod baseline and "
                "the final alpha peak did not improve; the prototype was removed."
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
        fail(f"transport-trial rejection contracts not proven: {missing}")
    if report.get("decision", {}).get("promote_trial") is not False:
        fail("transport trial rejection report cannot promote the trial")


def verify_json(path: Path) -> int:
    report = load_json(path)
    validate_report(report)
    print(f"academic_twophase_qlt03_lm_transport_trial VERIFY-PASS json={path}")
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
