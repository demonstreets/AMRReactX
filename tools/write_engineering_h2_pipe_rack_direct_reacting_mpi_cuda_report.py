#!/usr/bin/env python3
"""Write/verify direct H2 pipe-rack reacting MPI+CUDA sustained evidence."""
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
STATUS_PASS = "PASS-H2-PIPE-RACK-DIRECT-REACTING-MPI-CUDA-SUSTAINED"
RUN_STATUS = "PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-SUSTAINED"
DEFAULT_OUTPUT_ROOT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_mpi_cuda_20260727"
)
DEFAULT_RUN_ROOT = Path("/tmp/codex_h2_pipe_rack_reacting_mpi_cuda_2rank_20260727_200step_v2")

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
    summary = load_json(summary_path)
    require(summary.get("status") == RUN_STATUS, f"run summary status is not {RUN_STATUS}")
    input_summary = parse_input(input_path)
    mpi_ranks = int(summary.get("mpi_ranks", 0))
    cuda_devices = int(summary.get("cuda_devices", 0))
    max_step = int(summary.get("max_step", 0))
    require(max_step == input_summary["max_step"], "summary max_step does not match input max_step")
    require(mpi_ranks >= 2, "MPI+CUDA report requires at least 2 MPI ranks")
    require(cuda_devices >= 2, "MPI+CUDA report requires at least 2 CUDA devices")
    require(max_step >= 200, "MPI+CUDA sustained report requires at least 200 steps")

    caps = summary.get("validated_capabilities", {})
    require(isinstance(caps, dict), "summary validated_capabilities missing")
    require(caps.get("mpi_cuda_parallel") is True, "summary does not validate MPI+CUDA parallel")
    require(caps.get("sustained_reacting_fire_development") is True, "summary does not validate sustained fire")
    checks = summary.get("sustained_reaction_checks", {})
    require(isinstance(checks, dict), "summary sustained checks missing")
    require(int(checks.get("sustained_output_count", 0)) >= 4, "too few sustained reaction outputs")
    require(float(checks.get("final_y_h2o_max", 0.0)) > 1.0e-4, "H2O product growth too small")

    run_log = run_log_path.read_text(encoding="utf-8", errors="replace")
    require(f"MPI initialized with {mpi_ranks} MPI processes" in run_log, "MPI rank marker missing")
    require(f"CUDA initialized with {cuda_devices} devices" in run_log, "CUDA device marker missing")
    require("Creating ReactorBase instance: ReactorCvode" in run_log, "ReactorCvode marker missing")
    require("Initializing CVODE:" in run_log, "CVODE marker missing")
    require(f"STEP [{max_step - 1}]" in run_log, "final step marker missing")
    require("AMReX" in run_log and "finalized" in run_log.lower(), "AMReX did not finalize")
    hits = [line.strip() for line in run_log.splitlines() if FAILURE_RE.search(line)]
    require(not hits, f"solver failure markers found: {hits[:5]}")

    header0 = parse_header(run_dir / "plt00000" / "Header")
    final_plot = f"plt{max_step:05d}"
    header_final_path = run_dir / final_plot / "Header"
    header_final = parse_header(header_final_path)
    require(header_final["time"] > header0["time"], "plotfile time did not advance")

    evidence = [
        evidence_entry("run_log", run_log_path),
        evidence_entry("run_summary", summary_path),
        evidence_entry("input", input_path),
        evidence_entry("plt00000_header", run_dir / "plt00000" / "Header"),
        evidence_entry(f"{final_plot}_header", header_final_path),
        evidence_entry("cube_obstacle_stl", run_dir / "codex_cube_block.stl"),
        evidence_entry("vertical_cylinder_obstacle_stl", run_dir / "codex_vertical_cylinder.stl"),
        evidence_entry("pipe_rack_obstacle_stl", run_dir / "codex_pipe_rack.stl"),
        evidence_entry("merged_pipe_rack_obstacles_stl", run_dir / "codex_merged_pipe_rack_obstacles.stl"),
        evidence_entry("reproducible_smoke_script", Path("tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh")),
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS,
        "title": "H2 Pipe-Rack Direct Reacting MPI+CUDA Sustained Evidence",
        "decision": "direct_engineering_pipe_rack_leak_obstacle_reacting_ignition_mpi_cuda_pass",
        "run_root": str(run_root),
        "run_dir": str(run_dir),
        "validated_capabilities": {
            "direct_engineering_obstacle_reacting_smoke": True,
            "sustained_reacting_fire_development": True,
            "pipe_rack_stl_obstacles": True,
            "h2_leak_source": True,
            "initial_flammable_cloud": True,
            "ignition_hotspot": True,
            "reactor_cvode": True,
            "cvode_gmres": True,
            "reacting_heat_release_variables": True,
            "mpi_cuda_parallel": True,
            "mpi_ranks": mpi_ranks,
            "cuda_devices": cuda_devices,
            "calibrated_fire_or_blast_model": False,
            "full_duration_fire_propagation": False,
        },
        "input_summary": input_summary,
        "run_log_checks": {
            "mpi_ranks": mpi_ranks,
            "cuda_devices": cuda_devices,
            "reactor_marker": True,
            "cvode_marker": True,
            "amrex_finalized": True,
            "solver_failure_marker_count": 0,
        },
        "plotfile_checks": {
            "initial_time": header0["time"],
            "final_time": header_final["time"],
            "plotfiles": summary.get("plotfiles", []),
            "variables": header_final["variables"],
            "reaction_history": summary.get("reaction_history", []),
            "sustained_reaction_checks": checks,
        },
        "limitations": [
            f"{input_summary['max_step']}-step MPI+CUDA sustained-fire gate, not a production GPU scaling curve.",
            "Synthetic cube/cylinder/pipe-rack STL geometry, not real plant CAD.",
            "Not calibrated radiation/overpressure validation.",
        ],
        "evidence_files": evidence,
    }


