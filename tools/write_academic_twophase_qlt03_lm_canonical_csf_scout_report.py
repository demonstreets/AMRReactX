#!/usr/bin/env python3
"""Write/verify QLT-03 low-Mach canonical-strength CSF scout evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STATUS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-CANONICAL-CSF-SCOUT"


def fail(message: str) -> None:
    raise RuntimeError(message)


def compact_inputs(path: Path) -> str:
    return " ".join(" ".join(line.split("#", 1)[0].split()) for line in path.read_text(errors="replace").splitlines())


def build_report(repo_root: Path, inputs: Path, bridge_report: Path) -> dict:
    bridge = json.loads(bridge_report.read_text())
    compact = compact_inputs(inputs)
    contracts = bridge.get("bridge_contracts", {})
    source = (repo_root / "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H").read_text(errors="replace")
    report = {
        "status": STATUS,
        "scope": (
            "Short-window QLT-03 low-Mach Aux-alpha scout with canonical Hysing "
            "surface-tension coefficient sigma=24.5 and no CSF force cap. This "
            "does not claim the final t=3 Hysing reference comparison."
        ),
        "inputs": str(inputs),
        "bridge_report": str(bridge_report),
        "time": bridge.get("time"),
        "alpha_mass_relative_drift": bridge.get("alpha_mass_relative_drift"),
        "alpha_center_y_initial": bridge.get("initial_alpha_metrics", {}).get("alpha_center_y"),
        "alpha_center_y_final": bridge.get("alpha_center_y"),
        "alpha_center_displacement": bridge.get("alpha_center_displacement"),
        "alpha_mean_rise_velocity_y": bridge.get("alpha_mean_rise_velocity_y"),
        "alpha_circularity": bridge.get("alpha_circularity"),
        "alpha_interface_length": bridge.get("alpha_interface_length"),
        "canonical_csf_contracts": {
            "sigma_is_hysing_case1_value": "prob.surface_tension_sigma = 24.5" in compact,
            "csf_force_cap_disabled": "prob.surface_tension_force_cap = 0.0" in compact,
            "canonical_light_phase_convention_configured": contracts.get("canonical_light_phase_convention_configured") is True,
            "canonical_boundary_conditions_configured": contracts.get("canonical_boundary_conditions_configured") is True,
            "canonical_observables_recorded": contracts.get("canonical_observables_recorded") is True,
            "short_window_stable_no_nan_abort_or_segfault": contracts.get("run_log_has_no_nan_abort_or_segfault") is True,
            "alpha_mass_conserved": contracts.get("alpha_mass_conserved") is True,
            "alpha_center_of_mass_rises": contracts.get("alpha_center_of_mass_rises") is True,
            "alpha_mean_rise_velocity_positive": contracts.get("alpha_mean_rise_velocity_positive") is True,
            "csf_source_is_uncapped_when_force_cap_nonpositive": "force_cap > 0.0 && force_mag > force_cap" in source,
        },
        "cleared_gate": "canonical-strength uncapped CSF short-window stability and observable response",
        "remaining_qlt03_work": [
            "extend canonical-strength CSF run to final time t=3",
            "compare center of mass, rise velocity, circularity, and final shape against Hysing Case 1 reference ranges",
        ],
    }
    validate_report(report)
    return report


def validate_report(report: dict) -> None:
    if report.get("status") != STATUS:
        fail(f"unexpected status: {report.get('status')}")
    contracts = report.get("canonical_csf_contracts", {})
    missing = [key for key, value in contracts.items() if value is not True]
    if missing:
        fail(f"canonical CSF contracts not proven: {missing}")
    if report.get("time", 0.0) < 0.4:
        fail(f"canonical CSF scout time too short: {report.get('time')}")
    if abs(report.get("alpha_mass_relative_drift", 1.0)) > 1.0e-12:
        fail(f"alpha mass drift too large: {report.get('alpha_mass_relative_drift')}")
    if report.get("alpha_center_y_final", -1.0e99) <= report.get("alpha_center_y_initial", 1.0e99):
        fail("alpha center did not rise")
    if report.get("alpha_mean_rise_velocity_y", -1.0e99) <= 0.0:
        fail("mean rise velocity is not positive")
    if report.get("alpha_circularity", 0.0) <= 0.0:
        fail("circularity is not positive")
    if report.get("alpha_interface_length", 0.0) <= 0.0:
        fail("interface length is not positive")


def verify_json(path: Path) -> int:
    report = json.loads(path.read_text())
    validate_report(report)
    print(f"academic_twophase_qlt03_lm_canonical_csf_scout VERIFY-PASS json={path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--bridge-report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()
    if args.verify_json is not None:
        return verify_json(args.verify_json)
    if args.inputs is None or args.bridge_report is None or args.output is None:
        fail("--inputs, --bridge-report, and --output are required unless --verify-json is used")
    report = build_report(args.repo_root, args.inputs, args.bridge_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
