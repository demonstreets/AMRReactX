#!/usr/bin/env python3
"""Write/verify the liquefied-gas external vaporization source contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-CONTRACT"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_liquefied_external_vaporization_contract_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_liquefied_external_vaporization_contract_report.md"
CONTRACT_DOC = Path("docs/codex_audit/engineering_liquefied_external_vaporization_source_contract.md")
SOURCE_CSV = Path("examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv")
BASE_INPUT = Path("examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke")
GENERATED_INPUT = DEFAULT_ROOT / "input.codex_lng_external_vaporization_source_t2s"
GENERATED_MAPPING_JSON = DEFAULT_ROOT / "external_vaporization_source_mapping_t2s.json"

MASTER_PLAN = Path.home() / "pele_cfd_master_plan.md"
PELELMEX_PROB_CPP = Path("examples/engineering/h2_leak_3d/pelelmex_prob.cpp")
PELELMEX_PROB_H = Path("examples/engineering/h2_leak_3d/pelelmex_prob.H")
CONVERTER = Path("tools/codex_make_external_vaporization_source_input.py")

MULTI_FUEL_BOUNDARY = Path(
    "docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/"
    "engineering_multi_fuel_capability_boundary_report.json"
)
GASIFIED_SURROGATE = Path(
    "docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/"
    "engineering_gasified_lng_lpg_surrogate_report.json"
)
FUEL_SPECIES_GUARD = Path(
    "docs/codex_audit/evidence/engineering_fuel_species_guard_20260806/"
    "engineering_fuel_species_guard_report.json"
)

REQUIRED_CONTRACT_SNIPPETS = [
    "Engineering Liquefied External Vaporization Source Contract",
    "external vaporization model",
    "prob.leak_model = fixed_mass_flow",
    "prob.fuel_species",
    "prob.leak_rate",
    "prob.leak_schedule_times",
    "prob.leak_schedule_rates",
    "prob.leak_schedule_temperatures",
    "prob.leak_schedule_vel_x",
    "prob.leak_schedule_vel_y",
    "prob.leak_schedule_vel_z",
    "prob.leak_schedule_radius",
    "prob.leak_schedule_x",
    "prob.leak_schedule_y",
    "prob.leak_schedule_z",
    "prob.leak_T",
    "codex_lng_external_vaporization_source_template.csv",
    "tools/codex_make_external_vaporization_source_input.py",
    "cfd_solves_liquid_phase_change = false",
    "cfd_solves_flashing_discharge = false",
    "cfd_solves_pool_spread_evaporation = false",
    "not a production claim for liquid tank rupture",
]


class ContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def write_contract_doc(path: Path) -> None:
    lines = [
        "# Engineering Liquefied External Vaporization Source Contract",
        "",
        "This contract is the supported bridge from an external vaporization model into the current PeleLMeX gas-phase engineering leak solver.",
        "",
        "## Scope",
        "",
        "- The external vaporization model supplies gas-phase source data as a CSV time series.",
        "- The CFD input generated from the CSV uses `prob.leak_model = fixed_mass_flow`.",
        "- The generated input sets `prob.fuel_species`, `prob.leak_rate`, `prob.leak_schedule_times`, `prob.leak_schedule_rates`, `prob.leak_schedule_temperatures`, `prob.leak_schedule_vel_x`, `prob.leak_schedule_vel_y`, `prob.leak_schedule_vel_z`, `prob.leak_schedule_radius`, `prob.leak_schedule_x`, `prob.leak_schedule_y`, `prob.leak_schedule_z`, `prob.leak_T`, source velocity, radius, and location when those columns are present.",
        "- `cfd_solves_liquid_phase_change = false`",
        "- `cfd_solves_flashing_discharge = false`",
        "- `cfd_solves_pool_spread_evaporation = false`",
        "- This is not a production claim for liquid tank rupture, flashing two-phase discharge, cryogenic pool spread, or ground heat-transfer closure.",
        "",
        "## Required CSV",
        "",
        "Template: `examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv`",
        "",
        "Required columns: `time_s`, `mdot_kg_s`, `vapor_T_K`, `fuel_species`. Up to 64 strictly increasing time rows are supported for `mdot(t)`, `vapor_T(t)`, optional `velocity(t)`, and optional single-source `radius/location(t)` coupling.",
        "",
        "Optional columns: `leak_vel_x_m_s`, `leak_vel_y_m_s`, `leak_vel_z_m_s`, `source_radius_m`, `source_x_m`, `source_y_m`, `source_z_m`, `source_pressure_Pa`.",
        "",
        "## Command",
        "",
        "```bash",
        "python3 tools/codex_make_external_vaporization_source_input.py --source-csv examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv --base-input examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke --time 2.0 --output-input docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/input.codex_lng_external_vaporization_source_t2s --output-json docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/external_vaporization_source_mapping_t2s.json",
        "python3 tools/write_engineering_liquefied_external_vaporization_contract_report.py",
        "bash tools/verify_engineering_liquefied_external_vaporization_contract.sh",
        "```",
        "",
        "## Operational Meaning",
        "",
        "Use this path when a separate thermodynamic, consequence, or process-safety model has already converted a liquefied release into a gas-phase vaporization mass flow rate. The current CFD calculation then starts from that gas-phase source and covers dispersion, ignition, flame development, and obstacle interaction within the already verified gas-phase scope.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_converter() -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(CONVERTER),
        "--source-csv",
        str(SOURCE_CSV),
        "--base-input",
        str(BASE_INPUT),
        "--time",
        "2.0",
        "--output-input",
        str(GENERATED_INPUT),
        "--output-json",
        str(GENERATED_MAPPING_JSON),
    ]
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    require(result.returncode == 0, f"converter failed rc={result.returncode}: {result.stderr.strip()}")
    return {
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def validate_generated_input(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    checks = {
        "sets_fixed_mass_flow": "prob.leak_model = fixed_mass_flow" in text,
        "sets_ch4_species": "prob.fuel_species = CH4" in text,
        "sets_interpolated_rate": "prob.leak_rate = 0.0008" in text,
        "sets_schedule_count": "prob.leak_schedule_count =" in text,
        "sets_schedule_times": "prob.leak_schedule_times =" in text,
        "sets_schedule_rates": "prob.leak_schedule_rates =" in text,
        "sets_schedule_temperatures": "prob.leak_schedule_temperatures =" in text,
        "sets_schedule_velocity_x": "prob.leak_schedule_vel_x =" in text,
        "sets_schedule_velocity_y": "prob.leak_schedule_vel_y =" in text,
        "sets_schedule_velocity_z": "prob.leak_schedule_vel_z =" in text,
        "sets_schedule_radius": "prob.leak_schedule_radius =" in text,
        "sets_schedule_location_x": "prob.leak_schedule_x =" in text,
        "sets_schedule_location_y": "prob.leak_schedule_y =" in text,
        "sets_schedule_location_z": "prob.leak_schedule_z =" in text,
        "sets_vapor_temperature": "prob.leak_T = 300" in text or "prob.leak_T = 300.0" in text,
    }
    for key, ok in checks.items():
        require(ok, f"generated input check failed: {key}")
    return checks


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    multi = load_json(Path(args.multi_fuel_boundary))
    gasified = load_json(Path(args.gasified_surrogate))
    guard = load_json(Path(args.fuel_species_guard))
    require(multi.get("status") == "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY", "multi-fuel boundary is not passing")
    require(gasified.get("status") == "PASS-ENGINEERING-GASIFIED-LNG-LPG-SURROGATE-BOUNDARY", "gasified surrogate boundary is not passing")
    require(guard.get("status") == "PASS-ENGINEERING-FUEL-SPECIES-GUARD", "fuel species guard is not passing")
    require(guard.get("summary", {}).get("prevents_unknown_fuel_silent_fallback") is True, "fuel guard does not prevent silent fallback")

    master_text = MASTER_PLAN.read_text(encoding="utf-8")
    prob_cpp_text = PELELMEX_PROB_CPP.read_text(encoding="utf-8")
    prob_h_text = PELELMEX_PROB_H.read_text(encoding="utf-8")
    require("液相蒸发气体泄漏" in master_text, "master plan liquid evaporation gas-release scope not found")
    require("ENG-08" in master_text and "液体池蒸发源项" in master_text, "master plan ENG-08 not found")
    require("fixed_mass_flow" in prob_cpp_text, "fixed_mass_flow leak model missing")
    require("pressure_orifice" in prob_cpp_text, "pressure_orifice leak model missing")
    require("tank_blowdown" in prob_cpp_text, "tank_blowdown leak model missing")
    require("linepack_blowdown" in prob_cpp_text, "linepack_blowdown leak model missing")
    phase_change_terms = ["flashing_discharge", "pool_evaporation", "liquid_pool_spread"]
    internal_phase_change_hits = [term for term in phase_change_terms if term in prob_cpp_text or term in prob_h_text]

    write_contract_doc(CONTRACT_DOC)
    conversion = run_converter()
    mapping = load_json(GENERATED_MAPPING_JSON)
    require(mapping.get("status") == "PASS-EXTERNAL-VAPORIZATION-SOURCE-INPUT", "generated mapping JSON is not passing")
    time_series = mapping.get("source_time_series", {})
    require(time_series.get("emitted_to_input") is True, "generated mapping did not emit a mdot(t) schedule")
    require(time_series.get("point_count", 0) >= 2, "generated mdot(t) schedule has too few points")
    require(len(time_series.get("vapor_T_K", [])) == time_series.get("point_count"), "generated vapor_T(t) schedule is incomplete")
    has_velocity_schedule = all(
        len(time_series.get(key, [])) == time_series.get("point_count")
        for key in ("leak_vel_x_m_s", "leak_vel_y_m_s", "leak_vel_z_m_s")
    )
    has_geometry_schedule = all(
        len(time_series.get(key, [])) == time_series.get("point_count")
        for key in ("source_radius_m", "source_x_m", "source_y_m", "source_z_m")
    )
    limitations = mapping.get("limitations", {})
    require(limitations.get("cfd_solves_liquid_phase_change") is False, "mapping must not claim liquid phase-change solving")
    require(limitations.get("cfd_solves_flashing_discharge") is False, "mapping must not claim flashing-discharge solving")
    require(limitations.get("cfd_solves_pool_spread_evaporation") is False, "mapping must not claim pool-evaporation solving")
    input_checks = validate_generated_input(GENERATED_INPUT)

    contract_text = CONTRACT_DOC.read_text(encoding="utf-8")
    missing_snippets = [snippet for snippet in REQUIRED_CONTRACT_SNIPPETS if snippet not in contract_text]
    ready = not missing_snippets and not internal_phase_change_hits

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-CONTRACT",
        "summary": {
            "external_vaporization_contract_ready": ready,
            "external_vaporization_source_mapping_ready": mapping.get("status") == "PASS-EXTERNAL-VAPORIZATION-SOURCE-INPUT",
            "quasi_steady_segment_input_ready": all(input_checks.values()),
            "mdot_time_series_input_ready": time_series.get("emitted_to_input") is True,
            "mdot_time_series_point_count": time_series.get("point_count"),
            "vapor_temperature_time_series_input_ready": len(time_series.get("vapor_T_K", [])) == time_series.get("point_count"),
            "velocity_time_series_input_ready": has_velocity_schedule,
            "geometry_time_series_input_ready": has_geometry_schedule,
            "cfd_solves_liquid_phase_change": False,
            "cfd_solves_flashing_discharge": False,
            "cfd_solves_pool_spread_evaporation": False,
            "internal_phase_change_model_detected": bool(internal_phase_change_hits),
            "overclaim_prevented": True,
            "supported_surrogate_species": ["H2", "CH4", "C3H8"],
        },
        "conversion": conversion,
        "generated_input_checks": input_checks,
        "internal_phase_change_hits": internal_phase_change_hits,
        "missing_contract_snippets": missing_snippets,
        "evidence_files": [
            evidence_entry("contract_doc", CONTRACT_DOC),
            evidence_entry("source_csv_template", SOURCE_CSV),
            evidence_entry("base_gasified_lng_input", BASE_INPUT),
            evidence_entry("generated_input", GENERATED_INPUT),
            evidence_entry("generated_mapping_json", GENERATED_MAPPING_JSON),
            evidence_entry("converter", CONVERTER),
            evidence_entry("multi_fuel_boundary", Path(args.multi_fuel_boundary)),
            evidence_entry("gasified_surrogate", Path(args.gasified_surrogate)),
            evidence_entry("fuel_species_guard", Path(args.fuel_species_guard)),
            evidence_entry("pelelmex_prob_cpp", PELELMEX_PROB_CPP),
            evidence_entry("pelelmex_prob_h", PELELMEX_PROB_H),
        ],
    }


def verify_report(report: dict[str, Any]) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(report.get("status") == STATUS, "report is not PASS")
    summary = report.get("summary", {})
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("external_vaporization_contract_ready") is True, "contract is not ready")
    require(summary.get("external_vaporization_source_mapping_ready") is True, "mapping is not ready")
    require(summary.get("quasi_steady_segment_input_ready") is True, "generated segment input is not ready")
    require(summary.get("mdot_time_series_input_ready") is True, "generated mdot(t) schedule is not ready")
    require(summary.get("mdot_time_series_point_count", 0) >= 2, "generated mdot(t) schedule has too few points")
    require(summary.get("vapor_temperature_time_series_input_ready") is True, "generated vapor_T(t) schedule is not ready")
    require(summary.get("velocity_time_series_input_ready") is True, "generated velocity(t) schedule is not ready")
    require(summary.get("geometry_time_series_input_ready") is True, "generated radius/location(t) schedule is not ready")
    require(summary.get("cfd_solves_liquid_phase_change") is False, "report overclaims liquid phase change")
    require(summary.get("cfd_solves_flashing_discharge") is False, "report overclaims flashing discharge")
    require(summary.get("cfd_solves_pool_spread_evaporation") is False, "report overclaims pool evaporation")
    require(summary.get("internal_phase_change_model_detected") is False, "unexpected internal phase-change model detected")
    require(summary.get("overclaim_prevented") is True, "overclaim guard not set")
    require(report.get("missing_contract_snippets") == [], "contract doc missing required snippets")
    for item in report.get("evidence_files", []):
        path = Path(item["path"])
        require(path.is_file(), f"missing evidence file: {path}")
        require(sha256_file(path) == item.get("sha256"), f"evidence sha256 mismatch: {path}")


def write_outputs(report: dict[str, Any], json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = report["summary"]
    lines = [
        "# Engineering Liquefied External Vaporization Contract Report",
        "",
        f"- Status: `{report['status']}`",
        f"- External vaporization contract ready: `{summary['external_vaporization_contract_ready']}`",
        f"- Generated gas-source input ready: `{summary['quasi_steady_segment_input_ready']}`",
        f"- CFD solves liquid phase change: `{summary['cfd_solves_liquid_phase_change']}`",
        f"- CFD solves flashing discharge: `{summary['cfd_solves_flashing_discharge']}`",
        f"- CFD solves pool spread/evaporation: `{summary['cfd_solves_pool_spread_evaporation']}`",
        f"- Supported surrogate species: `{', '.join(summary['supported_surrogate_species'])}`",
        "",
        "## Evidence",
        "",
    ]
    for item in report["evidence_files"]:
        lines.append(f"- `{item['label']}`: `{item['path']}`")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--multi-fuel-boundary", default=str(MULTI_FUEL_BOUNDARY))
    ap.add_argument("--gasified-surrogate", default=str(GASIFIED_SURROGATE))
    ap.add_argument("--fuel-species-guard", default=str(FUEL_SPECIES_GUARD))
    ap.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    ap.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    ap.add_argument("--verify-json")
    args = ap.parse_args()
    try:
      if args.verify_json:
          report = load_json(Path(args.verify_json))
          verify_report(report)
          print(f"engineering_liquefied_external_vaporization_contract VERIFY-PASS json={args.verify_json} status={report['status']}")
          return 0
      report = build_report(args)
      verify_report(report)
      write_outputs(report, Path(args.output_json), Path(args.output_md))
      print(f"engineering_liquefied_external_vaporization_contract PASS json={args.output_json} status={report['status']}")
      return 0
    except ContractError as exc:
      print(f"engineering_liquefied_external_vaporization_contract FAIL {exc}", file=sys.stderr)
      return 2


if __name__ == "__main__":
    raise SystemExit(main())
