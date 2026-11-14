#!/usr/bin/env python3
"""Audit mass and boundary consistency for liquefied-release external gas sources."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2
STATUS = "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_liquefied_release_source_balance_20260807")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_liquefied_release_source_balance_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_liquefied_release_source_balance_report.md"

SOURCE_MODEL_ROOT = Path("docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807")
SOURCE_MODEL_REPORT = SOURCE_MODEL_ROOT / "engineering_liquefied_release_vaporization_source_model_report.json"
CUDA_SMOKE_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_cuda_smoke_20260807/"
    "engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.json"
)
CASE_SPECS = {
    "lng_ch4_screening_release": {
        "species": "CH4",
        "csv": SOURCE_MODEL_ROOT / "lng_ch4_screening_release/lng_ch4_screening_release_source.csv",
        "model": SOURCE_MODEL_ROOT / "lng_ch4_screening_release/lng_ch4_screening_release_source_model.json",
        "mapping": SOURCE_MODEL_ROOT / "lng_ch4_screening_release/lng_ch4_screening_release_source_mapping.json",
        "input": SOURCE_MODEL_ROOT / "lng_ch4_screening_release/input.lng_ch4_screening_release.generated",
    },
    "lpg_c3h8_screening_release": {
        "species": "C3H8",
        "csv": SOURCE_MODEL_ROOT / "lpg_c3h8_screening_release/lpg_c3h8_screening_release_source.csv",
        "model": SOURCE_MODEL_ROOT / "lpg_c3h8_screening_release/lpg_c3h8_screening_release_source_model.json",
        "mapping": SOURCE_MODEL_ROOT / "lpg_c3h8_screening_release/lpg_c3h8_screening_release_source_mapping.json",
        "input": SOURCE_MODEL_ROOT / "lpg_c3h8_screening_release/input.lpg_c3h8_screening_release.generated",
    },
}

CSV_COLUMNS = (
    "time_s",
    "mdot_kg_s",
    "vapor_T_K",
    "fuel_species",
    "leak_vel_x_m_s",
    "leak_vel_y_m_s",
    "leak_vel_z_m_s",
    "source_radius_m",
    "source_x_m",
    "source_y_m",
    "source_z_m",
    "source_pressure_Pa",
)


class SourceBalanceError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceBalanceError(message)


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
        raise SourceBalanceError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SourceBalanceError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def finite(raw: str, label: str) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise SourceBalanceError(f"{label} is not numeric: {raw!r}") from exc
    require(math.isfinite(value), f"{label} is not finite: {value!r}")
    return value


def read_csv(path: Path) -> list[dict[str, Any]]:
    require(path.is_file(), f"missing source CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        require(reader.fieldnames == list(CSV_COLUMNS), f"unexpected CSV columns in {path}: {reader.fieldnames}")
        rows: list[dict[str, Any]] = []
        for idx, row in enumerate(reader, 1):
            parsed = {name: finite(row[name], f"{path} row {idx} {name}") for name in CSV_COLUMNS if name != "fuel_species"}
            parsed["fuel_species"] = str(row["fuel_species"]).strip()
            rows.append(parsed)
    require(rows, f"source CSV contains no rows: {path}")
    return rows


def trapezoid_integral(times: list[float], values: list[float]) -> float:
    total = 0.0
    for left_t, right_t, left_v, right_v in zip(times, times[1:], values, values[1:]):
        total += 0.5 * (left_v + right_v) * (right_t - left_t)
    return total


def float_list(raw: str, label: str) -> list[float]:
    values = [finite(item, f"{label}[{idx}]") for idx, item in enumerate(str(raw).split())]
    require(values, f"{label} is empty")
    return values


def assert_close_lists(actual: list[float], expected: list[float], label: str, rel_tol: float = 1.0e-9, abs_tol: float = 1.0e-9) -> None:
    require(len(actual) == len(expected), f"{label} length mismatch: {len(actual)} != {len(expected)}")
    for idx, (left, right) in enumerate(zip(actual, expected)):
        require(
            math.isclose(left, right, rel_tol=rel_tol, abs_tol=abs_tol),
            f"{label}[{idx}] mismatch: {left} != {right}",
        )


def audit_case(case_name: str, spec: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = read_csv(Path(spec["csv"]))
    model = load_json(Path(spec["model"]))
    mapping = load_json(Path(spec["mapping"]))
    generated_input = Path(spec["input"]).read_text(encoding="utf-8")

    species = str(spec["species"])
    times = [float(row["time_s"]) for row in rows]
    mdots = [float(row["mdot_kg_s"]) for row in rows]
    temps = [float(row["vapor_T_K"]) for row in rows]
    radii = [float(row["source_radius_m"]) for row in rows]
    pressures = [float(row["source_pressure_Pa"]) for row in rows]
    vel_x = [float(row["leak_vel_x_m_s"]) for row in rows]
    vel_y = [float(row["leak_vel_y_m_s"]) for row in rows]
    vel_z = [float(row["leak_vel_z_m_s"]) for row in rows]
    xs = [float(row["source_x_m"]) for row in rows]
    ys = [float(row["source_y_m"]) for row in rows]
    zs = [float(row["source_z_m"]) for row in rows]

    require(all(row["fuel_species"] == species for row in rows), f"{case_name} species drifted from {species}")
    require(all(right > left for left, right in zip(times, times[1:])), f"{case_name} time_s is not strictly increasing")
    require(min(times) >= 0.0, f"{case_name} starts before t=0")
    require(all(mdot >= 0.0 for mdot in mdots), f"{case_name} contains negative mdot")
    require(max(mdots) > 0.0, f"{case_name} has no positive mdot")
    require(all(left >= right for left, right in zip(mdots, mdots[1:])), f"{case_name} mdot is not monotone nonincreasing")
    require(all(200.0 <= temp <= 500.0 for temp in temps), f"{case_name} vapor_T_K outside screening gas-source bounds")
    require(all(50_000.0 <= pressure <= 1_500_000.0 for pressure in pressures), f"{case_name} source_pressure_Pa outside bounds")
    require(all(0.0 < radius <= 1.0 for radius in radii), f"{case_name} source_radius_m outside bounds")
    require(all(0.0 <= x <= 2.0 and 0.0 <= y <= 1.0 and 0.0 <= z <= 1.0 for x, y, z in zip(xs, ys, zs)), f"{case_name} source location outside smoke domain")
    require(all(math.sqrt(x * x + y * y + z * z) > 0.0 for x, y, z in zip(vel_x, vel_y, vel_z)), f"{case_name} contains zero jet speed")
    require(all(math.sqrt(x * x + y * y + z * z) < 200.0 for x, y, z in zip(vel_x, vel_y, vel_z)), f"{case_name} jet speed outside screening bound")

    msum = model.get("summary", {})
    require(model.get("status") == "PASS-LIQUEFIED-RELEASE-VAPORIZATION-CSV", f"{case_name} source model not passing")
    require(msum.get("model_is_screening_source_generator") is True, f"{case_name} is not marked as screening source generator")
    require(msum.get("cfd_solves_liquid_phase_change") is False, f"{case_name} overclaims liquid phase-change CFD")
    require(msum.get("cfd_solves_pool_spread_evaporation") is False, f"{case_name} overclaims pool spread evaporation")
    require(msum.get("cfd_solves_flashing_discharge") is False, f"{case_name} overclaims flashing discharge CFD")
    require(msum.get("fuel_species") == species, f"{case_name} model species mismatch")
    require(msum.get("gas_mdot_decays") is True, f"{case_name} model did not record decaying gas mdot")
    require(msum.get("gas_mdot_positive") is True, f"{case_name} model did not record positive gas mdot")

    initial_inventory = float(msum["initial_inventory_kg"])
    remaining_inventory = float(msum["remaining_inventory_kg"])
    vaporized_fraction = float(msum["vaporized_fraction_to_gas_source"])
    liquid_mass_released = initial_inventory - remaining_inventory
    gas_mass_integral = trapezoid_integral(times, mdots)
    expected_gas_mass = liquid_mass_released * vaporized_fraction
    relative_mass_error = abs(gas_mass_integral - expected_gas_mass) / max(expected_gas_mass, 1.0e-12)
    require(initial_inventory > remaining_inventory >= 0.0, f"{case_name} inventory did not decrease consistently")
    require(0.0 < vaporized_fraction < 1.0, f"{case_name} vaporized fraction outside (0, 1)")
    require(0.0 < gas_mass_integral < initial_inventory, f"{case_name} gas mass integral outside inventory bounds")
    require(gas_mass_integral <= liquid_mass_released * 1.001, f"{case_name} gas mass exceeds released liquid mass")
    require(relative_mass_error <= 0.20, f"{case_name} gas mass integral disagrees with source-model inventory by {relative_mass_error:.3g}")

    applied = mapping.get("applied_replacements", {})
    require(mapping.get("status") == "PASS-EXTERNAL-VAPORIZATION-SOURCE-INPUT", f"{case_name} mapping not passing")
    require(mapping.get("source_csv") == str(spec["csv"]), f"{case_name} mapping source_csv mismatch")
    require(mapping.get("output_input") == str(spec["input"]), f"{case_name} mapping output_input mismatch")
    require(applied.get("prob.fuel_species") == species, f"{case_name} mapped fuel species mismatch")
    require(applied.get("prob.leak_model") == "fixed_mass_flow", f"{case_name} mapped leak model mismatch")
    require(int(applied.get("prob.leak_schedule_count", "-1")) == len(rows), f"{case_name} mapped schedule count mismatch")
    assert_close_lists(float_list(applied["prob.leak_schedule_times"], f"{case_name} schedule times"), times, f"{case_name} schedule times")
    assert_close_lists(float_list(applied["prob.leak_schedule_rates"], f"{case_name} schedule rates"), mdots, f"{case_name} schedule rates")
    assert_close_lists(float_list(applied["prob.leak_schedule_temperatures"], f"{case_name} schedule temperatures"), temps, f"{case_name} schedule temperatures")
    assert_close_lists(float_list(applied["prob.leak_schedule_radius"], f"{case_name} schedule radius"), radii, f"{case_name} schedule radius")
    assert_close_lists(float_list(applied["prob.leak_schedule_vel_x"], f"{case_name} schedule vel_x"), vel_x, f"{case_name} schedule vel_x")
    assert_close_lists(float_list(applied["prob.leak_schedule_vel_y"], f"{case_name} schedule vel_y"), vel_y, f"{case_name} schedule vel_y")
    assert_close_lists(float_list(applied["prob.leak_schedule_vel_z"], f"{case_name} schedule vel_z"), vel_z, f"{case_name} schedule vel_z")
    assert_close_lists(float_list(applied["prob.leak_schedule_x"], f"{case_name} schedule x"), xs, f"{case_name} schedule x")
    assert_close_lists(float_list(applied["prob.leak_schedule_y"], f"{case_name} schedule y"), ys, f"{case_name} schedule y")
    assert_close_lists(float_list(applied["prob.leak_schedule_z"], f"{case_name} schedule z"), zs, f"{case_name} schedule z")
    require(f"prob.fuel_species = {species}" in generated_input, f"{case_name} generated input missing fuel species")
    require("prob.leak_model = fixed_mass_flow" in generated_input, f"{case_name} generated input missing fixed mass-flow model")

    result = {
        "case": case_name,
        "species": species,
        "point_count": len(rows),
        "time_start_s": times[0],
        "time_end_s": times[-1],
        "mdot_max_kg_s": max(mdots),
        "mdot_final_kg_s": mdots[-1],
        "gas_mass_integral_kg": gas_mass_integral,
        "liquid_mass_released_kg": liquid_mass_released,
        "expected_gas_mass_from_inventory_kg": expected_gas_mass,
        "inventory_mass_relative_error": relative_mass_error,
        "vaporized_fraction_to_gas_source": vaporized_fraction,
        "vapor_T_min_K": min(temps),
        "vapor_T_max_K": max(temps),
        "source_pressure_min_Pa": min(pressures),
        "source_pressure_max_Pa": max(pressures),
        "source_radius_min_m": min(radii),
        "source_radius_max_m": max(radii),
        "jet_speed_max_m_s": max(math.sqrt(x * x + y * y + z * z) for x, y, z in zip(vel_x, vel_y, vel_z)),
        "mapping_schedule_matches_csv": True,
        "generated_input_matches_mapping": True,
        "cfd_solves_liquid_phase_change": False,
        "cfd_solves_pool_spread_evaporation": False,
        "cfd_solves_flashing_discharge": False,
    }
    evidence = [
        evidence_entry(f"{case_name}_source_csv", Path(spec["csv"])),
        evidence_entry(f"{case_name}_source_model", Path(spec["model"])),
        evidence_entry(f"{case_name}_source_mapping", Path(spec["mapping"])),
        evidence_entry(f"{case_name}_generated_input", Path(spec["input"])),
    ]
    return result, evidence


def build_report() -> dict[str, Any]:
    source_model_report = load_json(SOURCE_MODEL_REPORT)
    cuda_smoke_report = load_json(CUDA_SMOKE_REPORT)
    require(source_model_report.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL", "source-model report is not passing")
    require(cuda_smoke_report.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE", "source-model CUDA smoke report is not passing")

    case_results: dict[str, Any] = {}
    evidence_files = [
        evidence_entry("source_model_report", SOURCE_MODEL_REPORT),
        evidence_entry("source_model_cuda_smoke_report", CUDA_SMOKE_REPORT),
    ]
    for case_name, spec in CASE_SPECS.items():
        result, evidence = audit_case(case_name, spec)
        case_results[case_name] = result
        evidence_files.extend(evidence)

    gas_mass_total = sum(float(case["gas_mass_integral_kg"]) for case in case_results.values())
    ready = (
        len(case_results) == 2
        and all(case["mapping_schedule_matches_csv"] for case in case_results.values())
        and all(case["generated_input_matches_mapping"] for case in case_results.values())
        and all(float(case["inventory_mass_relative_error"]) <= 0.20 for case in case_results.values())
        and all(case["cfd_solves_liquid_phase_change"] is False for case in case_results.values())
        and gas_mass_total > 0.0
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE",
        "summary": {
            "liquefied_release_source_balance_ready": ready,
            "case_count": len(case_results),
            "species": sorted({case["species"] for case in case_results.values()}),
            "total_gas_mass_integral_kg": gas_mass_total,
            "max_inventory_mass_relative_error": max(float(case["inventory_mass_relative_error"]) for case in case_results.values()),
            "mapping_schedule_matches_csv": all(case["mapping_schedule_matches_csv"] for case in case_results.values()),
            "generated_input_matches_mapping": all(case["generated_input_matches_mapping"] for case in case_results.values()),
            "source_model_cuda_smoke_status": cuda_smoke_report.get("status"),
            "cfd_solves_liquid_phase_change": False,
            "cfd_solves_pool_spread_evaporation": False,
            "cfd_solves_flashing_discharge": False,
            "production_phase_change_claim_allowed": False,
            "overclaim_guard_active": True,
        },
        "cases": case_results,
        "limitations": [
            "This report audits external gas-source schedules and PeleLMeX input mappings.",
            "It does not convert the current model into an internal liquid phase-change, flashing, or pool-spread CFD solver.",
            "Use measured or higher-fidelity source terms when strict production phase-change claims are required.",
        ],
        "evidence_files": evidence_files,
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, f"unexpected status: {data.get('status')}")
    summary = data.get("summary")
    cases = data.get("cases")
    require(isinstance(summary, dict), "missing summary")
    require(isinstance(cases, dict), "missing cases")
    require(summary.get("liquefied_release_source_balance_ready") is True, "source balance is not ready")
    require(summary.get("case_count") == 2, "unexpected case count")
    require(summary.get("species") == ["C3H8", "CH4"], "unexpected species set")
    require(summary.get("total_gas_mass_integral_kg") > 0.0, "gas mass integral is not positive")
    require(summary.get("max_inventory_mass_relative_error") <= 0.20, "inventory mass balance error too large")
    require(summary.get("mapping_schedule_matches_csv") is True, "mapping schedules do not match CSV")
    require(summary.get("generated_input_matches_mapping") is True, "generated input does not match mapping")
    require(summary.get("source_model_cuda_smoke_status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE", "CUDA smoke evidence is not passing")
    require(summary.get("cfd_solves_liquid_phase_change") is False, "liquid phase-change boundary changed unexpectedly")
    require(summary.get("cfd_solves_pool_spread_evaporation") is False, "pool evaporation boundary changed unexpectedly")
    require(summary.get("cfd_solves_flashing_discharge") is False, "flashing discharge boundary changed unexpectedly")
    require(summary.get("production_phase_change_claim_allowed") is False, "production phase-change claim changed unexpectedly")
    require(summary.get("overclaim_guard_active") is True, "overclaim guard is not active")
    for case_name in CASE_SPECS:
        case = cases.get(case_name)
        require(isinstance(case, dict), f"missing case result: {case_name}")
        require(case.get("mapping_schedule_matches_csv") is True, f"{case_name} mapping schedule mismatch")
        require(case.get("generated_input_matches_mapping") is True, f"{case_name} generated input mismatch")
        require(case.get("inventory_mass_relative_error") <= 0.20, f"{case_name} mass balance error too large")
        require(case.get("gas_mass_integral_kg") > 0.0, f"{case_name} gas mass integral is not positive")
        require(case.get("gas_mass_integral_kg") < case.get("liquid_mass_released_kg"), f"{case_name} gas mass exceeds liquid release")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Engineering Liquefied-Release Source Balance Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Case count: `{summary['case_count']}`",
        f"- Species: `{', '.join(summary['species'])}`",
        f"- Total gas mass integral kg: `{summary['total_gas_mass_integral_kg']}`",
        f"- Max inventory mass relative error: `{summary['max_inventory_mass_relative_error']}`",
        f"- Mapping schedule matches CSV: `{summary['mapping_schedule_matches_csv']}`",
        f"- Generated input matches mapping: `{summary['generated_input_matches_mapping']}`",
        f"- CUDA smoke: `{summary['source_model_cuda_smoke_status']}`",
        f"- Internal liquid phase-change CFD: `{summary['cfd_solves_liquid_phase_change']}`",
        f"- Pool spread evaporation CFD: `{summary['cfd_solves_pool_spread_evaporation']}`",
        f"- Flashing discharge CFD: `{summary['cfd_solves_flashing_discharge']}`",
        f"- Production phase-change claim allowed: `{summary['production_phase_change_claim_allowed']}`",
        f"- Overclaim guard active: `{summary['overclaim_guard_active']}`",
        "",
        "## Cases",
        "",
    ]
    for case_name, case in report["cases"].items():
        lines.extend(
            [
                f"### {case_name}",
                "",
                f"- Species: `{case['species']}`",
                f"- Points: `{case['point_count']}`",
                f"- Time span s: `{case['time_start_s']} .. {case['time_end_s']}`",
                f"- Gas mass integral kg: `{case['gas_mass_integral_kg']}`",
                f"- Expected gas mass kg: `{case['expected_gas_mass_from_inventory_kg']}`",
                f"- Inventory relative error: `{case['inventory_mass_relative_error']}`",
                f"- Jet speed max m/s: `{case['jet_speed_max_m_s']}`",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"engineering_liquefied_release_source_balance VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"engineering_liquefied_release_source_balance PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
