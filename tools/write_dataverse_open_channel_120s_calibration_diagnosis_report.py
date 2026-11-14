#!/usr/bin/env python3
"""Write/verify a diagnosis report for the DataverseNO 120 s CFD/reference mismatch."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "DIAGNOSED-DATAVERSE-OPEN-CHANNEL-H2-120S-CALIBRATION-GAPS"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_120s_calibration_diagnosis_20260804")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_120s_calibration_diagnosis_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_120s_calibration_diagnosis_report.md"

CFD_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_cfd_120s_peak_window_mpi_cuda_20260804")
AGREEMENT_REPORT = CFD_ROOT / "dataverse_open_channel_cfd_agreement_attempt_report.json"
INPUT_DECK = CFD_ROOT / "input.dataverse_open_channel_h2_scout_3d"
SENSOR_COORDS = CFD_ROOT / "sensors.dataverse_open_channel_solver_coords.json"
GEOMETRY_REPORT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_geometry_mapping_20260803/"
    "dataverse_open_channel_geometry_mapping_report.json"
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
    return {
        "label": label,
        "path": path.as_posix(),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    require(isinstance(data, dict), f"expected JSON object: {path}")
    return data


def parse_input_deck(path: Path) -> dict[str, str]:
    params: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        params[key.strip()] = value.strip()
    return params


def float_param(params: dict[str, str], key: str) -> float:
    require(key in params, f"missing input parameter: {key}")
    return float(params[key].split()[0])


def vector_param(params: dict[str, str], key: str) -> list[float]:
    require(key in params, f"missing input parameter: {key}")
    return [float(item) for item in params[key].split()]


def finite_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        f = float(value)
        return f if math.isfinite(f) else None
    return None


def nearest_cell_center_distance(point: dict[str, float], prob_lo: list[float], cell_size: list[float], n_cell: list[float]) -> float:
    distances = []
    for axis, lo, dx, n in zip(("x", "y", "z"), prob_lo, cell_size, n_cell):
        unclamped = round((point[axis] - (lo + 0.5 * dx)) / dx)
        idx = min(max(int(unclamped), 0), int(n) - 1)
        center = lo + (idx + 0.5) * dx
        distances.append(point[axis] - center)
    return math.sqrt(sum(d * d for d in distances))


def sensor_check_summary(check: dict[str, Any], coords: dict[str, dict[str, Any]]) -> dict[str, Any]:
    sid = str(check["sensor_id"])
    ref_peak = float(check["reference_peak_x_h2"])
    sim_peak = float(check["simulation_peak_x_h2"])
    peak_rel_error = float(check["peak_rel_error"])
    nrmse = float(check["nrmse_by_reference_peak_or_lfl"])
    arrival_abs_error = finite_or_none(check.get("arrival_abs_error_s"))
    coord = coords.get(sid, {})
    peak_bias = "over" if sim_peak > ref_peak else "under"
    return {
        "sensor_id": sid,
        "solver_x_m": coord.get("x"),
        "solver_y_m": coord.get("y"),
        "solver_z_m": coord.get("z"),
        "reference_peak_x_h2": ref_peak,
        "simulation_peak_x_h2": sim_peak,
        "peak_rel_error": peak_rel_error,
        "peak_bias": peak_bias,
        "nrmse": nrmse,
        "arrival_abs_error_s": arrival_abs_error,
        "arrival_error_is_infinite": arrival_abs_error is None and check.get("arrival_abs_error_s") is not None,
        "peak_passed": bool(check["peak_passed"]),
        "nrmse_passed": bool(check["nrmse_passed"]),
        "arrival_passed": bool(check["arrival_passed"]),
        "passed": bool(check["passed"]),
    }


def build_report() -> dict[str, Any]:
    agreement = load_json(AGREEMENT_REPORT)
    geometry = load_json(GEOMETRY_REPORT)
    sensors = load_json(SENSOR_COORDS)
    params = parse_input_deck(INPUT_DECK)

    summary = agreement["summary"]
    require(summary.get("simulation_time_end_s", 0.0) >= 119.9, "120 s CFD agreement run is not complete")
    require(summary.get("simulation_mass_ratio_final") == 1.0, "120 s CFD mass-ratio evidence is not exact")

    channel = geometry["channel_geometry"]
    reference_inlet_radius = float(channel["inlet_diameter_m"]) / 2.0
    numerical_radius = float_param(params, "prob.leak_radius")
    radius_ratio = numerical_radius / reference_inlet_radius
    area_ratio = radius_ratio * radius_ratio

    reference_solver_source = {
        "x": float(channel["inlet_center_y_m"]),
        "y": float(channel["inlet_center_x_m"]),
        "z": float(channel["inlet_center_z_m"]),
    }
    numerical_source = {
        "x": float_param(params, "prob.leak_xc"),
        "y": float_param(params, "prob.leak_yc"),
        "z": float_param(params, "prob.leak_zc"),
    }
    source_offset = {
        axis: numerical_source[axis] - reference_solver_source[axis]
        for axis in ("x", "y", "z")
    }

    n_cell = vector_param(params, "amr.n_cell")
    prob_lo = vector_param(params, "geometry.prob_lo")
    prob_hi = vector_param(params, "geometry.prob_hi")
    cell_size = [(hi - lo) / n for lo, hi, n in zip(prob_lo, prob_hi, n_cell)]
    radius_cells = numerical_radius / min(cell_size)
    reference_radius_cells = reference_inlet_radius / min(cell_size)
    min_active_radius_at_reference_source = nearest_cell_center_distance(
        reference_solver_source, prob_lo, cell_size, n_cell
    )

    coord_map = {str(item["id"]): item for item in sensors["sensors"]}
    checks = [
        sensor_check_summary(check, coord_map)
        for check in agreement["comparison"]["sensor_checks"]
    ]
    severe_peak = [c for c in checks if c["peak_rel_error"] > 0.75]
    severe_over = [c for c in severe_peak if c["peak_bias"] == "over"]
    severe_under = [c for c in severe_peak if c["peak_bias"] == "under"]
    infinite_arrival = [c for c in checks if c["arrival_error_is_infinite"]]
    near_source_over = [
        c for c in severe_over
        if c["solver_z_m"] is not None and c["solver_z_m"] >= 0.55
    ]

    diagnosis = {
        "primary_failure_mode": "source_model_and_geometry_calibration_not_numerical_stability",
        "source_radius_too_large_for_strict_experiment_parity": radius_ratio > 10.0,
        "source_center_height_offset_is_material": abs(source_offset["z"]) >= 0.05,
        "all_regular_geometry_used": params.get("eb2.geom_type") == "all_regular",
        "coarse_wall_sensor_sampling_used": min(cell_size) >= 0.04,
        "reference_source_requires_grid_aware_radius_or_refinement": min_active_radius_at_reference_source > 0.04,
        "reactor_null_used_for_dispersion_only": params.get("peleLM.chem_integrator") == "ReactorNull",
        "strict_blocker_cleared": False,
    }

    next_calibration_inputs = {
        "prob.leak_zc": reference_solver_source["z"],
        "minimum_active_radius_at_reference_source_on_current_grid_m": min_active_radius_at_reference_source,
        "prob.leak_radius_options_m_current_grid": [0.05, 0.06, 0.08],
        "prob.leak_radius_options_m_requires_refinement_or_cell_projection": [0.025, 0.04],
        "prob.leak_rate": float_param(params, "prob.leak_rate"),
        "amr.n_cell_options": ["232 36 32", "174 27 24"],
        "geometry_required_change": "replace eb2.geom_type=all_regular with encoded DataverseNO internal component/obstacle bounds before strict geometry parity",
        "scoring_policy": "re-run 45 s first for LFL timing, then 120 s for peak-window agreement after source-height/radius changes",
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "summary": {
            "agreement_status": agreement["status"],
            "simulation_time_end_s": summary["simulation_time_end_s"],
            "simulation_mass_ratio_final": summary["simulation_mass_ratio_final"],
            "sensor_count": summary["sensor_count"],
            "failed_sensor_count": summary["failed_sensor_count"],
            "peak_pass_count": summary["peak_pass_count"],
            "nrmse_pass_count": summary["nrmse_pass_count"],
            "arrival_pass_count": summary["arrival_pass_count"],
            "numerical_source_radius_m": numerical_radius,
            "reference_inlet_radius_m": reference_inlet_radius,
            "source_radius_ratio": radius_ratio,
            "source_area_ratio": area_ratio,
            "source_center_z_offset_m": source_offset["z"],
            "minimum_active_radius_at_reference_source_on_current_grid_m": min_active_radius_at_reference_source,
            "all_regular_geometry_used": diagnosis["all_regular_geometry_used"],
            "severe_peak_error_count": len(severe_peak),
            "severe_peak_overprediction_count": len(severe_over),
            "severe_peak_underprediction_count": len(severe_under),
            "infinite_arrival_error_count": len(infinite_arrival),
            "near_source_high_sensor_overprediction_count": len(near_source_over),
            "strict_external_plume_blocker_cleared": False,
            "ready_for_next_calibration_sweep": True,
        },
        "diagnosis": diagnosis,
        "reference_solver_source_center_m": reference_solver_source,
        "numerical_source_center_m": numerical_source,
        "source_center_offset_m": source_offset,
        "mesh": {
            "n_cell": n_cell,
            "cell_size_m": cell_size,
            "numerical_source_radius_cells": radius_cells,
            "reference_inlet_radius_cells": reference_radius_cells,
        },
        "next_calibration_inputs": next_calibration_inputs,
        "worst_peak_error_sensors": sorted(checks, key=lambda c: c["peak_rel_error"], reverse=True)[:10],
        "worst_nrmse_sensors": sorted(checks, key=lambda c: c["nrmse"], reverse=True)[:10],
        "infinite_arrival_error_sensors": infinite_arrival,
        "sensor_checks": checks,
        "evidence_files": [
            evidence_entry("dataverse_120s_agreement_report", AGREEMENT_REPORT),
            evidence_entry("dataverse_120s_input_deck", INPUT_DECK),
            evidence_entry("dataverse_120s_sensor_coords", SENSOR_COORDS),
            evidence_entry("dataverse_geometry_mapping_report", GEOMETRY_REPORT),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("sensor_count") == 29, "sensor count mismatch")
    require(summary.get("simulation_time_end_s", 0.0) >= 119.9, "120 s run not represented")
    require(summary.get("simulation_mass_ratio_final") == 1.0, "mass ratio evidence missing")
    require(summary.get("source_radius_ratio", 0.0) > 10.0, "source radius ratio diagnosis missing")
    require(abs(summary.get("source_center_z_offset_m", 0.0)) >= 0.05, "source height offset diagnosis missing")
    require(summary.get("minimum_active_radius_at_reference_source_on_current_grid_m", 0.0) > 0.04, "grid-aware minimum radius diagnosis missing")
    require(summary.get("strict_external_plume_blocker_cleared") is False, "diagnosis must not clear strict blocker")
    require(summary.get("ready_for_next_calibration_sweep") is True, "next calibration sweep not ready")
    require(data.get("diagnosis", {}).get("primary_failure_mode") == "source_model_and_geometry_calibration_not_numerical_stability", "primary diagnosis mismatch")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# DataverseNO 120s Calibration Diagnosis",
        "",
        f"- Status: `{report['status']}`",
        f"- 120 s agreement status: `{s['agreement_status']}`",
        f"- Source radius ratio vs experiment: `{s['source_radius_ratio']}`",
        f"- Source area ratio vs experiment: `{s['source_area_ratio']}`",
        f"- Source center z offset: `{s['source_center_z_offset_m']}` m",
        f"- Minimum active radius at reference source on current grid: `{s['minimum_active_radius_at_reference_source_on_current_grid_m']}` m",
        f"- Severe peak errors: `{s['severe_peak_error_count']}`",
        f"- Severe over/under prediction: `{s['severe_peak_overprediction_count']}` / `{s['severe_peak_underprediction_count']}`",
        f"- Infinite LFL arrival errors: `{s['infinite_arrival_error_count']}`",
        f"- Strict external plume blocker cleared: `{s['strict_external_plume_blocker_cleared']}`",
        "",
        "## Next Calibration Inputs",
        "",
    ]
    for key, value in report["next_calibration_inputs"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"dataverse_open_channel_120s_calibration_diagnosis VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"dataverse_open_channel_120s_calibration_diagnosis PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
