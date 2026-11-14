#!/usr/bin/env python3
"""Write/verify C3H8 gas-phase leak/fire CPU, CPU/MPI, single-CUDA, and MPI+CUDA evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-C3H8-GAS-PHASE-CPU-CPU-MPI-SINGLE-CUDA-MPI-CUDA"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_c3h8_gas_phase_cpu_cuda_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_c3h8_gas_phase_cpu_cuda_report.md"
DEFAULT_STAGED_ROOT = DEFAULT_ROOT / "runtime_evidence"

DEFAULT_COLD_ROOT = Path("/tmp/codex_c3h8_cold_plume_cpu_20260806")
DEFAULT_CPU_FIRE_ROOT = Path("/tmp/codex_c3h8_pipe_rack_delayed_ignition_cpu_120step_20260806")
DEFAULT_MPI_FIRE_ROOT = Path("/tmp/codex_c3h8_pipe_rack_delayed_ignition_mpi_120step_20260806")
DEFAULT_CUDA_FIRE_ROOT = Path("/tmp/codex_c3h8_pipe_rack_delayed_ignition_cuda_120step_20260806")
DEFAULT_MPICUDA_FIRE_ROOT = Path("/tmp/codex_c3h8_pipe_rack_delayed_ignition_mpicuda_rankmapped_120step_20260806")

COLD_INPUT = "input.c3h8_cold_plume_10step"
CPU_FIRE_INPUT = "input.codex_c3h8_pipe_rack_delayed_ignition_cpu_120step"
MPI_FIRE_INPUT = "input.codex_c3h8_pipe_rack_delayed_ignition_mpi_120step"
CUDA_FIRE_INPUT = "input.codex_c3h8_pipe_rack_delayed_ignition_cuda_120step"
MPICUDA_FIRE_INPUT = "input.codex_c3h8_pipe_rack_delayed_ignition_mpicuda_rankmapped_120step"
PLOTS = ("plt00000", "plt00020", "plt00040", "plt00060", "plt00080", "plt00100", "plt00120")

FAILURE_RE = re.compile(
    r"(^|[^A-Za-z])(nan|inf)([^A-Za-z]|$)|Backtrace|Segmentation|SIGSEGV|"
    r"CUDA error|GPU last error|Abort|Wrong solve_type|CVODE solve failed|"
    r"reactor failed|deltaT_iters not converged|error while loading",
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


def copy_if_needed(src: Path, dst: Path) -> None:
    require(src.is_file(), f"missing source evidence file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists() or sha256_file(src) != sha256_file(dst):
        shutil.copy2(src, dst)


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def stage_dir(src: Path, dst: Path, files: tuple[str, ...]) -> None:
    require(src.is_dir(), f"missing runtime directory: {src}")
    dst.mkdir(parents=True, exist_ok=True)
    for name in files:
        copy_if_needed(src / name, dst / name)


def stage_fire_dir(src: Path, dst: Path, input_name: str, build_log_name: str) -> None:
    stage_dir(
        src,
        dst,
        (
            input_name,
            "run.log",
            "run.status",
            "fextrema_selected.log",
            "codex_merged_pipe_rack_obstacles.stl",
            "codex_cube_block.stl",
            "codex_vertical_cylinder.stl",
            "codex_pipe_rack.stl",
        ),
    )
    copy_if_needed(src / build_log_name, dst / build_log_name)
    for plot in PLOTS:
        header = src / plot / "Header"
        if header.is_file():
            copy_if_needed(header, dst / plot / "Header")


def stage_runtime_evidence(
    cold_root: Path,
    cpu_fire_root: Path,
    mpi_fire_root: Path,
    cuda_fire_root: Path,
    mpicuda_fire_root: Path,
    staged_root: Path,
) -> None:
    stage_dir(
        cold_root,
        staged_root / "cold_cpu",
        (
            COLD_INPUT,
            "run.log",
            "run.status",
            "c3h8_mini_cpu_build.log",
            "c3h8_mini_cpu_rebuild_label_fix.log",
        ),
    )
    stage_fire_dir(cpu_fire_root, staged_root / "fire_cpu", CPU_FIRE_INPUT, "propane_fc_cpu_clean_build.log")
    stage_fire_dir(mpi_fire_root, staged_root / "fire_mpi", MPI_FIRE_INPUT, "propane_fc_mpi_clean_build.log")
    stage_fire_dir(cuda_fire_root, staged_root / "fire_cuda", CUDA_FIRE_INPUT, "propane_fc_cuda_clean_build.log")
    stage_fire_dir(
        mpicuda_fire_root,
        staged_root / "fire_mpicuda",
        MPICUDA_FIRE_INPUT,
        "propane_fc_mpicuda_clean_build.log",
    )
    copy_if_needed(mpicuda_fire_root / "rank_gpu_wrapper.sh", staged_root / "fire_mpicuda" / "rank_gpu_wrapper.sh")


def required_runtime_roots(args: argparse.Namespace) -> tuple[Path, ...]:
    return (
        Path(args.cold_root),
        Path(args.cpu_fire_root),
        Path(args.mpi_fire_root),
        Path(args.cuda_fire_root),
        Path(args.mpicuda_fire_root),
    )


def staged_evidence_ready(staged_root: Path) -> bool:
    required_files = (
        staged_root / "cold_cpu" / COLD_INPUT,
        staged_root / "cold_cpu" / "run.log",
        staged_root / "cold_cpu" / "run.status",
        staged_root / "fire_cpu" / CPU_FIRE_INPUT,
        staged_root / "fire_cpu" / "run.log",
        staged_root / "fire_cpu" / "run.status",
        staged_root / "fire_cpu" / "fextrema_selected.log",
        staged_root / "fire_mpi" / MPI_FIRE_INPUT,
        staged_root / "fire_mpi" / "run.log",
        staged_root / "fire_mpi" / "run.status",
        staged_root / "fire_mpi" / "fextrema_selected.log",
        staged_root / "fire_cuda" / CUDA_FIRE_INPUT,
        staged_root / "fire_cuda" / "run.log",
        staged_root / "fire_cuda" / "run.status",
        staged_root / "fire_cuda" / "fextrema_selected.log",
        staged_root / "fire_mpicuda" / MPICUDA_FIRE_INPUT,
        staged_root / "fire_mpicuda" / "run.log",
        staged_root / "fire_mpicuda" / "run.status",
        staged_root / "fire_mpicuda" / "fextrema_selected.log",
        staged_root / "fire_mpicuda" / "rank_gpu_wrapper.sh",
    )
    return all(path.is_file() for path in required_files)


def run_status(path: Path) -> int:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except FileNotFoundError as exc:
        raise ReportError(f"missing run.status: {path}") from exc
    except ValueError as exc:
        raise ReportError(f"invalid run.status: {path}") from exc


def parse_input(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")

    def value(name: str) -> str:
        match = re.search(rf"^\s*{re.escape(name)}\s*=\s*(.+?)\s*$", text, re.MULTILINE)
        require(match is not None, f"missing input parameter {name} in {path}")
        return match.group(1).strip()

    return {
        "max_step": int(value("amr.max_step")),
        "plot_int": int(value("amr.plot_int")),
        "n_cell": value("amr.n_cell"),
        "fuel_species": value("prob.fuel_species"),
        "chem_integrator": value("peleLM.chem_integrator"),
        "do_react": value("peleLM.do_react") == "1",
        "cloud_yfuel": float(value("prob.cloud_YFuel")) if "prob.cloud_YFuel" in text else None,
        "cloud_yo2": float(value("prob.cloud_YO2")) if "prob.cloud_YO2" in text else None,
        "cloud_yn2": float(value("prob.cloud_YN2")) if "prob.cloud_YN2" in text else None,
        "ignition_source": value("prob.ignition_source") == "1" if "prob.ignition_source" in text else False,
        "obstacle_geometry": value("prob.obstacle_geometry") if "prob.obstacle_geometry" in text else "all_regular",
    }


def parse_fextrema(path: Path) -> dict[str, dict[str, dict[str, float]]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    result: dict[str, dict[str, dict[str, float]]] = {}
    current: str | None = None
    for line in text.splitlines():
        plot_match = re.match(r"^==\s+(plt\d+)\s+==$", line.strip())
        if plot_match:
            current = plot_match.group(1)
            result[current] = {}
            continue
        if current is None:
            continue
        value_match = re.match(
            r"^\s*(temp|HeatRelease|Y\(H2O\)|Y\(CO2\)|Y\(C3H8\)|I_R\(C3H8\))\s+"
            r"([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*$",
            line,
        )
        if value_match:
            result[current][value_match.group(1)] = {
                "min": float(value_match.group(2)),
                "max": float(value_match.group(3)),
            }
    require("plt00120" in result, f"fextrema log missing final plot: {path}")
    return result


def no_failure_markers(text: str, label: str) -> None:
    hits = [line.strip() for line in text.splitlines() if FAILURE_RE.search(line)]
    require(not hits, f"{label} failure markers found: {hits[:5]}")


def validate_cold(root: Path) -> dict[str, Any]:
    run_log = (root / "run.log").read_text(encoding="utf-8", errors="replace")
    input_summary = parse_input(root / COLD_INPUT)
    require(run_status(root / "run.status") == 0, "C3H8 cold plume run did not exit 0")
    require("Engineering leak fuel species: name=C3H8, index=2, mechanism_species_count=3" in run_log,
            "C3H8 cold plume did not use c3h8_mini species index")
    require("Applying C3H8 leak source" in run_log, "C3H8 cold plume source marker missing")
    require("Final simulation time: 0.01" in run_log, "C3H8 cold plume did not reach 10 steps")
    require(input_summary["chem_integrator"] == "ReactorNull", "cold plume did not use ReactorNull")
    no_failure_markers(run_log, "C3H8 cold plume")
    return {
        "status": "PASS-C3H8-COLD-PLUME-CPU",
        "mechanism": "c3h8_mini",
        "mechanism_species_count": 3,
        "fuel_species_index": 2,
        "max_step": input_summary["max_step"],
    }


def validate_fire(root: Path, input_name: str, platform: str) -> dict[str, Any]:
    run_log = (root / "run.log").read_text(encoding="utf-8", errors="replace")
    input_summary = parse_input(root / input_name)
    extrema = parse_fextrema(root / "fextrema_selected.log")
    final = extrema["plt00120"]
    peak_temp = max(plot["temp"]["max"] for plot in extrema.values() if "temp" in plot)
    peak_heat = max(abs(plot["HeatRelease"]["min"]) for plot in extrema.values() if "HeatRelease" in plot)
    peak_heat = max(peak_heat, max(abs(plot["HeatRelease"]["max"]) for plot in extrema.values() if "HeatRelease" in plot))
    min_ir = min(plot["I_R(C3H8)"]["min"] for plot in extrema.values() if "I_R(C3H8)" in plot)
    require(run_status(root / "run.status") == 0, f"C3H8 {platform} fire run did not exit 0")
    require("Engineering leak fuel species: name=C3H8, index=31, mechanism_species_count=34" in run_log,
            f"C3H8 {platform} fire did not use propane_fc")
    require("Creating ReactorBase instance: ReactorCvode" in run_log, f"C3H8 {platform} fire missing CVODE marker")
    require("C3H8 delayed ignition source: enabled=1" in run_log, f"C3H8 {platform} ignition marker missing")
    require("Final simulation time: 1.2e-06" in run_log or "Final simulation time: 1.199999" in run_log,
            f"C3H8 {platform} fire did not reach 120 steps")
    require("AMReX" in run_log and "finalized" in run_log, f"C3H8 {platform} AMReX finalization marker missing")
    if platform == "mpi":
        require("MPI initialized with 2 MPI processes" in run_log, "C3H8 MPI fire did not initialize two ranks")
    if platform == "mpicuda":
        require("MPI initialized with 2 MPI processes" in run_log, "C3H8 MPI+CUDA fire did not initialize two ranks")
        require("CUDA initialized with 2 devices." in run_log, "C3H8 MPI+CUDA fire did not expose two GPUs")
        require("rank_gpu_wrapper: local_rank=0 CUDA_VISIBLE_DEVICES=0" in run_log,
                "C3H8 MPI+CUDA rank 0 GPU binding missing")
        require("rank_gpu_wrapper: local_rank=1 CUDA_VISIBLE_DEVICES=1" in run_log,
                "C3H8 MPI+CUDA rank 1 GPU binding missing")
    if platform == "cuda":
        require("CUDA initialized with 1 device." in run_log, "C3H8 CUDA fire did not initialize one GPU")
    require(input_summary["fuel_species"] == "C3H8", f"C3H8 {platform} fire input did not select C3H8")
    require(input_summary["chem_integrator"] == "ReactorCvode", f"C3H8 {platform} fire did not use ReactorCvode")
    require(input_summary["ignition_source"] is True, f"C3H8 {platform} fire did not enable delayed ignition")
    require(input_summary["obstacle_geometry"] == "stl", f"C3H8 {platform} fire did not use STL obstacles")
    require(peak_temp > 2000.0, f"C3H8 {platform} peak temperature too low: {peak_temp}")
    require(peak_heat > 1.0e6, f"C3H8 {platform} heat-release magnitude too small: {peak_heat}")
    require(final["Y(H2O)"]["max"] > 1.0e-6, f"C3H8 {platform} final H2O too small")
    require(final["Y(CO2)"]["max"] > 1.0e-8, f"C3H8 {platform} final CO2 too small")
    require(min_ir < -1.0, f"C3H8 {platform} fuel consumption rate too small")
    no_failure_markers(run_log, f"C3H8 {platform} fire")
    return {
        "status": f"PASS-C3H8-PROPANE-FC-FIRE-{platform.upper()}",
        "mechanism": "propane_fc",
        "mechanism_species_count": 34,
        "fuel_species_index": 31,
        "max_step": input_summary["max_step"],
        "peak_temperature": peak_temp,
        "peak_heat_release_abs": peak_heat,
        "final_y_h2o_max": final["Y(H2O)"]["max"],
        "final_y_co2_max": final["Y(CO2)"]["max"],
        "min_ir_c3h8": min_ir,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    staged_root = Path(args.staged_root)
    if not args.no_stage:
        roots = required_runtime_roots(args)
        if all(root.is_dir() for root in roots):
            stage_runtime_evidence(*roots, staged_root)
        else:
            missing = [str(root) for root in roots if not root.is_dir()]
            require(
                staged_evidence_ready(staged_root),
                "missing runtime directories and staged evidence is incomplete: " + ", ".join(missing),
            )

    cold = validate_cold(staged_root / "cold_cpu")
    cpu_fire = validate_fire(staged_root / "fire_cpu", CPU_FIRE_INPUT, "cpu")
    mpi_fire = validate_fire(staged_root / "fire_mpi", MPI_FIRE_INPUT, "mpi")
    cuda_fire = validate_fire(staged_root / "fire_cuda", CUDA_FIRE_INPUT, "cuda")
    mpicuda_fire = validate_fire(staged_root / "fire_mpicuda", MPICUDA_FIRE_INPUT, "mpicuda")

    evidence = [
        evidence_entry("cold_cpu_run_log", staged_root / "cold_cpu" / "run.log"),
        evidence_entry("cold_cpu_input", staged_root / "cold_cpu" / COLD_INPUT),
        evidence_entry("cpu_fire_run_log", staged_root / "fire_cpu" / "run.log"),
        evidence_entry("cpu_fire_input", staged_root / "fire_cpu" / CPU_FIRE_INPUT),
        evidence_entry("cpu_fire_fextrema", staged_root / "fire_cpu" / "fextrema_selected.log"),
        evidence_entry("mpi_fire_run_log", staged_root / "fire_mpi" / "run.log"),
        evidence_entry("mpi_fire_input", staged_root / "fire_mpi" / MPI_FIRE_INPUT),
        evidence_entry("mpi_fire_fextrema", staged_root / "fire_mpi" / "fextrema_selected.log"),
        evidence_entry("cuda_fire_run_log", staged_root / "fire_cuda" / "run.log"),
        evidence_entry("cuda_fire_input", staged_root / "fire_cuda" / CUDA_FIRE_INPUT),
        evidence_entry("cuda_fire_fextrema", staged_root / "fire_cuda" / "fextrema_selected.log"),
        evidence_entry("mpicuda_fire_run_log", staged_root / "fire_mpicuda" / "run.log"),
        evidence_entry("mpicuda_fire_input", staged_root / "fire_mpicuda" / MPICUDA_FIRE_INPUT),
        evidence_entry("mpicuda_fire_fextrema", staged_root / "fire_mpicuda" / "fextrema_selected.log"),
        evidence_entry("mpicuda_rank_gpu_wrapper", staged_root / "fire_mpicuda" / "rank_gpu_wrapper.sh"),
        evidence_entry("propane_fc_cpu_clean_build", staged_root / "fire_cpu" / "propane_fc_cpu_clean_build.log"),
        evidence_entry("propane_fc_mpi_clean_build", staged_root / "fire_mpi" / "propane_fc_mpi_clean_build.log"),
        evidence_entry("propane_fc_cuda_clean_build", staged_root / "fire_cuda" / "propane_fc_cuda_clean_build.log"),
        evidence_entry("propane_fc_mpicuda_clean_build", staged_root / "fire_mpicuda" / "propane_fc_mpicuda_clean_build.log"),
    ]

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "title": "Engineering C3H8 Gas-Phase CPU/MPI/CUDA Evidence",
        "summary": {
            "c3h8_cold_plume_cpu_passed": True,
            "c3h8_propane_fc_fire_cpu_passed": True,
            "c3h8_propane_fc_fire_cpu_mpi_passed": True,
            "c3h8_propane_fc_fire_cuda_passed": True,
            "c3h8_propane_fc_fire_mpi_cuda_passed": True,
            "c3h8_rank_mapped_two_gpu_mpi_cuda_passed": True,
            "gas_phase_propane_initial_engineering_probe_ready": True,
            "propane_gas_phase_production_ready": False,
            "liquefied_propane_or_lpg_phase_change_ready": False,
            "prevents_liquefied_gas_overclaim": True,
        },
        "cold_plume": cold,
        "cpu_fire": cpu_fire,
        "mpi_fire": mpi_fire,
        "cuda_fire": cuda_fire,
        "mpicuda_fire": mpicuda_fire,
        "evidence": evidence,
        "limitations": [
            "This validates gas-phase C3H8 source injection and reduced pipe-rack ignition/fire probes only.",
            "It does not validate LPG tank rupture, flashing, liquid-pool evaporation, droplet breakup, or cold dense-gas ground slumping.",
            "External propane fire/plume comparison thresholds remain required before a production propane safety claim.",
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS, "status mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("c3h8_cold_plume_cpu_passed") is True, "cold C3H8 probe missing")
    require(summary.get("c3h8_propane_fc_fire_cpu_passed") is True, "C3H8 CPU fire probe missing")
    require(summary.get("c3h8_propane_fc_fire_cpu_mpi_passed") is True, "C3H8 CPU/MPI fire probe missing")
    require(summary.get("c3h8_propane_fc_fire_cuda_passed") is True, "C3H8 CUDA fire probe missing")
    require(summary.get("c3h8_propane_fc_fire_mpi_cuda_passed") is True, "C3H8 MPI+CUDA fire probe missing")
    require(summary.get("c3h8_rank_mapped_two_gpu_mpi_cuda_passed") is True, "C3H8 rank-mapped two-GPU probe missing")
    require(summary.get("propane_gas_phase_production_ready") is False, "must not claim propane production readiness")
    require(summary.get("liquefied_propane_or_lpg_phase_change_ready") is False, "must not claim LPG phase-change readiness")
    for section in ("cpu_fire", "mpi_fire", "cuda_fire", "mpicuda_fire"):
        payload = data.get(section)
        require(isinstance(payload, dict), f"{section} missing")
        require(float(payload.get("peak_temperature", 0.0)) > 2000.0, f"{section} peak temp too low")
        require(float(payload.get("peak_heat_release_abs", 0.0)) > 1.0e6, f"{section} heat release too low")
        require(float(payload.get("final_y_h2o_max", 0.0)) > 1.0e-6, f"{section} H2O too low")
        require(float(payload.get("final_y_co2_max", 0.0)) > 1.0e-8, f"{section} CO2 too low")
    evidence = data.get("evidence")
    require(isinstance(evidence, list) and len(evidence) >= 16, "evidence list incomplete")
    if verify_hashes:
        for item in evidence:
            path = Path(item["path"])
            require(path.is_file(), f"missing hashed evidence: {path}")
            require(sha256_file(path) == item["sha256"], f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    cpu = report["cpu_fire"]
    mpi = report["mpi_fire"]
    cuda = report["cuda_fire"]
    mpicuda = report["mpicuda_fire"]
    lines = [
        "# Engineering C3H8 Gas-Phase CPU/MPI/CUDA Evidence",
        "",
        f"- Status: `{report['status']}`",
        f"- C3H8 cold plume CPU passed: `{s['c3h8_cold_plume_cpu_passed']}`",
        f"- C3H8 propane_fc CPU fire passed: `{s['c3h8_propane_fc_fire_cpu_passed']}`",
        f"- C3H8 propane_fc CPU/MPI fire passed: `{s['c3h8_propane_fc_fire_cpu_mpi_passed']}`",
        f"- C3H8 propane_fc CUDA fire passed: `{s['c3h8_propane_fc_fire_cuda_passed']}`",
        f"- C3H8 propane_fc MPI+CUDA fire passed: `{s['c3h8_propane_fc_fire_mpi_cuda_passed']}`",
        f"- C3H8 rank-mapped two-GPU MPI+CUDA passed: `{s['c3h8_rank_mapped_two_gpu_mpi_cuda_passed']}`",
        f"- Propane gas-phase production ready: `{s['propane_gas_phase_production_ready']}`",
        f"- LPG/liquefied propane phase-change ready: `{s['liquefied_propane_or_lpg_phase_change_ready']}`",
        "",
        "## Fire Metrics",
        "",
        "| Platform | Peak T [K] | Peak abs HeatRelease | Final max Y(H2O) | Final max Y(CO2) | Min I_R(C3H8) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| CPU | {cpu['peak_temperature']:.6g} | {cpu['peak_heat_release_abs']:.6g} | "
            f"{cpu['final_y_h2o_max']:.6g} | {cpu['final_y_co2_max']:.6g} | {cpu['min_ir_c3h8']:.6g} |"
        ),
        (
            f"| CPU/MPI | {mpi['peak_temperature']:.6g} | {mpi['peak_heat_release_abs']:.6g} | "
            f"{mpi['final_y_h2o_max']:.6g} | {mpi['final_y_co2_max']:.6g} | {mpi['min_ir_c3h8']:.6g} |"
        ),
        (
            f"| CUDA | {cuda['peak_temperature']:.6g} | {cuda['peak_heat_release_abs']:.6g} | "
            f"{cuda['final_y_h2o_max']:.6g} | {cuda['final_y_co2_max']:.6g} | {cuda['min_ir_c3h8']:.6g} |"
        ),
        (
            f"| MPI+CUDA | {mpicuda['peak_temperature']:.6g} | {mpicuda['peak_heat_release_abs']:.6g} | "
            f"{mpicuda['final_y_h2o_max']:.6g} | {mpicuda['final_y_co2_max']:.6g} | {mpicuda['min_ir_c3h8']:.6g} |"
        ),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(["", "## Evidence", ""])
    lines.extend(f"- `{item['label']}`: `{item['path']}` sha256=`{item['sha256']}`" for item in report["evidence"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cold-root", default=str(DEFAULT_COLD_ROOT))
    parser.add_argument("--cpu-fire-root", default=str(DEFAULT_CPU_FIRE_ROOT))
    parser.add_argument("--mpi-fire-root", default=str(DEFAULT_MPI_FIRE_ROOT))
    parser.add_argument("--cuda-fire-root", default=str(DEFAULT_CUDA_FIRE_ROOT))
    parser.add_argument("--mpicuda-fire-root", default=str(DEFAULT_MPICUDA_FIRE_ROOT))
    parser.add_argument("--staged-root", default=str(DEFAULT_STAGED_ROOT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--no-stage", action="store_true")
    parser.add_argument("--verify-json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.verify_json:
            data = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
            validate_report(data, verify_hashes=True)
            print(f"engineering_c3h8_gas_phase_cpu_cuda VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report(args)
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_c3h8_gas_phase_cpu_cuda PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except (ReportError, OSError, json.JSONDecodeError) as exc:
        print(f"engineering_c3h8_gas_phase_cpu_cuda FAIL {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
