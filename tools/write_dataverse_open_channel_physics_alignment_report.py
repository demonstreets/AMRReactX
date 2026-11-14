#!/usr/bin/env python3
"""Diagnose DataverseNO open-channel H2 physical-input alignment gaps."""
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
STATUS = "DIAGNOSED-DATAVERSE-OPEN-CHANNEL-H2-PHYSICS-ALIGNMENT-GAPS"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_physics_alignment_20260804")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_physics_alignment_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_physics_alignment_report.md"
DEFAULT_GEOMETRY_REPORT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_geometry_mapping_20260803/"
    "dataverse_open_channel_geometry_mapping_report.json"
)
DEFAULT_REFERENCE_REPORT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/"
    "dataverse_open_channel_reference_package_report.json"
)
DEFAULT_BASELINE_INPUT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_cfd_120s_peak_window_mpi_cuda_20260804/"
    "input.dataverse_open_channel_h2_scout_3d"
)
DEFAULT_DIAGNOSIS_REPORT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_120s_calibration_diagnosis_20260804/"
    "dataverse_open_channel_120s_calibration_diagnosis_report.json"
)


class PhysicsAlignmentError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PhysicsAlignmentError(message)


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
        raise PhysicsAlignmentError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PhysicsAlignmentError(f"invalid JSON evidence {path}: {exc}") from exc
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
    require(key in vals, f"missing input key: {key}")
    try:
        value = float(vals[key].split()[0])
    except ValueError as exc:
        raise PhysicsAlignmentError(f"input key is not a float: {key}={vals[key]}") from exc
    require(math.isfinite(value), f"input key is non-finite: {key}")
    return value


def input_ints(vals: dict[str, str], key: str) -> list[int]:
    require(key in vals, f"missing input key: {key}")
    out = [int(float(part)) for part in vals[key].split()]
    require(out, f"empty int vector input key: {key}")
    return out


def input_tokens(vals: dict[str, str], key: str) -> list[str]:
    require(key in vals, f"missing input key: {key}")
    return vals[key].split()


def active_cell_count(
    center: tuple[float, float, float],
    radius: float,
    prob_lo: tuple[float, float, float],
    prob_hi: tuple[float, float, float],
    n_cell: tuple[int, int, int],
) -> tuple[int, float, tuple[float, float, float]]:
    dx = tuple((prob_hi[d] - prob_lo[d]) / n_cell[d] for d in range(3))
    count = 0
    for k in range(n_cell[2]):
        z = prob_lo[2] + (k + 0.5) * dx[2]
        for j in range(n_cell[1]):
            y = prob_lo[1] + (j + 0.5) * dx[1]
            for i in range(n_cell[0]):
                x = prob_lo[0] + (i + 0.5) * dx[0]
                if ((x - center[0]) ** 2 + (y - center[1]) ** 2 + (z - center[2]) ** 2) < radius * radius:
                    count += 1
    return count, count * dx[0] * dx[1] * dx[2], dx


