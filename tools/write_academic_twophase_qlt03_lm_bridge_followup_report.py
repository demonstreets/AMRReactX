#!/usr/bin/env python3
"""Write or verify QLT-03 low-Mach bridge follow-up gap report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STATUS = "PASS-ACADEMIC-TWOPHASE-QLT03-LM-BRIDGE-FOLLOWUP"


def require_contains(path: Path, needle: str) -> bool:
    return needle in path.read_text(errors="replace")


def build_report(repo_root: Path, bridge_report: Path) -> dict:
    bridge = json.loads(bridge_report.read_text())
    advance = repo_root / "external/PeleLMeX/Source/PeleLMeX_Advance.cpp"
    setup = repo_root / "external/PeleLMeX/Source/PeleLMeX_Setup.cpp"
    psf = repo_root / "external/PeleLMeX/Source/PeleLMeX_ProblemSpecificFunctions.H"
    bridge_prob = repo_root / "examples/academic/qlt03_lm_aux_bridge/pelelmex_prob.H"
    bridge_inputs = repo_root / "examples/academic/qlt03_lm_aux_bridge/inputs"
    forces = repo_root / "external/PeleLMeX/Source/PeleLMeX_Forces.cpp"
    projection = repo_root / "external/PeleLMeX/Source/PeleLMeX_Projection.cpp"
    transport = repo_root / "external/PeleLMeX/Source/PeleLMeX_TransportProp.cpp"
    return {
        "status": STATUS,
        "scope": (
            "Tracks what QLT-03 low-Mach bridge evidence now proves and what "
            "still blocks a canonical VOF/CSF bubble-rise solve."
        ),
        "bridge_report": str(bridge_report),
        "bridge_status": bridge.get("status"),
        "bridge_time": bridge.get("time"),
        "alpha_mass_relative_drift": bridge.get("alpha_mass_relative_drift"),
        "alpha_center_displacement": bridge.get("alpha_center_displacement"),
        "aux_transport_scheme": bridge.get("aux_transport_scheme"),
        "source_contracts": {
            "incompressible_aux_advance_uses_mac_face_flux": (
                require_contains(advance, "MAC-projected face")
                and require_contains(advance, "umac(i + 1, j, k)")
                and require_contains(advance, "div_flux")
                and require_contains(advance, "pelelmex_aux_limited_state")
                and require_contains(bridge_inputs, "peleLM.incompressible_aux_advect_scheme = 2")
            ),
            "incompressible_setup_still_uses_constant_rho_mu": (
                require_contains(setup, "peleLM.rho is needed when running incompressible")
                and require_contains(setup, "peleLM.mu is needed when running incompressible")
            ),
            "problem_specific_ext_source_hook_accepts_aux_argument": (
                require_contains(psf, "modify_ext_sources(")
                and require_contains(psf, "const amrex::MultiFab* aux_old")
                and require_contains(psf, "const amrex::MultiFab* aux_new")
                and require_contains(psf, "call_modify_ext_sources_impl")
            ),
            "qlt03_bridge_csf_source_reads_aux_alpha": (
                require_contains(bridge_prob, "const amrex::MultiFab* aux_new")
                and require_contains(bridge_prob, "aux_new->const_arrays()")
                and require_contains(bridge_prob, "surface_tension_sigma")
                and require_contains(bridge_prob, "curvature")
                and require_contains(bridge_prob, "src[nbx](i, j, k, VELX)")
                and require_contains(bridge_prob, "force_x = -sigma * curvature * grad_x")
            ),
            "incompressible_velocity_force_scaling_reads_aux_density": (
                require_contains(forces, "m_incompressible_aux_density")
                and require_contains(forces, "aux_rho_heavy")
                and require_contains(forces, "aux_rho_light")
                and require_contains(forces, "force_ma[box_no](i, j, k, n) /= rho_lcl")
            ),
            "qlt03_bridge_enables_aux_density_ratio": (
                require_contains(bridge_inputs, "peleLM.incompressible_aux_density = true")
                and require_contains(bridge_inputs, "peleLM.incompressible_aux_density_comp = 0")
                and require_contains(bridge_inputs, "peleLM.incompressible_aux_rho_heavy = 1000.0")
                and require_contains(bridge_inputs, "peleLM.incompressible_aux_rho_light = 100.0")
                and require_contains(bridge_inputs, "peleLM.incompressible_aux_alpha_is_light = true")
                and require_contains(forces, "m_incompressible_aux_alpha_is_light")
                and require_contains(projection, "m_incompressible_aux_alpha_is_light")
                and require_contains(transport, "m_incompressible_aux_alpha_is_light")
            ),
            "qlt03_bridge_rises_with_light_alpha_phase": (
                bridge.get("bridge_contracts", bridge.get("contracts", {})).get("canonical_light_phase_convention_configured") is True
                and bridge.get("bridge_contracts", bridge.get("contracts", {})).get("alpha_center_of_mass_rises") is True
                and bridge.get("bridge_contracts", bridge.get("contracts", {})).get("alpha_mean_rise_velocity_positive") is True
                and bridge.get("alpha_center_y", -1.0e99)
                > bridge.get("initial_alpha_metrics", {}).get("alpha_center_y", 1.0e99)
                and bridge.get("alpha_mean_rise_velocity_y", -1.0e99) > 0.0
            ),
            "incompressible_aux_density_projection_uses_alpha_sigma": (
                require_contains(projection, "fillIncompressibleAuxDensitySigma")
                and require_contains(projection, "m_incompressible == 0 || m_incompressible_aux_density != 0")
                and require_contains(projection, "m_incompressible != 0 && m_incompressible_aux_density == 0")
                and require_contains(projection, "dt / rho_lcl")
            ),
            "incompressible_aux_viscosity_sets_diffusion_coefficients": (
                require_contains(transport, "m_incompressible_aux_viscosity")
                and require_contains(transport, "m_incompressible_aux_mu_heavy")
                and require_contains(transport, "m_incompressible_aux_mu_light")
                and require_contains(transport, "visc_ma[box_no](i, j, k)")
                and require_contains(bridge_inputs, "peleLM.incompressible_aux_viscosity = true")
                and require_contains(bridge_inputs, "peleLM.incompressible_aux_mu_heavy = 10.0")
                and require_contains(bridge_inputs, "peleLM.incompressible_aux_mu_light = 1.0")
            ),
            "qlt03_bridge_uses_canonical_boundary_conditions": (
                require_contains(bridge_inputs, "geometry.is_periodic = 0 0")
                and require_contains(bridge_inputs, "peleLM.lo_bc = SlipWallAdiab NoSlipWallAdiab")
                and require_contains(bridge_inputs, "peleLM.hi_bc = SlipWallAdiab NoSlipWallAdiab")
                and require_contains(bridge_inputs, "prob.v0 = 0.0")
                and require_contains(bridge_prob, "void bcnormal(")
                and require_contains(bridge_prob, "void bcnormal_aux(")
            ),
            "qlt03_bridge_records_canonical_observables": (
                bridge.get("bridge_contracts", bridge.get("contracts", {})).get("canonical_boundary_conditions_configured") is True
                and bridge.get("bridge_contracts", bridge.get("contracts", {})).get("canonical_observables_recorded") is True
                and bridge.get("canonical_inputs", {}).get("domain_1x2") is True
                and bridge.get("canonical_inputs", {}).get("slip_side_walls") is True
                and bridge.get("canonical_inputs", {}).get("no_slip_top_bottom") is True
                and bridge.get("alpha_mean_rise_velocity_y") is not None
                and bridge.get("alpha_circularity") is not None
                and bridge.get("alpha_interface_length") is not None
            ),
        },
        "cleared_gates": [
            "PeleLMeX incompressible state can carry Aux alpha without thermochemical state writes",
            "Aux alpha is advanced with MAC-projected face-flux divergence and optional TVD limited face states",
            "Alpha integral is conserved in the QLT-03 bridge smoke",
            "Alpha center of mass moves over the bridge window",
            "User-defined PeleLMeX external sources can access Aux alpha for CSF-style forcing",
            "Aux alpha can drive local incompressible velocity-force density scaling",
            "Aux alpha can drive local incompressible projection sigma and grad-pressure scaling",
            "Aux alpha can drive local incompressible velocity diffusion viscosity coefficients",
            "QLT-03 bridge uses nonperiodic 1x2 canonical bubble-rise boundary conditions",
            "QLT-03 bridge records center-of-mass, rise-velocity, circularity, and interface-length observables",
            "QLT-03 bridge treats alpha=1 as the light bubble phase and demonstrates upward buoyant response",
        ],
        "remaining_gates": [
            "higher-resolution/grid-convergence confirmation for final-shape fidelity",
            "true production VOF/CSF transport replacement if topology-changing interface fidelity is required",
        ],
    }


def verify_report(path: Path) -> int:
    data = json.loads(path.read_text())
    if data.get("status") != STATUS:
        raise RuntimeError(f"unexpected status: {data.get('status')}")
    contracts = data.get("source_contracts", {})
    required_true = [
        "incompressible_aux_advance_uses_mac_face_flux",
        "incompressible_setup_still_uses_constant_rho_mu",
        "problem_specific_ext_source_hook_accepts_aux_argument",
        "qlt03_bridge_csf_source_reads_aux_alpha",
        "incompressible_velocity_force_scaling_reads_aux_density",
        "qlt03_bridge_enables_aux_density_ratio",
        "qlt03_bridge_rises_with_light_alpha_phase",
        "incompressible_aux_density_projection_uses_alpha_sigma",
        "incompressible_aux_viscosity_sets_diffusion_coefficients",
        "qlt03_bridge_uses_canonical_boundary_conditions",
        "qlt03_bridge_records_canonical_observables",
    ]
    missing = [key for key in required_true if contracts.get(key) is not True]
    if missing:
        raise RuntimeError(f"unproven source contracts: {missing}")
    if abs(data.get("alpha_mass_relative_drift", 1.0)) > 1.0e-12:
        raise RuntimeError("bridge alpha mass drift too large")
    if data.get("alpha_center_displacement", 0.0) < 1.0e-3:
        raise RuntimeError("bridge alpha center displacement too small")
    print(f"academic_twophase_qlt03_lm_bridge_followup VERIFY-PASS json={path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--bridge-report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()
    if args.verify_json is not None:
        return verify_report(args.verify_json)
    if args.bridge_report is None or args.output is None:
        raise RuntimeError("--bridge-report and --output are required unless --verify-json is used")
    report = build_report(args.repo_root, args.bridge_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
