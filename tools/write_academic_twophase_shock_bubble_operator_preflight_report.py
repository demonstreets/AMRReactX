#!/usr/bin/env python3
"""Write/verify shock-bubble two-phase operator preflight evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "PASS-ACADEMIC-TWOPHASE-SHOCK-BUBBLE-OPERATOR-PREFLIGHT"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/academic_twophase_shock_bubble_operator_preflight_20260730")
DEFAULT_JSON = DEFAULT_ROOT / "academic_twophase_shock_bubble_operator_preflight_report.json"
DEFAULT_MD = DEFAULT_ROOT / "academic_twophase_shock_bubble_operator_preflight_report.md"

SOURCES = {
    "two_phase_hllc": Path("src/academic/twophase/TwoPhaseHLLC.H"),
    "two_phase_eos": Path("src/academic/twophase/TwoPhaseEOS.H"),
    "stiffened_gas": Path("src/academic/twophase/StiffenedGas.H"),
    "csf": Path("src/academic/twophase/CSF.H"),
    "twophase_modules": Path("src/academic/twophase/twophase_modules.H"),
    "shock_droplet_example": Path("examples/academic/shock_droplet/inputs"),
    "spray_test_example": Path("examples/academic/spray_test/inputs"),
}


class ReportError(RuntimeError):
    pass


@dataclass(frozen=True)
class EOS:
    gamma: float
    p_inf: float = 0.0


@dataclass(frozen=True)
class State:
    rho: float
    u: float
    p: float
    eos: EOS
    y: tuple[float, float]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def evidence_entry(name: str, path: Path) -> dict[str, Any]:
    return {
        "name": name,
        "path": str(path),
        "exists": path.exists(),
        "sha256": sha256(path) if path.is_file() else None,
    }


def soundspeed(state: State) -> float:
    return math.sqrt(state.eos.gamma * (state.p + state.eos.p_inf) / state.rho)


def internal_energy(rho: float, p: float, eos: EOS) -> float:
    return (p + eos.gamma * eos.p_inf) / ((eos.gamma - 1.0) * rho)


def pvrs(left: State, right: State) -> float:
    c_l = soundspeed(left)
    c_r = soundspeed(right)
    p_est = 0.5 * (left.p + right.p) - 0.125 * (right.u - left.u) * (left.rho + right.rho) * (c_l + c_r)
    return max(p_est, 1.0)


def wave_q(p_star: float, p: float, gamma: float) -> float:
    if p_star <= p:
        return 1.0
    return math.sqrt(1.0 + (gamma + 1.0) / (2.0 * gamma) * (p_star / p - 1.0))


def hllc_oracle(left: State, right: State) -> dict[str, Any]:
    c_l = soundspeed(left)
    c_r = soundspeed(right)
    p_star = pvrs(left, right)
    q_l = wave_q(p_star, left.p, left.eos.gamma)
    q_r = wave_q(p_star, right.p, right.eos.gamma)
    s_l = left.u - c_l * q_l
    s_r = right.u + c_r * q_r
    denom = left.rho * (s_l - left.u) - right.rho * (s_r - right.u)
    if abs(denom) > 1.0e-40:
        s_star = (right.p - left.p + left.rho * left.u * (s_l - left.u) - right.rho * right.u * (s_r - right.u)) / denom
    else:
        s_star = 0.5 * (left.u + right.u)

    rho_l_star = left.rho * (s_l - left.u) / (s_l - s_star)
    rho_r_star = right.rho * (s_r - right.u) / (s_r - s_star)
    e_l = internal_energy(left.rho, left.p, left.eos)
    e_r = internal_energy(right.rho, right.p, right.eos)
    e_l_star = internal_energy(rho_l_star, p_star, left.eos)
    e_r_star = internal_energy(rho_r_star, p_star, right.eos)
    e_tot_l = 0.5 * left.u * left.u + e_l
    e_tot_r = 0.5 * right.u * right.u + e_r
    e_tot_l_star = 0.5 * s_star * s_star + e_l_star
    e_tot_r_star = 0.5 * s_star * s_star + e_r_star

    if s_l >= 0.0:
        region = "supersonic_left"
        flux_rho = left.rho * left.u
        flux_u = left.rho * left.u * left.u + left.p
        flux_eden = (left.rho * e_tot_l + left.p) * left.u
        flux_eint = left.rho * left.u * e_l
        y_face = left.y
        u_star = left.u
    elif s_star >= 0.0:
        region = "left_star"
        flux_rho = left.rho * left.u + s_l * (rho_l_star - left.rho)
        flux_u = (left.rho * left.u * left.u + left.p) + s_l * (rho_l_star * s_star - left.rho * left.u)
        flux_eden = (left.rho * e_tot_l + left.p) * left.u + s_l * (rho_l_star * e_tot_l_star - left.rho * e_tot_l)
        flux_eint = rho_l_star * s_star * e_l_star
        y_face = left.y
        u_star = s_star
    elif s_r >= 0.0:
        region = "right_star"
        flux_rho = right.rho * right.u + s_r * (rho_r_star - right.rho)
        flux_u = (right.rho * right.u * right.u + right.p) + s_r * (rho_r_star * s_star - right.rho * right.u)
        flux_eden = (right.rho * e_tot_r + right.p) * right.u + s_r * (rho_r_star * e_tot_r_star - right.rho * e_tot_r)
        flux_eint = rho_r_star * s_star * e_r_star
        y_face = right.y
        u_star = s_star
    else:
        region = "supersonic_right"
        flux_rho = right.rho * right.u
        flux_u = right.rho * right.u * right.u + right.p
        flux_eden = (right.rho * e_tot_r + right.p) * right.u
        flux_eint = right.rho * right.u * e_r
        y_face = right.y
        u_star = right.u

    flux_rho_y = [flux_rho * y for y in y_face]
    values = {
        "c_l": c_l,
        "c_r": c_r,
        "p_star": p_star,
        "q_l": q_l,
        "q_r": q_r,
        "s_l": s_l,
        "s_star": s_star,
        "s_r": s_r,
        "rho_l_star": rho_l_star,
        "rho_r_star": rho_r_star,
        "e_l_star": e_l_star,
        "e_r_star": e_r_star,
        "flux_rho": flux_rho,
        "flux_u": flux_u,
        "flux_eden": flux_eden,
        "flux_eint": flux_eint,
        "flux_rho_y": flux_rho_y,
        "u_star": u_star,
    }
    finite = all(math.isfinite(float(v)) for v in values.values() if not isinstance(v, list)) and all(math.isfinite(float(v)) for v in flux_rho_y)
    species_consistent = abs(sum(y_face) - 1.0) <= 1.0e-12
    return {
        "region": region,
        "values": values,
        "contracts": {
            "finite_flux_and_waves": finite,
            "positive_sound_speeds": c_l > 0.0 and c_r > 0.0,
            "positive_p_star": p_star > 0.0,
            "ordered_waves": s_l < s_star < s_r,
            "positive_star_densities": rho_l_star > 0.0 and rho_r_star > 0.0,
            "positive_star_internal_energies": e_l_star > 0.0 and e_r_star > 0.0,
            "upwind_species_mass_fractions_normalized": species_consistent,
        },
    }


def case_definitions() -> dict[str, tuple[State, State]]:
    air = EOS(gamma=1.4, p_inf=0.0)
    helium = EOS(gamma=1.667, p_inf=0.0)
    water = EOS(gamma=4.4, p_inf=6.0e8)
    return {
        "mach_like_air_shock_into_light_bubble": (
            State(rho=1.225, u=420.0, p=8.0e5, eos=air, y=(1.0, 0.0)),
            State(rho=0.18, u=0.0, p=1.0e5, eos=helium, y=(0.0, 1.0)),
        ),
        "air_shock_impinging_water_like_interface": (
            State(rho=1.225, u=520.0, p=1.2e6, eos=air, y=(1.0, 0.0)),
            State(rho=1000.0, u=0.0, p=1.0e5, eos=water, y=(0.0, 1.0)),
        ),
        "water_driver_reflecting_into_air_bubble": (
            State(rho=1000.0, u=80.0, p=8.0e6, eos=water, y=(0.0, 1.0)),
            State(rho=1.225, u=0.0, p=1.0e5, eos=air, y=(1.0, 0.0)),
        ),
    }


def source_contracts() -> dict[str, bool]:
    hllc = SOURCES["two_phase_hllc"].read_text(encoding="utf-8")
    eos = SOURCES["two_phase_eos"].read_text(encoding="utf-8")
    csf = SOURCES["csf"].read_text(encoding="utf-8")
    modules = SOURCES["twophase_modules"].read_text(encoding="utf-8")
    return {
        "hllc_flux_template_present": "twophase_hllc_flux" in hllc and "template <int NSPEC>" in hllc,
        "stiffened_gas_sound_speed_present": "p_inf" in hllc and "twophase_soundspeed" in hllc,
        "positive_pvrs_floor_present": "return amrex::max<amrex::Real>(p_pvrs, 1.0)" in hllc,
        "hllc_ordering_comments_present": "S_L < S* < S_R" in hllc,
        "species_upwind_present": "Y_face" in hllc and "flux_rhoY" in hllc,
        "two_phase_eos_alpha_switch_present": "alpha_tiny" in eos and "stiffened" in eos.lower(),
        "csf_source_present": "csf_force" in csf and "sigma" in csf,
        "twophase_modules_exports_hllc_and_csf": "TwoPhaseHLLC.H" in modules and "CSF.H" in modules,
    }


def build_report() -> dict[str, Any]:
    missing = [str(path) for path in SOURCES.values() if not path.exists()]
    if missing:
        raise ReportError(f"missing required source/example files: {missing}")

    src_contracts = source_contracts()
    case_results = {}
    for name, (left, right) in case_definitions().items():
        result = hllc_oracle(left, right)
        result["left"] = {
            "rho": left.rho,
            "u": left.u,
            "p": left.p,
            "gamma": left.eos.gamma,
            "p_inf": left.eos.p_inf,
            "y": list(left.y),
        }
        result["right"] = {
            "rho": right.rho,
            "u": right.u,
            "p": right.p,
            "gamma": right.eos.gamma,
            "p_inf": right.eos.p_inf,
            "y": list(right.y),
        }
        case_results[name] = result

    per_case_pass = {
        name: all(result["contracts"].values())
        for name, result in case_results.items()
    }
    all_cases_pass = all(per_case_pass.values())
    all_sources_pass = all(src_contracts.values())

    gates = [
        {
            "name": "source_contracts_present",
            "status": "PASS" if all_sources_pass else "NOT_READY",
            "metric": src_contracts,
            "target": "TwoPhaseHLLC/TwoPhaseEOS/CSF source contracts present",
            "evidence": [str(path) for path in SOURCES.values()],
        },
        {
            "name": "hllc_shock_interface_oracle_cases",
            "status": "PASS" if all_cases_pass else "NOT_READY",
            "metric": per_case_pass,
            "target": "all shock-interface oracle cases satisfy finite/positive/ordered HLLC contracts",
            "evidence": [str(SOURCES["two_phase_hllc"])],
        },
        {
            "name": "full_cfd_shock_bubble_not_claimed",
            "status": "PASS",
            "metric": False,
            "target": "operator preflight must not promote complete shock-bubble CFD validation",
            "evidence": [],
        },
    ]

    return {
        "schema_version": 1,
        "status": STATUS,
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "Operator-level shock-bubble preflight for the academic two-phase HLLC/EOS/CSF path.",
        "summary": {
            "shock_bubble_operator_preflight_ready": all_sources_pass and all_cases_pass,
            "shock_bubble_full_cfd_validation_ready": False,
            "case_count": len(case_results),
            "source_contracts_passed": all_sources_pass,
            "oracle_cases_passed": all_cases_pass,
            "remaining_work": [
                "Create and run a full CFD shock-bubble validation case with resolved bubble geometry, shock interaction, plot diagnostics, and conservation checks.",
                "Compare bubble deformation or interface-location metrics against a published or documented internal reference before promoting shock-bubble full validation.",
            ],
        },
        "gates": gates,
        "case_results": case_results,
        "source_contracts": src_contracts,
        "evidence": [
            *(evidence_entry(name, path) for name, path in SOURCES.items()),
            evidence_entry("preflight_writer", Path("tools/write_academic_twophase_shock_bubble_operator_preflight_report.py")),
        ],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Shock-Bubble Operator Preflight",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- Operator preflight ready: `{summary['shock_bubble_operator_preflight_ready']}`",
        f"- Full CFD shock-bubble validation ready: `{summary['shock_bubble_full_cfd_validation_ready']}`",
        f"- Oracle case count: `{summary['case_count']}`",
        "",
        "## Gates",
        "",
    ]
    for item in report["gates"]:
        lines.append(f"- `{item['status']}` {item['name']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_report(report: dict[str, Any]) -> None:
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ReportError(message)

    require(report.get("status") == STATUS, "unexpected preflight status")
    summary = report.get("summary", {})
    require(summary.get("shock_bubble_operator_preflight_ready") is True, "operator preflight should be ready")
    require(summary.get("shock_bubble_full_cfd_validation_ready") is False, "full CFD validation must not be claimed")
    require(summary.get("case_count") == 3, "expected three oracle cases")
    for name, result in report.get("case_results", {}).items():
        failed = [key for key, value in result.get("contracts", {}).items() if value is not True]
        require(not failed, f"case {name} failed contracts: {failed}")
    gates = {item.get("name"): item.get("status") for item in report.get("gates", [])}
    require(gates.get("source_contracts_present") == "PASS", "source contracts did not pass")
    require(gates.get("hllc_shock_interface_oracle_cases") == "PASS", "oracle cases did not pass")
    require(gates.get("full_cfd_shock_bubble_not_claimed") == "PASS", "full CFD non-promotion gate missing")
    for entry in report.get("evidence", []):
        path = Path(str(entry.get("path", "")))
        require(path.is_file(), f"missing evidence file: {path}")
        require(sha256(path) == entry.get("sha256"), f"sha256 mismatch: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()

    if args.verify_json:
        report = load_json(args.verify_json)
        verify_report(report)
        print(
            "academic_twophase_shock_bubble_operator_preflight VERIFY-PASS "
            f"json={args.verify_json} status={report['status']} "
            f"operator_ready={report['summary']['shock_bubble_operator_preflight_ready']}"
        )
        return 0

    report = build_report()
    verify_report(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        write_markdown(report, args.markdown)
    print(
        "academic_twophase_shock_bubble_operator_preflight PASS "
        f"json={args.output} status={report['status']} "
        f"operator_ready={report['summary']['shock_bubble_operator_preflight_ready']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
