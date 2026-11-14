#!/usr/bin/env python3
"""Write/verify initial integrated engineering acceptance evidence for H2 CFD."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = "PASS-H2-INTEGRATED-ENGINEERING-INITIAL-ACCEPTANCE"

DEFAULT_OUTPUT_ROOT = Path(
    "docs/codex_audit/evidence/engineering_h2_integrated_initial_acceptance_20260728"
)
DEFAULT_OBSTACLE = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_gpu_fire_obstacle_20260727/"
    "pipe_rack_gpu_fire_obstacle_report.json"
)
DEFAULT_LARGE = Path(
    "docs/codex_audit/evidence/engineering_h2_large_acceptance_20260727/"
    "h2_large_acceptance_report.json"
)
DEFAULT_CUDA_FIRE = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_cuda_2000step_20260727/"
    "pipe_rack_direct_reacting_cuda_report.json"
)
DEFAULT_MPI_CUDA_FIRE = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_mpi_cuda_2000step_20260727/"
    "pipe_rack_direct_reacting_mpi_cuda_report.json"
)
DEFAULT_LARGEGRID_CUDA = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_largegrid_cuda_20260727/"
    "pipe_rack_direct_reacting_cuda_report.json"
)
DEFAULT_LARGEGRID_MPI_CUDA = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_20260727/"
    "pipe_rack_direct_reacting_mpi_cuda_report.json"
)
DEFAULT_RESTART = Path(
    "docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_mpi_cuda_restart_20260727/"
    "pipe_rack_reacting_mpi_cuda_restart_report.json"
)
DEFAULT_FIRE_TRACEABILITY = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_consequence_traceability_20260727/"
    "fire_consequence_traceability_report.json"
)


class AcceptanceError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AcceptanceError(message)


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
        raise AcceptanceError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AcceptanceError(f"invalid JSON evidence: {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def ratio_close(value: Any, tol: float = 0.02) -> bool:
    return finite(value) and abs(float(value) - 1.0) <= tol


def nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key, default)
    return cur


def validate_obstacle_report(report: dict[str, Any]) -> dict[str, Any]:
    require(report.get("status") == "PASS-H2-PIPE-RACK-GPU-FIRE-OBSTACLE-SMOKE", "obstacle report did not PASS")
    caps = report.get("validated_capabilities") if isinstance(report.get("validated_capabilities"), dict) else {}
    required_caps = [
        "cpu_obstacle_leak_dispersion",
        "gpu_obstacle_leak_dispersion",
        "mpi_cuda_obstacle_leak_dispersion",
        "cube_obstacle_stl",
        "vertical_cylinder_obstacle_stl",
        "pipe_rack_multi_pipe_obstacle_stl",
        "merged_multi_file_stl_obstacle",
        "fire_consequence_screening",
    ]
    for key in required_caps:
        require(caps.get(key) is True, f"obstacle capability not validated: {key}")
    require(int(caps.get("mpi_cuda_ranks", 0)) >= 2, "MPI+CUDA obstacle run requires at least 2 ranks")
    require(int(caps.get("mpi_cuda_devices", 0)) >= 2, "MPI+CUDA obstacle run requires at least 2 CUDA devices")
    for label in ("cpu", "gpu", "mpi_cuda"):
        metrics = report.get(f"{label}_metrics") if isinstance(report.get(f"{label}_metrics"), dict) else {}
        checks = report.get(f"{label}_log_checks") if isinstance(report.get(f"{label}_log_checks"), dict) else {}
        require(ratio_close(metrics.get("mass_ratio"), 0.01), f"{label} obstacle mass ratio out of tolerance")
        require(checks.get("amrex_finalized") is True, f"{label} obstacle run did not finalize")
        require(int(checks.get("failure_marker_count", -1)) == 0, f"{label} obstacle run has failure markers")
    return {
        "status": report["status"],
        "cpu_mass_ratio": report["cpu_metrics"]["mass_ratio"],
        "gpu_mass_ratio": report["gpu_metrics"]["mass_ratio"],
        "mpi_cuda_mass_ratio": report["mpi_cuda_metrics"]["mass_ratio"],
        "mpi_cuda_ranks": caps["mpi_cuda_ranks"],
        "mpi_cuda_devices": caps["mpi_cuda_devices"],
        "obstacle_sources": report["gpu_metrics"]["stl_source_files"],
        "fire_screening_status": nested(report, "fire_screening_summary", "status"),
    }


def validate_large_acceptance(report: dict[str, Any]) -> dict[str, Any]:
    require(report.get("status") == "PASS-H2-LARGE-ENGINEERING-ACCEPTANCE", "large acceptance report did not PASS")
    metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
    require(int(metrics.get("max_step", 0)) >= 120, "large acceptance max_step below 120")
    require(int(metrics.get("base_cell_count", 0)) >= 200_000, "base cell count below engineering gate")
    require(int(metrics.get("equivalent_finest_cell_count", 0)) >= 1_000_000, "equivalent finest cell count below engineering gate")
    require(ratio_close(metrics.get("baseline_final_mass_ratio"), 0.02), "baseline large mass ratio out of tolerance")
    require(ratio_close(metrics.get("amr_final_mass_ratio"), 0.02), "AMR large mass ratio out of tolerance")
    require(int(metrics.get("amr_regrid_count", 0)) > 0, "AMR large case did not regrid")
    return {
        "status": report["status"],
        "max_step": metrics["max_step"],
        "base_cell_count": metrics["base_cell_count"],
        "equivalent_finest_cell_count": metrics["equivalent_finest_cell_count"],
        "baseline_final_mass_ratio": metrics["baseline_final_mass_ratio"],
        "amr_final_mass_ratio": metrics["amr_final_mass_ratio"],
        "amr_regrid_count": metrics["amr_regrid_count"],
    }


def validate_reacting_report(
    report: dict[str, Any],
    *,
    min_steps: int,
    min_outputs: int,
    min_mpi: int,
    min_cuda: int,
    min_temp_max: float,
) -> dict[str, Any]:
    require(str(report.get("status", "")).startswith("PASS-H2-PIPE-RACK-DIRECT-REACTING"), "reacting report did not PASS")
    inputs = report.get("input_summary") if isinstance(report.get("input_summary"), dict) else {}
    checks = report.get("run_log_checks") if isinstance(report.get("run_log_checks"), dict) else {}
    plot_checks = report.get("plotfile_checks") if isinstance(report.get("plotfile_checks"), dict) else {}
    sustained = plot_checks.get("sustained_reaction_checks") if isinstance(plot_checks.get("sustained_reaction_checks"), dict) else {}
    require(inputs.get("chem_integrator") == "ReactorCvode", "reacting case must use ReactorCvode")
    require(inputs.get("ignition_hotspot") is True, "reacting case missing ignition hotspot")
    require(inputs.get("initial_flammable_cloud") is True, "reacting case missing initial flammable cloud")
    require(inputs.get("obstacle_geometry") == "stl", "reacting case missing STL obstacles")
    require(int(inputs.get("max_step", 0)) >= min_steps, "reacting max_step below gate")
    require(int(checks.get("mpi_ranks", 0)) >= min_mpi, "reacting MPI ranks below gate")
    require(int(checks.get("cuda_devices", 0)) >= min_cuda, "reacting CUDA devices below gate")
    require(checks.get("amrex_finalized") is True, "reacting run did not finalize")
    failure_count = checks.get("solver_failure_marker_count", checks.get("failure_marker_count", -1))
    require(int(failure_count) == 0, "reacting run has failure markers")
    require(plot_checks.get("required_reacting_fire_variables_present", True) is True, "reacting variables missing")
    require(int(sustained.get("sustained_output_count", 0)) >= min_outputs, "too few sustained reacting outputs")
    require(float(sustained.get("final_y_h2o_max", 0.0)) > float(sustained.get("initial_y_h2o_max", 0.0)), "H2O did not grow")
    require(float(sustained.get("final_y_h2o_max", 0.0)) > 1.0e-3, "final H2O too small for fire-development gate")
    history = plot_checks.get("reaction_history") if isinstance(plot_checks.get("reaction_history"), list) else []
    require(any(finite(row.get("heat_release_abs_max")) and float(row["heat_release_abs_max"]) > 1.0e6 for row in history if isinstance(row, dict)), "heat release did not exceed stiff-reaction gate")
    require(
        any(finite(row.get("temp_max")) and float(row["temp_max"]) > min_temp_max for row in history if isinstance(row, dict)),
        "temperature did not develop above ignition baseline",
    )
    return {
        "status": report["status"],
        "max_step": inputs["max_step"],
        "mpi_ranks": checks["mpi_ranks"],
        "cuda_devices": checks["cuda_devices"],
        "plotfile_count": len(plot_checks.get("plotfiles", [])),
        "sustained_output_count": sustained["sustained_output_count"],
        "final_time": sustained["final_time"],
        "final_y_h2o_max": sustained["final_y_h2o_max"],
    }


def validate_restart(report: dict[str, Any]) -> dict[str, Any]:
    require(report.get("status") == "PASS-H2-PIPE-RACK-DIRECT-REACTING-MPI-CUDA-RESTART-SUSTAINED", "restart report did not PASS")
    checks = report.get("restart_checks") if isinstance(report.get("restart_checks"), dict) else {}
    require(int(checks.get("mpi_ranks", 0)) >= 2, "restart MPI ranks below gate")
    require(int(checks.get("cuda_devices", 0)) >= 2, "restart CUDA devices below gate")
    require(int(checks.get("post_restart_sustained_output_count", 0)) >= 4, "post-restart sustained outputs below gate")
    require(float(checks.get("final_y_h2o_max", 0.0)) > 1.0e-3, "restart final H2O too small")
    return {
        "status": report["status"],
        "mpi_ranks": checks["mpi_ranks"],
        "cuda_devices": checks["cuda_devices"],
        "post_restart_sustained_output_count": checks["post_restart_sustained_output_count"],
        "final_y_h2o_max": checks["final_y_h2o_max"],
    }


def validate_fire_traceability(report: dict[str, Any]) -> dict[str, Any]:
    require(report.get("status") == "PASS-H2-FIRE-CONSEQUENCE-TRACEABILITY", "fire traceability report did not PASS")
    limitations = " ".join(str(item) for item in report.get("limitations", []))
    require("not external calibration" in limitations, "fire traceability must explicitly avoid calibration claim")
    trace = report.get("screening_traceability") if isinstance(report.get("screening_traceability"), dict) else {}
    formula_checks = trace.get("formula_checks") if isinstance(trace.get("formula_checks"), list) else []
    distance_checks = trace.get("distance_checks") if isinstance(trace.get("distance_checks"), list) else []
    direct_checks = report.get("direct_reacting_fire_checks") if isinstance(report.get("direct_reacting_fire_checks"), dict) else {}
    require(formula_checks and all(item.get("passed") is True for item in formula_checks if isinstance(item, dict)), "fire formula checks not all passed")
    require(distance_checks and all(item.get("passed") is True for item in distance_checks if isinstance(item, dict)), "fire distance checks not all passed")
    require(direct_checks and all(item.get("passed") is True for item in direct_checks.values() if isinstance(item, dict)), "direct reacting fire traceability checks not all passed")
    return {
        "status": report["status"],
        "formula_check_count": len(formula_checks),
        "distance_check_count": len(distance_checks),
        "direct_reacting_check_count": len(direct_checks),
        "calibrated_fire_or_blast_model": False,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    paths = {
        "obstacle": Path(args.obstacle_report),
        "large_acceptance": Path(args.large_acceptance_report),
        "single_cuda_reacting_2000": Path(args.cuda_reacting_report),
        "mpi_cuda_reacting_2000": Path(args.mpi_cuda_reacting_report),
        "largegrid_cuda_reacting": Path(args.largegrid_cuda_reacting_report),
        "largegrid_mpi_cuda_reacting": Path(args.largegrid_mpi_cuda_reacting_report),
        "mpi_cuda_restart": Path(args.restart_report),
        "fire_traceability": Path(args.fire_traceability_report),
    }
    loaded = {name: load_json(path) for name, path in paths.items()}
    criteria = {
        "complex_obstacle_open_area_leak_dispersion_fire": validate_obstacle_report(loaded["obstacle"]),
        "large_amr_engineering_conservation": validate_large_acceptance(loaded["large_acceptance"]),
        "single_cuda_stiff_reacting_fire_2000step": validate_reacting_report(
            loaded["single_cuda_reacting_2000"], min_steps=2000, min_outputs=6, min_mpi=1, min_cuda=1, min_temp_max=2100.0
        ),
        "mpi_cuda_stiff_reacting_fire_2000step": validate_reacting_report(
            loaded["mpi_cuda_reacting_2000"], min_steps=2000, min_outputs=6, min_mpi=2, min_cuda=2, min_temp_max=2100.0
        ),
        "largegrid_single_cuda_reacting": validate_reacting_report(
            loaded["largegrid_cuda_reacting"], min_steps=300, min_outputs=4, min_mpi=1, min_cuda=1, min_temp_max=2005.0
        ),
        "largegrid_mpi_cuda_reacting": validate_reacting_report(
            loaded["largegrid_mpi_cuda_reacting"], min_steps=300, min_outputs=4, min_mpi=2, min_cuda=2, min_temp_max=2005.0
        ),
        "mpi_cuda_checkpoint_restart": validate_restart(loaded["mpi_cuda_restart"]),
        "fire_consequence_formula_traceability": validate_fire_traceability(loaded["fire_traceability"]),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "title": "Engineering H2 Integrated Initial Acceptance",
        "acceptance_scope": (
            "Complex-obstacle open-area H2 leak, dispersion, ignition, sustained reacting fire, "
            "CPU/GPU/MPI-CUDA stability, and conservation/physical-law sanity checks."
        ),
        "acceptance_basis": (
            "User-approved initial engineering gate. Real CAD ingestion, exact external plume datasets, "
            "and calibrated radiation/overpressure validation are explicitly deferred."
        ),
        "criteria": criteria,
        "deferred_items": [
            "real plant CAD ingestion and boundary-tag QA",
            "external SBEPV5 or field-test plume time-series agreement",
            "calibrated radiation/overpressure/fire consequence validation",
            "production GPU scaling curve beyond the current 2-rank MPI+CUDA gates",
        ],
        "clears_initial_integrated_engineering_goal": True,
        "clears_full_production_certification": False,
        "evidence_files": [evidence_entry(name, path) for name, path in paths.items()],
    }


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS, "invalid status")
    require(data.get("clears_initial_integrated_engineering_goal") is True, "initial gate not cleared")
    require(data.get("clears_full_production_certification") is False, "report must not clear full certification")
    criteria = data.get("criteria")
    require(isinstance(criteria, dict) and len(criteria) >= 8, "criteria missing")
    entries = data.get("evidence_files")
    require(isinstance(entries, list) and entries, "evidence files missing")
    if check_hashes:
        for item in entries:
            path = Path(str(item.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Engineering H2 Integrated Initial Acceptance",
        "",
        f"- Status: `{report['status']}`",
        f"- Clears initial integrated engineering goal: `{report['clears_initial_integrated_engineering_goal']}`",
        f"- Clears full production certification: `{report['clears_full_production_certification']}`",
        "",
        "## Scope",
        "",
        report["acceptance_scope"],
        "",
        "## Criteria",
        "",
    ]
    for name, values in report["criteria"].items():
        lines.append(f"### {name}")
        for key, value in values.items():
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
    lines += ["## Deferred Items", ""]
    for item in report["deferred_items"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--obstacle-report", default=str(DEFAULT_OBSTACLE))
    parser.add_argument("--large-acceptance-report", default=str(DEFAULT_LARGE))
    parser.add_argument("--cuda-reacting-report", default=str(DEFAULT_CUDA_FIRE))
    parser.add_argument("--mpi-cuda-reacting-report", default=str(DEFAULT_MPI_CUDA_FIRE))
    parser.add_argument("--largegrid-cuda-reacting-report", default=str(DEFAULT_LARGEGRID_CUDA))
    parser.add_argument("--largegrid-mpi-cuda-reacting-report", default=str(DEFAULT_LARGEGRID_MPI_CUDA))
    parser.add_argument("--restart-report", default=str(DEFAULT_RESTART))
    parser.add_argument("--fire-traceability-report", default=str(DEFAULT_FIRE_TRACEABILITY))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            print(f"engineering_h2_integrated_initial_acceptance VERIFY-PASS json={args.verify_json} status={data['status']}")
            return 0
        output_root = Path(args.output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        report = build_report(args)
        validate_report_object(report, check_hashes=False)
        json_path = output_root / "h2_integrated_initial_acceptance_report.json"
        md_path = output_root / "h2_integrated_initial_acceptance_report.md"
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, md_path)
        print(f"engineering_h2_integrated_initial_acceptance PASS json={json_path} status={report['status']}")
        return 0
    except AcceptanceError as exc:
        print(f"engineering_h2_integrated_initial_acceptance FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
