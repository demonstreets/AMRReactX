#!/usr/bin/env python3
"""Write/verify the liquefied phase-change overclaim guard report."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_liquefied_phase_change_overclaim_guard_20260811")
DEFAULT_JSON = DEFAULT_ROOT / "engineering_liquefied_phase_change_overclaim_guard_report.json"
DEFAULT_MD = DEFAULT_ROOT / "engineering_liquefied_phase_change_overclaim_guard_report.md"

REPORTS = {
    "multi_fuel_boundary": Path(
        "docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/"
        "engineering_multi_fuel_capability_boundary_report.json"
    ),
    "gasified_lng_lpg_surrogate": Path(
        "docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/"
        "engineering_gasified_lng_lpg_surrogate_report.json"
    ),
    "external_vaporization_contract": Path(
        "docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/"
        "engineering_liquefied_external_vaporization_contract_report.json"
    ),
    "external_vaporization_negative_selftest": Path(
        "docs/codex_audit/evidence/engineering_liquefied_external_vaporization_negative_selftest_20260806/"
        "engineering_liquefied_external_vaporization_negative_selftest_report.json"
    ),
    "vaporization_source_model": Path(
        "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/"
        "engineering_liquefied_release_vaporization_source_model_report.json"
    ),
    "vaporization_source_model_negative_selftest": Path(
        "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_negative_selftest_20260807/"
        "engineering_liquefied_release_vaporization_source_model_negative_selftest_report.json"
    ),
    "source_balance": Path(
        "docs/codex_audit/evidence/engineering_liquefied_release_source_balance_20260807/"
        "engineering_liquefied_release_source_balance_report.json"
    ),
    "source_balance_negative_selftest": Path(
        "docs/codex_audit/evidence/engineering_liquefied_release_source_balance_negative_selftest_20260807/"
        "engineering_liquefied_release_source_balance_negative_selftest_report.json"
    ),
    "thermal_plausibility": Path(
        "docs/codex_audit/evidence/engineering_liquefied_release_thermal_plausibility_20260811/"
        "engineering_liquefied_release_thermal_plausibility_report.json"
    ),
    "breach_source_contract": Path(
        "docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/"
        "engineering_liquefied_breach_source_contract_report.json"
    ),
}

EXPECTED_STATUS = {
    "multi_fuel_boundary": "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY",
    "gasified_lng_lpg_surrogate": "PASS-ENGINEERING-GASIFIED-LNG-LPG-SURROGATE-BOUNDARY",
    "external_vaporization_contract": "PASS-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-CONTRACT",
    "external_vaporization_negative_selftest": "PASS-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-NEGATIVE-SELFTEST",
    "vaporization_source_model": "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL",
    "vaporization_source_model_negative_selftest": (
        "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-NEGATIVE-SELFTEST"
    ),
    "source_balance": "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE",
    "source_balance_negative_selftest": "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE-NEGATIVE-SELFTEST",
    "thermal_plausibility": "PASS-ENGINEERING-LIQUEFIED-RELEASE-THERMAL-PLAUSIBILITY",
    "breach_source_contract": "PASS-ENGINEERING-LIQUEFIED-BREACH-SOURCE-CONTRACT",
}


class ReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportError(message)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    full = REPO_ROOT / path
    require(full.exists(), f"missing evidence: {path}")
    with full.open("r", encoding="utf-8") as f:
        data = json.load(f)
    require(isinstance(data, dict), f"evidence is not an object: {path}")
    return data


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with (REPO_ROOT / path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
    }


def bool_from(report: dict[str, Any], key: str) -> bool:
    summary = report.get("summary", {})
    require(isinstance(summary, dict), "summary missing or invalid")
    value = summary.get(key)
    require(isinstance(value, bool), f"summary flag missing or non-bool: {key}")
    return value


def optional_bool(report: dict[str, Any], key: str) -> bool | None:
    summary = report.get("summary", {})
    require(isinstance(summary, dict), "summary missing or invalid")
    value = summary.get(key)
    if value is None:
        return None
    require(isinstance(value, bool), f"summary flag non-bool: {key}")
    return value


def build_report() -> dict[str, Any]:
    reports = {name: load_json(path) for name, path in REPORTS.items()}
    for name, data in reports.items():
        require(data.get("status") == EXPECTED_STATUS[name], f"{name} status is not passing")

    multi = reports["multi_fuel_boundary"]
    surrogate = reports["gasified_lng_lpg_surrogate"]
    contract = reports["external_vaporization_contract"]
    external_negative = reports["external_vaporization_negative_selftest"]
    model = reports["vaporization_source_model"]
    model_negative = reports["vaporization_source_model_negative_selftest"]
    balance = reports["source_balance"]
    balance_negative = reports["source_balance_negative_selftest"]
    thermal = reports["thermal_plausibility"]
    breach_contract = reports["breach_source_contract"]

    bridge_ready_flags = {
        "multi_fuel_boundary_ready": True,
        "gasified_lng_given_source_surrogate_ready": bool_from(multi, "gasified_lng_given_source_surrogate_ready"),
        "gasified_lpg_given_source_surrogate_ready": bool_from(multi, "gasified_lpg_given_source_surrogate_ready"),
        "external_vaporization_contract_ready": bool_from(contract, "external_vaporization_contract_ready"),
        "vaporization_source_model_ready": bool_from(model, "liquefied_release_vaporization_source_model_ready"),
        "source_balance_ready": bool_from(balance, "liquefied_release_source_balance_ready"),
        "thermal_plausibility_ready": bool_from(thermal, "liquefied_release_thermal_plausibility_ready"),
        "breach_source_contract_ready": bool_from(breach_contract, "liquefied_breach_source_contract_ready"),
        "lng_ch4_source_ready": bool_from(model, "lng_ch4_screening_release_source_ready"),
        "lpg_c3h8_source_ready": bool_from(model, "lpg_c3h8_screening_release_source_ready"),
    }

    runtime_flags = {
        "external_vaporization_ch4_timeseries_cuda_passed": bool_from(
            multi, "external_vaporization_ch4_timeseries_cuda_passed"
        ),
        "external_vaporization_c3h8_timeseries_cuda_passed": bool_from(
            multi, "external_vaporization_c3h8_timeseries_cuda_passed"
        ),
        "liquefied_release_lng_ch4_generated_input_cuda_smoke_passed": bool_from(
            multi, "liquefied_release_lng_ch4_generated_input_cuda_smoke_passed"
        ),
        "liquefied_release_lpg_c3h8_generated_input_cuda_smoke_passed": bool_from(
            multi, "liquefied_release_lpg_c3h8_generated_input_cuda_smoke_passed"
        ),
    }

    negative_flags = {
        "external_vaporization_negative_selftest_ready": bool_from(external_negative, "negative_selftest_ready"),
        "vaporization_source_model_negative_selftest_ready": bool_from(model_negative, "negative_selftest_ready"),
        "source_balance_negative_selftest_ready": bool_from(
            balance_negative, "liquefied_release_source_balance_negative_selftest_ready"
        ),
        "guards_phase_change_overclaim": bool_from(balance_negative, "guards_phase_change_overclaim"),
        "guards_pool_fraction": bool_from(model_negative, "guards_pool_fraction"),
        "guards_vaporized_fraction": bool_from(model_negative, "guards_vaporized_fraction"),
        "guards_negative_vapor_temperature": bool_from(external_negative, "guards_negative_vapor_temperature"),
    }

    no_overclaim_flags = {
        "cfd_solves_liquid_phase_change": bool_from(balance, "cfd_solves_liquid_phase_change"),
        "cfd_solves_pool_spread_evaporation": bool_from(balance, "cfd_solves_pool_spread_evaporation"),
        "cfd_solves_flashing_discharge": bool_from(balance, "cfd_solves_flashing_discharge"),
        "production_phase_change_claim_allowed": bool_from(balance, "production_phase_change_claim_allowed"),
        "liquefied_gas_phase_change_ready": bool_from(multi, "liquefied_gas_phase_change_ready"),
        "lng_lpg_production_phase_change_claim_allowed": bool_from(
            surrogate, "lng_lpg_production_phase_change_claim_allowed"
        ),
        "liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation_ready": bool_from(
            surrogate, "liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation_ready"
        ),
    }

    for key, value in bridge_ready_flags.items():
        require(value is True, f"bridge readiness missing: {key}")
    for key, value in runtime_flags.items():
        require(value is True, f"CUDA/runtime evidence missing: {key}")
    for key, value in negative_flags.items():
        require(value is True, f"negative guard missing: {key}")
    for key, value in no_overclaim_flags.items():
        require(value is False, f"phase-change overclaim detected: {key}")

    contract_no_overclaim = all(
        optional_bool(contract, key) is False
        for key in ("cfd_solves_liquid_phase_change", "cfd_solves_pool_spread_evaporation", "cfd_solves_flashing_discharge")
    )
    model_no_overclaim = all(
        optional_bool(model, key) is False
        for key in ("cfd_solves_liquid_phase_change", "cfd_solves_pool_spread_evaporation", "cfd_solves_flashing_discharge")
    )
    thermal_no_overclaim = all(
        optional_bool(thermal, key) is False
        for key in ("cfd_solves_liquid_phase_change", "cfd_solves_pool_spread_evaporation", "cfd_solves_flashing_discharge")
    )
    breach_contract_no_overclaim = all(
        optional_bool(breach_contract, key) is False
        for key in ("cfd_solves_liquid_phase_change", "cfd_solves_pool_spread_evaporation", "cfd_solves_flashing_discharge")
    )
    require(contract_no_overclaim, "contract overclaims internal phase-change")
    require(model_no_overclaim, "source model overclaims internal phase-change")
    require(thermal_no_overclaim, "thermal plausibility report overclaims internal phase-change")
    require(breach_contract_no_overclaim, "breach source contract overclaims internal phase-change")
    require(bool_from(thermal, "all_vaporized_fraction_matches_screening_formula"), "thermal vaporized fraction check missing")
    require(bool_from(thermal, "all_heat_loads_positive"), "thermal heat-load check missing")
    require(optional_bool(thermal, "production_phase_change_claim_allowed") is False, "thermal report overclaims production phase-change")
    require(bool_from(breach_contract, "contract_accepts_screening_breach_inputs"), "breach source contract input flag missing")
    require(bool_from(breach_contract, "generates_external_gas_source_schedule"), "breach source contract schedule flag missing")
    require(optional_bool(breach_contract, "production_phase_change_claim_allowed") is False, "breach source contract overclaims production phase-change")

    summary: dict[str, Any] = {
        "gasified_lng_lpg_bridge_ready": True,
        "external_vaporization_bridge_ready": True,
        "liquefied_release_screening_source_ready": True,
        "liquefied_breach_source_contract_ready": True,
        "liquefied_release_thermal_plausibility_ready": True,
        "liquefied_release_cuda_runtime_ready": True,
        "negative_selftests_ready": True,
        "phase_change_overclaim_guard_ready": True,
        "cfd_solves_liquid_phase_change": False,
        "cfd_solves_pool_spread_evaporation": False,
        "cfd_solves_flashing_discharge": False,
        "production_phase_change_claim_allowed": False,
        "strict_liquefied_tank_rupture_phase_change_production_ready": False,
        "allowed_current_claim": (
            "external vaporization/gasified source bridge for LNG_CH4 and LPG_C3H8 dispersion, ignition, "
            "flame development, and obstacle interaction"
        ),
        "disallowed_current_claim": (
            "internal tank rupture, flashing multiphase discharge, liquid-pool spread/boiling, droplet breakup, "
            "ground heat transfer, or high-fidelity EOS-coupled liquefied-gas phase-change production modeling"
        ),
    }
    summary.update(bridge_ready_flags)
    summary.update(runtime_flags)
    summary.update({f"negative_{key}": value for key, value in negative_flags.items()})
    summary.update({f"guard_{key}": value for key, value in no_overclaim_flags.items()})

    return {
        "schema_version": 1,
        "status": "PASS-ENGINEERING-LIQUEFIED-PHASE-CHANGE-OVERCLAIM-GUARD",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "engineering LNG/LPG external-vaporization bridge and phase-change overclaim guard",
        "summary": summary,
        "evidence": [evidence_entry(label, path) for label, path in REPORTS.items()],
        "notes": [
            "This report permits gasified/external-vaporization LNG/LPG engineering source workflows only.",
            "It explicitly forbids claiming internal liquefied tank rupture, flashing discharge, pool spread/boiling, or EOS-coupled phase-change production readiness from the current evidence.",
            "Full liquefied phase-change production claims require future dedicated model development and validation artifacts.",
        ],
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Engineering Liquefied Phase-Change Overclaim Guard",
        "",
        f"- Status: `{report['status']}`",
        f"- Gasified LNG/LPG bridge ready: `{s['gasified_lng_lpg_bridge_ready']}`",
        f"- External vaporization bridge ready: `{s['external_vaporization_bridge_ready']}`",
        f"- Liquefied release screening source ready: `{s['liquefied_release_screening_source_ready']}`",
        f"- Liquefied breach source contract ready: `{s['liquefied_breach_source_contract_ready']}`",
        f"- CUDA runtime ready: `{s['liquefied_release_cuda_runtime_ready']}`",
        f"- Negative selftests ready: `{s['negative_selftests_ready']}`",
        f"- Phase-change overclaim guard ready: `{s['phase_change_overclaim_guard_ready']}`",
        "",
        "## Current Boundary",
        "",
        f"- Allowed current claim: {s['allowed_current_claim']}",
        f"- Disallowed current claim: {s['disallowed_current_claim']}",
        f"- Internal liquid phase-change CFD: `{s['cfd_solves_liquid_phase_change']}`",
        f"- Pool spread/boiling CFD: `{s['cfd_solves_pool_spread_evaporation']}`",
        f"- Flashing discharge CFD: `{s['cfd_solves_flashing_discharge']}`",
        f"- Production phase-change claim allowed: `{s['production_phase_change_claim_allowed']}`",
        "",
        "## Evidence",
        "",
    ]
    for item in report["evidence"]:
        lines.append(f"- `{item['label']}`: `{item['path']}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_report(report: dict[str, Any], verify_hashes: bool = False) -> None:
    require(report.get("status") == "PASS-ENGINEERING-LIQUEFIED-PHASE-CHANGE-OVERCLAIM-GUARD", "unexpected status")
    summary = report.get("summary", {})
    require(isinstance(summary, dict), "summary missing")
    for key in (
        "gasified_lng_lpg_bridge_ready",
        "external_vaporization_bridge_ready",
        "liquefied_release_screening_source_ready",
        "liquefied_breach_source_contract_ready",
        "liquefied_release_thermal_plausibility_ready",
        "liquefied_release_cuda_runtime_ready",
        "negative_selftests_ready",
        "phase_change_overclaim_guard_ready",
    ):
        require(summary.get(key) is True, f"{key} not true")
    for key in (
        "cfd_solves_liquid_phase_change",
        "cfd_solves_pool_spread_evaporation",
        "cfd_solves_flashing_discharge",
        "production_phase_change_claim_allowed",
        "strict_liquefied_tank_rupture_phase_change_production_ready",
    ):
        require(summary.get(key) is False, f"{key} overclaimed")
    require(isinstance(report.get("evidence"), list) and len(report["evidence"]) == len(REPORTS), "evidence missing")
    if verify_hashes:
        for item in report["evidence"]:
            path = Path(item["path"])
            require((REPO_ROOT / path).exists(), f"missing evidence path: {path}")
            require(sha256_file(path) == item.get("sha256"), f"evidence hash mismatch: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    parser.add_argument("--verify-json", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.verify_json:
            with (REPO_ROOT / args.verify_json).open("r", encoding="utf-8") as f:
                report = json.load(f)
            validate_report(report, verify_hashes=True)
            print(f"engineering_liquefied_phase_change_overclaim_guard VERIFY-PASS json={args.verify_json}")
            return 0

        report = build_report()
        validate_report(report, verify_hashes=False)
        output_json = REPO_ROOT / args.output_json
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, REPO_ROOT / args.output_md)
        print(
            "engineering_liquefied_phase_change_overclaim_guard PASS "
            f"json={args.output_json} md={args.output_md} status={report['status']}"
        )
        return 0
    except ReportError as exc:
        print(f"engineering_liquefied_phase_change_overclaim_guard FAIL {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
