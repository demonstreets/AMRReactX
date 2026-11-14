#!/usr/bin/env python3
"""Write/verify H2 pipe-rack delayed-ignition single-CUDA evidence."""

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
STATUS_PASS = "PASS-H2-PIPE-RACK-DELAYED-IGNITION-SINGLE-CUDA"
DEFAULT_OUTPUT_ROOT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cuda_20260805"
)
DEFAULT_OUTPUT_JSON = DEFAULT_OUTPUT_ROOT / "engineering_h2_pipe_rack_delayed_ignition_cuda_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_OUTPUT_ROOT / "engineering_h2_pipe_rack_delayed_ignition_cuda_report.md"
DEFAULT_STAGED_ROOT = DEFAULT_OUTPUT_ROOT / "runtime_evidence"
DEFAULT_RUN_ROOT = Path("/tmp/codex_h2_pipe_rack_delayed_ignition_cuda_20260805_p1e10")

RUN_STATUS = "PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-SUSTAINED"
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


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReportError(f"missing JSON report: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f"invalid JSON report {path}: {exc}") from exc
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
        run_dir / "input.codex_pipe_rack_reacting_single_cuda_20step",
        staged_root / "input.codex_pipe_rack_reacting_single_cuda_20step",
    )
    for name in ("plt00000", "plt00020", "plt00030", "plt00120"):
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
        "do_react": value("peleLM.do_react") == "1",
        "chem_integrator": value("peleLM.chem_integrator"),
        "cvode_solve_type": value("cvode.solve_type"),
        "initial_flammable_cloud": value("prob.initial_flammable_cloud") == "1",
        "ignition_hotspot": value("prob.ignition_hotspot") == "1",
        "ignition_source": value("prob.ignition_source") == "1",
        "ignition_start_time": float(value("prob.ignition_start_time")),
        "ignition_duration": float(value("prob.ignition_duration")),
        "ignition_power": float(value("prob.ignition_power")),
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
    input_path = staged_root / "input.codex_pipe_rack_reacting_single_cuda_20step"
    summary = load_json(summary_path)
    run_log = run_log_path.read_text(encoding="utf-8", errors="replace")
    input_summary = parse_input(input_path)

    require(summary.get("status") == RUN_STATUS, "source run summary is not PASS")
    caps = summary.get("validated_capabilities")
    require(isinstance(caps, dict), "summary missing validated_capabilities")
    require(caps.get("delayed_ignition_timed_energy_source") is True, "delayed ignition was not validated")
    require(caps.get("single_gpu_cuda") is True, "single CUDA capability was not validated")
    require(caps.get("sustained_reacting_fire_development") is True, "sustained fire was not validated")
    require(caps.get("ignition_hotspot") is False, "run still used initial ignition hotspot")
    require(input_summary["ignition_source"] is True, "input did not enable timed ignition source")
    require(input_summary["ignition_hotspot"] is False, "input did not disable initial ignition hotspot")
    require(input_summary["chem_integrator"] == "ReactorCvode", "input did not use ReactorCvode")
    require(input_summary["cvode_solve_type"] == "GMRES", "input did not use CUDA-compatible GMRES")
    require(input_summary["obstacle_geometry"] == "stl", "input did not use STL obstacles")

    checks = summary.get("sustained_reaction_checks")
    require(isinstance(checks, dict), "summary missing sustained_reaction_checks")
    require(int(summary.get("max_step", 0)) >= 120, "run did not reach at least 120 steps")
    require(float(checks.get("final_time", 0.0)) >= 1.0e-6, "run final time too short")
    require(int(checks.get("sustained_output_count", 0)) >= 7, "too few sustained reaction outputs")
    require(float(checks.get("final_y_h2o_max", 0.0)) > 1.0e-6, "H2O growth too small")
    history = summary.get("reaction_history")
    require(isinstance(history, list) and len(history) >= 10, "reaction history too short")
    post_ignition = [
        row for row in history
        if float(row.get("time", 0.0)) >= input_summary["ignition_start_time"] + input_summary["ignition_duration"]
    ]
    require(post_ignition, "no post-ignition plot samples")
    require(
        max(float(row.get("heat_release_abs_max", 0.0)) for row in post_ignition) > 1.0e5,
        "post-ignition heat release did not become strongly active",
    )
    require(
        max(float(row.get("ir_h2_abs_max", 0.0)) for row in post_ignition) > 1.0e-2,
        "post-ignition H2 reaction rate did not become strongly active",
    )
    for marker in (
        "CUDA initialized with 1 device",
        "H2 delayed ignition source: enabled=1",
        "Creating ReactorBase instance: ReactorCvode",
        "STEP [119]",
        "AMReX",
    ):
        require(marker in run_log, f"run log missing marker: {marker}")
    hits = [line.strip() for line in run_log.splitlines() if FAILURE_RE.search(line)]
    require(not hits, f"solver failure markers found: {hits[:5]}")

    evidence = [
        evidence_entry("staged_summary", summary_path),
        evidence_entry("staged_run_log", run_log_path),
        evidence_entry("staged_input", input_path),
        evidence_entry("plt00000_header", staged_root / "plt00000" / "Header"),
        evidence_entry("plt00020_header_pre_ignition_start", staged_root / "plt00020" / "Header"),
        evidence_entry("plt00030_header_ignition_window", staged_root / "plt00030" / "Header"),
        evidence_entry("plt00120_header_final", staged_root / "plt00120" / "Header"),
        evidence_entry("smoke_script", Path("tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh")),
        evidence_entry("problem_header", Path("examples/engineering/h2_leak_3d/pelelmex_prob.H")),
        evidence_entry("problem_parameter_reader", Path("examples/engineering/h2_leak_3d/pelelmex_prob.cpp")),
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS,
        "title": "H2 Pipe-Rack Delayed-Ignition Single-CUDA Evidence",
        "decision": "delayed_ignition_leak_obstacle_reacting_single_gpu_pass",
        "staged_evidence_root": str(staged_root),
        "source_run_root": str(run_root) if run_root else "",
        "input_summary": input_summary,
        "run_summary": {
            "max_step": summary["max_step"],
            "mpi_ranks": summary["mpi_ranks"],
            "cuda_devices": summary["cuda_devices"],
            "plotfiles": summary["plotfiles"],
            "sustained_reaction_checks": checks,
        },
        "validated_capabilities": {
            "h2_leak_source": True,
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
        "limitations": [
            "This is a reduced engineering gate, not calibrated overpressure/radiation agreement.",
            "The time scale is a stiff-reacting smoke window, not the full EXP002 3 s release and 2.5 s delayed ignition duration.",
            "Geometry remains synthetic cube/cylinder/pipe-rack STL, not a cleaned plant CAD import.",
        ],
        "evidence_files": evidence,
    }


def validate_report(report: dict[str, Any], check_hashes: bool = True) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "status is not PASS")
    caps = report.get("validated_capabilities")
    require(isinstance(caps, dict), "missing validated_capabilities")
    for name in (
        "h2_leak_source",
        "pipe_rack_stl_obstacles",
        "delayed_ignition_timed_energy_source",
        "initial_hotspot_not_used",
        "reactor_cvode",
        "cvode_gmres",
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
    require(int(checks.get("sustained_output_count", 0)) >= 7, "sustained output count too small")
    require(float(checks.get("final_y_h2o_max", 0.0)) > 1.0e-6, "final H2O max too small")
    if check_hashes:
        for entry in report.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry["sha256"], f"sha256 mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    run = report["run_summary"]
    checks = run["sustained_reaction_checks"]
    lines = [
        "# H2 Pipe-Rack Delayed-Ignition Single-CUDA Evidence",
        "",
        f"- Status: {report['status']}",
        f"- Decision: {report['decision']}",
        "- Scope: H2 leak + initial flammable cloud + STL cube/cylinder/pipe-rack obstacles + delayed timed ignition source + ReactorCvode chemistry.",
        "- Parallel path: single CUDA device through the MPI CUDA executable path.",
        f"- Steps/final time: {run['max_step']} steps; final_time={checks['final_time']}",
        f"- Sustained post-ignition outputs: {checks['sustained_output_count']}",
        f"- Final Y(H2O)_max: {checks['final_y_h2o_max']}",
        "- Initial hot spot was disabled; ignition came from the timed energy source.",
        "",
        "Limitation: this strengthens the engineering fire stability gate but does not clear calibrated overpressure/radiation validation.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--staged-root", default=str(DEFAULT_STAGED_ROOT))
    parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    parser.add_argument("--verify-json")
    parser.add_argument("--skip-hash-check", action="store_true")
    args = parser.parse_args()

    try:
        if args.verify_json:
            report = load_json(Path(args.verify_json))
            validate_report(report, check_hashes=not args.skip_hash_check)
            print(f"engineering_h2_pipe_rack_delayed_ignition_cuda VERIFY-PASS json={args.verify_json} status={report['status']}")
            return 0
        report = build_report(args)
        validate_report(report)
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(f"engineering_h2_pipe_rack_delayed_ignition_cuda PASS json={output_json} md={output_md} status={report['status']}")
        return 0
    except ReportError as exc:
        print(f"engineering_h2_pipe_rack_delayed_ignition_cuda FAIL {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
