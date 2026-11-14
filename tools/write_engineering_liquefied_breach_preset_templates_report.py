#!/usr/bin/env python3
"""Write/verify operator-editable LNG/LPG breach preset evidence."""
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
STATUS_PASS = "PASS-ENGINEERING-LIQUEFIED-BREACH-PRESET-TEMPLATES"
STATUS_NOT_READY = "NOT_READY-ENGINEERING-LIQUEFIED-BREACH-PRESET-TEMPLATES"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_liquefied_breach_preset_templates_20260811")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_liquefied_breach_preset_templates_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_liquefied_breach_preset_templates_report.md"

PRESET_DIR = Path("examples/engineering/h2_leak_3d/liquefied_breach_presets")
GENERATOR = Path("tools/codex_make_liquefied_release_vaporization_csv.py")
BREACH_CONTRACT_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/"
    "engineering_liquefied_breach_source_contract_report.json"
)
THERMAL_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_thermal_plausibility_20260811/"
    "engineering_liquefied_release_thermal_plausibility_report.json"
)

REQUIRED_PRESETS = {
    "lng_ch4_tank_breach_screening": ("LNG_CH4", "CH4"),
    "lpg_c3h8_pipe_rupture_screening": ("LPG_C3H8", "C3H8"),
}

GENERATOR_FIELDS = [
    "fluid",
    "inventory_kg",
    "initial_pressure_Pa",
    "ambient_pressure_Pa",
    "hole_diameter_m",
    "duration_s",
    "points",
    "discharge_coeff",
    "pressure_decay_exponent",
    "liquid_T_K",
    "vapor_T_K",
    "vaporized_fraction",
    "pool_vapor_fraction",
    "source_radius_m",
    "source_x_m",
    "source_y_m",
    "source_z_m",
    "jet_dir_x",
    "jet_dir_y",
    "jet_dir_z",
    "max_jet_speed_m_s",
]


