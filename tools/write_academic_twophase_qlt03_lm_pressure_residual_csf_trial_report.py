#!/usr/bin/env python3
"""Write/verify the rejected QLT-03 pressure-residual CSF trial report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STATUS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-PRESSURE-RESIDUAL-CSF-TRIAL-REJECTION"


def fail(message: str) -> None:
    raise RuntimeError(message)


def read_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    return json.loads(path.read_text())


def source_has_tokens(repo_root: Path) -> bool:
    tokens = ("surface_tension_force_form", "pressure_residual")
    for rel in (
        "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H",
        "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.cpp",
    ):
        text = (repo_root / rel).read_text(errors="replace")
        if any(token in text for token in tokens):
            return True
    return False


def build_report(repo_root: Path, summary_path: Path) -> dict:
    summary = read_json(summary_path)
    if summary.get("status") != "REJECT-ACADEMIC-TWOPHASE-QLT03-LM-PRESSURE-RESIDUAL-CSF-SHORT":
        fail(f"unexpected pressure-residual summary status: {summary.get('status')}")
    contracts = summary.get("contracts", {})
    cases = summary.get("cases", {})
    required_cases = ("pressure_residual_no_gravity", "pressure_residual_buoyant")
    for case in required_cases:
        if case not in cases:
            fail(f"missing case in pressure-residual summary: {case}")
    if source_has_tokens(repo_root):
        fail("pressure-residual CSF prototype tokens remain in QLT-03 source")

    rejection_reasons = []
    if not contracts.get("short_window_reaches_required_time", False):
        rejection_reasons.append("800-step short-window run did not reach t>=0.45")
    if not contracts.get("buoyant_mean_rise_positive", False):
        rejection_reasons.append("buoyant short-window alpha-weighted mean rise velocity was not positive")
    if not rejection_reasons:
        fail("summary does not contain a strong rejection reason")

    return {
        "status": STATUS,
        "scope": (
            "Machine-checkable rejection guard for a default-off QLT-03 pressure-residual "
            "CSF force-form candidate."
        ),
        "source_summary": str(summary_path),
        "short_trial_status": summary["status"],
        "cases": cases,
        "contracts": {
            "candidate_compiled": bool(contracts.get("compiled")),
            "candidate_had_no_log_failure_tokens": bool(
                contracts.get("no_gravity_has_no_log_failure_tokens")
                and contracts.get("buoyant_has_no_log_failure_tokens")
            ),
            "alpha_mass_conserved": bool(contracts.get("alpha_mass_conserved")),
            "alpha_bounded": bool(contracts.get("alpha_bounded")),
            "short_window_failed_time_gate": not bool(contracts.get("short_window_reaches_required_time")),
            "buoyant_mean_rise_not_positive": not bool(contracts.get("buoyant_mean_rise_positive")),
            "pressure_residual_prototype_not_retained": True,
        },
        "decision": {
            "promote_pressure_residual_csf": False,
            "rejection_reasons": rejection_reasons,
            "next_route": (
                "Do not use the alpha*grad(kappa) pressure-residual shortcut. Continue with a "
                "proper pressure-coupled balanced-force discretization or geometric/height-function curvature."
            ),
        },
    }


def verify(report: dict) -> None:
    if report.get("status") != STATUS:
        fail(f"unexpected report status: {report.get('status')}")
    contracts = report.get("contracts", {})
    required_true = (
        "candidate_compiled",
        "candidate_had_no_log_failure_tokens",
        "alpha_mass_conserved",
        "alpha_bounded",
        "short_window_failed_time_gate",
        "buoyant_mean_rise_not_positive",
        "pressure_residual_prototype_not_retained",
    )
    missing = [key for key in required_true if contracts.get(key) is not True]
    if missing:
        fail(f"pressure-residual rejection contracts not true: {missing}")
    decision = report.get("decision", {})
    if decision.get("promote_pressure_residual_csf") is not False:
        fail("pressure-residual CSF must not be promoted")
    if not decision.get("rejection_reasons"):
        fail("missing pressure-residual rejection reasons")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()
    if args.verify_json is not None:
        verify(read_json(args.verify_json))
        return 0
    if args.summary is None or args.output is None:
        fail("--summary and --output are required unless --verify-json is used")
    report = build_report(args.repo_root, args.summary)
    verify(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
