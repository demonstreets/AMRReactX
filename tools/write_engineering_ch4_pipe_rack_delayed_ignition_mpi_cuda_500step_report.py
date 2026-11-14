#!/usr/bin/env python3
"""Write/verify CH4 pipe-rack delayed-ignition 500-step rank-mapped MPI+CUDA evidence."""
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
STATUS = "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA-500STEP"
RUN_STATUS = "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA-RANKMAPPED-500STEP-P1E10"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_20260806")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.md"
DEFAULT_STAGED_ROOT = DEFAULT_ROOT / "runtime_evidence"
DEFAULT_RUN_ROOT = Path("/tmp/codex_ch4_pipe_rack_delayed_ignition_mpi_cuda_rankmapped_500step_p1e10_20260806")
DEFAULT_BUILD_LOG = Path("/tmp/codex_ch4_mpicuda_build_sundials_home_20260806.log")

INPUT_NAME = "input.codex_ch4_pipe_rack_delayed_ignition_mpi_cuda_rankmapped_500step"
PLOT_HEADERS = ("plt00000", "plt00050", "plt00150", "plt00300", "plt00500")
OBSTACLE_STLS = (
    "codex_cube_block.stl",
    "codex_vertical_cylinder.stl",
    "codex_pipe_rack.stl",
    "codex_merged_pipe_rack_obstacles.stl",
)

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


def require_log_marker(run_log: str, marker: str | tuple[str, ...]) -> None:
    if isinstance(marker, tuple):
        require(any(item in run_log for item in marker), f"run log missing one of markers: {marker}")
    else:
        require(marker in run_log, f"run log missing marker: {marker}")


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
        raise ReportError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f"invalid JSON evidence {path}: {exc}") from exc
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


