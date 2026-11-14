#!/usr/bin/env python3
"""Write or verify the academic gas-liquid detonation CUDA scout report."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


STATUS = "PASS-ACADEMIC-GAS-LIQUID-DETONATION-CUDA-SCOUT"
ROOT = Path("docs/codex_audit/evidence/academic_gas_liquid_detonation_cuda_scout_20260731")
REPORT = ROOT / "academic_gas_liquid_detonation_cuda_scout_report.json"
REPORT_MD = ROOT / "academic_gas_liquid_detonation_cuda_scout_report.md"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing required report: {path}")
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise TypeError(f"report is not a JSON object: {path}")
    return data


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


def check_run(name: str, run_dir: Path, *, mpi_ranks: int, cuda_devices: int) -> dict[str, Any]:
    run_log = require_file(run_dir / "run.log")
    input_path = require_file(run_dir / "inputs")
    exe = next(run_dir.glob("PeleC2d*.CUDA.ex"))
    plt0 = require_file(run_dir / "plt00000" / "Header")
    plt40 = require_file(run_dir / "plt00040" / "Header")
    job = require_file(run_dir / "plt00040" / "job_info")
    particle_header = require_file(run_dir / "plt00040" / "particles" / "Header")
    particle_tile_header = require_file(run_dir / "plt00040" / "particles" / "Level_0" / "Particle_H")

    run_text = run_log.read_text(errors="replace")
    failure_re = re.compile(
        r"(^|[^A-Za-z])(nan|inf)([^A-Za-z]|$)|Backtrace|Segmentation|SIGSEGV|"
        r"CUDA error|GPU last error:\s*(?!no error)|Abort|FAIL|error while loading",
        re.I,
    )
    hits = [line.strip() for line in run_text.splitlines() if failure_re.search(line)]
    if hits:
        raise RuntimeError(f"{name}: solver failure markers found: {hits[:5]}")

    required_markers = {
        f"CUDA initialized with {cuda_devices} device": "cuda device count",
        "Creating ReactorBase instance: ReactorCvode": "reacting CVODE solver",
    }
    if mpi_ranks > 1:
        required_markers[f"MPI initialized with {mpi_ranks} MPI processes"] = "mpi rank count"
    for marker, label in required_markers.items():
        if marker not in run_text:
            raise RuntimeError(f"{name}: missing {label} marker: {marker}")
    if "AMReX" not in run_text or "finalized" not in run_text.lower():
        raise RuntimeError(f"{name}: AMReX did not finalize")

    vars0, time0 = read_plot_header(plt0)
    vars40, time40 = read_plot_header(plt40)
    required_vars = {
        "density",
        "Temp",
        "pressure",
        "rho_NC7H16",
        "rho_O2",
        "rho_N2",
        "heatRelease",
        "spray_mass",
        "spray_temp",
        "spray_x_vel",
        "spray_rho_src",
        "spray_xmom_src",
        "spray_eng_src",
        "spray_rhoY_NC7H16_src",
    }
    missing = sorted(required_vars - set(vars40))
    if missing:
        raise RuntimeError(f"{name}: missing plot variables: {missing}")
    if not (math.isfinite(time0) and math.isfinite(time40) and time40 > time0):
        raise RuntimeError(f"{name}: plotfile time did not advance")

    job_text = job.read_text(errors="replace")
    if f"number of MPI processes: {mpi_ranks}" not in job_text:
        raise RuntimeError(f"{name}: job_info does not prove {mpi_ranks} MPI ranks")
    for needle in [
        'pelec.chem_integrator = "ReactorCvode"',
        "pelec.do_react = 1",
        "pelec.do_spray_particles = 1",
        "particles.mass_transfer = 1",
        "particles.mom_transfer = 1",
        "particles.use_breakup_model = KHRT",
        "cvode.solve_type = GMRES",
    ]:
        if needle not in job_text:
            raise RuntimeError(f"{name}: missing job_info marker: {needle}")
    input_text = input_path.read_text(errors="replace")
    if "max_step = 40" not in input_text or "stop_time = -1.0" not in input_text:
        raise RuntimeError(f"{name}: input does not prove forced 40-step run")

    data_files = sorted((run_dir / "plt00040" / "particles" / "Level_0").glob("DATA_*"))
    if not data_files:
        raise RuntimeError(f"{name}: missing particle DATA files")

    evidence = [
        ("run_log", run_log),
        ("input", input_path),
        ("executable", exe),
        ("plt00000_header", plt0),
        ("plt00040_header", plt40),
        ("plt00040_job_info", job),
        ("particle_header", particle_header),
        ("particle_tile_header", particle_tile_header),
        *[(f"particle_data_{idx}", path) for idx, path in enumerate(data_files)],
    ]
    return {
        "name": name,
        "status": "PASS",
        "run_dir": str(run_dir.resolve()),
        "mpi_ranks": mpi_ranks,
        "cuda_devices": cuda_devices,
        "max_step": 40,
        "initial_time": time0,
        "final_time": time40,
        "plot_variables": vars40,
        "particle_data_file_count": len(data_files),
        "evidence_files": [
            {"label": label, "path": str(path.resolve()), "sha256": sha(path)}
            for label, path in evidence
        ],
    }


def build_report() -> dict[str, Any]:
    single = check_run(
        "single_gpu_reacting_spray_detonation_40step",
        ROOT / "single_gpu_reacting_spray_detonation_40step",
        mpi_ranks=1,
        cuda_devices=1,
    )
    mpi_cuda = check_run(
        "mpi_cuda_reacting_spray_detonation_40step",
        ROOT / "mpi_cuda_reacting_spray_detonation_40step",
        mpi_ranks=2,
        cuda_devices=2,
    )
    build_logs = [
        require_file(ROOT / "build_cuda_sundials_home.log"),
        require_file(ROOT / "build_mpi_cuda.log"),
        require_file(ROOT / "ldd_cuda.log"),
        require_file(ROOT / "ldd_mpi_cuda.log"),
        require_file(ROOT / "single_gpu_launcher.log"),
        require_file(ROOT / "mpi_cuda_launcher.log"),
    ]
    return {
        "status": STATUS,
        "ready": True,
        "scope": "heptane-air droplet/spray reacting detonation CUDA scout",
        "case": "academic_shock_droplet_reacting_spray_detonation_cuda_scout",
        "run_root": str(ROOT.resolve()),
        "runs": [single, mpi_cuda],
        "summary": {
            "academic_gas_liquid_detonation_cuda_scout_ready": True,
            "single_gpu_reacting_spray_ready": True,
            "mpi_cuda_reacting_spray_ready": True,
            "max_mpi_ranks": 2,
            "max_cuda_devices": 2,
            "max_step": 40,
            "reaction_solver_marker_present": True,
            "spray_particle_output_present": True,
            "spray_source_terms_present": True,
            "time_advanced": True,
        },
        "validated_capabilities": {
            "gas_liquid_reacting_spray_shock_detonation_scout": True,
            "pelec_spray_particles": True,
            "heptane_air_reaction": True,
            "evaporation_mass_momentum_source_terms": True,
            "khrt_breakup_configuration": True,
            "single_gpu_cuda": True,
            "mpi_cuda_2rank_2device": True,
        },
        "limitations": [
            "Scout gate only: 40-step reduced-resolution run, not a long-duration two-phase detonation validation.",
            "This complements, but does not replace, the existing CPU gas-liquid detonation certification and budget evidence.",
            "The case proves CUDA/MPI+CUDA runtime viability for reacting spray physics; production-grade two-phase detonation still needs longer stability and quantitative validation windows.",
        ],
        "build_and_launcher_evidence": [
            {"label": path.name, "path": str(path.resolve()), "sha256": sha(path)}
            for path in build_logs
        ],
        "evidence_hash": sha(ROOT / "mpi_cuda_reacting_spray_detonation_40step" / "run.log"),
    }


def verify_report(path: Path) -> None:
    expected = build_report()
    actual = load_json(path)
    if actual.get("status") != STATUS:
        raise SystemExit(f"status is not pass: {actual.get('status')}")
    if actual.get("ready") is not True:
        raise SystemExit("ready flag is not true")
    summary = actual.get("summary", {})
    for key in [
        "academic_gas_liquid_detonation_cuda_scout_ready",
        "single_gpu_reacting_spray_ready",
        "mpi_cuda_reacting_spray_ready",
        "reaction_solver_marker_present",
        "spray_particle_output_present",
        "spray_source_terms_present",
        "time_advanced",
    ]:
        if summary.get(key) is not True:
            raise SystemExit(f"summary.{key} is not true")
    for key in ["max_mpi_ranks", "max_cuda_devices", "max_step"]:
        if summary.get(key) != expected["summary"][key]:
            raise SystemExit(f"summary.{key} drifted: {summary.get(key)}")
    actual_runs = {run.get("name"): run for run in actual.get("runs", [])}
    expected_runs = {run.get("name"): run for run in expected.get("runs", [])}
    if set(actual_runs) != set(expected_runs):
        raise SystemExit("run set drifted")
    for name, run in expected_runs.items():
        actual_run = actual_runs[name]
        if actual_run.get("status") != "PASS":
            raise SystemExit(f"run not PASS: {name}")
        actual_files = {entry.get("label"): entry for entry in actual_run.get("evidence_files", [])}
        for expected_entry in run["evidence_files"]:
            label = expected_entry["label"]
            actual_entry = actual_files.get(label)
            if actual_entry is None:
                raise SystemExit(f"{name}: missing evidence entry {label}")
            if actual_entry.get("sha256") != expected_entry["sha256"]:
                raise SystemExit(f"{name}: evidence hash drifted for {label}")
    print(f"academic_gas_liquid_detonation_cuda_scout VERIFY-PASS json={path} status={actual.get('status')}")


def write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# Academic gas-liquid detonation CUDA scout report",
        "",
        f"- status: {report['status']}",
        f"- case: {report['case']}",
        f"- run_root: {report['run_root']}",
        "",
        "## Runs",
        "",
    ]
    for run in report["runs"]:
        lines.append(
            f"- {run['name']}: {run['mpi_ranks']} MPI ranks, "
            f"{run['cuda_devices']} CUDA devices, max_step={run['max_step']}, "
            f"final_time={run['final_time']:.8e}"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.output == REPORT:
        write_markdown(report)
    print(f"wrote {args.output} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
