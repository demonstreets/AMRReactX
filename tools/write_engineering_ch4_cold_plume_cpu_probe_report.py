#!/usr/bin/env python3
"""Write/verify the engineering CH4 cold-plume CPU/MPI/CUDA probe evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-CH4-COLD-PLUME-CPU-MPI-CUDA-PROBE"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_ch4_cold_plume_cpu_probe_20260806")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_ch4_cold_plume_cpu_probe_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_ch4_cold_plume_cpu_probe_report.md"
RUNTIME = DEFAULT_ROOT / "runtime_evidence"
RUNTIME_MPI = DEFAULT_ROOT / "runtime_evidence_mpi"
RUNTIME_CUDA = DEFAULT_ROOT / "runtime_evidence_cuda"

RUN_LOG = RUNTIME / "run.log"
VALIDATION_LOG = RUNTIME / "validation.log"
BUILD_LOG = RUNTIME / "ch4_build.log"
INPUT_DECK = RUNTIME / "input.ch4_cold_plume_5step"
MPI_RUN_LOG = RUNTIME_MPI / "run.log"
MPI_VALIDATION_LOG = RUNTIME_MPI / "validation.log"
MPI_BUILD_LOG = RUNTIME_MPI / "ch4_mpi_build.log"
MPI_INPUT_DECK = RUNTIME_MPI / "input.ch4_cold_plume_5step_mpi"
CUDA_RUN_LOG = RUNTIME_CUDA / "run.log"
CUDA_VALIDATION_LOG = RUNTIME_CUDA / "validation.log"
CUDA_BUILD_LOG = RUNTIME_CUDA / "ch4_cuda_build.log"
CUDA_INPUT_DECK = RUNTIME_CUDA / "input.ch4_cold_plume_5step_cuda"
CUDA_NVCC_VERSION = RUNTIME_CUDA / "nvcc_version.txt"
PROB_H = Path("examples/engineering/h2_leak_3d/pelelmex_prob.H")
PROB_CPP = Path("examples/engineering/h2_leak_3d/pelelmex_prob.cpp")
VALIDATOR = Path("tools/validate_h2_leak_plume_history.py")


class Ch4ProbeError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Ch4ProbeError(message)


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
        raise Ch4ProbeError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise Ch4ProbeError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def parse_kv_pass_line(line: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, raw in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([^ ]+)", line):
        try:
            value = float(raw)
            out[key] = value
        except ValueError:
            out[key] = raw
    return out


def finite_float(data: dict[str, Any], key: str) -> float:
    try:
        value = float(data[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise Ch4ProbeError(f"missing/non-finite metric: {key}") from exc
    require(math.isfinite(value), f"non-finite metric: {key}")
    return value


def parse_validation_log(path: Path, run_log_path: Path, build_log_path: Path, input_path: Path) -> tuple[dict[str, Any], str, str, str]:
    run_log = run_log_path.read_text(encoding="utf-8", errors="replace")
    validation_log = path.read_text(encoding="utf-8", errors="replace")
    build_log = build_log_path.read_text(encoding="utf-8", errors="replace")
    input_text = input_path.read_text(encoding="utf-8", errors="replace")
    require("Mechanisms/CH4_lean" in build_log, f"build log does not prove CH4_lean mechanism: {build_log_path}")
    require("Engineering leak fuel species: name=CH4, index=10" in run_log, f"run log does not prove CH4 species selection: {run_log_path}")
    require("AMReX" in run_log and "finalized" in run_log, f"run log does not prove clean AMReX finalization: {run_log_path}")
    require("Unused ParmParse Variables" not in run_log, f"run log contains unused ParmParse variables: {run_log_path}")
    require(not re.search(r"\bnan\b|Abort::|amrex::Abort", run_log, re.IGNORECASE), f"run log contains NaN/abort marker: {run_log_path}")
    require("prob.fuel_species = CH4" in input_text, f"input deck does not set CH4 fuel species: {input_path}")
    pass_line = next(
        (line for line in validation_log.splitlines() if line.startswith("fuel_leak_plume_history_validation PASS")),
        "",
    )
    require(pass_line, f"CH4 plume validation PASS line missing: {path}")
    metrics = parse_kv_pass_line(pass_line)
    require(metrics.get("species") == "CH4", "validation species is not CH4")
    require(int(finite_float(metrics, "nplot")) >= 6, "CH4 validation has too few plotfiles")
    require(finite_float(metrics, "timeN") >= 5.0e-5, "CH4 validation did not reach 5 steps")
    require(abs(finite_float(metrics, "mass_ratioN") - 1.0) <= 1.0e-10, "CH4 mass/injected ratio is not conservative")
    require(finite_float(metrics, "mass_growth_ratio") >= 4.0, "CH4 mass growth ratio too small")
    require(finite_float(metrics, "max_YCH4") > 0.0, "CH4 plume did not develop")
    require(finite_float(metrics, "downstream_fraction") >= 0.30, "CH4 downstream fraction too small")
    require(finite_float(metrics, "upstream_fraction") >= 0.20, "CH4 upstream/source-side fraction too small")
    require(finite_float(metrics, "lateral_offset") <= 0.10, "CH4 lateral offset too large")
    return metrics, run_log, build_log, input_text


def metrics_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "plotfile_count": int(finite_float(metrics, "nplot")),
        "time_end_s": finite_float(metrics, "timeN"),
        "mass_ratio_final": finite_float(metrics, "mass_ratioN"),
        "mass_growth_ratio": finite_float(metrics, "mass_growth_ratio"),
        "max_ych4": finite_float(metrics, "max_YCH4"),
        "downstream_fraction": finite_float(metrics, "downstream_fraction"),
        "upstream_fraction": finite_float(metrics, "upstream_fraction"),
        "lateral_offset": finite_float(metrics, "lateral_offset"),
    }


def build_report(_: argparse.Namespace) -> dict[str, Any]:
    metrics, run_log, build_log, input_text = parse_validation_log(
        VALIDATION_LOG, RUN_LOG, BUILD_LOG, INPUT_DECK)
    mpi_metrics, mpi_run_log, mpi_build_log, mpi_input_text = parse_validation_log(
        MPI_VALIDATION_LOG, MPI_RUN_LOG, MPI_BUILD_LOG, MPI_INPUT_DECK)
    cuda_metrics, cuda_run_log, cuda_build_log, cuda_input_text = parse_validation_log(
        CUDA_VALIDATION_LOG, CUDA_RUN_LOG, CUDA_BUILD_LOG, CUDA_INPUT_DECK)
    prob_h = PROB_H.read_text(encoding="utf-8", errors="replace")
    prob_cpp = PROB_CPP.read_text(encoding="utf-8", errors="replace")
    nvcc_version = CUDA_NVCC_VERSION.read_text(encoding="utf-8", errors="replace")

    require("MPI initialized with 2 MPI processes" in mpi_run_log, "MPI run log does not prove 2-rank initialization")
    require("CUDA initialized with 1 device" in cuda_run_log, "CUDA run log does not prove single-device initialization")
    require("release 12.6" in nvcc_version, "nvcc version evidence does not show CUDA 12.6")
    require("source.species_index = pp->fuel_species_index" in prob_h, "source injection is not fuel-species configurable")
    require("CKSYMS_STR(species_names)" in prob_cpp, "species-name lookup is not implemented")

    plot_headers = [RUNTIME / f"plt{i:05d}" / "Header" for i in range(6)]
    mpi_plot_headers = [RUNTIME_MPI / f"plt{i:05d}" / "Header" for i in range(6)]
    cuda_plot_headers = [RUNTIME_CUDA / f"plt{i:05d}" / "Header" for i in range(6)]
    for header in plot_headers:
        require(header.is_file(), f"missing staged plot header: {header}")
    for header in mpi_plot_headers:
        require(header.is_file(), f"missing staged MPI plot header: {header}")
    for header in cuda_plot_headers:
        require(header.is_file(), f"missing staged CUDA plot header: {header}")
    cpu = metrics_summary(metrics)
    mpi = metrics_summary(mpi_metrics)
    cuda = metrics_summary(cuda_metrics)

    summary = {
        "species": "CH4",
        "chemistry_model": "CH4_lean",
        "cpu_probe_passed": True,
        "cpu_mpi_probe_passed": True,
        "mpi_probe_passed": True,
        "mpi_rank_count": 2,
        "single_cuda_probe_passed": True,
        "gpu_probe_passed": True,
        "production_ready": False,
        "plotfile_count": cpu["plotfile_count"],
        "time_end_s": cpu["time_end_s"],
        "mass_ratio_final": cpu["mass_ratio_final"],
        "mass_growth_ratio": cpu["mass_growth_ratio"],
        "max_ych4": cpu["max_ych4"],
        "downstream_fraction": cpu["downstream_fraction"],
        "upstream_fraction": cpu["upstream_fraction"],
        "lateral_offset": cpu["lateral_offset"],
        "mpi_plotfile_count": mpi["plotfile_count"],
        "mpi_time_end_s": mpi["time_end_s"],
        "mpi_mass_ratio_final": mpi["mass_ratio_final"],
        "mpi_mass_growth_ratio": mpi["mass_growth_ratio"],
        "mpi_max_ych4": mpi["max_ych4"],
        "mpi_downstream_fraction": mpi["downstream_fraction"],
        "mpi_upstream_fraction": mpi["upstream_fraction"],
        "mpi_lateral_offset": mpi["lateral_offset"],
        "cuda_plotfile_count": cuda["plotfile_count"],
        "cuda_time_end_s": cuda["time_end_s"],
        "cuda_mass_ratio_final": cuda["mass_ratio_final"],
        "cuda_mass_growth_ratio": cuda["mass_growth_ratio"],
        "cuda_max_ych4": cuda["max_ych4"],
        "cuda_downstream_fraction": cuda["downstream_fraction"],
        "cuda_upstream_fraction": cuda["upstream_fraction"],
        "cuda_lateral_offset": cuda["lateral_offset"],
        "cuda_version": "12.6",
        "amrex_cuda_arch": "60",
        "source_fuel_species_configurable": True,
        "ready_for_ch4_mpi_and_fire_probe": True,
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "title": "Engineering CH4 Cold-Plume CPU, MPI, And CUDA Probe",
        "summary": summary,
        "validation_metrics": {"cpu": metrics, "cpu_mpi": mpi_metrics, "single_cuda": cuda_metrics},
        "evidence_files": [
            evidence_entry("run_log", RUN_LOG),
            evidence_entry("validation_log", VALIDATION_LOG),
            evidence_entry("build_log", BUILD_LOG),
            evidence_entry("input_deck", INPUT_DECK),
            evidence_entry("mpi_run_log", MPI_RUN_LOG),
            evidence_entry("mpi_validation_log", MPI_VALIDATION_LOG),
            evidence_entry("mpi_build_log", MPI_BUILD_LOG),
            evidence_entry("mpi_input_deck", MPI_INPUT_DECK),
            evidence_entry("cuda_run_log", CUDA_RUN_LOG),
            evidence_entry("cuda_validation_log", CUDA_VALIDATION_LOG),
            evidence_entry("cuda_build_log", CUDA_BUILD_LOG),
            evidence_entry("cuda_input_deck", CUDA_INPUT_DECK),
            evidence_entry("cuda_nvcc_version", CUDA_NVCC_VERSION),
            evidence_entry("validator", VALIDATOR),
            evidence_entry("engineering_leak_prob_h", PROB_H),
            evidence_entry("engineering_leak_prob_cpp", PROB_CPP),
            *[evidence_entry(f"plot_header_{i:05d}", header) for i, header in enumerate(plot_headers)],
            *[evidence_entry(f"mpi_plot_header_{i:05d}", header) for i, header in enumerate(mpi_plot_headers)],
            *[evidence_entry(f"cuda_plot_header_{i:05d}", header) for i, header in enumerate(cuda_plot_headers)],
        ],
        "limitations": [
            "This is a short CPU, 2-rank CPU/MPI, and single-CUDA cold-plume probe for CH4 source injection and passive dispersion.",
            "It does not validate CH4 ignition, flame propagation, fire consequences, MPI+CUDA, or multi-GPU execution.",
            "It is not a natural-gas mixture or LNG vaporization validation.",
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS, "status mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("species") == "CH4", "species mismatch")
    require(summary.get("chemistry_model") == "CH4_lean", "chemistry model mismatch")
    require(summary.get("cpu_probe_passed") is True, "CPU probe did not pass")
    require(summary.get("cpu_mpi_probe_passed") is True, "CPU/MPI probe did not pass")
    require(summary.get("mpi_probe_passed") is True, "MPI probe flag did not pass")
    require(int(summary.get("mpi_rank_count", 0)) == 2, "MPI rank count mismatch")
    require(summary.get("single_cuda_probe_passed") is True, "single CUDA probe did not pass")
    require(summary.get("gpu_probe_passed") is True, "GPU probe flag did not pass")
    require(summary.get("production_ready") is False, "CH4 probe must not claim production readiness")
    require(summary.get("source_fuel_species_configurable") is True, "fuel species configurability missing")
    require(summary.get("ready_for_ch4_mpi_and_fire_probe") is True, "next-step readiness missing")
    require(float(summary.get("mass_ratio_final", 0.0)) == 1.0, "mass ratio final mismatch")
    require(float(summary.get("mass_growth_ratio", 0.0)) >= 4.0, "mass growth ratio too small")
    require(float(summary.get("max_ych4", 0.0)) > 0.0, "max CH4 mass fraction missing")
    require(float(summary.get("mpi_mass_ratio_final", 0.0)) == 1.0, "MPI mass ratio final mismatch")
    require(float(summary.get("mpi_mass_growth_ratio", 0.0)) >= 4.0, "MPI mass growth ratio too small")
    require(float(summary.get("mpi_max_ych4", 0.0)) > 0.0, "MPI max CH4 mass fraction missing")
    require(float(summary.get("cuda_mass_ratio_final", 0.0)) == 1.0, "CUDA mass ratio final mismatch")
    require(float(summary.get("cuda_mass_growth_ratio", 0.0)) >= 4.0, "CUDA mass growth ratio too small")
    require(float(summary.get("cuda_max_ych4", 0.0)) > 0.0, "CUDA max CH4 mass fraction missing")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Engineering CH4 Cold-Plume CPU, MPI, And CUDA Probe",
        "",
        f"- Status: `{report['status']}`",
        f"- Species: `{s['species']}`",
        f"- Chemistry model: `{s['chemistry_model']}`",
        f"- CPU probe passed: `{s['cpu_probe_passed']}`",
        f"- CPU/MPI probe passed: `{s['cpu_mpi_probe_passed']}`",
        f"- MPI rank count: `{s['mpi_rank_count']}`",
        f"- Single CUDA probe passed: `{s['single_cuda_probe_passed']}`",
        f"- Production ready: `{s['production_ready']}`",
        f"- Plotfiles: `{s['plotfile_count']}`",
        f"- Final time s: `{s['time_end_s']}`",
        f"- Final mass/injected ratio: `{s['mass_ratio_final']}`",
        f"- Max Y(CH4): `{s['max_ych4']}`",
        "",
        "## Limitations",
        "",
    ]
    for item in report["limitations"]:
        lines.append(f"- {item}")
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
            validate_report(data, verify_hashes=True)
            print(f"engineering_ch4_cold_plume_cpu_probe VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report(args)
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_ch4_cold_plume_cpu_probe PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except Ch4ProbeError as exc:
        print(f"engineering_ch4_cold_plume_cpu_probe FAIL {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
