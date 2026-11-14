#!/usr/bin/env python3
"""Write/verify CPU/MPI vs single-CUDA delayed-ignition parity evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-PIPE-RACK-DELAYED-IGNITION-CPU-GPU-PARITY"
DEFAULT_ROOT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cross_platform_20260805"
)
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_h2_pipe_rack_delayed_ignition_cross_platform_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_h2_pipe_rack_delayed_ignition_cross_platform_report.md"
DEFAULT_CUDA_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cuda_20260805/"
    "engineering_h2_pipe_rack_delayed_ignition_cuda_report.json"
)
DEFAULT_MPI_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_mpi_20260805/"
    "engineering_h2_pipe_rack_delayed_ignition_mpi_report.json"
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


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"JSON report is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def nested(report: dict[str, Any], *keys: str) -> Any:
    value: Any = report
    for key in keys:
        require(isinstance(value, dict), f"missing nested key {'.'.join(keys)}")
        require(key in value, f"missing nested key {'.'.join(keys)}")
        value = value[key]
    return value


def rel_diff(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1.0e-300)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    cuda_path = Path(args.cuda_report)
    mpi_path = Path(args.mpi_report)
    cuda = load_json(cuda_path)
    mpi = load_json(mpi_path)

    require(cuda.get("status") == "PASS-H2-PIPE-RACK-DELAYED-IGNITION-SINGLE-CUDA", "CUDA report is not PASS")
    require(mpi.get("status") == "PASS-H2-PIPE-RACK-DELAYED-IGNITION-CPU-MPI", "CPU/MPI report is not PASS")

    cuda_in = nested(cuda, "input_summary")
    mpi_in = nested(mpi, "input_summary")
    cuda_run = nested(cuda, "run_summary")
    mpi_run = nested(mpi, "run_summary")
    cuda_checks = nested(cuda_run, "sustained_reaction_checks")
    mpi_checks = nested(mpi_run, "sustained_reaction_checks")

    comparable_parameters = {
        "max_step": [cuda_in["max_step"], mpi_in["max_step"]],
        "plot_int": [cuda_in["plot_int"], mpi_in["plot_int"]],
        "n_cell": [cuda_in["n_cell"], mpi_in["n_cell"]],
        "chem_integrator": [cuda_in["chem_integrator"], mpi_in["chem_integrator"]],
        "cvode_solve_type": [cuda_in["cvode_solve_type"], mpi_in["cvode_solve_type"]],
        "initial_flammable_cloud": [cuda_in["initial_flammable_cloud"], mpi_in["initial_flammable_cloud"]],
        "ignition_hotspot": [cuda_in["ignition_hotspot"], mpi_in["ignition_hotspot"]],
        "ignition_source": [cuda_in["ignition_source"], mpi_in["ignition_source"]],
        "ignition_start_time": [cuda_in["ignition_start_time"], mpi_in["ignition_start_time"]],
        "ignition_duration": [cuda_in["ignition_duration"], mpi_in["ignition_duration"]],
        "ignition_power": [cuda_in["ignition_power"], mpi_in["ignition_power"]],
        "obstacle_geometry": [cuda_in["obstacle_geometry"], mpi_in["obstacle_geometry"]],
    }
    mismatches = [
        key for key, values in comparable_parameters.items()
        if values[0] != values[1]
    ]
    require(not mismatches, f"CPU/GPU input mismatch: {mismatches}")

    cuda_final_time = float(cuda_checks["final_time"])
    mpi_final_time = float(mpi_checks["final_time"])
    cuda_h2o = float(cuda_checks["final_y_h2o_max"])
    mpi_h2o = float(mpi_checks["final_y_h2o_max"])
    cuda_outputs = int(cuda_checks["sustained_output_count"])
    mpi_outputs = int(mpi_checks["sustained_output_count"])
    final_time_abs_diff = abs(cuda_final_time - mpi_final_time)
    final_h2o_rel_diff = rel_diff(cuda_h2o, mpi_h2o)

    require(int(cuda_run["max_step"]) == int(mpi_run["max_step"]) == int(cuda_in["max_step"]), "max_step mismatch")
    require(final_time_abs_diff <= float(args.max_final_time_abs_diff), "final time mismatch too large")
    require(cuda_outputs == mpi_outputs, "sustained reaction output count mismatch")
    require(cuda_outputs >= 7, "sustained output count too small for parity")
    require(final_h2o_rel_diff <= float(args.max_final_h2o_rel_diff), "final H2O relative difference too large")
    require(int(cuda_run["cuda_devices"]) >= 1, "CUDA report did not use a GPU")
    require(int(mpi_run["cuda_devices"]) == 0, "CPU/MPI report unexpectedly used CUDA")
    require(int(mpi_run["mpi_ranks"]) >= 2, "CPU/MPI report did not use at least 2 ranks")

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS,
        "title": "H2 Pipe-Rack Delayed-Ignition CPU/GPU Parity Evidence",
        "decision": "same_delayed_ignition_case_cpu_mpi_and_single_gpu_consistent",
        "compared_reports": {
            "single_cuda": str(cuda_path),
            "cpu_mpi": str(mpi_path),
        },
        "validated_capabilities": {
            "cpu_mpi_delayed_ignition_ready": True,
            "single_gpu_delayed_ignition_ready": True,
            "same_input_physics_parameters": True,
            "same_step_and_time_window": True,
            "sustained_reaction_count_consistent": True,
            "final_h2o_within_tolerance": True,
            "cpu_gpu_delayed_ignition_parity": True,
        },
        "comparison": {
            "max_step": int(cuda_run["max_step"]),
            "final_time_cuda": cuda_final_time,
            "final_time_cpu_mpi": mpi_final_time,
            "final_time_abs_diff": final_time_abs_diff,
            "final_y_h2o_max_cuda": cuda_h2o,
            "final_y_h2o_max_cpu_mpi": mpi_h2o,
            "final_y_h2o_rel_diff": final_h2o_rel_diff,
            "sustained_output_count_cuda": cuda_outputs,
            "sustained_output_count_cpu_mpi": mpi_outputs,
            "max_final_h2o_rel_diff_allowed": float(args.max_final_h2o_rel_diff),
            "max_final_time_abs_diff_allowed": float(args.max_final_time_abs_diff),
            "comparable_parameters": comparable_parameters,
        },
        "limitations": [
            "This compares reduced engineering stability outputs, not full-scale experimental overpressure/radiation calibration.",
            "CPU/MPI uses a premerged STL to avoid parallel STL merge races; single-CUDA uses the multi-file STL merge path.",
        ],
        "evidence_files": [
            evidence_entry("single_cuda_report", cuda_path),
            evidence_entry("cpu_mpi_report", mpi_path),
            evidence_entry("cuda_problem_header", Path("examples/engineering/h2_leak_3d/pelelmex_prob.H")),
            evidence_entry("cuda_problem_parameter_reader", Path("examples/engineering/h2_leak_3d/pelelmex_prob.cpp")),
            evidence_entry("single_cuda_smoke_script", Path("tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh")),
            evidence_entry("cpu_mpi_smoke_script", Path("tools/codex_smoke_engineering_h2_pipe_rack_delayed_ignition_mpi.sh")),
        ],
    }


def validate_report(report: dict[str, Any], check_hashes: bool = True) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "status is not PASS")
    caps = report.get("validated_capabilities")
    require(isinstance(caps, dict), "missing validated_capabilities")
    for name in (
        "cpu_mpi_delayed_ignition_ready",
        "single_gpu_delayed_ignition_ready",
        "same_input_physics_parameters",
        "same_step_and_time_window",
        "sustained_reaction_count_consistent",
        "final_h2o_within_tolerance",
        "cpu_gpu_delayed_ignition_parity",
    ):
        require(caps.get(name) is True, f"{name} not validated")
    comparison = report.get("comparison")
    require(isinstance(comparison, dict), "missing comparison")
    require(float(comparison["final_time_abs_diff"]) <= float(comparison["max_final_time_abs_diff_allowed"]), "final time tolerance failed")
    require(float(comparison["final_y_h2o_rel_diff"]) <= float(comparison["max_final_h2o_rel_diff_allowed"]), "final H2O tolerance failed")
    require(int(comparison["sustained_output_count_cuda"]) == int(comparison["sustained_output_count_cpu_mpi"]), "sustained output counts differ")
    if check_hashes:
        for entry in report.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry["sha256"], f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    c = report["comparison"]
    lines = [
        "# H2 Pipe-Rack Delayed-Ignition CPU/GPU Parity Evidence",
        "",
        f"- Status: {report['status']}",
        f"- Decision: {report['decision']}",
        f"- Steps/final time: {c['max_step']} steps; final_time_abs_diff={c['final_time_abs_diff']}",
        f"- Final Y(H2O) CUDA: {c['final_y_h2o_max_cuda']}",
        f"- Final Y(H2O) CPU/MPI: {c['final_y_h2o_max_cpu_mpi']}",
        f"- Final Y(H2O) relative difference: {c['final_y_h2o_rel_diff']}",
        f"- Sustained reaction outputs: CUDA={c['sustained_output_count_cuda']}, CPU/MPI={c['sustained_output_count_cpu_mpi']}",
        "",
        "Limitation: this is a reduced CPU/GPU parity gate, not a calibrated fire-consequence validation.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cuda-report", default=str(DEFAULT_CUDA_REPORT))
    parser.add_argument("--mpi-report", default=str(DEFAULT_MPI_REPORT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--max-final-h2o-rel-diff", type=float, default=0.05)
    parser.add_argument("--max-final-time-abs-diff", type=float, default=1.0e-18)
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    try:
        if args.verify_json:
            report = load_json(Path(args.verify_json))
            validate_report(report)
            print(f"engineering_h2_pipe_rack_delayed_ignition_cross_platform VERIFY-PASS json={args.verify_json} status={report['status']}")
            return 0
        report = build_report(args)
        validate_report(report)
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_h2_pipe_rack_delayed_ignition_cross_platform PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except (OSError, json.JSONDecodeError, ReportError) as exc:
        print(f"engineering_h2_pipe_rack_delayed_ignition_cross_platform FAIL {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
