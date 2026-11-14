#!/usr/bin/env python3
"""Write/verify the engineering multi-fuel input-template catalog report."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-ENGINEERING-MULTI-FUEL-TEMPLATE-CATALOG"
STATUS_NOT_READY = "NOT_READY-ENGINEERING-MULTI-FUEL-TEMPLATE-CATALOG"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_multi_fuel_template_catalog_20260811")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_multi_fuel_template_catalog_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_multi_fuel_template_catalog_report.md"

TEMPLATES = {
    "h2_fixed_mass_flow_timeseries": {
        "path": Path("examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_timeseries_smoke"),
        "fuel_species": "H2",
        "required": {
            "prob.leak_model": "fixed_mass_flow",
            "prob.leak_schedule_count": "4",
        },
        "required_keys": [
            "prob.leak_schedule_times",
            "prob.leak_schedule_rates",
            "prob.leak_schedule_temperatures",
            "prob.leak_schedule_radius",
            "prob.leak_schedule_x",
            "prob.leak_schedule_y",
            "prob.leak_schedule_z",
        ],
        "claim_boundary": "gas_time_series",
    },
    "h2_fixed_mass_flow_valve_schedule": {
        "path": Path("examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_valve_schedule_smoke"),
        "fuel_species": "H2",
        "required": {
            "prob.leak_model": "fixed_mass_flow",
            "prob.leak_valve_initial_fraction": "0.0",
            "prob.leak_valve_final_fraction": "1.0",
        },
        "required_keys": [
            "prob.leak_valve_open_time",
            "prob.leak_valve_ramp_time",
        ],
        "claim_boundary": "gas_valve_schedule",
    },
    "gasified_lng_ch4_cold_source": {
        "path": Path("examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke"),
        "fuel_species": "CH4",
        "required": {
            "peleLM.do_react": "1",
            "prob.leak_model": "fixed_mass_flow",
            "prob.leak_T": "200.0",
            "prob.initial_flammable_cloud": "1",
            "prob.ignition_source": "1",
            "prob.obstacle_geometry": "stl",
        },
        "required_keys": [
            "prob.cloud_YFuel",
            "prob.cloud_YO2",
            "prob.cloud_YN2",
            "prob.obstacle_stl_file",
        ],
        "claim_boundary": "gasified_lng_surrogate_not_liquid_phase_change",
        "nonclaim_terms": ["gas-phase source", "not a liquid LNG rupture", "flashing", "pool-evaporation"],
    },
    "gasified_lng_ch4_warmed_fire": {
        "path": Path("examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_warmed_fire_surrogate_mpicuda_500step"),
        "fuel_species": "CH4",
        "required": {
            "peleLM.do_react": "1",
            "amr.max_step": "500",
            "prob.leak_model": "fixed_mass_flow",
            "prob.leak_T": "300.0",
            "prob.initial_flammable_cloud": "1",
            "prob.ignition_source": "1",
            "prob.obstacle_geometry": "stl",
        },
        "required_keys": [
            "prob.cloud_YFuel",
            "prob.cloud_YO2",
            "prob.cloud_YN2",
            "prob.obstacle_stl_file",
        ],
        "claim_boundary": "gasified_lng_warmed_fire_surrogate_not_liquid_phase_change",
        "nonclaim_terms": ["pre-vaporized", "not a liquid LNG model", "flashing", "pool evaporation"],
    },
    "gasified_lpg_c3h8_fire": {
        "path": Path("examples/engineering/h2_leak_3d/input.codex_gasified_lpg_c3h8_surrogate_smoke"),
        "fuel_species": "C3H8",
        "required": {
            "peleLM.do_react": "1",
            "prob.leak_model": "fixed_mass_flow",
            "prob.initial_flammable_cloud": "1",
            "prob.ignition_source": "1",
            "prob.obstacle_geometry": "stl",
        },
        "required_keys": [
            "prob.cloud_YFuel",
            "prob.cloud_YO2",
            "prob.cloud_YN2",
            "prob.obstacle_stl_file",
        ],
        "claim_boundary": "gasified_lpg_surrogate_not_liquid_phase_change",
        "nonclaim_terms": ["gas-phase source", "not an LPG tank rupture", "flashing", "pool-evaporation"],
    },
}

CSV_TEMPLATE = Path("examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv")
REQUIRED_CSV_COLUMNS = [
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
]


class CatalogError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CatalogError(message)


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
        raise CatalogError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CatalogError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def parse_input(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def inspect_template(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    path = spec["path"]
    require(isinstance(path, Path), f"template path is invalid: {name}")
    text = path.read_text(encoding="utf-8")
    values = parse_input(path)
    missing_keys = [key for key in spec.get("required_keys", []) if key not in values]
    mismatches = {
        key: {"expected": expected, "actual": values.get(key)}
        for key, expected in spec.get("required", {}).items()
        if values.get(key) != expected
    }
    expected_fuel = spec["fuel_species"]
    actual_fuel = values.get("prob.fuel_species")
    nonclaim_terms = spec.get("nonclaim_terms", [])
    missing_nonclaim_terms = [term for term in nonclaim_terms if term not in text]
    ready = (
        actual_fuel == expected_fuel
        and not missing_keys
        and not mismatches
        and not missing_nonclaim_terms
    )
    return {
        "name": name,
        "path": str(path),
        "fuel_species": actual_fuel,
        "expected_fuel_species": expected_fuel,
        "claim_boundary": spec["claim_boundary"],
        "ready": ready,
        "missing_keys": missing_keys,
        "mismatches": mismatches,
        "missing_nonclaim_terms": missing_nonclaim_terms,
        "sha256": sha256_file(path),
    }


def inspect_csv_template(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing CSV template: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    require(rows, f"CSV template has no rows: {path}")
    fieldnames = list(rows[0].keys())
    missing_columns = [column for column in REQUIRED_CSV_COLUMNS if column not in fieldnames]
    times = [float(row["time_s"]) for row in rows]
    mdots = [float(row["mdot_kg_s"]) for row in rows]
    radii = [float(row["source_radius_m"]) for row in rows]
    species = sorted({row["fuel_species"] for row in rows})
    ready = (
        not missing_columns
        and times == sorted(times)
        and min(mdots) >= 0.0
        and min(radii) > 0.0
        and species == ["CH4"]
    )
    return {
        "path": str(path),
        "ready": ready,
        "row_count": len(rows),
        "columns": fieldnames,
        "missing_columns": missing_columns,
        "times_monotonic": times == sorted(times),
        "mdot_nonnegative": min(mdots) >= 0.0,
        "radius_positive": min(radii) > 0.0,
        "species": species,
        "sha256": sha256_file(path),
    }


def build_report() -> dict[str, Any]:
    templates = [inspect_template(name, spec) for name, spec in TEMPLATES.items()]
    csv_template = inspect_csv_template(CSV_TEMPLATE)
    ready_templates = [item for item in templates if item["ready"]]
    failed_templates = [item for item in templates if not item["ready"]]
    fuel_species_seen = sorted({item["fuel_species"] for item in templates})
    nonclaim_template_count = sum(1 for item in templates if "not_liquid_phase_change" in item["claim_boundary"])
    nonclaim_templates_ready = all(
        not item["missing_nonclaim_terms"]
        for item in templates
        if "not_liquid_phase_change" in item["claim_boundary"]
    )
    ready = (
        len(ready_templates) == len(templates)
        and csv_template["ready"]
        and fuel_species_seen == ["C3H8", "CH4", "H2"]
        and nonclaim_template_count == 3
        and nonclaim_templates_ready
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "multi_fuel_template_catalog_ready": ready,
            "template_count": len(templates),
            "ready_template_count": len(ready_templates),
            "failed_template_count": len(failed_templates),
            "fuel_species_seen": fuel_species_seen,
            "gasified_lng_lpg_surrogate_template_count": nonclaim_template_count,
            "liquefied_nonclaim_comments_present": nonclaim_templates_ready,
            "csv_template_ready": csv_template["ready"],
            "csv_template_row_count": csv_template["row_count"],
            "csv_template_species": csv_template["species"],
            "cfd_internal_liquid_phase_change_claim_allowed": False,
        },
        "templates": templates,
        "csv_template": csv_template,
        "findings": {
            "failed_templates": failed_templates,
            "csv_missing_columns": csv_template["missing_columns"],
        },
        "evidence_files": [evidence_entry(name, spec["path"]) for name, spec in TEMPLATES.items()]
        + [evidence_entry("lng_external_vaporization_csv_template", CSV_TEMPLATE)],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("multi_fuel_template_catalog_ready") is True, "multi-fuel template catalog is not ready")
    require(summary.get("template_count") == len(TEMPLATES), "unexpected template count")
    require(summary.get("ready_template_count") == len(TEMPLATES), "not all templates are ready")
    require(summary.get("failed_template_count") == 0, "some templates failed catalog checks")
    require(summary.get("fuel_species_seen") == ["C3H8", "CH4", "H2"], "unexpected fuel species set")
    require(summary.get("gasified_lng_lpg_surrogate_template_count") == 3, "unexpected LNG/LPG surrogate template count")
    require(summary.get("liquefied_nonclaim_comments_present") is True, "liquefied nonclaim comments are incomplete")
    require(summary.get("csv_template_ready") is True, "CSV template is not ready")
    require(summary.get("csv_template_row_count", 0) >= 4, "CSV template row count is too small")
    require(summary.get("csv_template_species") == ["CH4"], "CSV template species changed")
    require(
        summary.get("cfd_internal_liquid_phase_change_claim_allowed") is False,
        "catalog overclaimed CFD-internal liquid phase change",
    )
    for template in data.get("templates", []):
        require(isinstance(template, dict), "invalid template entry")
        require(template.get("ready") is True, f"template is not ready: {template.get('name')}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Engineering Multi-Fuel Template Catalog",
        "",
        f"- Status: `{report['status']}`",
        f"- Templates: `{summary['ready_template_count']}/{summary['template_count']}`",
        f"- Fuel species seen: `{', '.join(summary['fuel_species_seen'])}`",
        f"- CSV template ready: `{summary['csv_template_ready']}`",
        f"- Liquefied nonclaim comments present: `{summary['liquefied_nonclaim_comments_present']}`",
        f"- CFD-internal liquid phase-change claim allowed: `{summary['cfd_internal_liquid_phase_change_claim_allowed']}`",
        "",
        "## Templates",
        "",
    ]
    for item in report["templates"]:
        lines.append(
            f"- `{item['name']}`: `{item['path']}`, fuel=`{item['fuel_species']}`, ready=`{item['ready']}`"
        )
    lines.extend(
        [
            "",
            "## CSV Template",
            "",
            f"- Path: `{report['csv_template']['path']}`",
            f"- Rows: `{report['csv_template']['row_count']}`",
            f"- Species: `{', '.join(report['csv_template']['species'])}`",
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
        print(f"engineering_multi_fuel_template_catalog VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"engineering_multi_fuel_template_catalog PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