def copy_if_needed(src: Path, dst: Path) -> None:
    require(src.is_file(), f"missing source evidence file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists() or sha256_file(src) != sha256_file(dst):
        shutil.copy2(src, dst)


def stage_runtime_evidence(run_root: Path, staged_root: Path, build_log: Path) -> None:
    run_dir = run_root / "run"
    copy_if_needed(run_root / "summary.json", staged_root / "summary.json")
    copy_if_needed(run_root / "run.log", staged_root / "run.log")
    copy_if_needed(run_root / "run.status", staged_root / "run.status")
    copy_if_needed(run_dir / INPUT_NAME, staged_root / INPUT_NAME)
    copy_if_needed(run_dir / "rank_gpu_wrapper.sh", staged_root / "rank_gpu_wrapper.sh")
    if build_log.is_file():
        copy_if_needed(build_log, staged_root / "build_ch4_mpi_cuda.log")
    for name in OBSTACLE_STLS:
        copy_if_needed(run_dir / name, staged_root / name)
    for name in PLOT_HEADERS:
        copy_if_needed(run_dir / name / "Header", staged_root / name / "Header")


def parse_input(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")

    def value(name: str) -> str:
        match = re.search(rf"^\s*{re.escape(name)}\s*=\s*(.+?)\s*$", text, re.MULTILINE)
        require(match is not None, f"missing input parameter {name}")
        return match.group(1).strip()

    def first_value(*names: str) -> str:
        for name in names:
            match = re.search(rf"^\s*{re.escape(name)}\s*=\s*(.+?)\s*$", text, re.MULTILINE)
            if match is not None:
                return match.group(1).strip()
        raise ReportError(f"missing input parameter one of: {', '.join(names)}")

    return {
        "max_step": int(value("amr.max_step")),
        "plot_int": int(value("amr.plot_int")),
        "n_cell": value("amr.n_cell"),
        "fuel_species": value("prob.fuel_species"),
        "ignition_source": value("prob.ignition_source") == "1",
        "ignition_hotspot": value("prob.ignition_hotspot") == "1",
        "ignition_start_time": float(value("prob.ignition_start_time")),
        "ignition_duration": float(value("prob.ignition_duration")),
        "ignition_power": float(value("prob.ignition_power")),
        "chem_integrator": value("peleLM.chem_integrator"),
        "cvode_solve_type": value("cvode.solve_type"),
        "obstacle_geometry": value("prob.obstacle_geometry"),
        "obstacle_stl_files": first_value("prob.obstacle_stl_files", "prob.obstacle_stl_file"),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    output_root = Path(args.output_root)
    staged_root = Path(args.staged_root or (output_root / "runtime_evidence"))
    run_root = Path(args.run_root) if args.run_root else None
    build_log = Path(args.build_log)
    if run_root and run_root.exists():
        stage_runtime_evidence(run_root, staged_root, build_log)

    summary_path = staged_root / "summary.json"
    run_log_path = staged_root / "run.log"
    status_path = staged_root / "run.status"
    input_path = staged_root / INPUT_NAME
    summary = load_json(summary_path)
    run_log = run_log_path.read_text(encoding="utf-8", errors="replace")
    input_summary = parse_input(input_path)

    require(status_path.read_text(encoding="utf-8").strip() == "0", "source run status is not zero")
    require(summary.get("status") == RUN_STATUS, "source CH4 500-step MPI+CUDA summary is not PASS")
    require(summary.get("species") == "CH4", "summary species is not CH4")
    require(summary.get("chemistry_model") == "CH4_lean", "summary chemistry model is not CH4_lean")
    require(int(summary.get("max_step", 0)) >= 500, "CH4 long fire run did not reach 500 steps")
    require(int(summary.get("mpi_ranks", 0)) == 2, "CH4 long fire run did not use two MPI ranks")
    require(int(summary.get("cuda_devices", 0)) == 2, "CH4 long fire run did not expose two CUDA devices")
    require(summary.get("rank_gpu_bindings") == {"0": "0", "1": "1"}, "rank-local GPU bindings missing")
    require(input_summary["max_step"] == 500, "input max_step is not 500")
    require(input_summary["plot_int"] == 50, "input plot_int is not 50")
    require(input_summary["fuel_species"] == "CH4", "input did not select CH4 fuel species")
    require(input_summary["ignition_source"] is True, "input did not enable timed ignition")
    require(input_summary["ignition_hotspot"] is False, "input used initial hot spot")
    require(input_summary["ignition_power"] == 1.0e10, "input ignition power does not match stable window")
    require(input_summary["chem_integrator"] == "ReactorCvode", "input did not use ReactorCvode")
    require(input_summary["cvode_solve_type"] == "GMRES", "input did not use GMRES")
    require(input_summary["obstacle_geometry"] == "stl", "input did not use STL obstacles")

    caps = summary.get("validated_capabilities")
    require(isinstance(caps, dict), "summary missing validated_capabilities")
    for name in (
        "ch4_leak_source",
        "pipe_rack_stl_obstacles",
        "delayed_ignition_timed_energy_source",
        "mpi_cuda_parallel",
        "rank_local_gpu_binding",
        "multi_gpu_two_physical_devices",
        "longer_sustained_post_ignition_fire_development",
        "late_window_reactive_fire_maintained",
        "no_nan_inf_or_solver_abort",
    ):
        require(caps.get(name) is True, f"{name} not validated by source summary")

    checks = summary.get("sustained_reaction_checks")
    require(isinstance(checks, dict), "summary missing sustained reaction checks")
    require(int(checks.get("sustained_output_count", 0)) >= 8, "too few sustained CH4 long fire outputs")
    require(int(checks.get("late_reactive_output_count", 0)) >= 4, "too few late reactive CH4 outputs")
    require(float(checks.get("peak_y_h2o_max", 0.0)) > 1.0e-4, "peak H2O product growth too small")
    require(float(checks.get("peak_y_co2_max", 0.0)) > 1.0e-8, "peak CO2 product growth too small")
    require(float(checks.get("final_y_h2o_max", 0.0)) > 5.0e-5, "final H2O residual too small")
    require(float(checks.get("final_heat_release_abs", 0.0)) > 1.0e5, "final heat release too small")
    require(float(checks.get("final_ir_ch4_abs", 0.0)) > 1.0e-3, "final CH4 reaction rate too small")
    require(float(checks.get("final_temp_max", 0.0)) > 900.0, "final temperature too small")
    require(float(checks.get("final_time", 0.0)) >= 4.99e-6, "final time is too short")

    for marker in (
        "rank_gpu_wrapper: local_rank=0 CUDA_VISIBLE_DEVICES=0",
        "rank_gpu_wrapper: local_rank=1 CUDA_VISIBLE_DEVICES=1",
        "MPI initialized with 2 MPI processes",
        "CUDA initialized with 2 devices",
        "SUNDIALS initialized",
        "Engineering leak fuel species: name=CH4",
        (
            "Engineering leak UserDefined EB STL: file=codex_merged_pipe_rack_obstacles.stl",
            "H2 leak UserDefined EB STL: file=codex_merged_pipe_rack_obstacles.stl",
        ),
        "buildFromSTL: built AMReX EB2 IndexSpace from codex_merged_pipe_rack_obstacles.stl",
        ("CH4 delayed ignition source: enabled=1", "H2 delayed ignition source: enabled=1"),
        "Creating ReactorBase instance: ReactorCvode",
        "STEP [499]",
        "Final simulation time: 5e-06",
        "AMReX",
    ):
        require_log_marker(run_log, marker)
    require("Multiple GPUs are visible" not in run_log, "rank-mapped run emitted multi-GPU visibility warning")
    hits = [line.strip() for line in run_log.splitlines() if FAILURE_RE.search(line)]
    require(not hits, f"solver failure markers found: {hits[:5]}")

    evidence = [
        evidence_entry("staged_summary", summary_path),
        evidence_entry("staged_run_log", run_log_path),
        evidence_entry("staged_run_status", status_path),
        evidence_entry("staged_input", input_path),
        evidence_entry("rank_gpu_wrapper", staged_root / "rank_gpu_wrapper.sh"),
        evidence_entry("build_log", staged_root / "build_ch4_mpi_cuda.log"),
        evidence_entry("cube_obstacle_stl", staged_root / "codex_cube_block.stl"),
        evidence_entry("vertical_cylinder_stl", staged_root / "codex_vertical_cylinder.stl"),
        evidence_entry("pipe_rack_stl", staged_root / "codex_pipe_rack.stl"),
        evidence_entry("merged_pipe_rack_stl", staged_root / "codex_merged_pipe_rack_obstacles.stl"),
        evidence_entry("plt00000_header_initial", staged_root / "plt00000" / "Header"),
        evidence_entry("plt00050_header_fire_growth", staged_root / "plt00050" / "Header"),
        evidence_entry("plt00150_header_peak_products", staged_root / "plt00150" / "Header"),
        evidence_entry("plt00300_header_late_reactive", staged_root / "plt00300" / "Header"),
        evidence_entry("plt00500_header_final", staged_root / "plt00500" / "Header"),
        evidence_entry("engineering_leak_prob_h", Path("examples/engineering/h2_leak_3d/pelelmex_prob.H")),
        evidence_entry("engineering_leak_prob_cpp", Path("examples/engineering/h2_leak_3d/pelelmex_prob.cpp")),
    ]
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "title": "Engineering CH4 Pipe-Rack Delayed-Ignition MPI+CUDA 500-Step Probe",
        "decision": "ch4_rank_mapped_mpi_cuda_longer_sustained_fire_window_pass",
        "staged_evidence_root": str(staged_root),
        "source_run_root": str(run_root) if run_root else "",
        "input_summary": input_summary,
        "run_summary": {
            "max_step": summary["max_step"],
            "mpi_ranks": summary["mpi_ranks"],
            "cuda_devices": summary["cuda_devices"],
            "rank_gpu_bindings": summary["rank_gpu_bindings"],
            "plot_interval": summary["plot_interval"],
            "chemistry_model": summary["chemistry_model"],
            "plotfiles": summary["plotfiles"],
            "sustained_reaction_checks": checks,
        },
        "validated_capabilities": {
            "ch4_leak_source": True,
            "pipe_rack_stl_obstacles": True,
            "initial_flammable_cloud": True,
            "delayed_ignition_timed_energy_source": True,
            "reactor_cvode": True,
            "cvode_gmres": True,
            "rank_mapped_mpi_cuda_parallel": True,
            "two_physical_gpus_used": True,
            "longer_sustained_post_ignition_fire_development": True,
            "late_window_reactive_fire_maintained": True,
            "no_nan_inf_or_solver_abort": True,
        },
        "limitations": [
            "This 500-step probe is longer than the ignition smoke tests, but it is still not a calibrated full-duration natural-gas production campaign.",
            "The late window is a decaying but still reactive hot plume; production qualification still needs scenario-specific duration and acceptance thresholds.",
            "The geometry is synthetic cube/cylinder/pipe-rack STL, not a real cleaned plant CAD import.",
            "Radiation, overpressure, LNG vaporization, and multi-component natural-gas composition validation are outside this probe.",
        ],
        "evidence_files": evidence,
    }
    validate_report(report, check_hashes=False)
    return report


def validate_report(report: dict[str, Any], check_hashes: bool = True) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS, "status mismatch")
    run = report.get("run_summary")
    require(isinstance(run, dict), "missing run_summary")
    checks = run.get("sustained_reaction_checks")
    require(isinstance(checks, dict), "missing sustained reaction checks")
    require(int(run.get("max_step", 0)) >= 500, "max_step too small")
    require(int(run.get("mpi_ranks", 0)) == 2, "MPI rank count mismatch")
    require(int(run.get("cuda_devices", 0)) == 2, "CUDA device count mismatch")
    require(run.get("rank_gpu_bindings") == {"0": "0", "1": "1"}, "rank GPU bindings mismatch")
    require(int(checks.get("sustained_output_count", 0)) >= 8, "sustained output count too small")
    require(int(checks.get("late_reactive_output_count", 0)) >= 4, "late reactive output count too small")
    require(float(checks.get("peak_y_h2o_max", 0.0)) > 1.0e-4, "peak H2O max too small")
    require(float(checks.get("final_heat_release_abs", 0.0)) > 1.0e5, "final heat release too small")
    require(float(checks.get("final_ir_ch4_abs", 0.0)) > 1.0e-3, "final CH4 reaction rate too small")
    require(float(checks.get("final_time", 0.0)) >= 4.99e-6, "final time too short")
    caps = report.get("validated_capabilities")
    require(isinstance(caps, dict), "missing validated_capabilities")
    require(caps.get("longer_sustained_post_ignition_fire_development") is True, "long fire capability not validated")
    require(caps.get("late_window_reactive_fire_maintained") is True, "late reactive window not validated")
    if check_hashes:
        for entry in report.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    run = report["run_summary"]
    checks = run["sustained_reaction_checks"]
    lines = [
        "# Engineering CH4 Pipe-Rack Delayed-Ignition MPI+CUDA 500-Step Probe",
        "",
        f"- Status: `{report['status']}`",
        f"- Decision: `{report['decision']}`",
        f"- Chemistry model: `{run['chemistry_model']}`",
        f"- MPI ranks/CUDA devices: `{run['mpi_ranks']}` / `{run['cuda_devices']}`",
        f"- Rank GPU bindings: `{run['rank_gpu_bindings']}`",
        f"- Steps/final time: `{run['max_step']}` / `{checks['final_time']}`",
        f"- Sustained outputs: `{checks['sustained_output_count']}`",
        f"- Late reactive outputs: `{checks['late_reactive_output_count']}`",
        f"- Peak Y(H2O) max: `{checks['peak_y_h2o_max']}`",
        f"- Final Y(H2O) max: `{checks['final_y_h2o_max']}`",
        f"- Final heat release abs: `{checks['final_heat_release_abs']}`",
        f"- Final I_R(CH4) abs: `{checks['final_ir_ch4_abs']}`",
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
    parser.add_argument("--output-root", default=str(DEFAULT_ROOT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--staged-root", default=str(DEFAULT_STAGED_ROOT))
    parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    parser.add_argument("--build-log", default=str(DEFAULT_BUILD_LOG))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = load_json(Path(args.verify_json))
            validate_report(report, check_hashes=True)
            print(f"engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step VERIFY-PASS json={args.verify_json} status={report.get('status')}")
            return 0
        report = build_report(args)
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except (OSError, json.JSONDecodeError, ReportError) as exc:
        print(f"engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step FAIL {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
