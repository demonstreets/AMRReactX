#!/usr/bin/env python3
"""Write/verify CH4 pipe-rack delayed-ignition single-CUDA evidence."""
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
STATUS = "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-SINGLE-CUDA"
RUN_STATUS = "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-SINGLE-CUDA-P1E10"

DEFAULT_ROOT = Path(
    "docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_cuda_20260806"
)
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_ch4_pipe_rack_delayed_ignition_cuda_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_ch4_pipe_rack_delayed_ignition_cuda_report.md"
DEFAULT_STAGED_ROOT = DEFAULT_ROOT / "runtime_evidence"
DEFAULT_RUN_ROOT = Path("/tmp/codex_ch4_pipe_rack_delayed_ignition_single_cuda_p1e10_20260806")

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


def stage_runtime_evidence(run_root: Path, staged_root: Path) -> None:
    run_dir = run_root / "run"
    copy_if_needed(run_root / "summary.json", staged_root / "summary.json")
    copy_if_needed(run_root / "run.log", staged_root / "run.log")
    copy_if_needed(
        run_dir / "input.codex_ch4_pipe_rack_delayed_ignition_single_cuda_120step",
        staged_root / "input.codex_ch4_pipe_rack_delayed_ignition_single_cuda_120step",
    )
    for name in (
        "codex_cube_block.stl",
        "codex_vertical_cylinder.stl",
        "codex_pipe_rack.stl",
        "codex_merged_pipe_rack_obstacles.stl",
    ):
        copy_if_needed(run_dir / name, staged_root / name)
    for name in ("plt00000", "plt00020", "plt00030", "plt00040", "plt00120"):
        copy_if_needed(run_dir / name / "Header", staged_root / name / "Header")


