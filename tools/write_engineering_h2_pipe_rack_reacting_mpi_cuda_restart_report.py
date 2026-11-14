#!/usr/bin/env python3
"""Write/verify H2 pipe-rack reacting MPI+CUDA checkpoint/restart evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-PIPE-RACK-DIRECT-REACTING-MPI-CUDA-RESTART-SUSTAINED"
DEFAULT_RUN_ROOT = Path("/tmp/codex_h2_pipe_rack_reacting_mpi_cuda_restart_20260727_64x32x32_225to525")
DEFAULT_OUTPUT_ROOT = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_mpi_cuda_restart_20260727"
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
        raise ReportError(f"missing JSON: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReportError(f"invalid JSON {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def validate_summary(summary: dict[str, Any]) -> None:
    require(summary.get("status") == STATUS_PASS, "restart summary status is not PASS")
    require(summary.get("n_cell") == "64 32 32", "restart summary is not the large-grid case")
    require(int(summary.get("mpi_ranks", 0)) >= 2, "MPI rank count too small")
    require(int(summary.get("cuda_devices", 0)) >= 2, "CUDA device count too small")
    require(int(summary.get("initial_step", 0)) >= 200, "initial checkpoint step too small")
    require(int(summary.get("final_step", 0)) > int(summary.get("initial_step", 0)), "final step did not advance")
    require(int(summary.get("post_restart_sustained_output_count", 0)) >= 3, "too few post-restart fire outputs")
    require(float(summary.get("final_time", 0.0)) > float(summary.get("checkpoint_time", 0.0)), "time did not advance after restart")
    require(
        float(summary.get("final_y_h2o_max", 0.0)) > float(summary.get("checkpoint_y_h2o_max", 0.0)),
        "H2O did not continue growing after restart",
    )
    caps = summary.get("validated_capabilities", {})
    require(isinstance(caps, dict), "validated_capabilities missing")
    for name in (
        "checkpoint_written",
        "restart_from_checkpoint",
        "post_restart_sustained_fire_development",
        "mpi_cuda_parallel",
        "pipe_rack_stl_obstacles",
        "reactor_cvode",
        "cvode_gmres",
    ):
        require(caps.get(name) is True, f"{name} not validated")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_root = Path(args.run_root)
    summary_path = run_root / "restart_summary.json"
    summary = load_json(summary_path)
    validate_summary(summary)

    evidence = [evidence_entry("restart_summary", summary_path)]
    for item in summary.get("evidence_files", []):
        require(isinstance(item, dict), "bad nested evidence item")
        path = Path(item["path"])
        evidence.append(evidence_entry(item["label"], path))
        require(evidence[-1]["sha256"] == item["sha256"], f"nested evidence hash mismatch: {path}")

    for label, path in (
        ("input", run_root / "run" / "input.codex_pipe_rack_reacting_single_cuda_20step"),
        ("initial_summary", run_root / "initial_summary.json"),
        ("restart_smoke_script", Path("tools/codex_smoke_engineering_h2_pipe_rack_reacting_mpi_cuda_restart.sh")),
        ("base_reacting_smoke_script", Path("tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh")),
    ):
        if path.exists():
            evidence.append(evidence_entry(label, path))

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS_PASS,
        "title": "H2 Pipe-Rack Reacting MPI+CUDA Restart Evidence",
        "decision": "direct_engineering_pipe_rack_reacting_mpi_cuda_checkpoint_restart_pass",
        "run_root": str(run_root),
        "validated_capabilities": {
            "largegrid_64x32x32": True,
            "checkpoint_written": True,
            "restart_from_checkpoint": True,
            "post_restart_sustained_fire_development": True,
            "mpi_cuda_parallel": True,
            "pipe_rack_stl_obstacles": True,
            "reactor_cvode": True,
            "cvode_gmres": True,
            "calibrated_fire_or_blast_model": False,
        },
        "restart_checks": {
            "n_cell": summary["n_cell"],
            "initial_step": summary["initial_step"],
            "final_step": summary["final_step"],
            "mpi_ranks": summary["mpi_ranks"],
            "cuda_devices": summary["cuda_devices"],
            "checkpoint_time": summary["checkpoint_time"],
            "final_time": summary["final_time"],
            "checkpoint_y_h2o_max": summary["checkpoint_y_h2o_max"],
            "final_y_h2o_max": summary["final_y_h2o_max"],
            "post_restart_sustained_output_count": summary["post_restart_sustained_output_count"],
            "plotfiles": summary["plotfiles"],
        },
        "reaction_history": summary["reaction_history"],
        "limitations": [
            "Checkpoint/restart is validated for this synthetic pipe-rack fire gate, not every plant layout.",
            "The gate proves restartability and continued post-restart reaction on MPI+CUDA; it is not calibrated fire-consequence validation.",
        ],
        "evidence_files": evidence,
    }


def validate_report(report: dict[str, Any], check_hashes: bool = True) -> None:
    require(report.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(report.get("status") == STATUS_PASS, "status mismatch")
    caps = report.get("validated_capabilities", {})
    require(caps.get("restart_from_checkpoint") is True, "restart not validated")
    require(caps.get("mpi_cuda_parallel") is True, "MPI+CUDA not validated")
    checks = report.get("restart_checks", {})
    require(checks.get("n_cell") == "64 32 32", "large-grid check mismatch")
    require(int(checks.get("post_restart_sustained_output_count", 0)) >= 3, "post-restart output count too small")
    require(float(checks.get("final_y_h2o_max", 0.0)) > float(checks.get("checkpoint_y_h2o_max", 0.0)), "H2O did not grow")
    if check_hashes:
        for entry in report.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry["sha256"], f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    c = report["restart_checks"]
    lines = [
        "# H2 Pipe-Rack Reacting MPI+CUDA Restart Evidence",
        "",
        f"- Status: {report['status']}",
        f"- Grid: {c['n_cell']}",
        f"- Restart: checkpoint step {c['initial_step']} -> final step {c['final_step']}",
        f"- MPI/CUDA: {c['mpi_ranks']} ranks, {c['cuda_devices']} CUDA devices",
        f"- Time: {c['checkpoint_time']} -> {c['final_time']}",
        f"- Y(H2O)_max: {c['checkpoint_y_h2o_max']} -> {c['final_y_h2o_max']}",
        f"- Post-restart sustained fire outputs: {c['post_restart_sustained_output_count']}",
        "",
        "Limitation: restartability is proven for this synthetic pipe-rack fire gate, not calibrated production fire certification.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    ap.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
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
        json_path = output_root / "pipe_rack_reacting_mpi_cuda_restart_report.json"
        md_path = output_root / "pipe_rack_reacting_mpi_cuda_restart_report.md"
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, md_path)
        validate_report(load_json(json_path))
        print(f"WROTE {json_path} status={report['status']}")
        return 0
    except ReportError as exc:
        print(f"pipe_rack_reacting_mpi_cuda_restart_report FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
