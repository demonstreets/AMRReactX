#!/usr/bin/env python3
"""Write/verify the LNG/LPG breach-to-gas-source engineering contract."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-ENGINEERING-LIQUEFIED-BREACH-SOURCE-CONTRACT"
STATUS_NOT_READY = "NOT_READY-ENGINEERING-LIQUEFIED-BREACH-SOURCE-CONTRACT"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_liquefied_breach_source_contract_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_liquefied_breach_source_contract_report.md"

GENERATOR = Path("tools/codex_make_liquefied_release_vaporization_csv.py")
SOURCE_MODEL_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/"
    "engineering_liquefied_release_vaporization_source_model_report.json"
)
SOURCE_BALANCE_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_source_balance_20260807/"
    "engineering_liquefied_release_source_balance_report.json"
)
THERMAL_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_thermal_plausibility_20260811/"
    "engineering_liquefied_release_thermal_plausibility_report.json"
)


class BreachContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BreachContractError(message)


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
        raise BreachContractError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BreachContractError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def load_generator_module() -> Any:
    require(GENERATOR.is_file(), f"missing generator: {GENERATOR}")
    spec = importlib.util.spec_from_file_location("codex_make_liquefied_release_vaporization_csv", GENERATOR)
    require(spec is not None and spec.loader is not None, "unable to import liquefied-release generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(isinstance(getattr(module, "FLUIDS", None), dict), "generator does not expose FLUIDS")
    require(callable(getattr(module, "build_rows", None)), "generator does not expose build_rows")
    require(callable(getattr(module, "write_csv", None)), "generator does not expose write_csv")
    return module


def trapezoid_integral(times: list[float], values: list[float]) -> float:
    return sum(0.5 * (left_v + right_v) * (right_t - left_t) for left_t, right_t, left_v, right_v in zip(times, times[1:], values, values[1:]))


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"missing generated source CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    require(rows, f"generated source CSV is empty: {path}")
    return rows


CONTRACT_CASES: dict[str, dict[str, Any]] = {
    "lng_ch4_tank_breach_screening": {
        "fluid": "LNG_CH4",
        "breach_kind": "atmospheric_tank_breach_or_transfer_line_failure",
        "inventory_kg": 5000.0,
        "initial_pressure_Pa": 6.0e5,
        "ambient_pressure_Pa": 101325.0,
        "hole_diameter_m": 0.05,
        "duration_s": 60.0,
        "points": 13,
        "discharge_coeff": 0.62,
        "pressure_decay_exponent": 1.0,
        "liquid_T_K": 115.0,
        "vapor_T_K": 285.0,
        "vaporized_fraction": None,
        "pool_vapor_fraction": None,
        "source_radius_m": 0.10,
        "source_x_m": 0.55,
        "source_y_m": 0.50,
        "source_z_m": 0.10,
        "jet_dir_x": 1.0,
        "jet_dir_y": 0.0,
        "jet_dir_z": 0.0,
        "max_jet_speed_m_s": 200.0,
        "accepted_cfd_use": "LNG_CH4 external vaporization gas-source schedule for CH4 dispersion/ignition/fire",
    },
    "lpg_c3h8_pipe_rupture_screening": {
        "fluid": "LPG_C3H8",
        "breach_kind": "pressurized_lpg_pipe_or_small_vessel_breach",
        "inventory_kg": 2000.0,
        "initial_pressure_Pa": 9.0e5,
        "ambient_pressure_Pa": 101325.0,
        "hole_diameter_m": 0.025,
        "duration_s": 60.0,
        "points": 13,
        "discharge_coeff": 0.62,
        "pressure_decay_exponent": 1.0,
        "liquid_T_K": 245.0,
        "vapor_T_K": 300.0,
        "vaporized_fraction": None,
        "pool_vapor_fraction": None,
        "source_radius_m": 0.08,
        "source_x_m": 0.55,
        "source_y_m": 0.50,
        "source_z_m": 0.50,
        "jet_dir_x": 1.0,
        "jet_dir_y": 0.0,
        "jet_dir_z": 0.0,
        "max_jet_speed_m_s": 200.0,
        "accepted_cfd_use": "LPG_C3H8 external vaporization gas-source schedule for C3H8 dispersion/ignition/fire",
    },
}


REQUIRED_INPUT_FIELDS = [
    "fluid",
    "inventory_kg",
    "initial_pressure_Pa",
    "ambient_pressure_Pa",
    "hole_diameter_m",
    "duration_s",
    "liquid_T_K",
    "source_radius_m",
    "source_x_m",
    "source_y_m",
    "source_z_m",
    "jet_dir_x",
    "jet_dir_y",
    "jet_dir_z",
]


def namespace_from_case(case: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(**{key: value for key, value in case.items() if key != "accepted_cfd_use" and key != "breach_kind"})


def evaluate_case(name: str, case: dict[str, Any], module: Any, output_root: Path) -> dict[str, Any]:
    rows, generator_summary = module.build_rows(namespace_from_case(case))
    case_root = output_root / name
    csv_path = case_root / f"{name}_source.csv"
    contract_path = case_root / f"{name}_breach_contract.json"
    module.write_csv(csv_path, rows)

    csv_rows = read_csv(csv_path)
    times = [float(row["time_s"]) for row in csv_rows]
    mdots = [float(row["mdot_kg_s"]) for row in csv_rows]
    velocities = [
        math.sqrt(
            float(row["leak_vel_x_m_s"]) ** 2
            + float(row["leak_vel_y_m_s"]) ** 2
            + float(row["leak_vel_z_m_s"]) ** 2
        )
        for row in csv_rows
    ]
    gas_mass_kg = trapezoid_integral(times, mdots)
    liquid_mass_released = float(generator_summary["initial_inventory_kg"]) - float(generator_summary["remaining_inventory_kg"])
    vaporized_fraction = float(generator_summary["vaporized_fraction_to_gas_source"])
    expected_gas_mass = liquid_mass_released * vaporized_fraction
    mass_error = abs(gas_mass_kg - expected_gas_mass) / max(expected_gas_mass, 1.0e-12)

    require(all(field in case for field in REQUIRED_INPUT_FIELDS), f"{name} missing required input fields")
    require(all(right > left for left, right in zip(times, times[1:])), f"{name} time is not strictly increasing")
    require(all(mdot >= 0.0 for mdot in mdots), f"{name} contains negative gas mdot")
    require(max(mdots) > 0.0, f"{name} contains no positive gas mdot")
    require(0.0 < vaporized_fraction < 1.0, f"{name} vaporized fraction outside (0, 1)")
    require(0.0 < liquid_mass_released <= float(generator_summary["initial_inventory_kg"]), f"{name} liquid release mass inconsistent")
    require(gas_mass_kg <= liquid_mass_released * 1.001, f"{name} gas mass exceeds released liquid")
    require(mass_error <= 0.20, f"{name} gas mass differs from inventory model by {mass_error:.3g}")
    require(max(velocities) <= float(case["max_jet_speed_m_s"]) * 1.000001, f"{name} jet speed cap violated")
    require(generator_summary["cfd_solves_liquid_phase_change"] is False, f"{name} overclaims liquid phase-change CFD")
    require(generator_summary["cfd_solves_flashing_discharge"] is False, f"{name} overclaims flashing discharge CFD")
    require(generator_summary["cfd_solves_pool_spread_evaporation"] is False, f"{name} overclaims pool evaporation CFD")

    contract = {
        "schema_version": 1,
        "case": name,
        "breach_kind": case["breach_kind"],
        "accepted_cfd_use": case["accepted_cfd_use"],
        "required_input_fields": REQUIRED_INPUT_FIELDS,
        "generator_inputs": {key: case[key] for key in sorted(case) if key not in {"accepted_cfd_use", "breach_kind"}},
        "generator_summary": generator_summary,
        "derived": {
            "gas_mass_integral_kg": gas_mass_kg,
            "liquid_mass_released_kg": liquid_mass_released,
            "expected_gas_mass_kg": expected_gas_mass,
            "gas_mass_relative_error": mass_error,
            "peak_gas_mdot_kg_s": max(mdots),
            "peak_jet_speed_m_s": max(velocities),
            "time_window_s": [times[0], times[-1]],
        },
        "claim_boundary": {
            "contract_accepts_screening_breach_inputs": True,
            "generates_external_gas_source_schedule": True,
            "cfd_solves_liquid_phase_change": False,
            "cfd_solves_flashing_discharge": False,
            "cfd_solves_pool_spread_evaporation": False,
            "production_phase_change_claim_allowed": False,
        },
        "source_csv": str(csv_path),
    }
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "case": name,
        "fluid": case["fluid"],
        "breach_kind": case["breach_kind"],
        "fuel_species": generator_summary["fuel_species"],
        "source_ready": True,
        "contract_path": str(contract_path),
        "source_csv": str(csv_path),
        "vaporized_fraction_to_gas_source": vaporized_fraction,
        "liquid_mass_released_kg": liquid_mass_released,
        "gas_mass_integral_kg": gas_mass_kg,
        "gas_mass_relative_error": mass_error,
        "peak_gas_mdot_kg_s": max(mdots),
        "peak_jet_speed_m_s": max(velocities),
        "cfd_solves_liquid_phase_change": False,
        "cfd_solves_flashing_discharge": False,
        "cfd_solves_pool_spread_evaporation": False,
        "production_phase_change_claim_allowed": False,
    }


def validate_upstream_reports() -> list[dict[str, Any]]:
    expected = {
        "source_model": (SOURCE_MODEL_REPORT, "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL"),
        "source_balance": (SOURCE_BALANCE_REPORT, "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE"),
        "thermal_plausibility": (THERMAL_REPORT, "PASS-ENGINEERING-LIQUEFIED-RELEASE-THERMAL-PLAUSIBILITY"),
    }
    entries = []
    for label, (path, status) in expected.items():
        data = load_json(path)
        require(data.get("status") == status, f"{label} upstream status is not passing")
        summary = data.get("summary", {})
        require(isinstance(summary, dict), f"{label} summary missing")
        for key in ("cfd_solves_liquid_phase_change", "cfd_solves_flashing_discharge", "cfd_solves_pool_spread_evaporation"):
            require(summary.get(key) is False, f"{label} overclaims {key}")
        entries.append(evidence_entry(label, path))
    return entries


def build_report(output_root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    module = load_generator_module()
    upstream_evidence = validate_upstream_reports()
    fluids = module.FLUIDS
    require({"LNG_CH4", "LPG_C3H8"}.issubset(fluids), "generator lacks LNG_CH4 or LPG_C3H8")

    cases = [evaluate_case(name, case, module, output_root) for name, case in CONTRACT_CASES.items()]
    ready = all(case["source_ready"] for case in cases)
    evidence_files = upstream_evidence + [evidence_entry(f"{case['case']}_contract", Path(case["contract_path"])) for case in cases]
    evidence_files.extend(evidence_entry(f"{case['case']}_source_csv", Path(case["source_csv"])) for case in cases)

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "scope": "engineering LNG/LPG breach input contract for external gas-source CFD workflows",
        "summary": {
            "liquefied_breach_source_contract_ready": ready,
            "case_count": len(cases),
            "fluids": sorted({case["fluid"] for case in cases}),
            "species": sorted({case["fuel_species"] for case in cases}),
            "required_input_fields": REQUIRED_INPUT_FIELDS,
            "contract_accepts_screening_breach_inputs": True,
            "generates_external_gas_source_schedule": True,
            "mass_energy_plausibility_upstream_ready": True,
            "max_gas_mass_relative_error": max(case["gas_mass_relative_error"] for case in cases),
            "max_peak_jet_speed_m_s": max(case["peak_jet_speed_m_s"] for case in cases),
            "cfd_solves_liquid_phase_change": False,
            "cfd_solves_flashing_discharge": False,
            "cfd_solves_pool_spread_evaporation": False,
            "production_phase_change_claim_allowed": False,
            "allowed_current_claim": (
                "screening LNG/LPG tank-or-pipe breach inputs can produce audited external gas-source schedules "
                "for gas dispersion, ignition, and fire simulations"
            ),
            "disallowed_current_claim": (
                "the CFD solver does not yet solve internal tank rupture, flashing multiphase discharge, "
                "liquid-pool spread/boiling, ground heat transfer, or EOS-coupled liquid phase change"
            ),
        },
        "cases": cases,
        "evidence_files": evidence_files,
        "limitations": [
            "This is an engineering source contract, not a high-fidelity liquefied-gas rupture solver.",
            "Use measured or process-safety source schedules when available; this contract keeps the screening inputs traceable when they are not.",
            "A production claim for complete LNG/LPG liquid phase-change CFD still requires dedicated model development and validation evidence.",
        ],
    }
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "breach source contract is not passing")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("liquefied_breach_source_contract_ready") is True, "contract is not ready")
    require(summary.get("case_count") == 2, "unexpected case count")
    require(summary.get("fluids") == ["LNG_CH4", "LPG_C3H8"], "unexpected fluids")
    require(summary.get("species") == ["C3H8", "CH4"], "unexpected species")
    require(summary.get("contract_accepts_screening_breach_inputs") is True, "screening breach inputs not accepted")
    require(summary.get("generates_external_gas_source_schedule") is True, "external gas source not generated")
    require(summary.get("mass_energy_plausibility_upstream_ready") is True, "upstream mass/energy plausibility missing")
    require(summary.get("max_gas_mass_relative_error") <= 0.20, "gas mass relative error too large")
    require(summary.get("cfd_solves_liquid_phase_change") is False, "liquid phase-change CFD overclaimed")
    require(summary.get("cfd_solves_flashing_discharge") is False, "flashing discharge CFD overclaimed")
    require(summary.get("cfd_solves_pool_spread_evaporation") is False, "pool evaporation CFD overclaimed")
    require(summary.get("production_phase_change_claim_allowed") is False, "production phase-change claim overclaimed")
    cases = data.get("cases")
    require(isinstance(cases, list) and len(cases) == 2, "missing case details")
    for case in cases:
        require(case.get("source_ready") is True, f"{case.get('case')} not ready")
        require(case.get("gas_mass_relative_error") <= 0.20, f"{case.get('case')} mass error too large")
        require(case.get("gas_mass_integral_kg") > 0.0, f"{case.get('case')} gas integral not positive")
        require(case.get("liquid_mass_released_kg") > 0.0, f"{case.get('case')} liquid release not positive")
        require(case.get("production_phase_change_claim_allowed") is False, f"{case.get('case')} overclaims production phase change")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Engineering Liquefied Breach Source Contract",
        "",
        f"- Status: `{report['status']}`",
        f"- Contract ready: `{summary['liquefied_breach_source_contract_ready']}`",
        f"- Fluids: `{', '.join(summary['fluids'])}`",
        f"- Species: `{', '.join(summary['species'])}`",
        f"- Generates external gas-source schedule: `{summary['generates_external_gas_source_schedule']}`",
        f"- Production phase-change claim allowed: `{summary['production_phase_change_claim_allowed']}`",
        "",
        "## Cases",
        "",
    ]
    for case in report["cases"]:
        lines.extend(
            [
                f"### {case['case']}",
                "",
                f"- Fluid/species: `{case['fluid']} / {case['fuel_species']}`",
                f"- Breach kind: `{case['breach_kind']}`",
                f"- Gas mass integral kg: `{case['gas_mass_integral_kg']:.6g}`",
                f"- Peak gas mdot kg/s: `{case['peak_gas_mdot_kg_s']:.6g}`",
                f"- Vaporized fraction: `{case['vaporized_fraction_to_gas_source']:.6g}`",
                f"- Contract: `{case['contract_path']}`",
                f"- Source CSV: `{case['source_csv']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            f"- Allowed: {summary['allowed_current_claim']}",
            f"- Disallowed: {summary['disallowed_current_claim']}",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report["limitations"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)

    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data)
            print(f"engineering_liquefied_breach_source_contract VERIFY-PASS json={args.verify_json} status={data['status']}")
            return 0
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        report = build_report(output_json.parent)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_liquefied_breach_source_contract PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except BreachContractError as exc:
        print(f"engineering_liquefied_breach_source_contract FAIL {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
