#!/usr/bin/env python3
"""Write/verify the rejected QLT-03 pseudo-levelset curvature trial report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STATUS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-PSEUDO-LEVELSET-CURVATURE-TRIAL-REJECTION"
BASELINE = {
    "center_of_mass_y_at_t3_abs_error": 0.08397702843906696,
    "minimum_circularity_abs_error": 0.19587871606339502,
    "baseline_t3_final_center_x_drift": 0.20401463328714692,
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def read_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    return json.loads(path.read_text())


def source_has_tokens(repo_root: Path) -> bool:
    tokens = ("pseudo_levelset", "levelset_normal", "surface_tension_curvature_scheme == 3")
    for rel in (
        "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H",
        "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.cpp",
    ):
        text = (repo_root / rel).read_text(errors="replace")
        if any(token in text for token in tokens):
            return True
    return False


def build_report(repo_root: Path, short_summary_path: Path, t3_report_path: Path) -> dict:
    short = read_json(short_summary_path)
    t3 = read_json(t3_report_path)
    if short.get("status") != "PASS-ACADEMIC-TWOPHASE-QLT03-LM-PSEUDO-LEVELSET-CURVATURE-SHORT":
        fail(f"unexpected short summary status: {short.get('status')}")
    if t3.get("status") != "NOT_READY-ACADEMIC-TWOPHASE-QLT03-LM-T3-REFERENCE-AGREEMENT":
        fail(f"unexpected t3 report status: {t3.get('status')}")
    if source_has_tokens(repo_root):
        fail("pseudo-levelset curvature prototype tokens remain in QLT-03 source")

    short_contracts = short.get("contracts", {})
    t3_contracts = t3.get("contracts", {})
    errors = t3.get("reference_errors", {})
    final = t3.get("time_series", {}).get("final", {})
    center_x_drift = abs(final.get("alpha_center_x", 0.5) - 0.5)

    worsened_center_height = (
        errors.get("center_of_mass_y_at_t3_abs_error", 0.0)
        > BASELINE["center_of_mass_y_at_t3_abs_error"]
    )
    worsened_circularity = (
        errors.get("minimum_circularity_abs_error", 0.0)
        > BASELINE["minimum_circularity_abs_error"]
    )
    improved_lateral_drift = center_x_drift < BASELINE["baseline_t3_final_center_x_drift"]

    return {
        "status": STATUS,
        "scope": (
            "Machine-checkable rejection guard for a default-off QLT-03 pseudo-levelset "
            "geometric curvature scheme=3 candidate."
        ),
        "short_summary": str(short_summary_path),
        "t3_report": str(t3_report_path),
        "short_status": short["status"],
        "t3_status": t3["status"],
        "short_cases": short.get("cases", {}),
        "t3_reference_errors": errors,
        "baseline_reference_errors": BASELINE,
        "t3_final_center_x_drift": center_x_drift,
        "contracts": {
            "candidate_compiled": bool(short_contracts.get("compiled")),
            "short_window_passed": all(bool(short_contracts.get(key)) for key in (
                "alpha_bounded",
                "alpha_mass_conserved",
                "short_window_reaches_required_time",
                "no_gravity_lateral_drift_improved_vs_canonical_csf",
                "buoyant_mean_rise_positive",
            )),
            "t3_reached_final_time": bool(t3_contracts.get("t3_final_time_reached")),
            "t3_mass_conserved": bool(t3_contracts.get("alpha_mass_conserved")),
            "t3_hysing_reference_not_cleared": not bool(t3_contracts.get("hysing_reference_agreement_cleared")),
            "t3_center_height_worse_than_baseline": worsened_center_height,
            "t3_circularity_worse_than_baseline": worsened_circularity,
            "t3_lateral_drift_improved_but_insufficient": improved_lateral_drift and worsened_circularity,
            "pseudo_levelset_prototype_not_retained": True,
        },
        "decision": {
            "promote_pseudo_levelset_curvature": False,
            "rejection_reasons": [
                "t=3 center-height reference error worsened versus retained baseline",
                "t=3 minimum-circularity reference error worsened versus retained baseline",
                "short-window lateral-drift improvement did not translate into Hysing agreement",
            ],
            "next_route": (
                "Use this as evidence that curvature geometry alone is not enough in the current diffuse Aux-alpha path. "
                "Continue toward pressure-coupled balanced-force treatment and/or a sharper conservative interface representation."
            ),
        },
    }


def verify(report: dict) -> None:
    if report.get("status") != STATUS:
        fail(f"unexpected report status: {report.get('status')}")
    contracts = report.get("contracts", {})
    required_true = (
        "candidate_compiled",
        "short_window_passed",
        "t3_reached_final_time",
        "t3_mass_conserved",
        "t3_hysing_reference_not_cleared",
        "t3_center_height_worse_than_baseline",
        "t3_circularity_worse_than_baseline",
        "t3_lateral_drift_improved_but_insufficient",
        "pseudo_levelset_prototype_not_retained",
    )
    missing = [key for key in required_true if contracts.get(key) is not True]
    if missing:
        fail(f"pseudo-levelset rejection contracts not true: {missing}")
    decision = report.get("decision", {})
    if decision.get("promote_pseudo_levelset_curvature") is not False:
        fail("pseudo-levelset curvature must not be promoted")
    if len(decision.get("rejection_reasons", [])) < 2:
        fail("missing pseudo-levelset rejection reasons")


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
    verify(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
