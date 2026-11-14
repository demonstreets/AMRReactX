#!/usr/bin/env python3
"""Write/verify direct H2 pipe-rack reacting single-CUDA smoke evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-SUSTAINED"
DEFAULT_OUTPUT_ROOT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_cuda_20260727"
)
DEFAULT_RUN_ROOT = Path("/tmp/codex_h2_pipe_rack_reacting_single_cuda_20260727_500step")

FAILURE_RE = re.compile(
    r"(^|[^A-Za-z])(nan|inf)([^A-Za-z]|$)|Backtrace|Segmentation|SIGSEGV|"
    r"CUDA error|GPU last error|Abort|Wrong solve_type|CVODE solve failed|"
    r"reactor failed|error while loading",
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


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReportError(f"missing JSON report: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f"invalid JSON report {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON report is not an object: {path}")
    return data


def parse_header(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    require(len(lines) > 8, f"plotfile header too short: {path}")
    nvars = int(lines[1].strip())
    variables = [lines[i].strip() for i in range(2, 2 + nvars)]
    time_value = float(lines[2 + nvars + 1].strip())
    required = {"Y(H2)", "Y(O2)", "Y(H2O)", "temp", "HeatRelease", "I_R(H2)", "I_R(O2)"}
    missing = sorted(required - set(variables))
    require(not missing, f"missing reacting/fire plot variables: {missing}")
    return {"nvars": nvars, "variables": variables, "time": time_value}


def parse_input(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")

    def value(name: str) -> str | None:
        m = re.search(rf"^\s*{re.escape(name)}\s*=\s*(.+?)\s*$", text, re.MULTILINE)
        return m.group(1).strip() if m else None

    require(value("peleLM.do_react") == "1", "input does not enable PeleLMeX reactions")
    require(value("peleLM.chem_integrator") == "ReactorCvode", "input does not use ReactorCvode")
    require(value("cvode.solve_type") == "GMRES", "input does not use GPU-compatible GMRES CVODE")
    require(value("prob.initial_flammable_cloud") == "1", "input does not seed flammable cloud")
    require(value("prob.ignition_hotspot") == "1", "input does not seed ignition hotspot")
    require(value("prob.obstacle_geometry") == "stl", "input does not use STL obstacles")
    return {
        "max_step": int(value("amr.max_step") or "0"),
        "plot_int": int(value("amr.plot_int") or "0"),
        "n_cell": value("amr.n_cell"),
        "chem_integrator": "ReactorCvode",
        "cvode_solve_type": "GMRES",
        "initial_flammable_cloud": True,
        "ignition_hotspot": True,
        "obstacle_geometry": "stl",
        "obstacle_stl_files": value("prob.obstacle_stl_files"),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_root = Path(args.run_root)
    run_dir = run_root / "run"
    run_log_path = run_root / "run.log"
    summary_path = run_root / "summary.json"
    input_path = run_dir / "input.codex_pipe_rack_reacting_single_cuda_20step"
    header0_path = run_dir / "plt00000" / "Header"
    script_path = Path("tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh")

    require(run_dir.is_dir(), f"missing run dir: {run_dir}")
    require(run_log_path.is_file(), f"missing run log: {run_log_path}")
    summary = load_json(summary_path)
    require(summary.get("status") == STATUS_PASS, f"run summary status is not {STATUS_PASS}")
    run_log = run_log_path.read_text(encoding="utf-8", errors="replace")
    input_summary = parse_input(input_path)
    max_step = int(summary.get("max_step", input_summary["max_step"]))
    require(max_step == input_summary["max_step"], "summary max_step does not match input max_step")
    final_plot_name = f"plt{max_step:05d}"
    header_final_path = run_dir / final_plot_name / "Header"
    header0 = parse_header(header0_path)
    header_final = parse_header(header_final_path)
    require(input_summary["max_step"] >= 100, "max_step must be at least 100 for sustained ignition evidence")
    require(input_summary["plot_int"] > 0, "plot_int must be positive")
    require("MPI initialized with 1 MPI processes" in run_log, "run log does not prove singleton MPI launch")
    require("CUDA initialized with 1 device" in run_log, "run log does not prove one CUDA device")
    require("Creating ReactorBase instance: ReactorCvode" in run_log, "ReactorCvode marker missing")
    require("Initializing CVODE:" in run_log, "CVODE initialization marker missing")
    require("H2 leak UserDefined EB STL files: count=3" in run_log, "multi-file STL pipe-rack marker missing")
    require("Applying H2 leak source:" in run_log, "H2 leak source marker missing")
    require(f"STEP [{max_step - 1}]" in run_log, f"run did not reach STEP [{max_step - 1}]")
    require("AMReX" in run_log and "finalized" in run_log.lower(), "AMReX did not finalize")
    hits = [line.strip() for line in run_log.splitlines() if FAILURE_RE.search(line)]
    require(not hits, f"solver failure markers found: {hits[:5]}")
    require(header_final["time"] > header0["time"], "plotfile time did not advance")

    plotfiles = sorted(p.name for p in run_dir.glob("plt[0-9][0-9][0-9][0-9][0-9]"))
    require("plt00000" in plotfiles and final_plot_name in plotfiles, "required plotfiles missing")
    reaction_history = summary.get("reaction_history")
    require(isinstance(reaction_history, list) and len(reaction_history) >= 4, "missing sustained reaction history")
    sustained_checks = summary.get("sustained_reaction_checks")
    require(isinstance(sustained_checks, dict), "missing sustained reaction checks")
    require(int(sustained_checks.get("sustained_output_count", 0)) >= 4, "too few sustained reaction output points")
    require(
        float(sustained_checks.get("final_y_h2o_max", 0.0))
        > float(sustained_checks.get("initial_y_h2o_max", 0.0)),
        "H2O did not grow",
    )
    require(float(sustained_checks.get("final_time", 0.0)) > 0.0, "final reaction time did not advance")
    evidence = [
        evidence_entry("run_log", run_log_path),
        evidence_entry("input", input_path),
        evidence_entry("plt00000_header", header0_path),
        evidence_entry(f"{final_plot_name}_header", header_final_path),
        evidence_entry("cube_obstacle_stl", run_dir / "codex_cube_block.stl"),
        evidence_entry("vertical_cylinder_obstacle_stl", run_dir / "codex_vertical_cylinder.stl"),
        evidence_entry("pipe_rack_obstacle_stl", run_dir / "codex_pipe_rack.stl"),
        evidence_entry("merged_pipe_rack_obstacles_stl", run_dir / "codex_merged_pipe_rack_obstacles.stl"),
        evidence_entry("run_summary", summary_path),
    ]
    if script_path.exists():
        evidence.append(evidence_entry("reproducible_smoke_script", script_path))

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS,
        "title": "H2 Pipe-Rack Direct Reacting Single-CUDA Evidence",
        "decision": "direct_engineering_pipe_rack_leak_obstacle_reacting_ignition_single_gpu_pass",
        "run_root": str(run_root),
        "run_dir": str(run_dir),
        "validated_capabilities": {
            "direct_engineering_obstacle_reacting_smoke": True,
            "sustained_reacting_fire_development": True,
            "pipe_rack_stl_obstacles": True,
            "cube_obstacle_stl": True,
            "vertical_cylinder_obstacle_stl": True,
            "multi_pipe_rack_stl": True,
            "h2_leak_source": True,
            "initial_flammable_cloud": True,
            "ignition_hotspot": True,
            "reactor_cvode": True,
            "cvode_gmres": True,
            "reacting_heat_release_variables": True,
            "single_gpu_cuda": True,
            "mpi_cuda_2rank_2device": False,
            "full_duration_fire_propagation": False,
            "calibrated_fire_or_blast_model": False,
        },
        "input_summary": input_summary,
        "run_log_checks": {
            "mpi_ranks": 1,
            "cuda_devices": 1,
            "reactor_marker": True,
            "cvode_marker": True,
            "amrex_finalized": True,
            "solver_failure_marker_count": 0,
        },
        "plotfile_checks": {
            "initial_time": header0["time"],
            "final_time": header_final["time"],
            "plotfiles": plotfiles,
            "variables": header_final["variables"],
            "required_reacting_fire_variables_present": True,
            "reaction_history": reaction_history,
            "sustained_reaction_checks": sustained_checks,
        },
        "limitations": [
            f"{input_summary['max_step']}-step single-GPU direct reacting sustained-fire case, not full-duration calibrated fire spread.",
            "Uses synthetic cube/cylinder/pipe-rack STL geometry, not real plant CAD.",
            "This gate proves the integrated engineering path starts, reacts, writes plotfiles, and finalizes cleanly on CUDA; it does not replace calibrated radiation/overpressure validation.",
        ],
        "evidence_files": evidence,
    }


def validate_report(report: dict[str, Any], check_hashes: bool = True) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "status is not PASS")
    caps = report.get("validated_capabilities")
    require(isinstance(caps, dict), "missing validated_capabilities")
    for name in (
        "direct_engineering_obstacle_reacting_smoke",
        "sustained_reacting_fire_development",
        "pipe_rack_stl_obstacles",
        "h2_leak_source",
        "initial_flammable_cloud",
        "ignition_hotspot",
        "reactor_cvode",
        "cvode_gmres",
        "reacting_heat_release_variables",
        "single_gpu_cuda",
    ):
        require(caps.get(name) is True, f"{name} not validated")
    checks = report.get("run_log_checks")
    require(isinstance(checks, dict), "missing run_log_checks")
    require(checks.get("mpi_ranks") == 1, "MPI rank check mismatch")
    require(checks.get("cuda_devices") == 1, "CUDA device check mismatch")
    plot = report.get("plotfile_checks")
    require(isinstance(plot, dict), "missing plotfile_checks")
    require(float(plot.get("final_time", 0.0)) > float(plot.get("initial_time", -1.0)), "time did not advance")
    checks = plot.get("sustained_reaction_checks")
    require(isinstance(checks, dict), "missing sustained reaction checks")
    require(int(checks.get("sustained_output_count", 0)) >= 4, "too few sustained reaction output points")
    require(float(checks.get("final_y_h2o_max", 0.0)) > float(checks.get("initial_y_h2o_max", 0.0)), "H2O did not grow")
    if check_hashes:
        for entry in report.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry["sha256"], f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    plot = report["plotfile_checks"]
    checks = plot["sustained_reaction_checks"]
    lines = [
        "# H2 Pipe-Rack Direct Reacting Single-CUDA Evidence",
        "",
        f"- Status: {report['status']}",
        f"- Decision: {report['decision']}",
        "- Scope: engineering h2_leak_3d with cube/cylinder/pipe-rack STL obstacles, H2 leak source, initial flammable cloud, ignition hotspot, and ReactorCvode chemistry.",
        "- Parallel path: singleton MPI launch on one CUDA device.",
        f"- Steps/plotfiles: {report['input_summary']['max_step']} steps; {', '.join(plot['plotfiles'])}",
        f"- Plotfile time advanced: {plot['initial_time']} -> {plot['final_time']}",
        "- Reacting variables present: HeatRelease, I_R(H2), I_R(O2), Y(H2), Y(O2), Y(H2O).",
        f"- Sustained reaction outputs: {checks['sustained_output_count']} points; final Y(H2O)_max={checks['final_y_h2o_max']}",
        "",
        "Limitation: this is a direct integrated CUDA sustained-fire gate, not a calibrated fire-spread certification.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    ap.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
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
        json_path = output_root / "pipe_rack_direct_reacting_cuda_report.json"
        md_path = output_root / "pipe_rack_direct_reacting_cuda_report.md"
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, md_path)
        validate_report(load_json(json_path))
        print(f"WROTE {json_path} status={report['status']}")
        return 0
    except ReportError as exc:
        print(f"pipe_rack_direct_reacting_cuda_report FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
