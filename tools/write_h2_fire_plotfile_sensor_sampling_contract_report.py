#!/usr/bin/env python3
"""Write/verify H2 fire plotfile sensor-sampling contract evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS = "PASS-H2-FIRE-PLOTFILE-SENSOR-SAMPLING-CONTRACT"
ROOT = Path("docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_contract_20260807")
DEFAULT_JSON = ROOT / "h2_fire_plotfile_sensor_sampling_contract_report.json"
DEFAULT_MD = ROOT / "h2_fire_plotfile_sensor_sampling_contract_report.md"
SENSOR_CSV = ROOT / "synthetic_pressure_sensor_locations.csv"
TIMESERIES_CSV = ROOT / "synthetic_pressure_sensor_timeseries.csv"
EXTRACTOR_JSON = ROOT / "plotfile_sensor_timeseries_extraction_report.json"
EXTRACTOR = Path("tools/codex_extract_plotfile_sensor_timeseries.py")
PLOTFILES = [
    Path("examples/engineering/h2_leak_3d/plt00000"),
    Path("examples/engineering/h2_leak_3d/plt00001"),
]
VARIABLES = ["avg_pressure", "temp", "Y(H2)"]


class ContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


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
        raise ContractError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def write_sensor_csv(path: Path) -> None:
    rows = [
        ("P01", 0.0625, 0.0625, 0.0625, "synthetic_non_cell_center_corner_probe"),
        ("P02", 0.25, 0.25, 0.25, "synthetic_non_cell_center_near_source_axis_probe"),
        ("P03", 0.50, 0.3125, 0.3125, "synthetic_non_cell_center_mid_domain_probe"),
        ("P04", 0.875, 0.375, 0.375, "synthetic_non_cell_center_far_field_probe"),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["sensor_id", "x_m", "y_m", "z_m", "source_basis"])
        writer.writerows(rows)


def run_extractor() -> None:
    cmd = [
        "python3",
        str(EXTRACTOR),
        "--sensor-csv",
        str(SENSOR_CSV),
        "--variables",
        *VARIABLES,
        "--sampling-mode",
        "linear",
        "--output-csv",
        str(TIMESERIES_CSV),
        "--output-json",
        str(EXTRACTOR_JSON),
    ]
    for plotfile in PLOTFILES:
        cmd.extend(["--plotfile", str(plotfile)])
    proc = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (ROOT / "extractor.log").write_text(proc.stdout, encoding="utf-8")
    require(proc.returncode == 0, f"extractor failed rc={proc.returncode}; see {ROOT / 'extractor.log'}")


def read_timeseries(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"missing timeseries CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    require(rows, "timeseries CSV has no rows")
    return rows


def build_report(_: argparse.Namespace) -> dict[str, Any]:
    require(EXTRACTOR.is_file(), f"missing extractor: {EXTRACTOR}")
    for plotfile in PLOTFILES:
        require((plotfile / "Header").is_file(), f"missing plotfile Header: {plotfile}")
    write_sensor_csv(SENSOR_CSV)
    run_extractor()

    extractor = load_json(EXTRACTOR_JSON)
    rows = read_timeseries(TIMESERIES_CSV)
    sensor_ids = sorted({row["sensor_id"] for row in rows})
    times = sorted({float(row["time_s"]) for row in rows})
    required_columns = {
        "plotfile",
        "time_s",
        "sensor_id",
        "sampling_mode",
        "requested_x_m",
        "requested_y_m",
        "requested_z_m",
        "sampled_x_m",
        "sampled_y_m",
        "sampled_z_m",
        "nearest_cell_distance_m",
        *VARIABLES,
    }
    missing_columns = sorted(required_columns.difference(rows[0].keys()))
    finite_value_count = 0
    max_nearest = 0.0
    max_abs_avg_pressure = 0.0
    sampling_modes = sorted({row.get("sampling_mode") for row in rows})
    for row in rows:
        require(not missing_columns, f"missing CSV columns: {missing_columns}")
        require(row.get("sampling_mode") == "linear", "sensor sampling contract must use linear mode")
        for name in ["nearest_cell_distance_m", *VARIABLES]:
            value = float(row[name])
            require(value == value and abs(value) < 1.0e300, f"non-finite {name}")
            finite_value_count += 1
        max_nearest = max(max_nearest, float(row["nearest_cell_distance_m"]))
        max_abs_avg_pressure = max(max_abs_avg_pressure, abs(float(row["avg_pressure"])))

    ready = (
        extractor.get("status") == "PASS-PLOTFILE-SENSOR-TIMESERIES-EXTRACTION"
        and extractor.get("summary", {}).get("sensor_timeseries_extracted") is True
        and len(rows) == len(PLOTFILES) * len(sensor_ids)
        and len(sensor_ids) == 4
        and len(times) == 2
        and not missing_columns
        and sampling_modes == ["linear"]
        and max_nearest > 0.0
        and max_abs_avg_pressure > 0.0
        and extractor.get("summary", {}).get("strict_fire_calibration_blocker_cleared") is False
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-H2-FIRE-PLOTFILE-SENSOR-SAMPLING-CONTRACT",
        "summary": {
            "plotfile_sensor_sampling_contract_ready": ready,
            "plotfile_count": len(PLOTFILES),
            "sensor_count": len(sensor_ids),
            "time_count": len(times),
            "row_count": len(rows),
            "variables": VARIABLES,
            "sampling_mode": "linear",
            "linear_interpolation_used": extractor.get("summary", {}).get("linear_interpolation_used") is True,
            "finite_value_count": finite_value_count,
            "max_nearest_cell_distance_m": max_nearest,
            "max_abs_avg_pressure_proxy": max_abs_avg_pressure,
            "pressure_sensor_timeseries_path_ready": True,
            "uses_synthetic_sensor_coordinates": True,
            "uses_non_cell_center_sensor_coordinates": True,
            "current_outputs_sufficient_for_exp002_pressure_agreement": False,
            "case_aligned_pressure_sensor_agreement": False,
            "radiation_agreement_executed": False,
            "strict_fire_calibration_blocker_cleared": False,
        },
        "claim_boundary": [
            "This proves a reusable plotfile sensor-sampling output path.",
            "It proves linear interpolation for non-cell-center synthetic sensor coordinates.",
            "It uses synthetic in-domain sensor locations, not EXP002 sensor coordinates.",
            "It samples avg_pressure as a pressure proxy and does not claim calibrated overpressure agreement.",
            "It does not address calibrated radiation agreement.",
        ],
        "output_files": {
            "sensor_csv": str(SENSOR_CSV),
            "timeseries_csv": str(TIMESERIES_CSV),
            "extractor_json": str(EXTRACTOR_JSON),
            "extractor_log": str(ROOT / "extractor.log"),
        },
        "evidence_files": [
            evidence_entry("plotfile_sensor_extractor", EXTRACTOR),
            evidence_entry("sensor_csv", SENSOR_CSV),
            evidence_entry("timeseries_csv", TIMESERIES_CSV),
            evidence_entry("extractor_json", EXTRACTOR_JSON),
            evidence_entry("extractor_log", ROOT / "extractor.log"),
            *[evidence_entry(f"{plotfile.name}_header", plotfile / "Header") for plotfile in PLOTFILES],
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS, "status mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("plotfile_sensor_sampling_contract_ready") is True, "sensor sampling contract not ready")
    require(summary.get("sensor_count") == 4, "unexpected sensor count")
    require(summary.get("time_count") == 2, "unexpected time count")
    require(summary.get("row_count") == 8, "unexpected extracted row count")
    require(summary.get("sampling_mode") == "linear", "linear sampling mode not recorded")
    require(summary.get("linear_interpolation_used") is True, "linear interpolation not exercised")
    require(summary.get("max_nearest_cell_distance_m", 0.0) > 0.0, "non-cell-center sensor distance not exercised")
    require(summary.get("pressure_sensor_timeseries_path_ready") is True, "pressure timeseries path not ready")
    require(summary.get("uses_synthetic_sensor_coordinates") is True, "synthetic sensor coordinate flag missing")
    require(summary.get("uses_non_cell_center_sensor_coordinates") is True, "non-cell-center sensor coordinate flag missing")
    require(summary.get("current_outputs_sufficient_for_exp002_pressure_agreement") is False, "EXP002 pressure agreement overclaimed")
    require(summary.get("case_aligned_pressure_sensor_agreement") is False, "case-aligned pressure agreement overclaimed")
    require(summary.get("radiation_agreement_executed") is False, "radiation agreement overclaimed")
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "strict blocker overclaimed")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# H2 Fire Plotfile Sensor Sampling Contract",
        "",
        f"- Status: `{report['status']}`",
        f"- Plotfiles: `{s['plotfile_count']}`",
        f"- Sensors: `{s['sensor_count']}`",
        f"- Rows: `{s['row_count']}`",
        f"- Variables: `{s['variables']}`",
        f"- Sampling mode: `{s['sampling_mode']}`",
        f"- Linear interpolation used: `{s['linear_interpolation_used']}`",
        f"- Pressure sensor time-series path ready: `{s['pressure_sensor_timeseries_path_ready']}`",
        f"- Uses synthetic sensor coordinates: `{s['uses_synthetic_sensor_coordinates']}`",
        f"- Uses non-cell-center sensor coordinates: `{s['uses_non_cell_center_sensor_coordinates']}`",
        f"- EXP002 pressure agreement ready: `{s['current_outputs_sufficient_for_exp002_pressure_agreement']}`",
        f"- Strict fire calibration blocker cleared: `{s['strict_fire_calibration_blocker_cleared']}`",
        "",
        "## Claim Boundary",
        "",
    ]
    lines.extend(f"- {item}" for item in report["claim_boundary"])
    lines += ["", "## Evidence", ""]
    lines.extend(f"- `{entry['label']}`: `{entry['path']}`" for entry in report["evidence_files"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    ap.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    ap.add_argument("--verify-json", type=Path)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(args.verify_json)
            validate_report(data)
            print(f"h2_fire_plotfile_sensor_sampling_contract VERIFY-PASS json={args.verify_json} status={data['status']}")
            return 0
        report = build_report(args)
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, args.output_md)
        print(f"h2_fire_plotfile_sensor_sampling_contract PASS json={args.output_json} md={args.output_md} status={report['status']}")
        return 0
    except (ContractError, OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError) as exc:
        print(f"h2_fire_plotfile_sensor_sampling_contract FAIL: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