class PresetTemplateError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PresetTemplateError(message)


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
        raise PresetTemplateError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PresetTemplateError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def load_generator_module() -> Any:
    require(GENERATOR.is_file(), f"missing generator: {GENERATOR}")
    spec = importlib.util.spec_from_file_location("codex_make_liquefied_release_vaporization_csv", GENERATOR)
    require(spec is not None and spec.loader is not None, "unable to import liquefied-release generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(callable(getattr(module, "build_rows", None)), "generator does not expose build_rows")
    require(callable(getattr(module, "write_csv", None)), "generator does not expose write_csv")
    require(isinstance(getattr(module, "FLUIDS", None), dict), "generator does not expose FLUIDS")
    return module


def namespace_from_preset(preset: dict[str, Any]) -> SimpleNamespace:
    missing = [field for field in GENERATOR_FIELDS if field not in preset]
    require(not missing, f"preset missing generator fields: {missing}")
    return SimpleNamespace(**{field: preset[field] for field in GENERATOR_FIELDS})


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"missing generated CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    require(rows, f"generated CSV is empty: {path}")
    return rows


def trapezoid_integral(times: list[float], values: list[float]) -> float:
    return sum(0.5 * (lv + rv) * (rt - lt) for lt, rt, lv, rv in zip(times, times[1:], values, values[1:]))


def audit_preset(name: str, path: Path, output_root: Path, module: Any) -> dict[str, Any]:
    preset = load_json(path)
    expected_fluid, expected_species = REQUIRED_PRESETS[name]
    require(preset.get("fluid") == expected_fluid, f"{name} fluid mismatch")
    require(isinstance(preset.get("accepted_cfd_use"), str) and preset["accepted_cfd_use"], f"{name} accepted_cfd_use missing")
    require(isinstance(preset.get("breach_kind"), str) and preset["breach_kind"], f"{name} breach_kind missing")

    rows, summary = module.build_rows(namespace_from_preset(preset))
    csv_path = output_root / name / f"{name}_source.csv"
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
    gas_mass = trapezoid_integral(times, mdots)
    require(summary.get("fuel_species") == expected_species, f"{name} species mismatch")
    require(summary.get("gas_mdot_positive") is True, f"{name} has no positive gas mdot")
    require(summary.get("pressure_decays") is True, f"{name} pressure does not decay")
    require(summary.get("model_is_screening_source_generator") is True, f"{name} is not marked as screening")
    require(summary.get("cfd_solves_liquid_phase_change") is False, f"{name} overclaims liquid phase change")
    require(summary.get("cfd_solves_flashing_discharge") is False, f"{name} overclaims flashing discharge")
    require(summary.get("cfd_solves_pool_spread_evaporation") is False, f"{name} overclaims pool evaporation")
    require(all(right > left for left, right in zip(times, times[1:])), f"{name} time is not increasing")
    require(all(mdot >= 0.0 for mdot in mdots), f"{name} contains negative mdot")
    require(gas_mass > 0.0, f"{name} gas mass is not positive")
    require(max(velocities) <= float(preset["max_jet_speed_m_s"]) * 1.000001, f"{name} jet speed cap violated")

    return {
        "name": name,
        "preset_path": str(path),
        "source_csv": str(csv_path),
        "fluid": expected_fluid,
        "fuel_species": expected_species,
        "breach_kind": preset["breach_kind"],
        "accepted_cfd_use": preset["accepted_cfd_use"],
        "ready": True,
        "time_window_s": [times[0], times[-1]],
        "point_count": len(csv_rows),
        "gas_mass_integral_kg": gas_mass,
        "peak_gas_mdot_kg_s": max(mdots),
        "peak_jet_speed_m_s": max(velocities),
        "vaporized_fraction_to_gas_source": summary["vaporized_fraction_to_gas_source"],
        "cfd_solves_liquid_phase_change": False,
        "cfd_solves_flashing_discharge": False,
        "cfd_solves_pool_spread_evaporation": False,
    }


def validate_upstream_reports() -> list[dict[str, Any]]:
    expected = [
        (BREACH_CONTRACT_REPORT, "PASS-ENGINEERING-LIQUEFIED-BREACH-SOURCE-CONTRACT"),
        (THERMAL_REPORT, "PASS-ENGINEERING-LIQUEFIED-RELEASE-THERMAL-PLAUSIBILITY"),
    ]
    entries = []
    for path, status in expected:
        data = load_json(path)
        require(data.get("status") == status, f"upstream status is not passing: {path}")
        summary = data.get("summary", {})
        require(summary.get("cfd_solves_liquid_phase_change") is False, f"{path} overclaims liquid phase change")
        entries.append(evidence_entry(path.stem, path))
    return entries


def build_report(output_root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    module = load_generator_module()
    require(set(REQUIRED_PRESETS).issubset({path.stem for path in PRESET_DIR.glob("*.json")}), "missing required presets")
    upstream = validate_upstream_reports()
    cases = []
    for name in sorted(REQUIRED_PRESETS):
        cases.append(audit_preset(name, PRESET_DIR / f"{name}.json", output_root, module))

    ready = (
        len(cases) == 2
        and all(case["ready"] for case in cases)
        and sorted({case["fluid"] for case in cases}) == ["LNG_CH4", "LPG_C3H8"]
        and sorted({case["fuel_species"] for case in cases}) == ["C3H8", "CH4"]
    )
    evidence_files = upstream + [evidence_entry(f"{case['name']}_preset", Path(case["preset_path"])) for case in cases]
    evidence_files.extend(evidence_entry(f"{case['name']}_source_csv", Path(case["source_csv"])) for case in cases)
    evidence_files.append(evidence_entry("liquefied_release_generator", GENERATOR))

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "scope": "operator-editable LNG/LPG breach presets that generate CFD gas-source CSV schedules",
        "summary": {
            "liquefied_breach_preset_templates_ready": ready,
            "editable_json_presets": True,
            "preset_count": len(cases),
            "fluids": sorted({case["fluid"] for case in cases}),
            "species": sorted({case["fuel_species"] for case in cases}),
            "generates_cfd_source_csv": all(Path(case["source_csv"]).is_file() for case in cases),
            "max_peak_gas_mdot_kg_s": max(case["peak_gas_mdot_kg_s"] for case in cases),
            "max_peak_jet_speed_m_s": max(case["peak_jet_speed_m_s"] for case in cases),
            "cfd_solves_liquid_phase_change": False,
            "cfd_solves_flashing_discharge": False,
            "cfd_solves_pool_spread_evaporation": False,
            "production_phase_change_claim_allowed": False,
        },
        "cases": cases,
        "evidence_files": evidence_files,
        "limitations": [
            "Presets are screening source inputs for the gas-phase CFD bridge.",
            "They are intended to be edited or replaced by measured/process-safety source schedules when available.",
            "They do not turn PeleLMeX into a complete LNG/LPG liquid phase-change rupture solver.",
        ],
    }


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "preset templates are not passing")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("liquefied_breach_preset_templates_ready") is True, "preset templates are not ready")
    require(summary.get("editable_json_presets") is True, "presets are not marked editable")
    require(summary.get("preset_count") == 2, "unexpected preset count")
    require(summary.get("fluids") == ["LNG_CH4", "LPG_C3H8"], "unexpected fluids")
    require(summary.get("species") == ["C3H8", "CH4"], "unexpected species")
    require(summary.get("generates_cfd_source_csv") is True, "CFD CSV generation is not ready")
    for key in (
        "cfd_solves_liquid_phase_change",
        "cfd_solves_flashing_discharge",
        "cfd_solves_pool_spread_evaporation",
        "production_phase_change_claim_allowed",
    ):
        require(summary.get(key) is False, f"overclaim guard failed for {key}")
    cases = data.get("cases")
    require(isinstance(cases, list) and len(cases) == 2, "missing case details")
    for case in cases:
        require(case.get("ready") is True, f"{case.get('name')} not ready")
        require(case.get("gas_mass_integral_kg") > 0.0, f"{case.get('name')} gas mass is not positive")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Engineering Liquefied Breach Preset Templates",
        "",
        f"- Status: `{report['status']}`",
        f"- Presets ready: `{summary['liquefied_breach_preset_templates_ready']}`",
        f"- Editable JSON presets: `{summary['editable_json_presets']}`",
        f"- Fluids: `{', '.join(summary['fluids'])}`",
        f"- Species: `{', '.join(summary['species'])}`",
        f"- Generates CFD source CSV: `{summary['generates_cfd_source_csv']}`",
        f"- Production phase-change claim allowed: `{summary['production_phase_change_claim_allowed']}`",
        "",
        "## Cases",
        "",
    ]
    for case in report["cases"]:
        lines.extend(
            [
                f"### {case['name']}",
                "",
                f"- Preset: `{case['preset_path']}`",
                f"- Source CSV: `{case['source_csv']}`",
                f"- Fluid/species: `{case['fluid']} / {case['fuel_species']}`",
                f"- Peak gas mdot kg/s: `{case['peak_gas_mdot_kg_s']:.6g}`",
                f"- Gas mass integral kg: `{case['gas_mass_integral_kg']:.6g}`",
                "",
            ]
        )
    lines.extend(["## Limitations", ""])
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
            print(f"engineering_liquefied_breach_preset_templates VERIFY-PASS json={args.verify_json} status={data['status']}")
            return 0
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        report = build_report(output_json.parent)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_liquefied_breach_preset_templates PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except PresetTemplateError as exc:
        print(f"engineering_liquefied_breach_preset_templates FAIL {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
