#!/usr/bin/env python3
"""Audit thermal plausibility of screening liquefied-release gas sources."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-ENGINEERING-LIQUEFIED-RELEASE-THERMAL-PLAUSIBILITY"
STATUS_NOT_READY = "NOT_READY-ENGINEERING-LIQUEFIED-RELEASE-THERMAL-PLAUSIBILITY"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_liquefied_release_thermal_plausibility_20260811")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_liquefied_release_thermal_plausibility_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_liquefied_release_thermal_plausibility_report.md"

GENERATOR = Path("tools/codex_make_liquefied_release_vaporization_csv.py")
SOURCE_MODEL_ROOT = Path("docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807")
SOURCE_MODEL_REPORT = SOURCE_MODEL_ROOT / "engineering_liquefied_release_vaporization_source_model_report.json"
SOURCE_BALANCE_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_source_balance_20260807/"
    "engineering_liquefied_release_source_balance_report.json"
)
SOURCE_MODEL_CUDA_SMOKE_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_cuda_smoke_20260807/"
    "engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.json"
)

CASE_SPECS = {
    "lng_ch4_screening_release": {
        "fluid": "LNG_CH4",
        "species": "CH4",
        "csv": SOURCE_MODEL_ROOT / "lng_ch4_screening_release/lng_ch4_screening_release_source.csv",
        "model": SOURCE_MODEL_ROOT / "lng_ch4_screening_release/lng_ch4_screening_release_source_model.json",
    },
    "lpg_c3h8_screening_release": {
        "fluid": "LPG_C3H8",
        "species": "C3H8",
        "csv": SOURCE_MODEL_ROOT / "lpg_c3h8_screening_release/lpg_c3h8_screening_release_source.csv",
        "model": SOURCE_MODEL_ROOT / "lpg_c3h8_screening_release/lpg_c3h8_screening_release_source_model.json",
    },
}


class ThermalPlausibilityError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ThermalPlausibilityError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ThermalPlausibilityError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ThermalPlausibilityError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def load_generator_fluids() -> dict[str, dict[str, Any]]:
    require(GENERATOR.is_file(), f"missing generator: {GENERATOR}")
    spec = importlib.util.spec_from_file_location("codex_make_liquefied_release_vaporization_csv", GENERATOR)
    require(spec is not None and spec.loader is not None, "unable to load liquefied release generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fluids = getattr(module, "FLUIDS", None)
    require(isinstance(fluids, dict), "generator does not expose FLUIDS")
    return fluids


def finite(raw: str, label: str) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ThermalPlausibilityError(f"{label} is not numeric: {raw!r}") from exc
    require(math.isfinite(value), f"{label} is not finite: {value!r}")
    return value


def read_csv(path: Path) -> list[dict[str, Any]]:
    require(path.is_file(), f"missing source CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    require(rows, f"source CSV contains no rows: {path}")
    return rows


def trapezoid_integral(times: list[float], values: list[float]) -> float:
    return sum(
        0.5 * (left_v + right_v) * (right_t - left_t)
        for left_t, right_t, left_v, right_v in zip(times, times[1:], values, values[1:])
    )


def audit_case(case_name: str, spec: dict[str, Any], fluids: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fluid_name = str(spec["fluid"])
    props = fluids[fluid_name]
    rows = read_csv(Path(spec["csv"]))
    model = load_json(Path(spec["model"]))
    summary = model.get("summary", {})
    require(model.get("status") == "PASS-LIQUEFIED-RELEASE-VAPORIZATION-CSV", f"{case_name} generator status is not passing")
    require(summary.get("fluid") == fluid_name, f"{case_name} fluid mismatch")
    require(summary.get("fuel_species") == spec["species"], f"{case_name} species mismatch")
    require(summary.get("model_is_screening_source_generator") is True, f"{case_name} is not marked as screening generator")
    require(summary.get("cfd_solves_liquid_phase_change") is False, f"{case_name} overclaims liquid phase-change CFD")
    require(summary.get("cfd_solves_flashing_discharge") is False, f"{case_name} overclaims flashing discharge CFD")
    require(summary.get("cfd_solves_pool_spread_evaporation") is False, f"{case_name} overclaims pool evaporation")

    times = [finite(row["time_s"], f"{case_name} time_s") for row in rows]
    mdots = [finite(row["mdot_kg_s"], f"{case_name} mdot_kg_s") for row in rows]
    vapor_t = [finite(row["vapor_T_K"], f"{case_name} vapor_T_K") for row in rows]
    require(all(right > left for left, right in zip(times, times[1:])), f"{case_name} time is not increasing")
    require(all(row["fuel_species"] == spec["species"] for row in rows), f"{case_name} CSV species drift")
    require(all(mdot >= 0.0 for mdot in mdots), f"{case_name} has negative mdot")
    require(max(mdots) > 0.0, f"{case_name} has no positive mdot")
    require(all(200.0 <= temp <= 500.0 for temp in vapor_t), f"{case_name} vapor temperature outside gas-source bounds")

    initial_inventory = float(summary["initial_inventory_kg"])
    remaining_inventory = float(summary["remaining_inventory_kg"])
    liquid_mass_released = initial_inventory - remaining_inventory
    vaporized_fraction = float(summary["vaporized_fraction_to_gas_source"])
    gas_mass_integral = trapezoid_integral(times, mdots)

    boiling_t = float(props["boiling_T_K"])
    liquid_t = float(summary["liquid_T_K"])
    liquid_cp = float(props["liquid_cp_J_kg_K"])
    latent_heat = float(props["latent_heat_J_kg"])
    default_pool_fraction = float(props["default_pool_vapor_fraction"])
    sensible_delta_t = max(0.0, liquid_t - boiling_t)
    flash_fraction_from_superheat = sensible_delta_t * liquid_cp / latent_heat
    expected_vaporized_fraction = max(1.0e-4, min(0.95, flash_fraction_from_superheat + default_pool_fraction))
    external_pool_assisted_fraction = vaporized_fraction - flash_fraction_from_superheat

    require(initial_inventory > 0.0, f"{case_name} initial inventory is not positive")
    require(0.0 <= remaining_inventory < initial_inventory, f"{case_name} remaining inventory is inconsistent")
    require(0.0 < liquid_mass_released <= initial_inventory, f"{case_name} released mass is inconsistent")
    require(0.0 < vaporized_fraction < 1.0, f"{case_name} vaporized fraction outside (0, 1)")
    require(
        math.isclose(vaporized_fraction, expected_vaporized_fraction, rel_tol=1.0e-10, abs_tol=1.0e-12),
        f"{case_name} vaporized fraction no longer matches screening formula",
    )
    require(0.0 <= flash_fraction_from_superheat <= vaporized_fraction, f"{case_name} flash fraction is inconsistent")
    require(0.0 <= external_pool_assisted_fraction <= 0.95, f"{case_name} external pool fraction outside bounds")
    require(math.isclose(external_pool_assisted_fraction, default_pool_fraction, rel_tol=1.0e-10, abs_tol=1.0e-12), f"{case_name} default pool fraction changed")
    require(gas_mass_integral > 0.0, f"{case_name} gas integral is not positive")
    require(gas_mass_integral <= liquid_mass_released * 1.001, f"{case_name} gas source mass exceeds released liquid mass")

    expected_gas_mass_from_inventory = liquid_mass_released * vaporized_fraction
    mass_relative_error = abs(gas_mass_integral - expected_gas_mass_from_inventory) / max(
        expected_gas_mass_from_inventory, 1.0e-12
    )
    require(mass_relative_error <= 0.20, f"{case_name} gas integral differs from inventory model by {mass_relative_error:.3g}")

    sensible_energy_available_j = liquid_mass_released * sensible_delta_t * liquid_cp
    flash_latent_load_j = liquid_mass_released * flash_fraction_from_superheat * latent_heat
    external_pool_latent_load_j = liquid_mass_released * external_pool_assisted_fraction * latent_heat
    gas_source_latent_load_j = gas_mass_integral * latent_heat
    require(sensible_energy_available_j >= 0.0, f"{case_name} sensible energy is negative")
    require(flash_latent_load_j >= 0.0, f"{case_name} flash latent load is negative")
    require(external_pool_latent_load_j > 0.0, f"{case_name} external pool latent load is not positive")
    require(gas_source_latent_load_j > 0.0, f"{case_name} gas-source latent load is not positive")
    require(
        math.isclose(sensible_energy_available_j, flash_latent_load_j, rel_tol=1.0e-10, abs_tol=1.0e-6),
        f"{case_name} superheat flash energy is not self-consistent",
    )
    require(min(vapor_t) >= boiling_t, f"{case_name} vapor temperature is below boiling temperature")

    result = {
        "case": case_name,
        "fluid": fluid_name,
        "species": str(spec["species"]),
        "liquid_T_K": liquid_t,
        "boiling_T_K": boiling_t,
        "vapor_T_min_K": min(vapor_t),
        "vapor_T_max_K": max(vapor_t),
        "initial_inventory_kg": initial_inventory,
        "remaining_inventory_kg": remaining_inventory,
        "liquid_mass_released_kg": liquid_mass_released,
        "gas_mass_integral_kg": gas_mass_integral,
        "expected_gas_mass_from_inventory_kg": expected_gas_mass_from_inventory,
        "gas_mass_relative_error": mass_relative_error,
        "vaporized_fraction_to_gas_source": vaporized_fraction,
        "flash_fraction_from_superheat": flash_fraction_from_superheat,
        "external_pool_assisted_fraction": external_pool_assisted_fraction,
        "default_pool_vapor_fraction": default_pool_fraction,
        "vaporized_fraction_matches_screening_formula": True,
        "sensible_energy_available_J": sensible_energy_available_j,
        "flash_latent_load_J": flash_latent_load_j,
        "external_pool_latent_load_J": external_pool_latent_load_j,
        "gas_source_latent_load_J": gas_source_latent_load_j,
        "thermal_plausibility_ready": True,
        "cfd_solves_liquid_phase_change": False,
        "cfd_solves_flashing_discharge": False,
        "cfd_solves_pool_spread_evaporation": False,
    }
    evidence = [
        evidence_entry(f"{case_name}_source_csv", Path(spec["csv"])),
        evidence_entry(f"{case_name}_source_model", Path(spec["model"])),
    ]
    return result, evidence


def build_report() -> dict[str, Any]:
    fluids = load_generator_fluids()
    source_model = load_json(SOURCE_MODEL_REPORT)
    source_balance = load_json(SOURCE_BALANCE_REPORT)
    cuda_smoke = load_json(SOURCE_MODEL_CUDA_SMOKE_REPORT)
    require(source_model.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL", "source model is not passing")
    require(source_balance.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE", "source balance is not passing")
    require(cuda_smoke.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE", "CUDA smoke is not passing")

    cases: list[dict[str, Any]] = []
    evidence_files = [
        evidence_entry("liquefied_release_generator", GENERATOR),
        evidence_entry("liquefied_release_source_model_report", SOURCE_MODEL_REPORT),
        evidence_entry("liquefied_release_source_balance_report", SOURCE_BALANCE_REPORT),
        evidence_entry("liquefied_release_source_model_cuda_smoke_report", SOURCE_MODEL_CUDA_SMOKE_REPORT),
    ]
    for case_name, spec in CASE_SPECS.items():
        result, evidence = audit_case(case_name, spec, fluids)
        cases.append(result)
        evidence_files.extend(evidence)

    species = sorted({case["species"] for case in cases})
    ready = (
        len(cases) == 2
        and species == ["C3H8", "CH4"]
        and all(case["thermal_plausibility_ready"] for case in cases)
        and all(case["vaporized_fraction_matches_screening_formula"] for case in cases)
        and all(case["gas_mass_relative_error"] <= 0.20 for case in cases)
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "liquefied_release_thermal_plausibility_ready": ready,
            "case_count": len(cases),
            "species": species,
            "all_vaporized_fraction_matches_screening_formula": all(
                case["vaporized_fraction_matches_screening_formula"] for case in cases
            ),
            "all_flash_fraction_bounded": all(
                0.0 <= case["flash_fraction_from_superheat"] <= case["vaporized_fraction_to_gas_source"]
                for case in cases
            ),
            "all_external_pool_fraction_bounded": all(
                0.0 <= case["external_pool_assisted_fraction"] <= 0.95 for case in cases
            ),
            "all_heat_loads_positive": all(case["gas_source_latent_load_J"] > 0.0 for case in cases),
            "max_gas_mass_relative_error": max(case["gas_mass_relative_error"] for case in cases),
            "total_gas_source_latent_load_J": sum(case["gas_source_latent_load_J"] for case in cases),
            "source_model_status": source_model.get("status"),
            "source_balance_status": source_balance.get("status"),
            "cuda_smoke_status": cuda_smoke.get("status"),
            "claim_level": "screening_external_gas_source_thermal_plausibility_not_internal_liquid_solver",
            "production_phase_change_claim_allowed": False,
            "cfd_solves_liquid_phase_change": False,
            "cfd_solves_flashing_discharge": False,
            "cfd_solves_pool_spread_evaporation": False,
        },
        "cases": cases,
        "evidence_files": evidence_files,
        "limitations": [
            "This report audits the thermal plausibility of generated gas-source schedules only.",
            "It does not validate internal tank rupture mechanics, flashing multiphase discharge, liquid-pool spread, boiling heat transfer, or ground heat transfer.",
            "For production liquefied-gas phase-change claims, replace the screening source with measured, process-safety, or high-fidelity external-source data and add validation evidence.",
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "thermal plausibility report is not passing")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("liquefied_release_thermal_plausibility_ready") is True, "thermal plausibility is not ready")
    require(summary.get("case_count") == 2, "unexpected case count")
    require(summary.get("species") == ["C3H8", "CH4"], "unexpected species")
    require(summary.get("all_vaporized_fraction_matches_screening_formula") is True, "vaporized fraction formula mismatch")
    require(summary.get("all_flash_fraction_bounded") is True, "flash fraction is not bounded")
    require(summary.get("all_external_pool_fraction_bounded") is True, "external pool fraction is not bounded")
    require(summary.get("all_heat_loads_positive") is True, "heat loads are not positive")
    require(summary.get("max_gas_mass_relative_error") <= 0.20, "gas mass relative error is too large")
    require(summary.get("production_phase_change_claim_allowed") is False, "production phase-change claim was overclaimed")
    require(summary.get("cfd_solves_liquid_phase_change") is False, "liquid phase-change CFD was overclaimed")
    require(summary.get("cfd_solves_flashing_discharge") is False, "flashing discharge CFD was overclaimed")
    require(summary.get("cfd_solves_pool_spread_evaporation") is False, "pool evaporation CFD was overclaimed")
    cases = data.get("cases")
    require(isinstance(cases, list) and len(cases) == 2, "missing case details")
    for case in cases:
        require(case.get("thermal_plausibility_ready") is True, f"{case.get('case')} not ready")
        require(case.get("vaporized_fraction_matches_screening_formula") is True, f"{case.get('case')} formula mismatch")
        require(case.get("gas_mass_relative_error") <= 0.20, f"{case.get('case')} mass error too large")
        require(case.get("gas_source_latent_load_J") > 0.0, f"{case.get('case')} latent load not positive")
        require(case.get("cfd_solves_liquid_phase_change") is False, f"{case.get('case')} overclaims phase change")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], output: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Engineering Liquefied Release Thermal Plausibility",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- Thermal plausibility ready: {summary['liquefied_release_thermal_plausibility_ready']}",
        f"- Species: {', '.join(summary['species'])}",
        f"- Max gas mass relative error: {summary['max_gas_mass_relative_error']:.6g}",
        f"- Total gas-source latent load J: {summary['total_gas_source_latent_load_J']:.6g}",
        f"- Production phase-change claim allowed: {summary['production_phase_change_claim_allowed']}",
        "",
        "## Cases",
        "",
    ]
    for case in report["cases"]:
        lines.extend(
            [
                f"### {case['case']}",
                "",
                f"- Fluid/species: {case['fluid']} / {case['species']}",
                f"- Vaporized fraction: {case['vaporized_fraction_to_gas_source']:.6g}",
                f"- Flash fraction from superheat: {case['flash_fraction_from_superheat']:.6g}",
                f"- External pool-assisted fraction: {case['external_pool_assisted_fraction']:.6g}",
                f"- Gas mass integral kg: {case['gas_mass_integral_kg']:.6g}",
                f"- Gas-source latent load J: {case['gas_source_latent_load_J']:.6g}",
                "",
            ]
        )
    lines.extend(["## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data)
        print(f"liquefied_release_thermal_plausibility VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"liquefied_release_thermal_plausibility PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
