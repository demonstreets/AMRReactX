#!/usr/bin/env python3
"""Write or verify the academic gas-liquid detonation MPI+CUDA extended report."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


STATUS = "PASS-ACADEMIC-GAS-LIQUID-DETONATION-MPI-CUDA-EXTENDED"
ROOT = Path("docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_extended_20260803")
REPORT = ROOT / "academic_gas_liquid_detonation_mpi_cuda_extended_report.json"
REPORT_MD = ROOT / "academic_gas_liquid_detonation_mpi_cuda_extended_report.md"
RUN_DIR = ROOT / "mpi_cuda_reacting_spray_detonation_1000step"


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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing required report: {path}")
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise TypeError(f"report is not a JSON object: {path}")
    return data


def read_plot_header(path: Path) -> tuple[list[str], float, int]:
    lines = path.read_text(errors="replace").splitlines()
    nvars = int(lines[1].strip())
    variables = [lines[i].strip() for i in range(2, 2 + nvars)]
    time_value = float(lines[2 + nvars + 1].strip())
    step_value = -1
    for raw in reversed(lines[:90]):
        stripped = raw.strip()
        if stripped.isdigit():
            step_value = int(stripped)
            break
    return variables, time_value, step_value


def build_report() -> dict[str, Any]:
    run_log = require_file(RUN_DIR / "run.log")
    launcher_log = require_file(ROOT / "mpi_cuda_launcher.log")
    input_path = require_file(RUN_DIR / "inputs")
    exe = require_file(RUN_DIR / "PeleC2d.gnu.MPI.CUDA.ex")
    plt0_header = require_file(RUN_DIR / "plt00000" / "Header")
    plt1000_header = require_file(RUN_DIR / "plt01000" / "Header")
    plt1000_job = require_file(RUN_DIR / "plt01000" / "job_info")
    particle_header = require_file(RUN_DIR / "plt01000" / "particles" / "Header")
    particle_tile_header = require_file(RUN_DIR / "plt01000" / "particles" / "Level_0" / "Particle_H")

    expected_plots = ["plt00000", "plt00200", "plt00400", "plt00600", "plt00800", "plt01000"]
    missing_plots = [name for name in expected_plots if not (RUN_DIR / name / "Header").is_file()]
    if missing_plots:
        raise RuntimeError(f"missing sustained plotfiles: {missing_plots}")

    run_text = run_log.read_text(errors="replace")
    failure_re = re.compile(
        r"(^|[^A-Za-z])(nan|inf)([^A-Za-z]|$)|Backtrace|Segmentation|SIGSEGV|"
        r"CUDA error|GPU last error:\s*(?!no error)|Abort|FAIL|error while loading|"
        r"SUNDIALS_ERROR|CVode.*failed|cvode.*failed",
        re.I,
    )
    hits = [line.strip() for line in run_text.splitlines() if failure_re.search(line)]
    if hits:
        raise RuntimeError(f"solver failure markers found: {hits[:5]}")
    for marker in [
        "MPI initialized with 2 MPI processes",
        "CUDA initialized with 2 devices",
        "Creating ReactorBase instance: ReactorCvode",
        "STEP = 1000",
    ]:
        if marker not in run_text:
            raise RuntimeError(f"missing run marker: {marker}")
    if "AMReX" not in run_text or "finalized" not in run_text.lower():
        raise RuntimeError("AMReX did not finalize")

    vars0, time0, step0 = read_plot_header(plt0_header)
    vars1000, time1000, step1000 = read_plot_header(plt1000_header)
    required_vars = {
        "density",
        "Temp",
        "pressure",
        "rho_NC7H16",
        "rho_O2",
        "rho_N2",
        "rho_omega_NC7H16",
        "rho_omega_O2",
        "rho_omega_N2",
        "heatRelease",
        "spray_mass",
        "spray_density",
        "spray_temp",
        "spray_x_vel",
        "spray_rho_src",
        "spray_xmom_src",
        "spray_ymom_src",
        "spray_eng_src",
        "spray_rhoY_NC7H16_src",
    }
    missing_vars = sorted(required_vars - set(vars1000))
    if missing_vars:
        raise RuntimeError(f"missing final plot variables: {missing_vars}")
    if not (math.isfinite(time0) and math.isfinite(time1000) and time1000 > time0):
        raise RuntimeError("plotfile time did not advance")
    if step1000 not in {-1, 1000}:
        raise RuntimeError(f"final plot step is not 1000: {step1000}")

    job_text = plt1000_job.read_text(errors="replace")
    for needle in [
        "number of MPI processes: 2",
        "max_step = 1000",
        "amr.plot_int = 200",
        'pelec.chem_integrator = "ReactorCvode"',
        "pelec.do_react = 1",
        "pelec.do_spray_particles = 1",
        "particles.mass_transfer = 1",
        "particles.mom_transfer = 1",
        "particles.use_breakup_model = KHRT",
        "cvode.solve_type = GMRES",
    ]:
        if needle not in job_text:
            raise RuntimeError(f"missing job_info marker: {needle}")
    input_text = input_path.read_text(errors="replace")
    if "max_step = 1000" not in input_text or "stop_time = -1.0" not in input_text:
        raise RuntimeError("input does not prove forced 1000-step run")

    data_files = sorted((RUN_DIR / "plt01000" / "particles" / "Level_0").glob("DATA_*"))
    if not data_files:
        raise RuntimeError("missing final particle DATA files")

    evidence = [
        ("run_log", run_log),
        ("launcher_log", launcher_log),
        ("input", input_path),
        ("executable", exe),
        ("plt00000_header", plt0_header),
        ("plt01000_header", plt1000_header),
        ("plt01000_job_info", plt1000_job),
        ("particle_header", particle_header),
        ("particle_tile_header", particle_tile_header),
        *[(f"particle_data_{idx}", path) for idx, path in enumerate(data_files)],
    ]
    return {
        "status": STATUS,
        "ready": True,
        "scope": "1000-step heptane-air droplet/spray reacting detonation MPI+CUDA extended stability gate",
        "case": "academic_shock_droplet_reacting_spray_detonation_mpi_cuda_1000step",
        "run_root": str(ROOT.resolve()),
        "run_dir": str(RUN_DIR.resolve()),
        "mpi_ranks": 2,
        "cuda_devices": 2,
        "max_step": 1000,
        "plot_interval": 200,
        "plotfile_count": len(expected_plots),
        "initial_time": time0,
        "final_time": time1000,
        "final_plot_step": step1000,
        "particle_data_file_count": len(data_files),
        "plot_variables": vars1000,
        "summary": {
            "academic_gas_liquid_detonation_mpi_cuda_extended_ready": True,
            "mpi_cuda_reacting_spray_1000step_ready": True,
            "mpi_ranks": 2,
            "cuda_devices": 2,
            "max_step": 1000,
            "plot_interval": 200,
            "plotfile_count": len(expected_plots),
            "time_advanced": True,
            "reaction_solver_marker_present": True,
            "amrex_finalized": True,
            "spray_particle_output_present": True,
            "spray_source_terms_present": True,
            "final_time": time1000,
        },
        "validated_capabilities": {
            "gas_liquid_reacting_spray_shock_detonation_extended_window": True,
            "pelec_spray_particles": True,
            "heptane_air_reaction": True,
            "evaporation_mass_momentum_energy_source_terms": True,
            "khrt_breakup_configuration": True,
            "mpi_cuda_2rank_2device": True,
            "sustained_1000step_execution": True,
        },
        "limitations": [
            "Reduced-resolution 1000-step stability gate; not a grid-converged quantitative two-phase detonation validation.",
            "This strengthens the 300-step MPI+CUDA long gate and the 40-step scout, but external validation and grid studies remain separate strict-scope work.",
        ],
        "evidence_files": [
            {"label": label, "path": str(path.resolve()), "sha256": sha(path)}
            for label, path in evidence
        ],
        "evidence_hash": sha(run_log),
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
        "academic_gas_liquid_detonation_mpi_cuda_extended_ready",
        "mpi_cuda_reacting_spray_1000step_ready",
        "time_advanced",
        "reaction_solver_marker_present",
        "amrex_finalized",
        "spray_particle_output_present",
        "spray_source_terms_present",
    ]:
        if summary.get(key) is not True:
            raise SystemExit(f"summary.{key} is not true")
    for key in ["mpi_ranks", "cuda_devices", "max_step", "plot_interval", "plotfile_count"]:
        if summary.get(key) != expected["summary"][key]:
            raise SystemExit(f"summary.{key} drifted: {summary.get(key)}")
    actual_files = {entry.get("label"): entry for entry in actual.get("evidence_files", [])}
    for expected_entry in expected["evidence_files"]:
        label = expected_entry["label"]
        actual_entry = actual_files.get(label)
        if actual_entry is None:
            raise SystemExit(f"missing evidence entry: {label}")
        if actual_entry.get("sha256") != expected_entry["sha256"]:
            raise SystemExit(f"evidence hash drifted for {label}")
    print(f"academic_gas_liquid_detonation_mpi_cuda_extended VERIFY-PASS json={path} status={actual.get('status')}")


def write_markdown(report: dict[str, Any]) -> None:
    REPORT_MD.write_text(
        "# Academic gas-liquid detonation MPI+CUDA extended report\n\n"
        f"- status: {report['status']}\n"
        f"- case: {report['case']}\n"
        f"- mpi_ranks: {report['mpi_ranks']}\n"
        f"- cuda_devices: {report['cuda_devices']}\n"
        f"- max_step: {report['max_step']}\n"
        f"- plot_interval: {report['plot_interval']}\n"
        f"- final_time: {report['final_time']:.8e}\n"
        f"- run_dir: {report['run_dir']}\n",
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
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.output == REPORT:
        write_markdown(report)
    print(f"wrote {args.output} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
