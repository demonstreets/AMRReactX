#!/usr/bin/env python3
"""Write/verify multi-fuel external vaporization source-matrix evidence."""
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
STATUS = "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-MULTIFUEL-SOURCE-MATRIX"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_external_vaporization_multifuel_source_matrix_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_external_vaporization_multifuel_source_matrix_report.md"

CONVERTER = Path("tools/codex_make_external_vaporization_source_input.py")
BASE_INPUTS = {
    "H2": Path("examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_timeseries_smoke"),
    "CH4": Path("examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke"),
    "C3H8": Path("examples/engineering/h2_leak_3d/input.codex_gasified_lpg_c3h8_surrogate_smoke"),
}
H2_TIMESERIES_CUDA = Path(
    "docs/codex_audit/evidence/engineering_external_vaporization_timeseries_cuda_20260807/"
    "engineering_external_vaporization_timeseries_cuda_report.json"
)
CH4_500STEP = Path(
    "docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_20260806/"
    "engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.json"
)
C3H8_MATRIX = Path(
    "docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/"
    "engineering_c3h8_gas_phase_cpu_cuda_report.json"
)
LIQUEFIED_CONTRACT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/"
    "engineering_liquefied_external_vaporization_contract_report.json"
)

CSV_COLUMNS = [
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
ROWS = [
    (0.0, 0.0, 285.0, 0.20, 0.00, 0.00, 0.080, 0.42, 0.25, 0.20, 101325.0),
    (0.25, 0.00020, 300.0, 0.60, 0.05, 0.00, 0.095, 0.46, 0.27, 0.21, 101325.0),
    (0.75, 0.00045, 315.0, 0.35, -0.02, 0.04, 0.120, 0.51, 0.24, 0.23, 101325.0),
    (1.50, 0.00030, 295.0, 0.10, 0.02, 0.02, 0.100, 0.57, 0.26, 0.22, 101325.0),
]


class MultiFuelMatrixError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MultiFuelMatrixError(message)


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
        raise MultiFuelMatrixError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MultiFuelMatrixError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def write_source_csv(path: Path, species: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_COLUMNS)
        for row in ROWS:
            writer.writerow([row[0], row[1], row[2], species, *row[3:]])


def run_converter(species: str, source_csv: Path, output_input: Path, output_json: Path) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(CONVERTER),
        "--source-csv",
        str(source_csv),
        "--base-input",
        str(BASE_INPUTS[species]),
        "--time",
        "0.75",
        "--output-input",
        str(output_input),
        "--output-json",
        str(output_json),
    ]
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def build_species_entry(species: str) -> dict[str, Any]:
    source_csv = DEFAULT_ROOT / f"{species.lower()}_external_vaporization_timeseries.csv"
    output_input = DEFAULT_ROOT / f"input.codex_{species.lower()}_external_vaporization_timeseries"
    output_json = DEFAULT_ROOT / f"{species.lower()}_external_vaporization_timeseries_mapping.json"
    write_source_csv(source_csv, species)
    conversion = run_converter(species, source_csv, output_input, output_json)
    require(conversion["returncode"] == 0, f"{species} converter failed: {conversion['stderr']}")
    mapping = load_json(output_json)
    generated = output_input.read_text(encoding="utf-8")
    source_time_series = mapping.get("source_time_series", {})
    required_tokens = [
        f"prob.fuel_species = {species}",
        "prob.leak_model = fixed_mass_flow",
        "prob.leak_schedule_count = 4",
        "prob.leak_schedule_times =",
        "prob.leak_schedule_rates =",
        "prob.leak_schedule_temperatures =",
        "prob.leak_schedule_vel_x =",
        "prob.leak_schedule_vel_y =",
        "prob.leak_schedule_vel_z =",
        "prob.leak_schedule_radius =",
        "prob.leak_schedule_x =",
        "prob.leak_schedule_y =",
        "prob.leak_schedule_z =",
    ]
    missing_tokens = [token for token in required_tokens if token not in generated]
    replacements = mapping.get("applied_replacements", {})
    limitations = mapping.get("limitations", {})
    schedule_ready = (
        replacements.get("prob.fuel_species") == species
        and source_time_series.get("emitted_to_input") is True
        and source_time_series.get("fuel_species") == species
        and source_time_series.get("point_count") == 4
        and len(source_time_series.get("vapor_T_K", [])) == 4
        and len(source_time_series.get("leak_vel_x_m_s", [])) == 4
        and len(source_time_series.get("source_radius_m", [])) == 4
        and not missing_tokens
    )
    return {
        "species": species,
        "schedule_ready": schedule_ready,
        "missing_tokens": missing_tokens,
        "conversion": conversion,
        "mapping_summary": {
            "fuel_species": replacements.get("prob.fuel_species"),
            "time_series_fuel_species": source_time_series.get("fuel_species"),
            "point_count": source_time_series.get("point_count"),
            "emitted_to_input": source_time_series.get("emitted_to_input"),
            "sample": mapping.get("sample"),
            "cfd_solves_liquid_phase_change": limitations.get("cfd_solves_liquid_phase_change"),
            "cfd_solves_flashing_discharge": limitations.get("cfd_solves_flashing_discharge"),
            "cfd_solves_pool_spread_evaporation": limitations.get("cfd_solves_pool_spread_evaporation"),
        },
        "evidence_files": [
            evidence_entry(f"{species}_source_csv", source_csv),
            evidence_entry(f"{species}_generated_input", output_input),
            evidence_entry(f"{species}_mapping_json", output_json),
        ],
    }


