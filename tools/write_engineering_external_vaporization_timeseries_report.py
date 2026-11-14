#!/usr/bin/env python3
"""Write/verify external vaporization mdot(t) time-series coupling evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_external_vaporization_timeseries_20260806")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "engineering_external_vaporization_timeseries_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "engineering_external_vaporization_timeseries_report.md"

PROB_CPP = Path("examples/engineering/h2_leak_3d/pelelmex_prob.cpp")
PROB_HEADER = Path("examples/engineering/h2_leak_3d/pelelmex_prob.H")
CONVERTER = Path("tools/codex_make_external_vaporization_source_input.py")
SMOKE_INPUT = Path("examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_timeseries_smoke")
SMOKE_LOG = DEFAULT_ROOT / "fixed_mass_flow_timeseries_smoke.log"
CSV_TEMPLATE = Path("examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv")
BASE_INPUT = Path("examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke")
CONVERTER_OUTPUT_INPUT = DEFAULT_ROOT / "input.codex_lng_external_vaporization_timeseries"
CONVERTER_OUTPUT_JSON = DEFAULT_ROOT / "external_vaporization_timeseries_mapping.json"

BAD_LOG_TOKENS = (
    "Abort",
    "AMReX Error",
    "SIGABRT",
    "Segmentation fault",
    "nan",
    "NaN",
    "inf",
    "INF",
)


class TimeSeriesReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TimeSeriesReportError(message)


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
        raise TimeSeriesReportError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TimeSeriesReportError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def parse_float_series(pattern: str, text: str) -> list[float]:
    return [float(match.group(1)) for match in re.finditer(pattern, text)]


def run_converter() -> dict[str, Any]:
    CONVERTER_OUTPUT_INPUT.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(CONVERTER),
        "--source-csv",
        str(CSV_TEMPLATE),
        "--base-input",
        str(BASE_INPUT),
        "--time",
        "2.0",
        "--output-input",
        str(CONVERTER_OUTPUT_INPUT),
        "--output-json",
        str(CONVERTER_OUTPUT_JSON),
    ]
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    require(result.returncode == 0, f"converter failed rc={result.returncode}: {result.stderr.strip()}")
    return {
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def build_report() -> dict[str, Any]:
    require(PROB_CPP.is_file(), f"missing problem cpp: {PROB_CPP}")
    require(PROB_HEADER.is_file(), f"missing problem header: {PROB_HEADER}")
    require(CONVERTER.is_file(), f"missing converter: {CONVERTER}")
    require(SMOKE_INPUT.is_file(), f"missing smoke input: {SMOKE_INPUT}")
    require(SMOKE_LOG.is_file(), f"missing smoke log: {SMOKE_LOG}")

    cpp_text = PROB_CPP.read_text(encoding="utf-8")
    header_text = PROB_HEADER.read_text(encoding="utf-8")
    input_text = SMOKE_INPUT.read_text(encoding="utf-8")
    log_text = SMOKE_LOG.read_text(encoding="utf-8", errors="replace")

    conversion = run_converter()
    mapping = load_json(CONVERTER_OUTPUT_JSON)
    generated_input_text = CONVERTER_OUTPUT_INPUT.read_text(encoding="utf-8")
    source_time_series = mapping.get("source_time_series", {})

    source_has_schedule_storage = all(
        token in header_text
        for token in (
            "max_leak_schedule_points",
            "leak_schedule_count",
            "leak_schedule_times",
            "leak_schedule_rates",
            "leak_schedule_temperatures",
            "leak_schedule_vel_x",
            "leak_schedule_vel_y",
            "leak_schedule_vel_z",
            "leak_schedule_radius",
            "leak_schedule_x",
            "leak_schedule_y",
            "leak_schedule_z",
        )
    )
    parser_validates_schedule = all(
        token in cpp_text
        for token in (
            "prob.leak_schedule_times and prob.leak_schedule_rates must be provided together",
            "prob.leak_schedule_times/rates must contain 2 to 64 points",
            "prob.leak_schedule_times must be nonnegative and strictly increasing",
            "prob.leak_schedule_rates must be nonnegative",
            "prob.leak_schedule_temperatures must be positive",
            "prob.leak_schedule_vel_x/y/z must match leak_schedule_times/rates length",
            "prob.leak_schedule_radius must be positive",
            "prob.leak_schedule_radius and prob.leak_schedule_x/y/z are supported only for single-source leaks",
        )
    )
    runtime_interpolates_schedule = all(
        token in header_text
        for token in (
            "scheduled_reference_mdot",
            "scheduled_leak_T",
            "sample_time = time + 0.5 * dt",
            "pp->leak_schedule_rates[n + 1] - pp->leak_schedule_rates[n]",
            "pp->leak_schedule_temperatures[n + 1] -",
            "pp->leak_schedule_vel_x[n + 1] -",
            "scheduled_velocity=(",
            "pp->leak_schedule_radius[n + 1] -",
            "scheduled_center=(",
            "eos.TY2H(scheduled_leak_T",
            "fixed_mass_flow_timeseries",
        )
    )
    converter_emits_schedule = all(
        token in generated_input_text
        for token in (
            "prob.leak_schedule_count =",
            "prob.leak_schedule_times =",
            "prob.leak_schedule_rates =",
            "prob.leak_schedule_temperatures =",
            "prob.leak_schedule_vel_x =",
            "prob.leak_schedule_vel_y =",
            "prob.leak_schedule_vel_z =",
            "prob.leak_schedule_radius =",
            "prob.leak_schedule_x =",
            "prob.leak_schedule_y =",
            "prob.leak_schedule_z =",
        )
    )
    mapping_emits_time_series = (
        source_time_series.get("emitted_to_input") is True
        and source_time_series.get("point_count", 0) >= 2
    )
    input_uses_schedule = all(
        token in input_text
        for token in (
            "prob.leak_model = fixed_mass_flow",
            "prob.leak_schedule_count = 4",
            "prob.leak_schedule_times = 0.0 2.0e-5 4.0e-5 6.0e-5",
            "prob.leak_schedule_rates = 0.0 2.0e-5 1.0e-5 1.5e-5",
            "prob.leak_schedule_temperatures = 280.0 320.0 260.0 300.0",
            "prob.leak_schedule_vel_x = 0.5 1.5 0.25 1.0",
            "prob.leak_schedule_vel_y = 0.0 0.2 -0.1 0.0",
            "prob.leak_schedule_vel_z = 0.0 0.0 0.1 0.0",
            "prob.leak_schedule_radius = 0.12 0.15 0.10 0.13",
            "prob.leak_schedule_x = 0.45 0.50 0.55 0.60",
            "prob.leak_schedule_y = 0.25 0.27 0.23 0.25",
            "prob.leak_schedule_z = 0.25 0.25 0.28 0.25",
        )
    )

    bad_tokens = sorted({token for token in BAD_LOG_TOKENS if token in log_text})
    schedule_lines = [
        line for line in log_text.splitlines() if "leak fixed-mass-flow schedule:" in line
    ]
    schedule_counts = parse_float_series(r"schedule_count=([0-9.eE+-]+)", "\n".join(schedule_lines))
    scheduled_mdots = parse_float_series(
        r"scheduled_reference_mdot=([0-9.eE+-]+)", "\n".join(schedule_lines)
    )
    scheduled_temps = parse_float_series(
        r"scheduled_leak_T=([0-9.eE+-]+)", "\n".join(schedule_lines)
    )
    scheduled_vx = parse_float_series(
        r"scheduled_velocity=\(([0-9.eE+-]+),", "\n".join(schedule_lines)
    )
    scheduled_vy = parse_float_series(
        r"scheduled_velocity=\([0-9.eE+-]+,([0-9.eE+-]+),", "\n".join(schedule_lines)
    )
    scheduled_vz = parse_float_series(
        r"scheduled_velocity=\([0-9.eE+-]+,[0-9.eE+-]+,([0-9.eE+-]+)\)", "\n".join(schedule_lines)
    )
    scheduled_radius = parse_float_series(
        r"scheduled_radius=([0-9.eE+-]+)", "\n".join(schedule_lines)
    )
    scheduled_x = parse_float_series(
        r"scheduled_center=\(([0-9.eE+-]+),", "\n".join(schedule_lines)
    )
    scheduled_y = parse_float_series(
        r"scheduled_center=\([0-9.eE+-]+,([0-9.eE+-]+),", "\n".join(schedule_lines)
    )
    scheduled_z = parse_float_series(
        r"scheduled_center=\([0-9.eE+-]+,[0-9.eE+-]+,([0-9.eE+-]+)\)", "\n".join(schedule_lines)
    )
    effective_mdots = parse_float_series(r"effective_mdot=([0-9.eE+-]+)", "\n".join(schedule_lines))
    applied_mdots = parse_float_series(
        r"Applying H2 leak source: model=fixed_mass_flow_timeseries, mdot=([0-9.eE+-]+)",
        log_text,
    )
    schedule_count_ok = bool(schedule_counts) and all(int(value) == 4 for value in schedule_counts)
    mdot_varies = bool(scheduled_mdots) and min(scheduled_mdots) < max(scheduled_mdots)
    has_falling_segment = any(
        right < left for left, right in zip(scheduled_mdots, scheduled_mdots[1:])
    )
    has_rising_segment = any(
        right > left for left, right in zip(scheduled_mdots, scheduled_mdots[1:])
    )
    applied_matches_effective = applied_mdots == effective_mdots[: len(applied_mdots)]
    temp_varies = bool(scheduled_temps) and min(scheduled_temps) < max(scheduled_temps)
    temp_has_falling_segment = any(
        right < left for left, right in zip(scheduled_temps, scheduled_temps[1:])
    )
    temp_has_rising_segment = any(
        right > left for left, right in zip(scheduled_temps, scheduled_temps[1:])
    )
    vx_varies = bool(scheduled_vx) and min(scheduled_vx) < max(scheduled_vx)
    vy_varies = bool(scheduled_vy) and min(scheduled_vy) < max(scheduled_vy)
    vz_varies = bool(scheduled_vz) and min(scheduled_vz) < max(scheduled_vz)
    radius_varies = bool(scheduled_radius) and min(scheduled_radius) < max(scheduled_radius)
    x_varies = bool(scheduled_x) and min(scheduled_x) < max(scheduled_x)
    y_varies = bool(scheduled_y) and min(scheduled_y) < max(scheduled_y)
    z_varies = bool(scheduled_z) and min(scheduled_z) < max(scheduled_z)

    ready = (
        source_has_schedule_storage
        and parser_validates_schedule
        and runtime_interpolates_schedule
        and converter_emits_schedule
        and mapping_emits_time_series
        and input_uses_schedule
        and not bad_tokens
        and len(schedule_lines) >= 6
        and schedule_count_ok
        and mdot_varies
        and has_falling_segment
        and has_rising_segment
        and temp_varies
        and temp_has_falling_segment
        and temp_has_rising_segment
        and vx_varies
        and vy_varies
        and vz_varies
        and radius_varies
        and x_varies
        and y_varies
        and z_varies
        and applied_matches_effective
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES",
        "summary": {
            "external_vaporization_timeseries_ready": ready,
            "source_has_schedule_storage": source_has_schedule_storage,
            "parser_validates_schedule": parser_validates_schedule,
            "runtime_interpolates_schedule": runtime_interpolates_schedule,
            "converter_emits_schedule": converter_emits_schedule,
            "mapping_emits_time_series": mapping_emits_time_series,
            "input_uses_schedule": input_uses_schedule,
            "log_has_no_abort_or_nan": not bad_tokens,
            "bad_log_tokens": bad_tokens,
            "schedule_log_line_count": len(schedule_lines),
            "schedule_count_ok": schedule_count_ok,
            "scheduled_reference_mdot_min": min(scheduled_mdots) if scheduled_mdots else None,
            "scheduled_reference_mdot_max": max(scheduled_mdots) if scheduled_mdots else None,
            "scheduled_reference_mdot_varies": mdot_varies,
            "scheduled_reference_mdot_has_rising_segment": has_rising_segment,
            "scheduled_reference_mdot_has_falling_segment": has_falling_segment,
            "scheduled_leak_T_min": min(scheduled_temps) if scheduled_temps else None,
            "scheduled_leak_T_max": max(scheduled_temps) if scheduled_temps else None,
            "scheduled_leak_T_varies": temp_varies,
            "scheduled_leak_T_has_rising_segment": temp_has_rising_segment,
            "scheduled_leak_T_has_falling_segment": temp_has_falling_segment,
            "scheduled_velocity_x_min": min(scheduled_vx) if scheduled_vx else None,
            "scheduled_velocity_x_max": max(scheduled_vx) if scheduled_vx else None,
            "scheduled_velocity_y_min": min(scheduled_vy) if scheduled_vy else None,
            "scheduled_velocity_y_max": max(scheduled_vy) if scheduled_vy else None,
            "scheduled_velocity_z_min": min(scheduled_vz) if scheduled_vz else None,
            "scheduled_velocity_z_max": max(scheduled_vz) if scheduled_vz else None,
            "scheduled_velocity_x_varies": vx_varies,
            "scheduled_velocity_y_varies": vy_varies,
            "scheduled_velocity_z_varies": vz_varies,
            "scheduled_radius_min": min(scheduled_radius) if scheduled_radius else None,
            "scheduled_radius_max": max(scheduled_radius) if scheduled_radius else None,
            "scheduled_radius_varies": radius_varies,
            "scheduled_center_x_min": min(scheduled_x) if scheduled_x else None,
            "scheduled_center_x_max": max(scheduled_x) if scheduled_x else None,
            "scheduled_center_y_min": min(scheduled_y) if scheduled_y else None,
            "scheduled_center_y_max": max(scheduled_y) if scheduled_y else None,
            "scheduled_center_z_min": min(scheduled_z) if scheduled_z else None,
            "scheduled_center_z_max": max(scheduled_z) if scheduled_z else None,
            "scheduled_center_x_varies": x_varies,
            "scheduled_center_y_varies": y_varies,
            "scheduled_center_z_varies": z_varies,
            "applied_mdot_matches_effective_mdot": applied_matches_effective,
            "converter_schedule_point_count": source_time_series.get("point_count"),
            "converter_temperature_point_count": len(source_time_series.get("vapor_T_K", [])),
            "converter_velocity_x_point_count": len(source_time_series.get("leak_vel_x_m_s", [])),
            "converter_velocity_y_point_count": len(source_time_series.get("leak_vel_y_m_s", [])),
            "converter_velocity_z_point_count": len(source_time_series.get("leak_vel_z_m_s", [])),
            "converter_radius_point_count": len(source_time_series.get("source_radius_m", [])),
            "converter_location_x_point_count": len(source_time_series.get("source_x_m", [])),
            "converter_location_y_point_count": len(source_time_series.get("source_y_m", [])),
            "converter_location_z_point_count": len(source_time_series.get("source_z_m", [])),
        },
        "conversion": conversion,
        "log_samples": {
            "first_schedule_line": schedule_lines[0] if schedule_lines else "",
            "last_schedule_line": schedule_lines[-1] if schedule_lines else "",
            "scheduled_reference_mdots": scheduled_mdots,
            "scheduled_leak_Ts": scheduled_temps,
            "scheduled_velocity_x": scheduled_vx,
            "scheduled_velocity_y": scheduled_vy,
            "scheduled_velocity_z": scheduled_vz,
            "scheduled_radius": scheduled_radius,
            "scheduled_center_x": scheduled_x,
            "scheduled_center_y": scheduled_y,
            "scheduled_center_z": scheduled_z,
            "effective_mdots": effective_mdots,
        },
        "evidence_files": [
            evidence_entry("problem_cpp", PROB_CPP),
            evidence_entry("problem_header", PROB_HEADER),
            evidence_entry("converter", CONVERTER),
            evidence_entry("smoke_input", SMOKE_INPUT),
            evidence_entry("smoke_log", SMOKE_LOG),
            evidence_entry("converter_output_input", CONVERTER_OUTPUT_INPUT),
            evidence_entry("converter_output_json", CONVERTER_OUTPUT_JSON),
        ],
    }


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS, "report is not PASS")
    summary = data.get("summary", {})
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("external_vaporization_timeseries_ready") is True, "timeseries coupling is not ready")
    require(summary.get("source_has_schedule_storage") is True, "schedule storage missing")
    require(summary.get("parser_validates_schedule") is True, "schedule parser guards missing")
    require(summary.get("runtime_interpolates_schedule") is True, "runtime interpolation missing")
    require(summary.get("converter_emits_schedule") is True, "converter does not emit schedule")
    require(summary.get("mapping_emits_time_series") is True, "mapping JSON does not record time series")
    require(summary.get("input_uses_schedule") is True, "smoke input does not use schedule")
    require(summary.get("log_has_no_abort_or_nan") is True, "smoke log contains abort/nan markers")
    require(summary.get("schedule_log_line_count", 0) >= 6, "too few schedule log lines")
    require(summary.get("schedule_count_ok") is True, "wrong schedule count in log")
    require(summary.get("scheduled_reference_mdot_varies") is True, "schedule mdot did not vary")
    require(summary.get("scheduled_reference_mdot_has_rising_segment") is True, "schedule lacks rising segment")
    require(summary.get("scheduled_reference_mdot_has_falling_segment") is True, "schedule lacks falling segment")
    require(summary.get("scheduled_leak_T_varies") is True, "schedule leak temperature did not vary")
    require(summary.get("scheduled_leak_T_has_rising_segment") is True, "temperature schedule lacks rising segment")
    require(summary.get("scheduled_leak_T_has_falling_segment") is True, "temperature schedule lacks falling segment")
    require(summary.get("scheduled_velocity_x_varies") is True, "velocity x schedule did not vary")
    require(summary.get("scheduled_velocity_y_varies") is True, "velocity y schedule did not vary")
    require(summary.get("scheduled_velocity_z_varies") is True, "velocity z schedule did not vary")
    require(summary.get("scheduled_radius_varies") is True, "source radius schedule did not vary")
    require(summary.get("scheduled_center_x_varies") is True, "source x schedule did not vary")
    require(summary.get("scheduled_center_y_varies") is True, "source y schedule did not vary")
    require(summary.get("scheduled_center_z_varies") is True, "source z schedule did not vary")
    require(summary.get("applied_mdot_matches_effective_mdot") is True, "applied mdot does not match effective mdot")
    require(summary.get("converter_schedule_point_count", 0) >= 2, "converter schedule has too few points")
    require(summary.get("converter_temperature_point_count", 0) >= 2, "converter temperature schedule has too few points")
    require(summary.get("converter_velocity_x_point_count", 0) >= 2, "converter velocity x schedule has too few points")
    require(summary.get("converter_velocity_y_point_count", 0) >= 2, "converter velocity y schedule has too few points")
    require(summary.get("converter_velocity_z_point_count", 0) >= 2, "converter velocity z schedule has too few points")
    require(summary.get("converter_radius_point_count", 0) >= 2, "converter radius schedule has too few points")
    require(summary.get("converter_location_x_point_count", 0) >= 2, "converter location x schedule has too few points")
    require(summary.get("converter_location_y_point_count", 0) >= 2, "converter location y schedule has too few points")
    require(summary.get("converter_location_z_point_count", 0) >= 2, "converter location z schedule has too few points")
    if verify_hashes:
        for item in data.get("evidence_files", []):
            path = Path(str(item.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == item.get("sha256"), f"evidence sha256 mismatch: {path}")


def write_outputs(report: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = report["summary"]
    lines = [
        "# Engineering External Vaporization Time Series",
        "",
        f"- Status: `{report['status']}`",
        f"- Runtime interpolates schedule: `{summary['runtime_interpolates_schedule']}`",
        f"- Converter emits schedule: `{summary['converter_emits_schedule']}`",
        f"- Smoke log clean: `{summary['log_has_no_abort_or_nan']}`",
        f"- Schedule mdot range: `{summary['scheduled_reference_mdot_min']}` to `{summary['scheduled_reference_mdot_max']}`",
        f"- Schedule temperature range: `{summary['scheduled_leak_T_min']}` to `{summary['scheduled_leak_T_max']}`",
        f"- Schedule velocity x range: `{summary['scheduled_velocity_x_min']}` to `{summary['scheduled_velocity_x_max']}`",
        f"- Schedule radius range: `{summary['scheduled_radius_min']}` to `{summary['scheduled_radius_max']}`",
        f"- Schedule center x range: `{summary['scheduled_center_x_min']}` to `{summary['scheduled_center_x_max']}`",
        f"- Rising segment: `{summary['scheduled_reference_mdot_has_rising_segment']}`",
        f"- Falling segment: `{summary['scheduled_reference_mdot_has_falling_segment']}`",
        "",
        "## Evidence",
        "",
    ]
    for item in report["evidence_files"]:
        lines.append(f"- `{item['label']}`: `{item['path']}`")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data)
            print(f"engineering_external_vaporization_timeseries VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report()
        validate_report(report, verify_hashes=False)
        write_outputs(report, Path(args.output_json), Path(args.output_md))
        print(f"engineering_external_vaporization_timeseries {report['status']} json={args.output_json}")
        return 0
    except TimeSeriesReportError as exc:
        print(f"engineering_external_vaporization_timeseries ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