def parse_input(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")

    def value(name: str) -> str:
        match = re.search(rf"^\s*{re.escape(name)}\s*=\s*(.+?)\s*$", text, re.MULTILINE)
        require(match is not None, f"missing input parameter {name}")
        return match.group(1).strip()

    return {
        "max_step": int(value("amr.max_step")),
        "plot_int": int(value("amr.plot_int")),
        "n_cell": value("amr.n_cell"),
        "fuel_species": value("prob.fuel_species"),
        "cloud_yfuel": float(value("prob.cloud_YFuel")),
        "cloud_yo2": float(value("prob.cloud_YO2")),
        "cloud_yn2": float(value("prob.cloud_YN2")),
        "ignition_source": value("prob.ignition_source") == "1",
        "ignition_hotspot": value("prob.ignition_hotspot") == "1",
        "ignition_start_time": float(value("prob.ignition_start_time")),
        "ignition_duration": float(value("prob.ignition_duration")),
        "ignition_power": float(value("prob.ignition_power")),
        "chem_integrator": value("peleLM.chem_integrator"),
        "cvode_solve_type": value("cvode.solve_type"),
        "obstacle_geometry": value("prob.obstacle_geometry"),
        "obstacle_stl_files": value("prob.obstacle_stl_files"),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    output_root = Path(args.output_root)
    staged_root = Path(args.staged_root or (output_root / "runtime_evidence"))
    run_root = Path(args.run_root) if args.run_root else None
    if run_root and run_root.exists():
        stage_runtime_evidence(run_root, staged_root)

    summary_path = staged_root / "summary.json"
    run_log_path = staged_root / "run.log"
    input_path = staged_root / "input.codex_ch4_pipe_rack_delayed_ignition_single_cuda_120step"
    summary = load_json(summary_path)
    run_log = run_log_path.read_text(encoding="utf-8", errors="replace")
    input_summary = parse_input(input_path)

    require(summary.get("status") == RUN_STATUS, "source CH4 run summary is not PASS")
    require(summary.get("species") == "CH4", "summary species is not CH4")
    require(summary.get("chemistry_model") == "CH4_lean", "summary chemistry model is not CH4_lean")
    require(int(summary.get("max_step", 0)) >= 120, "CH4 fire run did not reach 120 steps")
    require(int(summary.get("cuda_devices", 0)) == 1, "CH4 fire run did not use one CUDA device")
    require(int(summary.get("mpi_ranks", 0)) == 1, "CH4 fire run was not a single-rank CUDA probe")
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
        "initial_flammable_cloud",
        "delayed_ignition_timed_energy_source",
        "reactor_cvode",
        "single_gpu_cuda",
        "sustained_post_ignition_fire_development",
        "no_nan_inf_or_solver_abort",
    ):
        require(caps.get(name) is True, f"{name} not validated by source summary")

    checks = summary.get("sustained_reaction_checks")
    require(isinstance(checks, dict), "summary missing sustained reaction checks")
    require(int(checks.get("sustained_output_count", 0)) >= 4, "too few sustained CH4 fire outputs")
    require(float(checks.get("final_y_h2o_max", 0.0)) > 1.0e-6, "CH4 fire H2O product growth too small")
    require(float(checks.get("final_y_co2_max", 0.0)) > 1.0e-10, "CH4 fire CO2 product growth too small")
    require(float(checks.get("max_heat_release_abs", 0.0)) > 100.0, "CH4 fire heat release too small")
    require(float(checks.get("max_ir_ch4_abs", 0.0)) > 1.0e-8, "CH4 reaction rate too small")
    require(float(checks.get("max_temp", 0.0)) > 1200.0, "CH4 fire temperature did not rise enough")
    require(float(checks.get("final_time", 0.0)) >= 1.0e-6, "CH4 fire final time too short")

    for marker in (
        "CUDA initialized with 1 device",
        "Engineering leak fuel species: name=CH4",
        (
            "Engineering leak UserDefined EB STL files: count=3",
            "H2 leak UserDefined EB STL files: count=3",
        ),
        ("CH4 delayed ignition source: enabled=1", "H2 delayed ignition source: enabled=1"),
        "Creating ReactorBase instance: ReactorCvode",
        "STEP [119]",
        "AMReX",
    ):
        require_log_marker(run_log, marker)
    hits = [line.strip() for line in run_log.splitlines() if FAILURE_RE.search(line)]
    require(not hits, f"solver failure markers found: {hits[:5]}")

    evidence = [
        evidence_entry("staged_summary", summary_path),
        evidence_entry("staged_run_log", run_log_path),
        evidence_entry("staged_input", input_path),
        evidence_entry("cube_obstacle_stl", staged_root / "codex_cube_block.stl"),
        evidence_entry("vertical_cylinder_stl", staged_root / "codex_vertical_cylinder.stl"),
        evidence_entry("pipe_rack_stl", staged_root / "codex_pipe_rack.stl"),
        evidence_entry("merged_pipe_rack_stl", staged_root / "codex_merged_pipe_rack_obstacles.stl"),
        evidence_entry("plt00000_header_initial", staged_root / "plt00000" / "Header"),
        evidence_entry("plt00020_header_ignition_start", staged_root / "plt00020" / "Header"),
        evidence_entry("plt00030_header_ignition_window", staged_root / "plt00030" / "Header"),
        evidence_entry("plt00040_header_post_ignition", staged_root / "plt00040" / "Header"),
        evidence_entry("plt00120_header_final", staged_root / "plt00120" / "Header"),
        evidence_entry("engineering_leak_prob_h", Path("examples/engineering/h2_leak_3d/pelelmex_prob.H")),
        evidence_entry("engineering_leak_prob_cpp", Path("examples/engineering/h2_leak_3d/pelelmex_prob.cpp")),
    ]
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "title": "Engineering CH4 Pipe-Rack Delayed-Ignition Single-CUDA Probe",
        "decision": "ch4_delayed_ignition_leak_obstacle_reacting_single_gpu_pass",
        "staged_evidence_root": str(staged_root),
        "source_run_root": str(run_root) if run_root else "",
        "input_summary": input_summary,
        "run_summary": {
            "max_step": summary["max_step"],
            "mpi_ranks": summary["mpi_ranks"],
            "cuda_devices": summary["cuda_devices"],
            "chemistry_model": summary["chemistry_model"],
            "plotfiles": summary["plotfiles"],
            "sustained_reaction_checks": checks,
        },
        "validated_capabilities": {
            "ch4_leak_source": True,
            "pipe_rack_stl_obstacles": True,
            "initial_flammable_cloud": True,
            "delayed_ignition_timed_energy_source": True,
            "initial_hotspot_not_used": True,
            "reactor_cvode": True,
            "cvode_gmres": True,
            "single_gpu_cuda": True,
            "sustained_post_ignition_fire_development": True,
            "no_nan_inf_or_solver_abort": True,
        },
        "negative_window_evidence": {
            "too_low_ignition_power_1e9": "stable_but_no_ignition",
            "too_high_ignition_power_1e11": "deltaT_iters_not_converged",
            "accepted_stable_window": "1e10",
        },
        "limitations": [
            "This is a reduced CH4 single-CUDA fire probe, not a calibrated natural-gas/LNG production validation.",
            "CPU/MPI, MPI+CUDA, and multi-GPU CH4 fire campaigns remain required before a broad CH4 production claim.",
            "The geometry is synthetic cube/cylinder/pipe-rack STL, not a real cleaned plant CAD import.",
            "Radiation, overpressure, and LNG vaporization/phase-change consequences are outside this probe.",
        ],
        "evidence_files": evidence,
    }
    validate_report(report, check_hashes=False)
    return report


