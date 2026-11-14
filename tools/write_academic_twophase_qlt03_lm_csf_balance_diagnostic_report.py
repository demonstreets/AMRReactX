#!/usr/bin/env python3
"""Write/verify QLT-03 low-Mach CSF balance and lateral-drift diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

STATUS_PASS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-CSF-BALANCE-DIAGNOSTIC"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing JSON: {path}")
    return json.loads(path.read_text())


def abs_drift(summary: dict, case: str) -> float:
    return abs(float(summary[case]["center_x_drift"]))


def build_report(repo_root: Path, output: Path) -> dict:
    evidence = repo_root / "docs/codex_audit/evidence"
    drift_path = evidence / "academic_twophase_qlt03_lm_drift_controls_20260730/drift_controls_summary.json"
    zero_net_path = evidence / "academic_twophase_qlt03_lm_zero_net_csf_short_20260730/zero_net_short_summary.json"
    baseline_t3_path = evidence / (
        "academic_twophase_qlt03_lm_t3_scout_20260730/"
        "academic_twophase_qlt03_lm_t3_scout_report.json"
    )
    drift = load_json(drift_path)
    zero_net = load_json(zero_net_path)
    baseline_t3 = load_json(baseline_t3_path)

    prob_h = repo_root / "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H"
    prob_cpp = repo_root / "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.cpp"
    source_text = prob_h.read_text(errors="replace") + "\n" + prob_cpp.read_text(errors="replace")
    zero_net_absent = all(
        token not in source_text
        for token in ("surface_tension_zero_net_force", "zero_net_force", "csf_balance")
    )

    no_csf_drift = abs_drift(drift, "canonical_no_csf")
    no_gravity_csf_drift = abs_drift(drift, "canonical_no_gravity")
    zero_net_no_gravity_drift = abs_drift(zero_net, "canonical_no_gravity_zero_net")
    zero_net_buoyant_drift = abs_drift(zero_net, "canonical_buoyant_zero_net")
    baseline_final_x = float(baseline_t3["time_series"]["final"]["alpha_center_x"])
    baseline_x_drift = abs(baseline_final_x - float(baseline_t3["time_series"]["samples"][0]["alpha_center_x"]))

    report = {
        "status": STATUS_PASS,
        "scope": (
            "QLT-03 low-Mach CSF balance diagnosis for the remaining Hysing "
            "bubble-rise blocker. This report distinguishes Aux transport, "
            "buoyancy, and high-sigma CSF-induced lateral drift, and records a "
            "rejected global zero-net correction attempt."
        ),
        "evidence": {
            "drift_controls_summary": str(drift_path),
            "zero_net_short_summary": str(zero_net_path),
            "baseline_t3_report": str(baseline_t3_path),
        },
        "metrics": {
            "canonical_no_csf_center_x_drift": no_csf_drift,
            "canonical_no_gravity_csf_center_x_drift": no_gravity_csf_drift,
            "zero_net_no_gravity_center_x_drift": zero_net_no_gravity_drift,
            "zero_net_buoyant_center_x_drift": zero_net_buoyant_drift,
            "baseline_t3_center_x_drift": baseline_x_drift,
            "baseline_t3_final_center_x": baseline_final_x,
            "baseline_t3_final_center_y": baseline_t3["time_series"]["final"]["alpha_center_y"],
            "baseline_t3_minimum_circularity_error": baseline_t3["reference_errors"]["minimum_circularity_abs_error"],
        },
        "contracts": {
            "no_csf_preserves_lateral_symmetry": no_csf_drift <= 1.0e-10,
            "canonical_csf_without_gravity_triggers_lateral_drift": no_gravity_csf_drift >= 1.0e-2,
            "baseline_t3_has_large_lateral_drift": baseline_x_drift >= 0.10,
            "zero_net_attempt_did_not_improve_no_gravity_drift": zero_net_no_gravity_drift >= no_gravity_csf_drift,
            "zero_net_attempt_did_not_improve_buoyant_short_drift": zero_net_buoyant_drift >= abs_drift(drift, "canonical_no_gravity"),
            "zero_net_prototype_not_retained": zero_net_absent,
            "qlt03_still_not_ready": str(baseline_t3.get("status", "")).startswith("NOT_READY-"),
        },
        "decision": {
            "promote_zero_net_csf": False,
            "next_route": (
                "Implement a pressure-coupled balanced-force CSF discretization "
                "or geometric/height-function curvature treatment; avoid global "
                "net-force/net-acceleration compensation and more local limiter "
                "changes."
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
    missing = [k for k, v in report.get("contracts", {}).items() if v is not True]
    if missing:
        fail(f"CSF balance diagnostic contracts not proven: {missing}")
    if report.get("decision", {}).get("promote_zero_net_csf") is not False:
        fail("zero-net CSF diagnostic cannot promote the rejected prototype")


def verify_json(path: Path) -> int:
    report = load_json(path)
    validate_report(report)
    print(f"academic_twophase_qlt03_lm_csf_balance_diagnostic VERIFY-PASS json={path}")
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
