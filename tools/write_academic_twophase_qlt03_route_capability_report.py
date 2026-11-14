#!/usr/bin/env python3
"""Write/verify QLT-03 next-route capability audit evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

STATUS_PASS = "PASS-ACADEMIC-TWOPHASE-QLT03-ROUTE-CAPABILITY-AUDIT"


def fail(message: str) -> None:
    raise RuntimeError(message)


def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing file: {path}")
    return path.read_text(errors="replace")


def contains_any(text: str, tokens: list[str]) -> bool:
    lower = text.lower()
    for token in tokens:
        if re.search(r"\b" + re.escape(token.lower()) + r"\b", lower):
            return True
    return False


def build_report(repo_root: Path, output: Path) -> dict:
    lm_prob = repo_root / "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H"
    lm_advance = repo_root / "external/PeleLMeX/Source/PeleLMeX_Advance.cpp"
    lm_psf = repo_root / "external/PeleLMeX/Source/PeleLMeX_ProblemSpecificFunctions.H"
    pelec_hydro = repo_root / "external/PeleC/Source/Hydro.cpp"
    pelec_godunov = repo_root / "external/PeleC/Source/Godunov.H"
    pelec_mol = repo_root / "external/PeleC/Source/MOL.cpp"
    qlt03_path = repo_root / (
        "docs/codex_audit/evidence/academic_twophase_qlt03_path_decision_20260730/"
        "academic_twophase_qlt03_path_decision_report.json"
    )
    sharpness_path = repo_root / (
        "docs/codex_audit/evidence/academic_twophase_qlt03_lm_interface_sharpness_20260730/"
        "interface_sharpness_report.json"
    )
    transport_path = repo_root / (
        "docs/codex_audit/evidence/academic_twophase_qlt03_lm_transport_trials_20260730/"
        "transport_trial_report.json"
    )
    curvature_path = repo_root / (
        "docs/codex_audit/evidence/academic_twophase_qlt03_lm_curvature_trials_20260730/"
        "curvature_trial_report.json"
    )
    lm_prob_text = read(lm_prob)
    lm_advance_text = read(lm_advance)
    lm_psf_text = read(lm_psf)
    pelec_text = "\n".join(read(p) for p in [pelec_hydro, pelec_godunov, pelec_mol])
    qlt03 = json.loads(read(qlt03_path))
    sharpness = json.loads(read(sharpness_path))
    transport = json.loads(read(transport_path))
    curvature = json.loads(read(curvature_path))

    lm_has_plic = contains_any(lm_prob_text + lm_advance_text + lm_psf_text, ["PLIC", "geometric reconstruction", "piecewise linear interface"])
    lm_has_aux_bridge = (
        "auxiliary scalars live with finite-volume fluxes" in lm_advance_text
        and "surface_tension_sigma" in lm_prob_text
        and "force_x = -sigma * curvature * grad_x" in lm_prob_text
    )
    pelec_has_vof_fct = (
        "vof_fct_flux" in pelec_text
        and "VOF (ADV[0]) uses FCT flux" in pelec_text
        and "use_twophase" in pelec_text
    )
    pelec_has_mules_like_compression = (
        "MULES compression" in pelec_text and "vof_mules_body_force" in pelec_text
    )
    rejected_trials_guarded = (
        curvature.get("contracts", {}).get("no_rejected_trial_promoted") is True
        and transport.get("contracts", {}).get("mc_limiter_prototype_not_retained") is True
    )
    sharpness_contracts = sharpness.get("contracts", {})
    qlt03_ready = bool(qlt03.get("qlt03_canonical_ready", False))
    contracts = {
        "low_mach_aux_bridge_present": lm_has_aux_bridge,
        "low_mach_route_has_no_existing_plic": not lm_has_plic,
        "pelec_route_has_vof_fct_reference_components": pelec_has_vof_fct,
        "pelec_mules_like_compression_is_not_low_mach_aux_transport": pelec_has_mules_like_compression,
        "rejected_curvature_and_transport_trials_are_guarded": rejected_trials_guarded,
        "interface_sharpness_diagnosis_points_to_transport_plus_balanced_force": (
            sharpness_contracts.get("alpha_peak_diffuses_substantially") is True
            and sharpness_contracts.get("minimum_circularity_is_primary_baseline_blocker") is True
            and sharpness_contracts.get("simple_curvature_smoothing_rejected") is True
        ),
        "qlt03_path_still_not_ready": qlt03_ready is False,
    }
    report = {
        "status": STATUS_PASS,
        "scope": (
            "Capability audit for the next QLT-03 academic two-phase route after "
            "rejecting local curvature smoothing and one-dimensional MC limiter trials."
        ),
        "inspected_files": {
            "low_mach_problem": str(lm_prob),
            "low_mach_aux_transport": str(lm_advance),
            "low_mach_problem_specific_functions": str(lm_psf),
            "pelec_hydro": str(pelec_hydro),
            "pelec_godunov": str(pelec_godunov),
            "pelec_mol": str(pelec_mol),
        },
        "evidence_inputs": {
            "qlt03_path_decision": str(qlt03_path),
            "interface_sharpness": str(sharpness_path),
            "rejected_transport_trials": str(transport_path),
            "rejected_curvature_trials": str(curvature_path),
        },
        "findings": [
            {
                "name": "low_mach_aux_bridge_is_diffuse_interface_not_plic",
                "status": "PASS",
                "detail": "PeleLMeX QLT-03 currently advects Aux alpha with finite-volume MAC-face fluxes and applies explicit CSF from diffuse alpha gradients.",
            },
            {
                "name": "no_existing_low_mach_geometric_reconstruction_found",
                "status": "PASS",
                "detail": "The inspected PeleLMeX low-Mach path does not expose an existing PLIC/geometric interface reconstruction to switch on.",
            },
            {
                "name": "pelec_vof_fct_is_reference_not_drop_in",
                "status": "PASS",
                "detail": "PeleC has VOF/FCT flux and MULES-like compression references, but they are coupled to PeleC's compressible two-phase flux path rather than PeleLMeX incompressible Aux transport.",
            },
        ],
        "contracts": contracts,
        "decision": {
            "qlt03_ready": False,
            "recommended_next_route": "design a dedicated low-Mach Aux-alpha conservative geometric/reinitialization or THINC-like sharp-interface transport gate, then couple it to balanced-force CSF",
            "avoid_next": [
                "promoting PeleC VOF/FCT code as a direct PeleLMeX replacement without an adaptation layer",
                "additional local curvature smoothing without sharper interface transport",
                "additional one-dimensional slope limiter swaps without a geometry-aware interface model",
            ],
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
        fail(f"route capability contracts not proven: {missing}")
    if report.get("decision", {}).get("qlt03_ready") is not False:
        fail("route capability report cannot mark QLT-03 ready")


def verify_json(path: Path) -> int:
    report = json.loads(read(path))
    validate_report(report)
    print(f"academic_twophase_qlt03_route_capability VERIFY-PASS json={path}")
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