def validate_report(report: dict[str, Any], check_hashes: bool = True) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS, "status mismatch")
    caps = report.get("validated_capabilities")
    require(isinstance(caps, dict), "missing validated_capabilities")
    for name in (
        "ch4_leak_source",
        "pipe_rack_stl_obstacles",
        "delayed_ignition_timed_energy_source",
        "single_gpu_cuda",
        "sustained_post_ignition_fire_development",
        "no_nan_inf_or_solver_abort",
    ):
        require(caps.get(name) is True, f"{name} not validated")
    run = report.get("run_summary")
    require(isinstance(run, dict), "missing run_summary")
    checks = run.get("sustained_reaction_checks")
    require(isinstance(checks, dict), "missing sustained reaction checks")
    require(int(run.get("max_step", 0)) >= 120, "max_step too small")
    require(int(run.get("cuda_devices", 0)) == 1, "CUDA device count mismatch")
    require(int(checks.get("sustained_output_count", 0)) >= 4, "sustained output count too small")
    require(float(checks.get("final_y_h2o_max", 0.0)) > 1.0e-6, "final H2O max too small")
    require(float(checks.get("final_y_co2_max", 0.0)) > 1.0e-10, "final CO2 max too small")
    require(float(checks.get("max_temp", 0.0)) > 1200.0, "max temperature too small")
    require(report.get("negative_window_evidence", {}).get("accepted_stable_window") == "1e10", "stable ignition window missing")
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
        "# Engineering CH4 Pipe-Rack Delayed-Ignition Single-CUDA Probe",
        "",
        f"- Status: `{report['status']}`",
        f"- Decision: `{report['decision']}`",
        f"- Chemistry model: `{run['chemistry_model']}`",
        f"- Steps/final time: `{run['max_step']}` / `{checks['final_time']}`",
        f"- Sustained outputs: `{checks['sustained_output_count']}`",
        f"- Max temperature: `{checks['max_temp']}`",
        f"- Final Y(H2O) max: `{checks['final_y_h2o_max']}`",
        f"- Final Y(CO2) max: `{checks['final_y_co2_max']}`",
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
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            report = load_json(Path(args.verify_json))
            validate_report(report, check_hashes=True)
            print(f"engineering_ch4_pipe_rack_delayed_ignition_cuda VERIFY-PASS json={args.verify_json} status={report.get('status')}")
            return 0
        report = build_report(args)
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_ch4_pipe_rack_delayed_ignition_cuda PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except (OSError, json.JSONDecodeError, ReportError) as exc:
        print(f"engineering_ch4_pipe_rack_delayed_ignition_cuda FAIL {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
