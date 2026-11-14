#!/usr/bin/env python3
"""Write/verify screening liquefied-release source-model evidence for the gas-source bridge."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_liquefied_release_vaporization_source_model_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_liquefied_release_vaporization_source_model_report.md"

GENERATOR = Path("tools/codex_make_liquefied_release_vaporization_csv.py")
CONVERTER = Path("tools/codex_make_external_vaporization_source_input.py")
CONTRACT_REPORT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/"
    "engineering_liquefied_external_vaporization_contract_report.json"
)
MULTI_FUEL_BOUNDARY_REPORT = Path(
    "docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/"
    "engineering_multi_fuel_capability_boundary_report.json"
)
LNG_BASE_INPUT = Path("examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke")
LPG_BASE_INPUT = Path("examples/engineering/h2_leak_3d/input.codex_gasified_lpg_c3h8_surrogate_smoke")


class SourceModelReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceModelReportError(message)


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
        raise SourceModelReportError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SourceModelReportError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def run_cmd(cmd: list[str]) -> dict[str, Any]:
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    require(result.returncode == 0, f"command failed rc={result.returncode}: {' '.join(cmd)}\n{result.stderr}")
    return {
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"missing generated CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    require(rows, f"generated CSV contains no rows: {path}")
    return rows


def validate_csv(path: Path, species: str) -> dict[str, Any]:
    rows = read_csv(path)
    times = [float(row["time_s"]) for row in rows]
    mdots = [float(row["mdot_kg_s"]) for row in rows]
    temps = [float(row["vapor_T_K"]) for row in rows]
    radii = [float(row["source_radius_m"]) for row in rows]
    vx = [float(row["leak_vel_x_m_s"]) for row in rows]
    require(all(row["fuel_species"] == species for row in rows), f"{path} species drifted from {species}")
    require(all(b > a for a, b in zip(times, times[1:])), f"{path} time is not strictly increasing")
    require(max(mdots) > 0.0, f"{path} has no positive gas-source mdot")
    require(mdots[-1] <= max(mdots), f"{path} final mdot is inconsistent")
    require(all(temp > 0.0 for temp in temps), f"{path} contains nonpositive vapor temperatures")
    require(all(radius > 0.0 for radius in radii), f"{path} contains nonpositive source radii")
    require(max(abs(value) for value in vx) > 0.0, f"{path} has no jet velocity")
    return {
        "point_count": len(rows),
        "species": species,
        "time_start_s": times[0],
        "time_end_s": times[-1],
        "mdot_max_kg_s": max(mdots),
        "mdot_final_kg_s": mdots[-1],
        "vapor_T_min_K": min(temps),
        "vapor_T_max_K": max(temps),
        "source_radius_m": radii[0],
        "jet_vx_max_m_s": max(vx),
    }


def validate_mapping(path: Path, species: str) -> dict[str, Any]:
    mapping = load_json(path)
    require(mapping.get("status") == "PASS-EXTERNAL-VAPORIZATION-SOURCE-INPUT", f"mapping did not pass: {path}")
    sample = mapping.get("sample", {})
    series = mapping.get("source_time_series", {})
    limitations = mapping.get("limitations", {})
    require(sample.get("fuel_species") == species, f"mapping sample species drifted from {species}")
    require(series.get("fuel_species") == species, f"mapping series species drifted from {species}")
    require(series.get("emitted_to_input") is True, "mapping did not emit schedule into input")
    require(len(series.get("mdot_kg_s", [])) == series.get("point_count"), "mapping mdot schedule length mismatch")
    require(len(series.get("vapor_T_K", [])) == series.get("point_count"), "mapping temperature schedule length mismatch")
    require(limitations.get("cfd_solves_liquid_phase_change") is False, "mapping overclaims liquid phase change")
    require(limitations.get("cfd_solves_flashing_discharge") is False, "mapping overclaims flashing discharge")
    require(limitations.get("cfd_solves_pool_spread_evaporation") is False, "mapping overclaims pool evaporation")
    return {
        "mapping_status": mapping.get("status"),
        "sample_time_s": mapping.get("sample_time_s"),
        "sample_mdot_kg_s": sample.get("mdot_kg_s"),
        "point_count": series.get("point_count"),
        "fuel_species": species,
        "emitted_to_input": True,
    }


def validate_generated_input(path: Path, species: str) -> None:
    text = path.read_text(encoding="utf-8")
    required = [
        f"prob.fuel_species = {species}",
        "prob.leak_model = fixed_mass_flow",
        "prob.leak_schedule_count =",
        "prob.leak_schedule_times =",
        "prob.leak_schedule_rates =",
        "prob.leak_schedule_temperatures =",
        "prob.leak_schedule_vel_x =",
        "prob.leak_schedule_radius =",
        "prob.leak_schedule_x =",
    ]
    missing = [item for item in required if item not in text]
    require(not missing, f"generated input missing {missing}: {path}")


def generate_case(
    label: str,
    fluid: str,
    species: str,
    base_input: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    root = Path(args.evidence_root) / label
    csv_path = root / f"{label}_source.csv"
    generator_json = root / f"{label}_source_model.json"
    output_input = root / f"input.{label}.generated"
    mapping_json = root / f"{label}_source_mapping.json"
    root.mkdir(parents=True, exist_ok=True)

    if fluid == "LNG_CH4":
        generator_cmd = [
            sys.executable,
            str(GENERATOR),
            "--fluid",
            fluid,
            "--inventory-kg",
            "25.0",
            "--initial-pressure-Pa",
            "650000.0",
            "--hole-diameter-m",
            "0.020",
            "--duration-s",
            "8.0",
            "--points",
            "9",
            "--liquid-T-K",
            "125.0",
            "--vapor-T-K",
            "285.0",
            "--source-radius-m",
            "0.08",
            "--output-csv",
            str(csv_path),
            "--output-json",
            str(generator_json),
        ]
    else:
        generator_cmd = [
            sys.executable,
            str(GENERATOR),
            "--fluid",
            fluid,
            "--inventory-kg",
            "18.0",
            "--initial-pressure-Pa",
            "850000.0",
            "--hole-diameter-m",
            "0.015",
            "--duration-s",
            "8.0",
            "--points",
            "9",
            "--liquid-T-K",
            "250.0",
            "--vapor-T-K",
            "300.0",
            "--source-radius-m",
            "0.08",
            "--output-csv",
            str(csv_path),
            "--output-json",
            str(generator_json),
        ]
    generator_run = run_cmd(generator_cmd)
    converter_run = run_cmd(
        [
            sys.executable,
            str(CONVERTER),
            "--source-csv",
            str(csv_path),
            "--base-input",
            str(base_input),
            "--time",
            "2.0",
            "--output-input",
            str(output_input),
            "--output-json",
            str(mapping_json),
        ]
    )
    generator_report = load_json(generator_json)
    require(generator_report.get("status") == "PASS-LIQUEFIED-RELEASE-VAPORIZATION-CSV", "generator report did not pass")
    summary = generator_report.get("summary", {})
    require(summary.get("fuel_species") == species, f"generator species drifted from {species}")
    require(summary.get("gas_mdot_positive") is True, "generator did not create positive gas mdot")
    require(summary.get("pressure_decays") is True, "generator did not record pressure decay")
    require(summary.get("cfd_solves_liquid_phase_change") is False, "generator overclaims liquid phase change")
    require(summary.get("cfd_solves_flashing_discharge") is False, "generator overclaims flashing discharge")
    require(summary.get("cfd_solves_pool_spread_evaporation") is False, "generator overclaims pool evaporation")
    csv_summary = validate_csv(csv_path, species)
    mapping_summary = validate_mapping(mapping_json, species)
    validate_generated_input(output_input, species)
    return {
        "label": label,
        "fluid": fluid,
        "species": species,
        "status": "PASS-LIQUEFIED-RELEASE-TO-GAS-SOURCE-CASE",
        "generator_summary": summary,
        "csv_summary": csv_summary,
        "mapping_summary": mapping_summary,
        "generator_run": generator_run,
        "converter_run": converter_run,
        "artifacts": {
            "source_csv": str(csv_path),
            "generator_json": str(generator_json),
            "generated_input": str(output_input),
            "mapping_json": str(mapping_json),
        },
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    contract = load_json(CONTRACT_REPORT)
    boundary = load_json(MULTI_FUEL_BOUNDARY_REPORT)
    require(contract.get("status") == "PASS-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-CONTRACT", "liquefied source contract is not passing")
    require(boundary.get("status") == "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY", "multi-fuel boundary is not passing")
    boundary_summary = boundary.get("summary", {})
    require(boundary_summary.get("external_vaporization_multifuel_timeseries_cuda_passed") is True, "multi-fuel external-vaporization CUDA evidence missing")
    require(boundary_summary.get("liquefied_gas_phase_change_ready") is False, "boundary must not claim liquefied phase-change readiness")

    lng = generate_case("lng_ch4_screening_release", "LNG_CH4", "CH4", LNG_BASE_INPUT, args)
    lpg = generate_case("lpg_c3h8_screening_release", "LPG_C3H8", "C3H8", LPG_BASE_INPUT, args)
    cases = [lng, lpg]
    ready = all(case["status"] == "PASS-LIQUEFIED-RELEASE-TO-GAS-SOURCE-CASE" for case in cases)
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL",
        "title": "Engineering Liquefied Release Vaporization Source Model",
        "summary": {
            "liquefied_release_vaporization_source_model_ready": ready,
            "lng_ch4_screening_release_source_ready": lng["status"] == "PASS-LIQUEFIED-RELEASE-TO-GAS-SOURCE-CASE",
            "lpg_c3h8_screening_release_source_ready": lpg["status"] == "PASS-LIQUEFIED-RELEASE-TO-GAS-SOURCE-CASE",
            "outputs_external_vaporization_csv": True,
            "outputs_pelelmex_fixed_mass_flow_schedule_input": True,
            "uses_existing_external_vaporization_converter": True,
            "multi_fuel_cuda_runtime_evidence_still_required_and_present": True,
            "cfd_solves_liquid_phase_change": False,
            "cfd_solves_flashing_discharge": False,
            "cfd_solves_pool_spread_evaporation": False,
            "claim_level": "screening_external_gas_source_generator_not_internal_liquid_solver",
            "production_phase_change_claim_allowed": False,
        },
        "cases": cases,
        "evidence_files": [
            evidence_entry("liquefied_release_vaporization_csv_generator", GENERATOR),
            evidence_entry("external_vaporization_source_input_converter", CONVERTER),
            evidence_entry("liquefied_external_vaporization_contract_report", CONTRACT_REPORT),
            evidence_entry("multi_fuel_capability_boundary_report", MULTI_FUEL_BOUNDARY_REPORT),
            evidence_entry("lng_source_csv", Path(lng["artifacts"]["source_csv"])),
            evidence_entry("lng_generator_json", Path(lng["artifacts"]["generator_json"])),
            evidence_entry("lng_generated_input", Path(lng["artifacts"]["generated_input"])),
            evidence_entry("lng_mapping_json", Path(lng["artifacts"]["mapping_json"])),
            evidence_entry("lpg_source_csv", Path(lpg["artifacts"]["source_csv"])),
            evidence_entry("lpg_generator_json", Path(lpg["artifacts"]["generator_json"])),
            evidence_entry("lpg_generated_input", Path(lpg["artifacts"]["generated_input"])),
            evidence_entry("lpg_mapping_json", Path(lpg["artifacts"]["mapping_json"])),
        ],
        "limitations": [
            "This evidence adds a reproducible engineering source generator upstream of the existing gas-source bridge.",
            "It does not implement internal tank rupture mechanics, flashing two-phase discharge, liquid-pool spread, boiling, or ground heat-transfer closure inside PeleLMeX.",
            "For production consequence work, replace the screening schedule with measured data or a validated process-safety release model when available.",
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS, "status mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("liquefied_release_vaporization_source_model_ready") is True, "source model readiness missing")
    require(summary.get("lng_ch4_screening_release_source_ready") is True, "LNG CH4 screening source missing")
    require(summary.get("lpg_c3h8_screening_release_source_ready") is True, "LPG C3H8 screening source missing")
    require(summary.get("outputs_external_vaporization_csv") is True, "CSV output flag missing")
    require(summary.get("outputs_pelelmex_fixed_mass_flow_schedule_input") is True, "PeleLMeX input output flag missing")
    require(summary.get("uses_existing_external_vaporization_converter") is True, "converter usage flag missing")
    require(summary.get("multi_fuel_cuda_runtime_evidence_still_required_and_present") is True, "runtime dependency flag missing")
    require(summary.get("cfd_solves_liquid_phase_change") is False, "must not claim liquid phase-change solving")
    require(summary.get("cfd_solves_flashing_discharge") is False, "must not claim flashing-discharge solving")
    require(summary.get("cfd_solves_pool_spread_evaporation") is False, "must not claim pool-evaporation solving")
    require(summary.get("production_phase_change_claim_allowed") is False, "must not claim production phase-change readiness")
    cases = data.get("cases")
    require(isinstance(cases, list) and len(cases) == 2, "case list incomplete")
    species = {case.get("species") for case in cases}
    require(species == {"CH4", "C3H8"}, f"unexpected case species: {species}")
    for case in cases:
        require(case.get("status") == "PASS-LIQUEFIED-RELEASE-TO-GAS-SOURCE-CASE", f"case failed: {case.get('label')}")
        gen = case.get("generator_summary", {})
        csv_summary = case.get("csv_summary", {})
        mapping = case.get("mapping_summary", {})
        require(gen.get("gas_mdot_positive") is True, f"case gas mdot not positive: {case.get('label')}")
        require(gen.get("pressure_decays") is True, f"case pressure did not decay: {case.get('label')}")
        require(csv_summary.get("point_count", 0) >= 2, f"case CSV too short: {case.get('label')}")
        require(mapping.get("emitted_to_input") is True, f"case mapping not emitted: {case.get('label')}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Engineering Liquefied Release Vaporization Source Model",
        "",
        f"- Status: `{report['status']}`",
        f"- LNG CH4 screening release source ready: `{s['lng_ch4_screening_release_source_ready']}`",
        f"- LPG C3H8 screening release source ready: `{s['lpg_c3h8_screening_release_source_ready']}`",
        f"- Outputs external vaporization CSV: `{s['outputs_external_vaporization_csv']}`",
        f"- Outputs PeleLMeX fixed-mass-flow schedule input: `{s['outputs_pelelmex_fixed_mass_flow_schedule_input']}`",
        f"- CFD solves liquid phase change: `{s['cfd_solves_liquid_phase_change']}`",
        f"- CFD solves flashing discharge: `{s['cfd_solves_flashing_discharge']}`",
        f"- CFD solves pool spread evaporation: `{s['cfd_solves_pool_spread_evaporation']}`",
        f"- Claim level: `{s['claim_level']}`",
        "",
        "## Cases",
        "",
    ]
    for case in report["cases"]:
        csv_summary = case["csv_summary"]
        gen = case["generator_summary"]
        lines.append(
            f"- `{case['label']}`: species `{case['species']}`, max gas mdot `{csv_summary['mdot_max_kg_s']:.6g}` kg/s, "
            f"vaporized fraction `{gen['vaporized_fraction_to_gas_source']:.6g}`"
        )
    lines += ["", "## Limitations", ""]
    for item in report["limitations"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", default=str(DEFAULT_ROOT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(f"engineering_liquefied_release_vaporization_source_model VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report(args)
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_liquefied_release_vaporization_source_model PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except SourceModelReportError as exc:
        print(f"engineering_liquefied_release_vaporization_source_model FAIL {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