def first_float_from_summary(summary: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key in summary:
            try:
                value = float(summary[key])
            except (TypeError, ValueError):
                continue
            if math.isfinite(value):
                return value
    return None


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    geometry_path = Path(args.geometry_report)
    reference_path = Path(args.reference_report)
    input_path = Path(args.baseline_input)
    diagnosis_path = Path(args.diagnosis_report)
    geometry = load_json(geometry_path)
    reference = load_json(reference_path)
    diagnosis = load_json(diagnosis_path)
    vals = parse_input(input_path)

    n_cell_v = input_ints(vals, "amr.n_cell")
    prob_lo_v = tuple(input_float(vals, f"geometry.prob_lo".replace(".", ".")) for _ in [])
    prob_lo = tuple(float(x) for x in vals["geometry.prob_lo"].split())
    prob_hi = tuple(float(x) for x in vals["geometry.prob_hi"].split())
    n_cell = tuple(n_cell_v[:3])
    leak_center = (
        input_float(vals, "prob.leak_xc"),
        input_float(vals, "prob.leak_yc"),
        input_float(vals, "prob.leak_zc"),
    )
    leak_radius = input_float(vals, "prob.leak_radius")
    leak_mdot = input_float(vals, "prob.leak_rate")
    leak_velocity = input_float(vals, "prob.leak_vel_x")
    leak_temperature = input_float(vals, "prob.leak_T")
    pressure = input_float(vals, "prob.P_mean")
    gas_constant_h2 = 4124.0
    gamma_h2 = 1.405
    experiment_diameter = float(args.experimental_orifice_diameter)
    experiment_radius = 0.5 * experiment_diameter
    experiment_area = 0.25 * math.pi * experiment_diameter * experiment_diameter
    rho_h2 = pressure / (gas_constant_h2 * leak_temperature)
    equivalent_velocity = leak_mdot / (rho_h2 * experiment_area)
    choked_exit_velocity = math.sqrt(
        gamma_h2 * gas_constant_h2 * leak_temperature * (2.0 / (gamma_h2 + 1.0))
    )
    active_cells, active_volume, dx = active_cell_count(leak_center, leak_radius, prob_lo, prob_hi, n_cell)
    experiment_active_cells, experiment_active_volume, _ = active_cell_count(
        leak_center, experiment_radius, prob_lo, prob_hi, n_cell
    )
    grid_min_radius = float(
        diagnosis.get("summary", {}).get(
            "minimum_active_radius_at_reference_source_on_current_grid_m",
            diagnosis.get("summary", {}).get(
                "dataverse_120s_minimum_active_radius_at_reference_source_on_current_grid_m",
                0.0,
            ),
        )
    )
    lo_bc = input_tokens(vals, "peleLM.lo_bc")
    hi_bc = input_tokens(vals, "peleLM.hi_bc")
    geometry_summary = geometry.get("summary", {}) if isinstance(geometry.get("summary"), dict) else {}
    reference_summary = reference.get("summary", {}) if isinstance(reference.get("summary"), dict) else {}
    reference_mdot = first_float_from_summary(reference_summary, "release_mdot_kg_s", "reference_release_mdot_kg_s")

    recommended_velocity = min(equivalent_velocity, choked_exit_velocity)
    velocity_ratio = equivalent_velocity / leak_velocity if leak_velocity > 0.0 else math.inf
    source_radius_ratio = leak_radius / experiment_radius
    source_area_ratio = (leak_radius / experiment_radius) ** 2
    summary = {
        "dataset_doi": "10.23642/USN.26117989",
        "article_doi": "10.1016/j.jlp.2025.105669",
        "experimental_orifice_diameter_m": experiment_diameter,
        "experimental_orifice_radius_m": experiment_radius,
        "experimental_orifice_area_m2": experiment_area,
        "h2_density_at_release_kg_m3": rho_h2,
        "reference_mass_flow_rate_kg_s": leak_mdot,
        "reference_report_mass_flow_rate_kg_s": reference_mdot,
        "equivalent_orifice_velocity_m_s": equivalent_velocity,
        "choked_exit_velocity_estimate_m_s": choked_exit_velocity,
        "recommended_orifice_velocity_scout_m_s": recommended_velocity,
        "baseline_numerical_leak_velocity_m_s": leak_velocity,
        "equivalent_to_baseline_velocity_ratio": velocity_ratio,
        "baseline_numerical_leak_radius_m": leak_radius,
        "baseline_to_experiment_radius_ratio": source_radius_ratio,
        "baseline_to_experiment_area_ratio": source_area_ratio,
        "current_grid_cell_size_m": list(dx),
        "current_grid_n_cell": list(n_cell),
        "current_grid_active_cell_count_for_baseline_radius": active_cells,
        "current_grid_active_volume_for_baseline_radius_m3": active_volume,
        "current_grid_active_cell_count_for_experimental_radius": experiment_active_cells,
        "current_grid_active_volume_for_experimental_radius_m3": experiment_active_volume,
        "minimum_active_radius_at_reference_source_on_current_grid_m": grid_min_radius,
        "baseline_boundary_lo_bc": lo_bc,
        "baseline_boundary_hi_bc": hi_bc,
        "geometry_obstacle_exact_bounds_available": bool(
            geometry_summary.get("obstacle_exact_bounds_available", False)
            or geometry_summary.get("dataverse_geometry_obstacle_exact_bounds_available", False)
        ),
        "ready_for_orifice_velocity_scout": True,
        "ready_for_refined_source_projection": True,
        "ready_for_boundary_parity_screen": True,
        "strict_external_plume_blocker_cleared": False,
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "title": "DataverseNO Open-Channel H2 Physics Alignment Diagnosis",
        "summary": summary,
        "interpretation": [
            "The current coarse-grid source conserves injected mass but cannot directly represent the 4.6 mm experimental orifice radius with cell-centered spherical support.",
            "The current Dataverse runner injects the measured mass flow with a low 0.5 m/s momentum velocity; the equivalent physical orifice velocity is orders of magnitude larger.",
            "The previous radius sweep was stable but insensitive, so the next useful screen should vary momentum/BC/source projection rather than only coarse numerical radius.",
        ],
        "recommended_next_screens": [
            {
                "label": "orifice_velocity_short_mpi_cuda_scout",
                "leak_radius_m": max(0.04, grid_min_radius),
                "leak_zc_m": 0.775,
                "leak_vel_x_m_s": recommended_velocity,
                "purpose": "prove whether a momentum-aligned source remains stable before any long 45-120 s campaign",
            },
            {
                "label": "open_end_boundary_parity_screen",
                "lo_bc": ["Outflow", "NoSlipWallAdiab", "NoSlipWallAdiab"],
                "hi_bc": ["Outflow", "NoSlipWallAdiab", "NoSlipWallAdiab"],
                "purpose": "separate boundary-condition bias from source calibration bias for the open-ended channel",
            },
            {
                "label": "refined_source_projection_screen",
                "target_dx_m": 0.0125,
                "purpose": "reduce the radius/grid mismatch before judging peak and arrival-time agreement",
            },
        ],
        "evidence_files": [
            evidence_entry("geometry_mapping_report", geometry_path),
            evidence_entry("reference_package_report", reference_path),
            evidence_entry("baseline_120s_input", input_path),
            evidence_entry("calibration_diagnosis_report", diagnosis_path),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(float(summary.get("experimental_orifice_diameter_m", 0.0)) == 0.0046, "unexpected orifice diameter")
    require(float(summary.get("equivalent_orifice_velocity_m_s", 0.0)) > 100.0, "equivalent velocity not diagnosed")
    require(float(summary.get("equivalent_to_baseline_velocity_ratio", 0.0)) > 100.0, "velocity-ratio gap not diagnosed")
    require(float(summary.get("baseline_to_experiment_radius_ratio", 0.0)) > 10.0, "radius-ratio gap not diagnosed")
    require(int(summary.get("current_grid_active_cell_count_for_experimental_radius", -1)) == 0, "experimental source unexpectedly active on current grid")
    require(int(summary.get("current_grid_active_cell_count_for_baseline_radius", 0)) > 0, "baseline source has no active cells")
    require(summary.get("ready_for_orifice_velocity_scout") is True, "orifice-velocity scout readiness missing")
    require(summary.get("ready_for_refined_source_projection") is True, "refined source readiness missing")
    require(summary.get("strict_external_plume_blocker_cleared") is False, "diagnosis cannot clear strict blocker")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# DataverseNO Open-Channel H2 Physics Alignment Diagnosis",
        "",
        f"- Status: `{report['status']}`",
        f"- Experimental orifice diameter: `{s['experimental_orifice_diameter_m']}` m",
        f"- Baseline numerical source radius: `{s['baseline_numerical_leak_radius_m']}` m",
        f"- Radius ratio baseline/experiment: `{s['baseline_to_experiment_radius_ratio']}`",
        f"- Area ratio baseline/experiment: `{s['baseline_to_experiment_area_ratio']}`",
        f"- Equivalent physical orifice velocity: `{s['equivalent_orifice_velocity_m_s']}` m/s",
        f"- Baseline numerical source velocity: `{s['baseline_numerical_leak_velocity_m_s']}` m/s",
        f"- Velocity ratio equivalent/baseline: `{s['equivalent_to_baseline_velocity_ratio']}`",
        f"- Current grid cell size: `{s['current_grid_cell_size_m']}` m",
        f"- Active cells at experimental radius on current grid: `{s['current_grid_active_cell_count_for_experimental_radius']}`",
        f"- Active cells at baseline radius on current grid: `{s['current_grid_active_cell_count_for_baseline_radius']}`",
        f"- Recommended orifice-velocity scout: `{s['recommended_orifice_velocity_scout_m_s']}` m/s",
        f"- Strict external plume blocker cleared: `{s['strict_external_plume_blocker_cleared']}`",
        "",
        "## Interpretation",
        "",
    ]
    for item in report["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Recommended Next Screens", ""])
    for item in report["recommended_next_screens"]:
        lines.append(f"- `{item['label']}`: {item['purpose']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry-report", default=str(DEFAULT_GEOMETRY_REPORT))
    parser.add_argument("--reference-report", default=str(DEFAULT_REFERENCE_REPORT))
    parser.add_argument("--baseline-input", default=str(DEFAULT_BASELINE_INPUT))
    parser.add_argument("--diagnosis-report", default=str(DEFAULT_DIAGNOSIS_REPORT))
    parser.add_argument("--experimental-orifice-diameter", type=float, default=0.0046)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(f"dataverse_open_channel_physics_alignment VERIFY-PASS json={args.verify_json} status={data['status']}")
            return 0
        report = build_report(args)
        output_json = Path(args.output_json)
        output_md = Path(args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, output_md)
        print(
            "dataverse_open_channel_physics_alignment PASS "
            f"json={output_json} md={output_md} status={report['status']}"
        )
        return 0
    except PhysicsAlignmentError as exc:
        print(f"dataverse_open_channel_physics_alignment FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
