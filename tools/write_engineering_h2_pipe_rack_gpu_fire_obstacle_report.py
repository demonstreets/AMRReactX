#!/usr/bin/env python3
"""Write/verify H2 pipe-rack obstacle GPU and fire-screening evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-PIPE-RACK-GPU-FIRE-OBSTACLE-SMOKE"
DEFAULT_OUTPUT_ROOT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_gpu_fire_obstacle_20260727"
)
DEFAULT_CPU_SUMMARY = Path(
    "/tmp/codex_h2_leak_pipe_rack_obstacle_20260727_cpu_v2/pipe_rack_obstacle_summary.csv"
)
DEFAULT_CPU_RUN_LOG = Path("/tmp/codex_h2_leak_pipe_rack_obstacle_20260727_cpu_v2/run.log")
DEFAULT_GPU_SUMMARY = Path(
    "/tmp/codex_h2_leak_pipe_rack_obstacle_20260727_cuda_v6_sm60/pipe_rack_obstacle_summary.csv"
)
DEFAULT_GPU_RUN_LOG = Path("/tmp/codex_h2_leak_pipe_rack_obstacle_20260727_cuda_v6_sm60/run.log")
DEFAULT_MPI_CUDA_SUMMARY = Path(
    "/tmp/codex_h2_leak_pipe_rack_obstacle_20260727_mpi_cuda_2rank_bg/"
    "pipe_rack_obstacle_summary.csv"
)
DEFAULT_MPI_CUDA_RUN_LOG = Path(
    "/tmp/codex_h2_leak_pipe_rack_obstacle_20260727_mpi_cuda_2rank_bg/run.log"
)
DEFAULT_FIRE_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_fire_consequence_metrics_20260727/"
    "fire_consequence_metrics_report.json"
)

FAILURE_RE = re.compile(
    r"(^|[^A-Za-z])(nan|inf)([^A-Za-z]|$)|Backtrace|Segmentation|SIGSEGV|FAIL|RuntimeWarning|Abort|"
    r"CUDA error|GPU last error|error while loading|cannot find|No such file",
    re.IGNORECASE,
)


class ReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportError(message)


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


def finite_float(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReportError(f"missing JSON report: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f"invalid JSON report {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON report is not an object: {path}")
    return data


def read_one_csv(path: Path) -> dict[str, str]:
    require(path.is_file(), f"missing summary CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    require(len(rows) == 1, f"expected one summary row in {path}, got {len(rows)}")
    return rows[0]


def check_summary(row: dict[str, str], label: str) -> dict[str, Any]:
    expected_sources = "codex_cube_block.stl;codex_vertical_cylinder.stl;codex_pipe_rack.stl"
    require(row.get("case") == "pipe_rack_cube_cylinder_pipes", f"{label}: unexpected case")
    require(row.get("stl_source_files") == expected_sources, f"{label}: wrong STL source list")
    require(row.get("stl_file") == "codex_merged_pipe_rack_obstacles.stl", f"{label}: wrong merged STL")
    require(int(row.get("stl_vertices", "0")) >= 1000, f"{label}: STL vertex count too small")
    for field in ("mass_ratio", "cloud_volume", "max_X"):
        require(finite_float(row.get(field)), f"{label}: invalid {field}")
    require(0.95 <= float(row["mass_ratio"]) <= 1.05, f"{label}: mass ratio out of bounds")
    require(float(row["cloud_volume"]) > 0.0, f"{label}: no flammable cloud")
    require(int(row.get("active_planes", "0")) >= 3, f"{label}: too few active hazard planes")
    require(int(row.get("flammable_planes", "0")) >= 1, f"{label}: no flammable hazard plane")
    return {
        "case": row["case"],
        "stl_source_files": row["stl_source_files"].split(";"),
        "merged_stl_file": row["stl_file"],
        "stl_vertices": int(row["stl_vertices"]),
        "stl_triangles": int(row.get("stl_triangles", "0")),
        "mass_ratio": float(row["mass_ratio"]),
        "cloud_volume": float(row["cloud_volume"]),
        "cloud_cells": int(row.get("cloud_cells", "0")),
        "active_planes": int(row["active_planes"]),
        "flammable_planes": int(row["flammable_planes"]),
        "max_X": float(row["max_X"]),
    }


def check_run_log(
    path: Path,
    label: str,
    require_cuda: bool,
    require_mpi_ranks: int | None = None,
) -> dict[str, Any]:
    require(path.is_file(), f"missing run log: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    require("AMReX" in text and "finalized" in text.lower(), f"{label}: AMReX did not finalize")
    require("buildFromSTL QA: file=codex_merged_pipe_rack_obstacles.stl" in text, f"{label}: missing STL QA marker")
    if require_cuda:
        require("CUDA initialized with" in text, f"{label}: CUDA initialization marker missing")
    if require_mpi_ranks is not None:
        require(
            f"MPI initialized with {require_mpi_ranks} MPI processes" in text,
            f"{label}: MPI rank marker missing",
        )
    hits = [line.strip() for line in text.splitlines() if FAILURE_RE.search(line)]
    require(not hits, f"{label}: failure markers found: {hits[:3]}")
    cuda_devices = None
    m = re.search(r"CUDA initialized with\s+([0-9]+)\s+devices?", text)
    if m:
        cuda_devices = int(m.group(1))
    return {
        "amrex_finalized": True,
        "cuda_initialized": "CUDA initialized with" in text,
        "cuda_devices": cuda_devices,
        "mpi_ranks": require_mpi_ranks,
        "stl_qa_marker": True,
        "failure_marker_count": 0,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    cpu_summary_path = Path(args.cpu_summary)
    cpu_run_log_path = Path(args.cpu_run_log)
    gpu_summary_path = Path(args.gpu_summary)
    gpu_run_log_path = Path(args.gpu_run_log)
    mpi_cuda_summary_path = Path(args.mpi_cuda_summary)
    mpi_cuda_run_log_path = Path(args.mpi_cuda_run_log)
    fire_path = Path(args.fire_consequence_report)

    cpu_metrics = check_summary(read_one_csv(cpu_summary_path), "cpu")
    gpu_metrics = check_summary(read_one_csv(gpu_summary_path), "gpu")
    mpi_cuda_metrics = check_summary(read_one_csv(mpi_cuda_summary_path), "mpi-cuda")
    cpu_log = check_run_log(cpu_run_log_path, "cpu", require_cuda=False)
    gpu_log = check_run_log(gpu_run_log_path, "gpu", require_cuda=True)
    mpi_cuda_log = check_run_log(
        mpi_cuda_run_log_path,
        "mpi-cuda",
        require_cuda=True,
        require_mpi_ranks=2,
    )
    fire = load_json(fire_path)
    fire_summary = fire.get("summary") if isinstance(fire.get("summary"), dict) else {}
    fire_ok = (
        fire.get("status") == "PASS-SCREENING"
        and fire.get("model_scope") == "engineering_screening_not_calibrated"
        and fire.get("clears_calibrated_fire_consequence_blocker") is False
        and finite_float(fire_summary.get("flammable_cloud_h2_mass_kg"))
        and float(fire_summary.get("flammable_cloud_h2_mass_kg")) > 0.0
        and finite_float(fire_summary.get("max_screening_flux_w_m2"))
        and float(fire_summary.get("max_screening_flux_w_m2")) > 0.0
    )
    require(fire_ok, "pipe-rack fire consequence screening report is not PASS-SCREENING")

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS,
        "title": "H2 Pipe-Rack Obstacle GPU and Fire-Screening Evidence",
        "validated_capabilities": {
            "cube_obstacle_stl": True,
            "vertical_cylinder_obstacle_stl": True,
            "pipe_rack_multi_pipe_obstacle_stl": True,
            "merged_multi_file_stl_obstacle": True,
            "cpu_obstacle_leak_dispersion": True,
            "gpu_obstacle_leak_dispersion": True,
            "mpi_cuda_obstacle_leak_dispersion": True,
            "mpi_cuda_ranks": 2,
            "mpi_cuda_devices": mpi_cuda_log["cuda_devices"],
            "gpu_cuda_arch": "sm_60",
            "fire_consequence_screening": True,
            "direct_coupled_3d_fire_propagation": False,
            "calibrated_fire_or_blast_model": False,
        },
        "cpu_metrics": cpu_metrics,
        "gpu_metrics": gpu_metrics,
        "mpi_cuda_metrics": mpi_cuda_metrics,
        "cpu_log_checks": cpu_log,
        "gpu_log_checks": gpu_log,
        "mpi_cuda_log_checks": mpi_cuda_log,
        "fire_screening_summary": {
            "status": fire.get("status"),
            "model_scope": fire.get("model_scope"),
            "flammable_cloud_h2_mass_kg": fire_summary.get("flammable_cloud_h2_mass_kg"),
            "source_limited_heat_release_w": fire_summary.get("source_limited_heat_release_w"),
            "flammable_cloud_energy_j": fire_summary.get("flammable_cloud_energy_j"),
            "max_screening_flux_w_m2": fire_summary.get("max_screening_flux_w_m2"),
            "max_screening_overpressure_kpa": fire_summary.get("max_screening_overpressure_kpa"),
        },
        "decision": "pipe_rack_obstacle_cpu_single_gpu_mpi_cuda_and_fire_screening_smoke_pass",
        "limitations": [
            "This is a smoke/engineering-screening obstacle case, not a production-size AMR pipe-rack campaign.",
            "Fire consequence evidence is source/cloud based screening, not calibrated direct 3D fire propagation.",
            "GPU evidence includes single-GPU CUDA and 2-rank MPI+CUDA execution on server P100 class devices; it is not a production GPU scaling curve.",
        ],
        "evidence_files": [
            evidence_entry("cpu_pipe_rack_summary", cpu_summary_path),
            evidence_entry("cpu_pipe_rack_run_log", cpu_run_log_path),
            evidence_entry("gpu_pipe_rack_summary", gpu_summary_path),
            evidence_entry("gpu_pipe_rack_run_log", gpu_run_log_path),
            evidence_entry("mpi_cuda_pipe_rack_summary", mpi_cuda_summary_path),
            evidence_entry("mpi_cuda_pipe_rack_run_log", mpi_cuda_run_log_path),
            evidence_entry("pipe_rack_fire_consequence_report", fire_path),
        ],
    }


def validate_report(report: dict[str, Any], check_hashes: bool = True) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "status is not PASS")
    caps = report.get("validated_capabilities")
    require(isinstance(caps, dict), "missing validated_capabilities")
    for name in (
        "cube_obstacle_stl",
        "vertical_cylinder_obstacle_stl",
        "pipe_rack_multi_pipe_obstacle_stl",
        "merged_multi_file_stl_obstacle",
        "cpu_obstacle_leak_dispersion",
        "gpu_obstacle_leak_dispersion",
        "mpi_cuda_obstacle_leak_dispersion",
        "fire_consequence_screening",
    ):
        require(caps.get(name) is True, f"{name} not validated")
    require(caps.get("direct_coupled_3d_fire_propagation") is False, "direct fire must remain false")
    require(caps.get("calibrated_fire_or_blast_model") is False, "calibrated fire/blast must remain false")
    for section in ("cpu_metrics", "gpu_metrics", "mpi_cuda_metrics"):
        metrics = report.get(section)
        require(isinstance(metrics, dict), f"missing {section}")
        require(float(metrics.get("mass_ratio", 0.0)) > 0.95, f"{section} mass ratio too small")
        require(float(metrics.get("cloud_volume", 0.0)) > 0.0, f"{section} cloud volume missing")
    gpu_log = report.get("gpu_log_checks")
    require(isinstance(gpu_log, dict) and gpu_log.get("cuda_initialized") is True, "GPU CUDA marker missing")
    mpi_cuda_log = report.get("mpi_cuda_log_checks")
    require(
        isinstance(mpi_cuda_log, dict)
        and mpi_cuda_log.get("cuda_initialized") is True
        and mpi_cuda_log.get("mpi_ranks") == 2,
        "MPI+CUDA marker missing",
    )
    if check_hashes:
        for entry in report.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry["sha256"], f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    cpu = report["cpu_metrics"]
    gpu = report["gpu_metrics"]
    mpi_cuda = report["mpi_cuda_metrics"]
    fire = report["fire_screening_summary"]
    lines = [
        "# H2 Pipe-Rack Obstacle GPU and Fire-Screening Evidence",
        "",
        f"- Status: {report['status']}",
        f"- Decision: {report['decision']}",
        "- Obstacles: cube STL, vertical cylinder STL, and multi-pipe pipe-rack STL",
        f"- CPU mass ratio / cloud volume: {cpu['mass_ratio']:.8e} / {cpu['cloud_volume']:.8e}",
        f"- GPU mass ratio / cloud volume: {gpu['mass_ratio']:.8e} / {gpu['cloud_volume']:.8e}",
        f"- MPI+CUDA mass ratio / cloud volume: {mpi_cuda['mass_ratio']:.8e} / {mpi_cuda['cloud_volume']:.8e}",
        f"- MPI+CUDA ranks / CUDA devices: {report['validated_capabilities']['mpi_cuda_ranks']} / {report['validated_capabilities']['mpi_cuda_devices']}",
        f"- GPU CUDA arch: {report['validated_capabilities']['gpu_cuda_arch']}",
        f"- Fire screening H2 mass / heat release: {fire['flammable_cloud_h2_mass_kg']} kg / {fire['source_limited_heat_release_w']} W",
        f"- Fire screening max flux / overpressure: {fire['max_screening_flux_w_m2']} W/m2 / {fire['max_screening_overpressure_kpa']} kPa",
        "",
        "The obstacle leak-dispersion path passed on CPU, single-GPU CUDA, and 2-rank MPI+CUDA. Fire evidence is engineering consequence screening from the detected cloud, not calibrated direct 3D fire propagation.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    ap.add_argument("--cpu-summary", default=str(DEFAULT_CPU_SUMMARY))
    ap.add_argument("--cpu-run-log", default=str(DEFAULT_CPU_RUN_LOG))
    ap.add_argument("--gpu-summary", default=str(DEFAULT_GPU_SUMMARY))
    ap.add_argument("--gpu-run-log", default=str(DEFAULT_GPU_RUN_LOG))
    ap.add_argument("--mpi-cuda-summary", default=str(DEFAULT_MPI_CUDA_SUMMARY))
    ap.add_argument("--mpi-cuda-run-log", default=str(DEFAULT_MPI_CUDA_RUN_LOG))
    ap.add_argument("--fire-consequence-report", default=str(DEFAULT_FIRE_REPORT))
    ap.add_argument("--verify-json")
    args = ap.parse_args()
    try:
        if args.verify_json:
            report = load_json(Path(args.verify_json))
            validate_report(report)
            print(f"VERIFY-PASS {args.verify_json} status={report['status']}")
            return 0
        output_root = Path(args.output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        report = build_report(args)
        validate_report(report)
        json_path = output_root / "pipe_rack_gpu_fire_obstacle_report.json"
        md_path = output_root / "pipe_rack_gpu_fire_obstacle_report.md"
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, md_path)
        validate_report(load_json(json_path))
        print(f"WROTE {json_path} status={report['status']}")
        return 0
    except ReportError as exc:
        print(f"pipe_rack_gpu_fire_obstacle_report FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
