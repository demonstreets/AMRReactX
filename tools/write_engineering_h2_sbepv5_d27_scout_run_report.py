#!/usr/bin/env python3
"""Write/verify SBEPV5 D27 program-side scout run evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS = "PASS-SBEPV5-D27-PROGRAM-SCOUT-RUN"
SCHEMA_VERSION = 1
DEFAULT_RUN_ROOT = Path("/tmp/codex_h2_sbepv5_d27_scout_cuda")
DEFAULT_OUTPUT_ROOT = Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_program_scout_run_20260727")


class ScoutRunError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ScoutRunError(message)


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


def copy_evidence_entries(report: dict[str, Any], output_root: Path) -> None:
    files_dir = output_root / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    copied_entries: list[dict[str, Any]] = []
    for item in report.get("evidence_files", []):
        label = str(item.get("label", "evidence")).strip() or "evidence"
        src = Path(str(item.get("path", "")))
        require(src.is_file(), f"missing source evidence file for copy: {src}")
        dst = files_dir / f"{label}{src.suffix}"
        shutil.copy2(src, dst)
        copied_entries.append(evidence_entry(label, dst))
    report["evidence_files"] = copied_entries


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ScoutRunError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ScoutRunError(f"invalid JSON evidence: {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def parse_input(path: Path) -> dict[str, str]:
    vals: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        vals[key.strip()] = value.strip()
    return vals


def input_float(vals: dict[str, str], key: str) -> float:
    require(key in vals, f"input {key} missing")
    try:
        value = float(vals[key])
    except ValueError as exc:
        raise ScoutRunError(f"input {key}={vals[key]!r} is not numeric") from exc
    require(math.isfinite(value), f"input {key} is not finite")
    return value


def require_close(actual: float, expected: float, label: str, tol: float = 1.0e-12) -> None:
    require(abs(actual - expected) <= tol, f"{label}={actual:.12e}, expected {expected:.12e}")


def count_csv_rows(path: Path) -> int:
    return max(0, len(path.read_text(encoding="utf-8").splitlines()) - 1)


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_root = Path(args.run_root)
    run_dir = run_root / "run"
    input_path = run_root / "input.sbepv5_d27_scout_h2_leak_3d"
    sensors_json_path = run_root / "sensors.sbepv5_d27_approx.json"
    run_log_path = run_root / "run.log"
    validation_log_path = run_root / "validation.log"
    plume_path = run_root / "h2_plume_observation_report.json"
    plume = load_json(plume_path)
    require(plume.get("status") == "PASS-H2-PLUME-OBSERVATION", "plume observation did not PASS")
    summary = plume.get("summary") if isinstance(plume.get("summary"), dict) else {}
    require(summary.get("sensor_timeseries_available") is True, "sensor time series unavailable")
    require(summary.get("plume_extents_available") is True, "plume extents unavailable")
    require(finite(summary.get("max_flammable_x")), "missing max flammable x")
    require(finite(summary.get("max_flammable_z")), "missing max flammable z")

    vals = parse_input(input_path)
    require(vals.get("geometry.prob_hi") == "1.20 0.20 0.90", "domain does not match D27 vessel dimensions")
    require_close(input_float(vals, "prob.leak_xc"), 0.075, "prob.leak_xc")
    require_close(input_float(vals, "prob.leak_yc"), 0.10, "prob.leak_yc")
    require_close(input_float(vals, "prob.leak_zc"), 0.145, "prob.leak_zc")
    require_close(input_float(vals, "prob.leak_vel_x"), 1.0, "prob.leak_vel_x")
    require(vals.get("prob.obstacle_geometry") == "stl", f"input prob.obstacle_geometry={vals.get('prob.obstacle_geometry')!r}, expected 'stl'")
    require("sbepv5_baffle_1_upper.stl" in vals.get("prob.obstacle_stl_files", ""), "baffle STL list missing")
    max_step = int(vals.get("amr.max_step", "0"))
    plot_int = int(vals.get("amr.plot_int", "0"))
    require(max_step >= int(args.min_steps), f"max_step {max_step} below required {args.min_steps}")
    require(plot_int > 0, "plot_int must be positive")

    run_log = run_log_path.read_text(encoding="utf-8", errors="replace")
    for needle in [
        "Applying H2 leak source:",
        "H2 leak UserDefined EB STL files: count=4",
        "Creating ReactorBase instance: ReactorNull",
        "AMReX",
        "finalized",
    ]:
        require(needle in run_log, f"run log missing marker: {needle}")
    if vals.get("amr.max_step"):
        require(f"STEP [{max_step - 1}]" in run_log, "final step marker missing")
    if args.require_cuda:
        require("CUDA initialized with" in run_log, "CUDA initialization marker missing")
    if int(args.min_mpi_ranks) > 1:
        require(f"MPI initialized with {int(args.min_mpi_ranks)} MPI processes" in run_log, "MPI marker missing")
    require(not re.search(r"\b(nan|inf)\b", run_log, re.IGNORECASE), "run log contains NaN/Inf marker")
    require("Unused ParmParse Variables" not in run_log, "unused ParmParse variables found")

    plotfiles = sorted(p.name for p in run_dir.glob("plt*") if p.is_dir() and (p / "Header").is_file())
    require(len(plotfiles) >= max_step // plot_int + 1, "too few plotfiles")
    extents_csv = Path(plume["outputs"]["plume_extents_csv"])
    sensors_csv = Path(plume["outputs"]["sensor_timeseries_csv"])
    sensor_count = int(plume.get("sensor_count", 0))
    require(sensor_count >= 8, "too few scout sensors")
    require(count_csv_rows(extents_csv) == len(plotfiles), "extent CSV rows do not match plotfiles")
    require(count_csv_rows(sensors_csv) == len(plotfiles) * sensor_count, "sensor CSV rows do not match plotfiles*sensors")

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "title": "HySafe SBEPV5 D27 Program-Side Scout Run",
        "benchmark_id": "hysafe_sbepv5_d27",
        "run_root": str(run_root),
        "run_dir": str(run_dir),
        "input_summary": {
            "max_step": max_step,
            "plot_int": plot_int,
            "fixed_dt": float(vals["amr.fixed_dt"]),
            "n_cell": vals["amr.n_cell"],
            "domain_m": vals["geometry.prob_hi"],
            "release_location_m": [float(vals["prob.leak_xc"]), float(vals["prob.leak_yc"]), float(vals["prob.leak_zc"])],
            "public_d27_jet_exit_location_m": [0.03, 0.10, 0.145],
            "numeric_source_shifted_inside_domain": True,
            "release_velocity_m_s": float(vals["prob.leak_vel_x"]),
            "public_d27_exit_velocity_m_s": 10.17,
            "release_mdot_kg_s": float(vals["prob.leak_rate"]),
            "baffle_stl_count": len(vals["prob.obstacle_stl_files"].split()),
        },
        "validated_outputs": {
            "cuda_run": bool(args.require_cuda),
            "mpi_ranks": int(args.min_mpi_ranks),
            "plotfile_count": len(plotfiles),
            "sensor_count": sensor_count,
            "sensor_timeseries_rows": count_csv_rows(sensors_csv),
            "plume_extent_rows": count_csv_rows(extents_csv),
            "program_sensor_sampling_available": True,
            "program_downwind_extent_available": True,
            "program_vertical_extent_available": True,
            "case_matched_external_dataset_ingested": False,
        },
        "plume_summary": summary,
        "plume_detection": {
            "species": plume.get("species", "H2"),
            "lower_threshold": plume.get("lfl"),
            "upper_threshold": plume.get("ufl"),
            "threshold_semantics": "low-concentration plume detection for D27 scout, not H2 flammability evidence",
        },
        "evidence_files": [
            evidence_entry("run_log", run_log_path),
            evidence_entry("validation_log", validation_log_path),
            evidence_entry("input", input_path),
            evidence_entry("sensors_json", sensors_json_path),
            evidence_entry("plume_observation_report", plume_path),
            evidence_entry("plume_extents_csv", extents_csv),
            evidence_entry("sensor_timeseries_csv", sensors_csv),
        ],
        "limitations": [
            "This is a program-side SBEPV5 D27 scout using public geometry/release facts and approximate baffle/sensor placement.",
            "The plume observation threshold is configured for low-concentration plume detection, not for claiming a flammable cloud.",
            "It is not an external experimental agreement claim because exact baffle bounds, exact sensor coordinates, and original/digitized Gas01..Gas12 histories are not ingested.",
        ],
        "clears_reference_data_blocker": False,
    }
    validate_report_object(report, check_hashes=False)
    return report


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS, "invalid status")
    require(data.get("benchmark_id") == "hysafe_sbepv5_d27", "benchmark id mismatch")
    outputs = data.get("validated_outputs") if isinstance(data.get("validated_outputs"), dict) else {}
    require(outputs.get("program_sensor_sampling_available") is True, "sensor sampling not validated")
    require(outputs.get("program_downwind_extent_available") is True, "downwind extent not validated")
    require(outputs.get("program_vertical_extent_available") is True, "vertical extent not validated")
    require(outputs.get("case_matched_external_dataset_ingested") is False, "scout must not claim external dataset ingestion")
    require(data.get("clears_reference_data_blocker") is False, "scout must not clear reference data blocker")
    entries = data.get("evidence_files")
    require(isinstance(entries, list) and entries, "evidence files missing")
    if check_hashes:
        for item in entries:
            path = Path(str(item.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# HySafe SBEPV5 D27 Program-Side Scout Run",
        "",
        f"- Status: `{report['status']}`",
        f"- Run root: `{report['run_root']}`",
        f"- Grid/steps: `{report['input_summary']['n_cell']}`; `{report['input_summary']['max_step']}` steps",
        f"- Plotfiles: `{report['validated_outputs']['plotfile_count']}`",
        f"- Sensors/rows: `{report['validated_outputs']['sensor_count']}` sensors; `{report['validated_outputs']['sensor_timeseries_rows']}` rows",
        f"- Max X(H2): `{report['plume_summary']['max_peak_X']}`",
        f"- Plume threshold: `{report['plume_detection']['lower_threshold']}` to `{report['plume_detection']['upper_threshold']}` mole fraction",
        f"- Max threshold-cloud x/z: `{report['plume_summary']['max_flammable_x']}`, `{report['plume_summary']['max_flammable_z']}`",
        "",
        "Limitations:",
    ]
    for item in report["limitations"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--min-steps", type=int, default=200)
    parser.add_argument("--require-cuda", action="store_true")
    parser.add_argument("--min-mpi-ranks", type=int, default=1)
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report_object(data, check_hashes=True)
            print(f"sbepv5_d27_scout_run_report VERIFY-PASS json={args.verify_json} status={data['status']}")
            return 0
        report = build_report(args)
        output_root = Path(args.output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        copy_evidence_entries(report, output_root)
        json_path = output_root / "sbepv5_d27_scout_run_report.json"
        md_path = output_root / "sbepv5_d27_scout_run_report.md"
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, md_path)
        print(f"sbepv5_d27_scout_run_report PASS json={json_path} status={report['status']}")
        return 0
    except ScoutRunError as exc:
        print(f"sbepv5_d27_scout_run_report FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