def build_report() -> dict[str, Any]:
    require(CONVERTER.is_file(), f"missing converter: {CONVERTER}")
    for species, base_input in BASE_INPUTS.items():
        require(base_input.is_file(), f"missing {species} base input: {base_input}")
    h2_cuda = load_json(H2_TIMESERIES_CUDA)
    ch4 = load_json(CH4_500STEP)
    c3h8 = load_json(C3H8_MATRIX)
    liquefied = load_json(LIQUEFIED_CONTRACT)
    require(h2_cuda.get("status") == "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES-CUDA", "H2 CUDA time-series report is not passing")
    require(ch4.get("status") == "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA-500STEP", "CH4 runtime report is not passing")
    require(c3h8.get("status") == "PASS-ENGINEERING-C3H8-GAS-PHASE-CPU-CPU-MPI-SINGLE-CUDA-MPI-CUDA", "C3H8 runtime report is not passing")
    require(
        liquefied.get("summary", {}).get("cfd_solves_liquid_phase_change") is False,
        "liquefied contract must not claim CFD-internal phase change",
    )

    species_entries = {species: build_species_entry(species) for species in BASE_INPUTS}
    all_species_ready = all(entry["schedule_ready"] for entry in species_entries.values())
    phase_change_not_claimed = all(
        entry["mapping_summary"]["cfd_solves_liquid_phase_change"] is False
        and entry["mapping_summary"]["cfd_solves_flashing_discharge"] is False
        and entry["mapping_summary"]["cfd_solves_pool_spread_evaporation"] is False
        for entry in species_entries.values()
    )
    ready = all_species_ready and phase_change_not_claimed

    evidence_files = [
        evidence_entry("converter", CONVERTER),
        evidence_entry("h2_timeseries_cuda_report", H2_TIMESERIES_CUDA),
        evidence_entry("ch4_500step_report", CH4_500STEP),
        evidence_entry("c3h8_matrix_report", C3H8_MATRIX),
        evidence_entry("liquefied_external_vaporization_contract", LIQUEFIED_CONTRACT),
    ]
    for species, base_input in BASE_INPUTS.items():
        evidence_files.append(evidence_entry(f"{species}_base_input", base_input))
        evidence_files.extend(species_entries[species]["evidence_files"])

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-EXTERNAL-VAPORIZATION-MULTIFUEL-SOURCE-MATRIX",
        "summary": {
            "external_vaporization_multifuel_source_matrix_ready": ready,
            "supported_species": sorted(BASE_INPUTS),
            "species_count": len(BASE_INPUTS),
            "all_species_schedule_generation_ready": all_species_ready,
            "phase_change_not_claimed": phase_change_not_claimed,
            "h2_cuda_time_series_runtime_passed": h2_cuda.get("status") == "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES-CUDA",
            "ch4_runtime_evidence_passed": ch4.get("status") == "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA-500STEP",
            "c3h8_runtime_evidence_passed": c3h8.get("status") == "PASS-ENGINEERING-C3H8-GAS-PHASE-CPU-CPU-MPI-SINGLE-CUDA-MPI-CUDA",
            "cfd_internal_liquid_phase_change_claim_allowed": liquefied.get("summary", {}).get("cfd_solves_liquid_phase_change") is True,
        },
        "species": species_entries,
        "evidence_files": evidence_files,
    }


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS, "report is not PASS")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("external_vaporization_multifuel_source_matrix_ready") is True, "multi-fuel source matrix is not ready")
    require(summary.get("supported_species") == ["C3H8", "CH4", "H2"], "unexpected supported species")
    require(summary.get("species_count") == 3, "unexpected species count")
    require(summary.get("all_species_schedule_generation_ready") is True, "not all species generated schedule inputs")
    require(summary.get("phase_change_not_claimed") is True, "phase-change overclaim detected")
    require(summary.get("h2_cuda_time_series_runtime_passed") is True, "H2 CUDA time-series runtime missing")
    require(summary.get("ch4_runtime_evidence_passed") is True, "CH4 runtime evidence missing")
    require(summary.get("c3h8_runtime_evidence_passed") is True, "C3H8 runtime evidence missing")
    require(summary.get("cfd_internal_liquid_phase_change_claim_allowed") is False, "CFD-internal liquid phase-change claim must remain false")
    species = data.get("species")
    require(isinstance(species, dict), "species matrix missing")
    for name in ("H2", "CH4", "C3H8"):
        entry = species.get(name)
        require(isinstance(entry, dict), f"missing species entry: {name}")
        require(entry.get("schedule_ready") is True, f"{name} schedule generation is not ready")
        require(entry.get("mapping_summary", {}).get("fuel_species") == name, f"{name} mapping has wrong fuel species")
        require(entry.get("mapping_summary", {}).get("point_count") == 4, f"{name} mapping has wrong point count")
        require(entry.get("mapping_summary", {}).get("cfd_solves_liquid_phase_change") is False, f"{name} mapping overclaims phase change")
    if verify_hashes:
        for item in data.get("evidence_files", []):
            path = Path(str(item.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"evidence sha256 mismatch: {path}")


def write_outputs(report: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Engineering External Vaporization Multi-Fuel Source Matrix",
        "",
        f"- Status: `{report['status']}`",
        f"- Supported species: `{', '.join(report['summary']['supported_species'])}`",
        f"- All species schedule generation ready: `{report['summary']['all_species_schedule_generation_ready']}`",
        f"- Phase change not claimed: `{report['summary']['phase_change_not_claimed']}`",
        f"- H2 CUDA time-series runtime passed: `{report['summary']['h2_cuda_time_series_runtime_passed']}`",
        f"- CH4 runtime evidence passed: `{report['summary']['ch4_runtime_evidence_passed']}`",
        f"- C3H8 runtime evidence passed: `{report['summary']['c3h8_runtime_evidence_passed']}`",
        "",
        "## Species Matrix",
        "",
    ]
    for species, entry in report["species"].items():
        summary = entry["mapping_summary"]
        lines.append(f"- `{species}`: schedule_ready=`{entry['schedule_ready']}`, point_count=`{summary['point_count']}`")
    lines += ["", "## Evidence", ""]
    lines.extend(f"- `{item['label']}`: `{item['path']}`" for item in report["evidence_files"])
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data)
            print(f"engineering_external_vaporization_multifuel_source_matrix VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report()
        validate_report(report, verify_hashes=False)
        write_outputs(report, Path(args.output_json), Path(args.output_md))
        print(f"engineering_external_vaporization_multifuel_source_matrix {report['status']} json={args.output_json}")
        return 0
    except (MultiFuelMatrixError, OSError) as exc:
        print(f"engineering_external_vaporization_multifuel_source_matrix ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
