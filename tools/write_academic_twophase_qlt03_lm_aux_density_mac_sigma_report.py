#!/usr/bin/env python3
"""Write/verify the QLT-03 Aux-density MAC projection sigma consistency report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STATUS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-AUX-DENSITY-MAC-SIGMA-CONSISTENCY"
T3_NOT_READY = "NOT_READY-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT"
SMOKE_PASS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-AUX-BRIDGE-SMOKE"

PRE_MAC_SIGMA_BASELINE = {
    "final_center_x_drift": 0.20401463328714692,
    "center_of_mass_y_at_t3_abs_error": 0.08397702843906696,
    "maximum_mean_rise_velocity_abs_error": 0.03962185343960288,
    "minimum_circularity_abs_error": 0.19587871606339502,
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def read_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    return json.loads(path.read_text())


def source_contracts(repo_root: Path) -> dict:
    source_path = repo_root / "external/PeleLMeX/Source/PeleLMeX_UMac.cpp"
    text = source_path.read_text(errors="replace")
    return {
        "helper_present": "fillIncompressibleAuxDensityMacSigma" in text,
        "mac_project_calls_aux_density_sigma": "fillIncompressibleAuxDensityMacSigma(" in text
        and "m_incompressible_aux_density_comp" in text,
        "mac_project_has_aux_density_guard": "m_incompressible_aux_density != 0" in text
        and "m_nAux > m_incompressible_aux_density_comp" in text,
        "constant_density_fallback_retained": "rhoInv = m_dt / (2.0 * m_rho)" in text
        and "rho_inv[lev][idim].setVal(rhoInv)" in text,
        "face_centered_alpha_to_rho_inverse": "alpha_face" in text
        and "alpha_to_rho_inv" in text
        and "rho_inv_x_ma" in text
        and "rho_inv_y_ma" in text,
    }


def build_report(repo_root: Path, smoke_report_path: Path, t3_report_path: Path) -> dict:
    smoke = read_json(smoke_report_path)
    t3 = read_json(t3_report_path)
    if smoke.get("status") != SMOKE_PASS:
        fail(f"unexpected smoke status: {smoke.get('status')}")
    if t3.get("status") != T3_NOT_READY:
        fail(f"unexpected t3 status: {t3.get('status')}")

    source = source_contracts(repo_root)
    final = t3.get("time_series", {}).get("final", {})
    final_center_x = final.get("alpha_center_x")
    if final_center_x is None:
        fail("missing t3 final alpha_center_x")
    new_center_x_drift = abs(float(final_center_x) - 0.5)
    errors = t3.get("reference_errors", {})
    contracts = t3.get("contracts", {})
    smoke_contracts = smoke.get("bridge_contracts", {})

    center_error = float(errors.get("center_of_mass_y_at_t3_abs_error", 0.0))
    velocity_error = float(errors.get("maximum_mean_rise_velocity_abs_error", 0.0))
    circularity_error = float(errors.get("minimum_circularity_abs_error", 0.0))

    return {
        "status": STATUS,
        "scope": (
            "Machine-checkable consistency guard for the QLT-03 low-Mach Aux-density "
            "MAC projection sigma fix. The fix makes MAC projection use face-centered "
            "Aux-alpha density when incompressible Aux-density is enabled, while retaining "
            "the constant-density fallback."
        ),
        "evidence": {
            "source": str(repo_root / "external/PeleLMeX/Source/PeleLMeX_UMac.cpp"),
            "smoke_report": str(smoke_report_path),
            "t3_report": str(t3_report_path),
        },
        "source_contracts": source,
        "smoke_metrics": {
            "status": smoke.get("status"),
            "time": smoke.get("time"),
            "alpha_center_x": smoke.get("alpha_center_x"),
            "alpha_center_y": smoke.get("alpha_center_y"),
            "alpha_mass_relative_drift": smoke.get("alpha_mass_relative_drift"),
            "alpha_max": smoke.get("alpha_max"),
            "alpha_mean_rise_velocity_y": smoke.get("alpha_mean_rise_velocity_y"),
        },
        "t3_metrics_after_fix": {
            "status": t3.get("status"),
            "time": t3.get("time"),
            "sample_count": t3.get("time_series", {}).get("sample_count"),
            "final_center_x": final_center_x,
            "final_center_x_drift": new_center_x_drift,
            "final_center_y": t3.get("alpha_center_y_final"),
            "final_circularity": t3.get("alpha_circularity_final"),
            "final_alpha_max": t3.get("alpha_max"),
            "max_mean_rise_velocity_y": t3.get("alpha_max_mean_rise_velocity_y"),
            "min_circularity": t3.get("alpha_min_circularity"),
            "alpha_mass_relative_drift": t3.get("alpha_mass_relative_drift"),
            "reference_errors": errors,
        },
        "pre_mac_sigma_baseline": PRE_MAC_SIGMA_BASELINE,
        "contracts": {
            "mac_projection_aux_density_sigma_present": all(source.values()),
            "smoke_passed_after_fix": smoke.get("status") == SMOKE_PASS
            and bool(smoke_contracts.get("alpha_mass_conserved"))
            and bool(smoke_contracts.get("alpha_mean_rise_velocity_positive"))
            and bool(smoke_contracts.get("run_log_has_no_nan_abort_or_segfault")),
            "t3_reached_final_time": bool(contracts.get("t3_final_time_reached")),
            "t3_mass_conserved": bool(contracts.get("alpha_mass_conserved")),
            "t3_log_has_no_nan_abort_or_segfault": bool(contracts.get("short_log_has_no_nan_abort_or_segfault")),
            "t3_sample_count_sufficient": bool(contracts.get("time_series_sample_count_sufficient")),
            "t3_still_not_ready": t3.get("status") == T3_NOT_READY
            and not bool(contracts.get("hysing_reference_agreement_cleared")),
            "lateral_drift_improved_vs_pre_mac_sigma_baseline": (
                new_center_x_drift < PRE_MAC_SIGMA_BASELINE["final_center_x_drift"]
            ),
            "center_height_error_worse_vs_pre_mac_sigma_baseline": (
                center_error > PRE_MAC_SIGMA_BASELINE["center_of_mass_y_at_t3_abs_error"]
            ),
            "velocity_error_improved_vs_pre_mac_sigma_baseline": (
                velocity_error < PRE_MAC_SIGMA_BASELINE["maximum_mean_rise_velocity_abs_error"]
            ),
            "circularity_error_worse_vs_pre_mac_sigma_baseline": (
                circularity_error > PRE_MAC_SIGMA_BASELINE["minimum_circularity_abs_error"]
            ),
        },
        "decision": {
            "retain_aux_density_mac_sigma_fix": True,
            "promote_qlt03_to_ready": False,
            "why_retain": [
                "MAC projection and nodal velocity projection now use consistent incompressible Aux-density sigma when the Aux-density option is enabled",
                "short QLT-03 smoke remains stable, bounded, mass-conserving, and buoyant",
                "t=3 scout remains stable and mass-conserving, with reduced lateral drift and improved maximum-rise-velocity error versus the pre-fix t=3 baseline",
            ],
            "why_not_ready": [
                "t=3 Hysing reference agreement is still not cleared",
                "center-height and minimum-circularity errors worsened versus the pre-MAC-sigma t=3 baseline",
                "the remaining issue still points to pressure-coupled balanced force and/or sharper conservative interface representation",
            ],
            "next_route": (
                "Keep the MAC sigma consistency fix as a correctness repair, then continue with "
                "pressure-coupled balanced-force treatment or a sharper conservative interface path "
                "before declaring academic two-phase QLT-03 ready."
            ),
        },
    }


def verify(report: dict) -> None:
    if report.get("status") != STATUS:
        fail(f"unexpected report status: {report.get('status')}")
    contracts = report.get("contracts", {})
    required_true = (
        "mac_projection_aux_density_sigma_present",
        "smoke_passed_after_fix",
        "t3_reached_final_time",
        "t3_mass_conserved",
        "t3_log_has_no_nan_abort_or_segfault",
        "t3_sample_count_sufficient",
        "t3_still_not_ready",
        "lateral_drift_improved_vs_pre_mac_sigma_baseline",
        "center_height_error_worse_vs_pre_mac_sigma_baseline",
        "velocity_error_improved_vs_pre_mac_sigma_baseline",
        "circularity_error_worse_vs_pre_mac_sigma_baseline",
    )
    missing = [key for key in required_true if contracts.get(key) is not True]
    if missing:
        fail(f"Aux-density MAC sigma contracts not true: {missing}")
    source_contracts = report.get("source_contracts", {})
    if not source_contracts or any(value is not True for value in source_contracts.values()):
        fail(f"source contracts not all true: {source_contracts}")
    decision = report.get("decision", {})
    if decision.get("retain_aux_density_mac_sigma_fix") is not True:
        fail("Aux-density MAC sigma fix must be retained")
    if decision.get("promote_qlt03_to_ready") is not False:
        fail("QLT-03 must not be promoted by this report")
    if len(decision.get("why_not_ready", [])) < 2:
        fail("missing not-ready rationale")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--smoke-report", type=Path)
    parser.add_argument("--t3-report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()
    if args.verify_json is not None:
        verify(read_json(args.verify_json))
        return 0
    if args.smoke_report is None or args.t3_report is None or args.output is None:
        fail("--smoke-report, --t3-report, and --output are required unless --verify-json is used")
    report = build_report(args.repo_root, args.smoke_report, args.t3_report)
    verify(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