def validate_report(report: dict[str, Any], check_hashes: bool = True) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "status is not PASS")
    caps = report.get("validated_capabilities", {})
    require(caps.get("mpi_cuda_parallel") is True, "MPI+CUDA not validated")
    require(int(caps.get("mpi_ranks", 0)) >= 2, "MPI rank count too small")
    require(int(caps.get("cuda_devices", 0)) >= 2, "CUDA device count too small")
    plot = report.get("plotfile_checks", {})
    checks = plot.get("sustained_reaction_checks", {})
    require(int(checks.get("sustained_output_count", 0)) >= 4, "too few sustained reaction outputs")
    require(float(checks.get("final_y_h2o_max", 0.0)) > 1.0e-4, "H2O product growth too small")
    if check_hashes:
        for entry in report.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry["sha256"], f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    checks = report["plotfile_checks"]["sustained_reaction_checks"]
    lines = [
        "# H2 Pipe-Rack Direct Reacting MPI+CUDA Sustained Evidence",
        "",
        f"- Status: {report['status']}",
        f"- Grid/steps: {report['input_summary']['n_cell']}; {report['input_summary']['max_step']} steps",
        f"- MPI/CUDA: {report['run_log_checks']['mpi_ranks']} ranks, {report['run_log_checks']['cuda_devices']} CUDA devices",
        f"- Final time: {report['plotfile_checks']['final_time']}",
        f"- Sustained reaction outputs: {checks['sustained_output_count']}",
        f"- Final Y(H2O)_max: {checks['final_y_h2o_max']}",
        "",
        "Limitation: this is sustained integrated MPI+CUDA evidence, not calibrated production fire certification.",
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
        json_path = output_root / "pipe_rack_direct_reacting_mpi_cuda_report.json"
        md_path = output_root / "pipe_rack_direct_reacting_mpi_cuda_report.md"
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, md_path)
        validate_report(load_json(json_path))
        print(f"WROTE {json_path} status={report['status']}")
        return 0
    except ReportError as exc:
        print(f"pipe_rack_direct_reacting_mpi_cuda_report FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
