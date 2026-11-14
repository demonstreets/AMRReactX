#!/usr/bin/env python3
"""Write or verify the academic gas detonation single-CUDA report."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from cfd_evidence_checks import reacting_pair_metrics


STATUS = "PASS-ACADEMIC-GAS-DETONATION-SINGLE-CUDA"
ROOT = Path("docs/codex_audit/evidence/academic_gas_detonation_single_cuda_20260803")
REPORT = ROOT / "academic_gas_detonation_single_cuda_report.json"
REPORT_MD = ROOT / "academic_gas_detonation_single_cuda_report.md"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"missing evidence file: {path}")
    return path


def read_plot_header(path: Path) -> tuple[list[str], float]:
    lines = path.read_text(errors="replace").splitlines()
    nvars = int(lines[1].strip())
    variables = [lines[i].strip() for i in range(2, 2 + nvars)]
    time_value = float(lines[2 + nvars + 1].strip())
    return variables, time_value


def build_report() -> dict[str, Any]:
    run_dir = ROOT / "run"
    run_log = require_file(ROOT / "run.log")
    launcher_log = require_file(ROOT / "launcher.log")
    input_path = require_file(run_dir / "input.codex_academic_gas_detonation_single_cuda")
    source_input = require_file(run_dir / "source_input.codex_academic_bench2gpu_detonation_mpi_cuda")
    ic_path = require_file(run_dir / "ic.txt")
    exe_path = require_file(run_dir / "PeleC3d.gnu.MPI.CUDA.ex")
    plt0_header = require_file(run_dir / "plt00000" / "Header")
    plt40_header = require_file(run_dir / "plt00040" / "Header")
    plt40_job = require_file(run_dir / "plt00040" / "job_info")

    run_text = run_log.read_text(errors="replace")
    failure_re = re.compile(
        r"(^|[^A-Za-z])(nan|inf)([^A-Za-z]|$)|Backtrace|Segmentation|SIGSEGV|"
        r"CUDA error|GPU last error:\s*(?!no error)|Abort|FAIL|error while loading",
        re.I,
    )
    failure_hits = [line.strip() for line in run_text.splitlines() if failure_re.search(line)]
    if failure_hits:
        raise RuntimeError(f"solver failure markers found: {failure_hits[:5]}")

    markers = {
        "mpi_1rank": "MPI initialized with 1 MPI processes" in run_text,
        "cuda_1device": (
            "CUDA initialized with 1 device." in run_text
            or "CUDA initialized with 1 devices" in run_text
        ),
        "reactor_rk64": "Creating ReactorBase instance: ReactorRK64" in run_text,
        "amrex_finalized": "AMReX" in run_text and "finalized" in run_text.lower(),
    }
    missing_markers = sorted(name for name, present in markers.items() if not present)
    if missing_markers:
        raise RuntimeError(f"missing runtime markers: {missing_markers}")

    vars0, time0 = read_plot_header(plt0_header)
    vars40, time40 = read_plot_header(plt40_header)
    required_vars = {
        "density",
        "Temp",
        "rho_H2",
        "rho_O2",
        "rho_H2O",
        "x_velocity",
        "y_velocity",
        "z_velocity",
    }
    missing_vars = sorted(required_vars - set(vars40))
    if missing_vars:
        raise RuntimeError(f"missing plot variables: {missing_vars}")
    if not (math.isfinite(time0) and math.isfinite(time40) and time40 > time0):
        raise RuntimeError("plotfile time did not advance")

    job_text = plt40_job.read_text(errors="replace")
    if "number of MPI processes: 1" not in job_text:
        raise RuntimeError("job_info does not prove one MPI rank")
    input_text = input_path.read_text(errors="replace")
    if "max_step = 40" not in input_text or "stop_time = -1.0" not in input_text:
        raise RuntimeError("input does not prove forced 40-step run")
    if "Hotspot Detonation IC" not in ic_path.read_text(errors="replace"):
        raise RuntimeError("detonation hotspot IC marker missing")

    physics_metrics = reacting_pair_metrics(run_dir / "plt00000", run_dir / "plt00040")

    evidence = [
        ("run_log", run_log),
        ("launcher_log", launcher_log),
        ("input", input_path),
        ("source_input", source_input),
        ("initial_condition_summary", ic_path),
        ("plt00000_header", plt0_header),
        ("plt00040_header", plt40_header),
        ("plt00040_job_info", plt40_job),
        ("reused_executable", exe_path),
    ]
    return {
        "status": STATUS,
        "physics_metrics": physics_metrics,
        "detonation_propagation_verified": False,
        "ready": True,
        "case": "academic_bench2gpu_hotspot_lidryer_detonation_single_cuda",
        "scope": "gas-phase H2/O2 detonation single-CUDA runtime gate",
        "run_root": str(ROOT.resolve()),
        "mpi_launcher": "OpenMPI mpirun",
        "mpi_ranks": 1,
        "cuda_devices": 1,
        "max_step": 40,
        "initial_time": time0,
        "final_time": time40,
        "plot_variables": vars40,
        "validated_capabilities": {
            "gas_phase_detonation_hotspot": True,
            "pelec_reacting_solver": True,
            "h2_o2_lidryer_mechanism": True,
            "single_mpi_rank": True,
            "single_cuda_device": True,
            "single_gpu_reacting_detonation_runtime": True,
        },
        "summary": {
            "academic_gas_detonation_single_cuda_ready": True,
            "mpi_ranks": 1,
            "cuda_devices": 1,
            "max_step": 40,
            "time_advanced": True,
            "reaction_solver_marker_present": markers["reactor_rk64"],
            "amrex_finalized": markers["amrex_finalized"],
            "critical_plot_variables_present": True,
            "initial_time": time0,
            "final_time": time40,
        },
        "limitations": [
            "Raw species conversion is required; this short runtime gate does not certify sustained detonation or cellular structure.",
            "40-step academic gas detonation single-CUDA runtime gate; not a full grid-convergence study.",
            "Hotspot detonation initialization is used as a robust GPU execution and reacting-flow stability gate.",
        ],
        "evidence_files": [
            {"label": label, "path": str(path.resolve()), "sha256": sha(path)}
            for label, path in evidence
        ],
        "evidence_hash": sha(run_log),
    }


def verify_report(path: Path) -> None:
    expected = build_report()
    actual = json.loads(path.read_text(encoding="utf-8"))
    if actual.get("status") != STATUS:
        raise SystemExit(f"status is not pass: {actual.get('status')}")
    if actual.get("ready") is not True:
        raise SystemExit("ready flag is not true")
    summary = actual.get("summary", {})
    if summary.get("academic_gas_detonation_single_cuda_ready") is not True:
        raise SystemExit("summary ready flag is not true")
    for key in ["mpi_ranks", "cuda_devices", "max_step"]:
        if summary.get(key) != expected["summary"][key]:
            raise SystemExit(f"summary.{key} drifted: {summary.get(key)}")
    for key in ["time_advanced", "reaction_solver_marker_present", "amrex_finalized", "critical_plot_variables_present"]:
        if summary.get(key) is not True:
            raise SystemExit(f"summary.{key} is not true")
    actual_files = {entry.get("label"): entry for entry in actual.get("evidence_files", [])}
    for expected_entry in expected["evidence_files"]:
        label = expected_entry["label"]
        actual_entry = actual_files.get(label)
        if actual_entry is None:
            raise SystemExit(f"missing evidence entry: {label}")
        if actual_entry.get("sha256") != expected_entry["sha256"]:
            raise SystemExit(f"evidence hash drifted for {label}")
    print(f"academic_gas_detonation_single_cuda VERIFY-PASS json={path} status={actual.get('status')}")


def write_markdown(report: dict[str, Any]) -> None:
    REPORT_MD.write_text(
        "# Academic gas detonation single-CUDA report\n\n"
        f"- status: {report['status']}\n"
        f"- case: {report['case']}\n"
        f"- mpi_ranks: {report['mpi_ranks']}\n"
        f"- cuda_devices: {report['cuda_devices']}\n"
        f"- max_step: {report['max_step']}\n"
        f"- final_time: {report['final_time']:.8e}\n"
        f"- run_root: {report['run_root']}\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=REPORT)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()
    if args.verify_json:
        verify_report(args.verify_json)
        return 0
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.output == REPORT:
        write_markdown(report)
    print(f"wrote {args.output} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
