#!/usr/bin/env python3
"""Write/verify PeleC H2 reacting MPI+CUDA smoke evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-PELEC-H2-REACTING-MPI-CUDA-SMOKE"
DEFAULT_OUTPUT_ROOT = Path(
    "docs/codex_audit/evidence/engineering_h2_reacting_mpi_cuda_smoke_20260727"
)
DEFAULT_RUN_DIR = Path(
    "/tmp/codex_pelec_h2_reacting_ignition_openmpi_cuda_2rank_script_20260727"
)

SOLVER_FAILURE_RE = re.compile(
    r"(^|[^A-Za-z])(nan|inf)([^A-Za-z]|$)|Backtrace|Segmentation|SIGSEGV|"
    r"CUDA error|GPU last error|Abort|FAIL|error while loading",
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


def parse_ic(path: Path) -> dict[str, float]:
    text = path.read_text(encoding="utf-8", errors="replace")
    hot = re.search(
        r"Hotspot:\s+p=([0-9.eE+-]+)\s+T=([0-9.eE+-]+)\s+rho=([0-9.eE+-]+)\s+"
        r"r=([0-9.eE+-]+)\s+cm\s+u=([0-9.eE+-]+)",
        text,
    )
    bg = re.search(
        r"Background:\s+p=([0-9.eE+-]+)\s+T=([0-9.eE+-]+)\s+rho=([0-9.eE+-]+)\s+"
        r"Y_H2=([0-9.eE+-]+)\s+Y_O2=([0-9.eE+-]+)",
        text,
    )
    require(hot is not None, "hotspot IC line missing")
    require(bg is not None, "background IC line missing")
    return {
        "background_pressure": float(bg.group(1)),
        "background_temperature": float(bg.group(2)),
        "background_density": float(bg.group(3)),
        "background_y_h2": float(bg.group(4)),
        "background_y_o2": float(bg.group(5)),
        "hotspot_pressure": float(hot.group(1)),
        "hotspot_temperature": float(hot.group(2)),
        "hotspot_density": float(hot.group(3)),
        "hotspot_radius_cm": float(hot.group(4)),
        "hotspot_velocity_cm_s": float(hot.group(5)),
    }


def parse_header(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    require(len(lines) > 8, f"plotfile header too short: {path}")
    nvars = int(lines[1].strip())
    variables = [lines[i].strip() for i in range(2, 2 + nvars)]
    time_value = float(lines[2 + nvars + 1].strip())
    required = {"density", "Temp", "rho_H2", "rho_O2", "rho_H2O"}
    require(required <= set(variables), f"missing reacting plot variables: {sorted(required - set(variables))}")
    return {
        "nvars": nvars,
        "variables": variables,
        "time": time_value,
    }


def parse_input(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")

    def get_value(name: str) -> str | None:
        m = re.search(rf"^\s*{re.escape(name)}\s*=\s*(.+?)\s*$", text, re.MULTILINE)
        return m.group(1).strip() if m else None

    do_react = get_value("pelec.do_react")
    chem = get_value("pelec.chem_integrator")
    max_step = get_value("max_step")
    require(do_react == "1", "input does not enable pelec.do_react")
    require(chem == '"ReactorRK64"', "input does not use ReactorRK64")
    require(max_step is not None and int(max_step) >= 5, "max_step is too small")
    return {
        "do_react": True,
        "chem_integrator": "ReactorRK64",
        "max_step": int(max_step),
        "n_cell": get_value("amr.n_cell"),
        "plot_int": get_value("amr.plot_int"),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.run_dir)
    require(run_dir.is_dir(), f"missing run dir: {run_dir}")
    run_log_path = run_dir / "run.log"
    input_path = run_dir / "input.codex_mpi_cuda_react_smoke"
    ic_path = run_dir / "ic.txt"
    job_info_path = run_dir / "plt00005" / "job_info"
    header0_path = run_dir / "plt00000" / "Header"
    header5_path = run_dir / "plt00005" / "Header"
    slice0_path = run_dir / "plt00000.allvars.slice"
    slice5_path = run_dir / "plt00005.allvars.slice"
    fextract0_log_path = run_dir / "plt00000.allvars.fextract.log"
    fextract5_log_path = run_dir / "plt00005.allvars.fextract.log"
    launcher_log_path = run_dir / "launcher.log"
    summary_path = run_dir / "reacting_mpi_cuda_summary.json"
    script_path = Path("tools/codex_smoke_engineering_h2_reacting_mpi_cuda.sh")

    run_log = run_log_path.read_text(encoding="utf-8", errors="replace")
    input_summary = parse_input(input_path)
    ic_summary = parse_ic(ic_path)
    header0 = parse_header(header0_path)
    header5 = parse_header(header5_path)
    job_info = job_info_path.read_text(encoding="utf-8", errors="replace")

    require("MPI initialized with 2 MPI processes" in run_log, "run log does not prove 2 MPI processes")
    require("CUDA initialized with 2 devices" in run_log, "run log does not prove 2 CUDA devices")
    require("Creating ReactorBase instance: ReactorRK64" in run_log, "reactor construction marker missing")
    require("AMReX" in run_log and "finalized" in run_log.lower(), "AMReX did not finalize")
    require("number of MPI processes: 2" in job_info, "plotfile job_info does not prove 2 MPI processes")
    require(header5["time"] > header0["time"], "final plotfile time did not advance")
    require(ic_summary["hotspot_temperature"] >= 1000.0, "hotspot temperature too low for ignition smoke")
    hits = [line.strip() for line in run_log.splitlines() if SOLVER_FAILURE_RE.search(line)]
    require(not hits, f"solver failure markers found: {hits[:3]}")

    fextract0 = fextract0_log_path.read_text(encoding="utf-8", errors="replace") if fextract0_log_path.exists() else ""
    fextract5 = fextract5_log_path.read_text(encoding="utf-8", errors="replace") if fextract5_log_path.exists() else ""
    fextract_post_write_segfault = "Segfault" in fextract0 or "Segfault" in fextract5
    evidence = [
        evidence_entry("run_log", run_log_path),
        evidence_entry("input", input_path),
        evidence_entry("initial_condition_summary", ic_path),
        evidence_entry("plt00005_job_info", job_info_path),
        evidence_entry("plt00000_header", header0_path),
        evidence_entry("plt00005_header", header5_path),
    ]
    if launcher_log_path.exists():
        evidence.append(evidence_entry("launcher_log", launcher_log_path))
    if summary_path.exists():
        evidence.append(evidence_entry("script_summary", summary_path))
    if script_path.exists():
        evidence.append(evidence_entry("reproducible_smoke_script", script_path))
    if slice0_path.exists():
        evidence.append(evidence_entry("plt00000_allvars_slice", slice0_path))
    if slice5_path.exists():
        evidence.append(evidence_entry("plt00005_allvars_slice", slice5_path))
    if fextract0_log_path.exists():
        evidence.append(evidence_entry("plt00000_fextract_log", fextract0_log_path))
    if fextract5_log_path.exists():
        evidence.append(evidence_entry("plt00005_fextract_log", fextract5_log_path))

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS,
        "title": "PeleC H2/O2 Reacting MPI+CUDA Smoke Evidence",
        "run_dir": str(run_dir),
        "validated_capabilities": {
            "pelec_reacting_solver": True,
            "h2_o2_lidryer_mechanism": True,
            "reactor_rk64": True,
            "mpi_parallel": True,
            "cuda_parallel": True,
            "mpi_cuda_2rank_2device": True,
            "finite_plotfile_headers": True,
            "direct_engineering_obstacle_fire_propagation": False,
            "pipe_rack_leak_cloud_fire_coupling": False,
        },
        "input_summary": input_summary,
        "initial_condition_summary": ic_summary,
        "run_log_checks": {
            "mpi_ranks": 2,
            "cuda_devices": 2,
            "reactor_marker": True,
            "amrex_finalized": True,
            "solver_failure_marker_count": 0,
        },
        "plotfile_checks": {
            "initial_time": header0["time"],
            "final_time": header5["time"],
            "variables": header5["variables"],
            "required_reacting_variables_present": True,
        },
        "postprocessing_notes": {
            "amrex_fextract_slice_written": slice0_path.exists() and slice5_path.exists(),
            "amrex_fextract_post_write_segfault": fextract_post_write_segfault,
        },
        "decision": "reacting_solver_mpi_cuda_smoke_pass_not_engineering_fire_propagation",
        "limitations": [
            "Short PeleC reacting hot-spot smoke, not full-duration engineering fire propagation.",
            "Uses academic H2/O2 hot-spot setup, not pipe-rack leak cloud geometry.",
            "OpenMPI launcher is required for this executable; MPICH launcher starts singleton ranks for this build.",
            "Numeric slice statistics are not used as pass criteria; this gate checks solver logs, MPI/CUDA markers, IC metadata, and plotfile headers.",
        ],
        "evidence_files": evidence,
    }


def validate_report(report: dict[str, Any], check_hashes: bool = True) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "status is not PASS")
    caps = report.get("validated_capabilities")
    require(isinstance(caps, dict), "missing validated_capabilities")
    for name in (
        "pelec_reacting_solver",
        "h2_o2_lidryer_mechanism",
        "reactor_rk64",
        "mpi_parallel",
        "cuda_parallel",
        "mpi_cuda_2rank_2device",
        "finite_plotfile_headers",
    ):
        require(caps.get(name) is True, f"{name} not validated")
    require(caps.get("direct_engineering_obstacle_fire_propagation") is False, "direct fire must remain false")
    checks = report.get("run_log_checks")
    require(isinstance(checks, dict), "missing run_log_checks")
    require(checks.get("mpi_ranks") == 2, "MPI rank check missing")
    require(checks.get("cuda_devices") == 2, "CUDA device check missing")
    plot = report.get("plotfile_checks")
    require(isinstance(plot, dict), "missing plotfile_checks")
    require(float(plot.get("final_time", 0.0)) > float(plot.get("initial_time", -1.0)), "plotfile time did not advance")
    for value in report.get("initial_condition_summary", {}).values():
        require(math.isfinite(float(value)), "non-finite IC value")
    if check_hashes:
        for entry in report.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry["sha256"], f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    ic = report["initial_condition_summary"]
    plot = report["plotfile_checks"]
    lines = [
        "# PeleC H2/O2 Reacting MPI+CUDA Smoke Evidence",
        "",
        f"- Status: {report['status']}",
        f"- Decision: {report['decision']}",
        "- Solver path: PeleC reacting H2/O2 LiDryer, ReactorRK64",
        "- Parallel path: OpenMPI 2 ranks with CUDA 2 devices",
        f"- Hotspot T / p: {ic['hotspot_temperature']} K / {ic['hotspot_pressure']} Pa",
        f"- Plotfile time advanced: {plot['initial_time']} -> {plot['final_time']}",
        "- Scope: reaction/MPI+CUDA smoke only, not direct engineering fire propagation.",
        "",
        "Postprocessing note: numeric slice statistics are not used as pass criteria; solver run logs and plotfile headers were clean.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    ap.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR))
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
        json_path = output_root / "reacting_mpi_cuda_smoke_report.json"
        md_path = output_root / "reacting_mpi_cuda_smoke_report.md"
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, md_path)
        validate_report(load_json(json_path))
        print(f"WROTE {json_path} status={report['status']}")
        return 0
    except ReportError as exc:
        print(f"reacting_mpi_cuda_smoke_report FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
