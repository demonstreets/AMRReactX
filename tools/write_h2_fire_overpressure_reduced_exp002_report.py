#!/usr/bin/env python3
"""Write/verify reduced DataverseNO EXP002 overpressure ingestion evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-FIRE-OVERPRESSURE-REDUCED-EXP002"
STATUS_NOT_READY = "NOT_READY-H2-FIRE-OVERPRESSURE-REDUCED-EXP002"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/h2_fire_overpressure_reduced_exp002_20260805")
DEFAULT_CSV = DEFAULT_ROOT / "Ign_pipe_geom_EXP_002.csv"
DEFAULT_PEAKS_CSV = DEFAULT_ROOT / "exp002_pressure_peak_summary.csv"
DEFAULT_WINDOW_CSV = DEFAULT_ROOT / "exp002_window_2600_2800ms_stride100.csv"
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "h2_fire_overpressure_reduced_exp002_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "h2_fire_overpressure_reduced_exp002_report.md"
DEFAULT_METADATA = Path(
    "docs/codex_audit/evidence/h2_fire_overpressure_dataverse_metadata_20260805/"
    "h2_fire_overpressure_dataverse_metadata_report.json"
)

EXPECTED_SIZE = 406415818
EXPECTED_MD5 = "f0e95dc5a2f1c6a1f98cb266f8360dcc"
PRESSURE_CHANNELS = {
    2: "Kanal trykk pos. 0",
    3: "Kanal Trykk pos.1",
    4: "Kanal Trykk pos. 2",
    5: "Kanal Trykk pos.3",
}


class ReducedExp002Error(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReducedExp002Error(message)


def hash_file(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReducedExp002Error(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReducedExp002Error(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def parse_float(value: str) -> float:
    return float(value.replace(",", "."))


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    entry = {
        "label": label,
        "path": str(path),
        "sha256": hash_file(path, "sha256"),
        "size_bytes": path.stat().st_size,
    }
    if path.suffix.lower() in {".csv", ".json"}:
        entry["md5"] = hash_file(path, "md5")
    return entry


def scan_csv(csv_path: Path, peaks_csv: Path, window_csv: Path) -> dict[str, Any]:
    require(csv_path.is_file(), f"missing EXP002 csv: {csv_path}")
    require(csv_path.stat().st_size == EXPECTED_SIZE, "EXP002 csv size mismatch")
    require(hash_file(csv_path, "md5") == EXPECTED_MD5, "EXP002 csv md5 mismatch")

    channel_stats = {
        idx: {
            "name": name,
            "min_voltage_v": math.inf,
            "min_voltage_time_ms": None,
            "max_voltage_v": -math.inf,
            "max_voltage_time_ms": None,
            "pretrigger_sum_v": 0.0,
            "pretrigger_count": 0,
            "peak_overpressure_raw_bar": -math.inf,
            "peak_overpressure_raw_time_ms": None,
            "peak_overpressure_baseline_corrected_bar": -math.inf,
            "peak_overpressure_baseline_corrected_time_ms": None,
        }
        for idx, name in PRESSURE_CHANNELS.items()
    }
    row_count = 0
    first_time = None
    last_time = None
    trigger_max = {"voltage_v": -math.inf, "time_ms": None}
    nozzle_min = {"voltage_v": math.inf, "time_ms": None}
    nozzle_max = {"voltage_v": -math.inf, "time_ms": None}
    window_rows_written = 0

    peaks_csv.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh, window_csv.open(
        "w", encoding="utf-8", newline=""
    ) as window_fh:
        reader = csv.reader(fh, delimiter=";")
        header = next(reader)
        units = next(reader)
        window_writer = csv.writer(window_fh)
        window_writer.writerow(
            [
                "time_ms",
                "trigger_v",
                "pressure_pos0_v",
                "pressure_pos1_v",
                "pressure_pos2_v",
                "pressure_pos3_v",
                "nozzle_pressure_v",
            ]
        )
        for row in reader:
            if len(row) < 7:
                continue
            time_ms = parse_float(row[0])
            if first_time is None:
                first_time = time_ms
            last_time = time_ms
            row_count += 1

            trigger_v = parse_float(row[1])
            if trigger_v > trigger_max["voltage_v"]:
                trigger_max = {"voltage_v": trigger_v, "time_ms": time_ms}
            nozzle_v = parse_float(row[6])
            if nozzle_v < nozzle_min["voltage_v"]:
                nozzle_min = {"voltage_v": nozzle_v, "time_ms": time_ms}
            if nozzle_v > nozzle_max["voltage_v"]:
                nozzle_max = {"voltage_v": nozzle_v, "time_ms": time_ms}

            values = {idx: parse_float(row[idx]) for idx in PRESSURE_CHANNELS}
            if time_ms < 0.0:
                for idx, voltage in values.items():
                    channel_stats[idx]["pretrigger_sum_v"] += voltage
                    channel_stats[idx]["pretrigger_count"] += 1
            for idx, voltage in values.items():
                stat = channel_stats[idx]
                if voltage < stat["min_voltage_v"]:
                    stat["min_voltage_v"] = voltage
                    stat["min_voltage_time_ms"] = time_ms
                if voltage > stat["max_voltage_v"]:
                    stat["max_voltage_v"] = voltage
                    stat["max_voltage_time_ms"] = time_ms
                raw_overpressure = -voltage
                if raw_overpressure > stat["peak_overpressure_raw_bar"]:
                    stat["peak_overpressure_raw_bar"] = raw_overpressure
                    stat["peak_overpressure_raw_time_ms"] = time_ms

            if 2600.0 <= time_ms <= 2800.0 and row_count % 100 == 0:
                window_writer.writerow([str(time_ms), trigger_v] + [values[idx] for idx in sorted(PRESSURE_CHANNELS)] + [nozzle_v])
                window_rows_written += 1

    for stat in channel_stats.values():
        count = stat["pretrigger_count"]
        baseline = stat["pretrigger_sum_v"] / count if count else 0.0
        stat["pretrigger_baseline_v"] = baseline
        stat.pop("pretrigger_sum_v", None)
        stat.pop("pretrigger_count", None)

    with csv_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.reader(fh, delimiter=";")
        next(reader)
        next(reader)
        for row in reader:
            if len(row) < 7:
                continue
            time_ms = parse_float(row[0])
            if not 2500.0 <= time_ms <= 3200.0:
                continue
            for idx in PRESSURE_CHANNELS:
                stat = channel_stats[idx]
                voltage = parse_float(row[idx])
                corrected = -(voltage - stat["pretrigger_baseline_v"])
                if corrected > stat["peak_overpressure_baseline_corrected_bar"]:
                    stat["peak_overpressure_baseline_corrected_bar"] = corrected
                    stat["peak_overpressure_baseline_corrected_time_ms"] = time_ms

    with peaks_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "channel",
                "name",
                "pretrigger_baseline_v",
                "peak_overpressure_raw_bar",
                "peak_overpressure_raw_time_ms",
                "peak_overpressure_baseline_corrected_bar",
                "peak_overpressure_baseline_corrected_time_ms",
                "min_voltage_v",
                "min_voltage_time_ms",
                "max_voltage_v",
                "max_voltage_time_ms",
            ]
        )
        for idx, stat in channel_stats.items():
            writer.writerow(
                [
                    idx,
                    stat["name"],
                    stat["pretrigger_baseline_v"],
                    stat["peak_overpressure_raw_bar"],
                    stat["peak_overpressure_raw_time_ms"],
                    stat["peak_overpressure_baseline_corrected_bar"],
                    stat["peak_overpressure_baseline_corrected_time_ms"],
                    stat["min_voltage_v"],
                    stat["min_voltage_time_ms"],
                    stat["max_voltage_v"],
                    stat["max_voltage_time_ms"],
                ]
            )

    return {
        "header": header,
        "units": units,
        "row_count": row_count,
        "first_time_ms": first_time,
        "last_time_ms": last_time,
        "trigger_max": trigger_max,
        "nozzle_min": nozzle_min,
        "nozzle_max": nozzle_max,
        "pressure_channels": {str(idx): stat for idx, stat in channel_stats.items()},
        "window_sample": {
            "path": str(window_csv),
            "time_min_ms": 2600.0,
            "time_max_ms": 2800.0,
            "stride_rows": 100,
            "rows_written": window_rows_written,
        },
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    csv_path = Path(args.csv_path)
    peaks_csv = Path(args.peaks_csv)
    window_csv = Path(args.window_csv)
    metadata = load_json(Path(args.metadata))
    scan = scan_csv(csv_path, peaks_csv, window_csv)
    metadata_summary = metadata.get("summary", {})

    peak_corrected = max(
        item["peak_overpressure_baseline_corrected_bar"] for item in scan["pressure_channels"].values()
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "summary": {
            "experiment_id": 2,
            "source_dataset_doi": "doi:10.18710/X044QK",
            "source_csv_file_id": 268220,
            "source_csv_filename": "Ign_pipe_geom_EXP_002.csv",
            "source_csv_size_bytes": csv_path.stat().st_size,
            "source_csv_md5_matches_dataverse": hash_file(csv_path, "md5") == EXPECTED_MD5,
            "metadata_report_status": metadata.get("status"),
            "metadata_experiment_matrix_row_count": metadata_summary.get("experiment_matrix_row_count"),
            "header_column_count": len(scan["header"]),
            "row_count": scan["row_count"],
            "first_time_ms": scan["first_time_ms"],
            "last_time_ms": scan["last_time_ms"],
            "pressure_channel_count": len(PRESSURE_CHANNELS),
            "peak_corrected_overpressure_bar": peak_corrected,
            "window_sample_rows": scan["window_sample"]["rows_written"],
            "reduced_overpressure_csv_ingested": True,
            "ready_for_reduced_validation_case": True,
            "strict_fire_calibration_blocker_cleared": False,
        },
        "experiment_matrix_row": {
            "EXP Number": 2,
            "Max Pressure [bar]": 69.781242370605469,
            "Max MFR [kg/s]": 9.7505403682589531e-3,
            "Avg Pressure [bar]": 45.449802398681641,
            "Avg MFR [kg/s]": 6.3507058657705784e-3,
            "Ignition place": 2,
            "Obstacle distance from the nozzle [cm]": 29,
            "H2 release time [s]": 3,
            "Ignition delay time [s]": 2.5,
            "comments": "",
        },
        "csv_scan": scan,
        "derived_artifacts": [
            evidence_entry("exp002_pressure_peak_summary_csv", peaks_csv),
            evidence_entry("exp002_window_sample_csv", window_csv),
        ],
        "recommended_next_steps": [
            "Map pressure channel positions from the associated experiment description or publication geometry.",
            "Build a reduced delayed-ignition H2 jet/pipe-obstacle validation case using EXP002 mass-flow, obstacle distance, release time, and ignition delay.",
            "Compare simulated peak overpressure and arrival time against the four baseline-corrected pressure channels.",
        ],
        "evidence_files": [
            evidence_entry("source_exp002_csv", csv_path),
            evidence_entry("metadata_report", Path(args.metadata)),
            evidence_entry("exp002_pressure_peak_summary_csv", peaks_csv),
            evidence_entry("exp002_window_sample_csv", window_csv),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "EXP002 reduced report is not passing")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("experiment_id") == 2, "unexpected experiment id")
    require(summary.get("source_csv_md5_matches_dataverse") is True, "source CSV md5 mismatch")
    require(summary.get("metadata_report_status") == "PASS-H2-FIRE-OVERPRESSURE-DATAVERSE-METADATA", "metadata report not ready")
    require(summary.get("header_column_count") == 7, "unexpected header column count")
    require(summary.get("row_count") == 5000004, "unexpected row count")
    require(summary.get("first_time_ms") < -499.0, "unexpected first time")
    require(summary.get("last_time_ms") > 4499.0, "unexpected last time")
    require(summary.get("pressure_channel_count") == 4, "unexpected pressure channel count")
    require(summary.get("peak_corrected_overpressure_bar") > 0.01, "peak corrected overpressure too small")
    require(summary.get("window_sample_rows", 0) > 1000, "window sample too small")
    require(summary.get("reduced_overpressure_csv_ingested") is True, "CSV not ingested")
    require(summary.get("ready_for_reduced_validation_case") is True, "not ready for reduced validation case")
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "must not clear strict fire blocker")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == hash_file(path, "sha256"), f"sha256 mismatch for {path}")
            if "md5" in entry:
                require(entry.get("md5") == hash_file(path, "md5"), f"md5 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# H2 Fire Overpressure Reduced EXP002",
        "",
        f"- Status: `{report['status']}`",
        f"- Dataset DOI: `{summary['source_dataset_doi']}`",
        f"- Source CSV: `{summary['source_csv_filename']}`",
        f"- CSV MD5 matches Dataverse: `{summary['source_csv_md5_matches_dataverse']}`",
        f"- Rows: `{summary['row_count']}`",
        f"- Time range ms: `{summary['first_time_ms']}` to `{summary['last_time_ms']}`",
        f"- Pressure channels: `{summary['pressure_channel_count']}`",
        f"- Peak corrected overpressure bar: `{summary['peak_corrected_overpressure_bar']}`",
        f"- Ready for reduced validation case: `{summary['ready_for_reduced_validation_case']}`",
        f"- Strict fire calibration blocker cleared: `{summary['strict_fire_calibration_blocker_cleared']}`",
        "",
        "## Pressure Channels",
        "",
        "| Channel | Baseline V | Peak Corrected Bar | Peak Time ms |",
        "|---:|---:|---:|---:|",
    ]
    for idx, stat in report["csv_scan"]["pressure_channels"].items():
        lines.append(
            f"| {idx} | `{stat['pretrigger_baseline_v']}` | "
            f"`{stat['peak_overpressure_baseline_corrected_bar']}` | "
            f"`{stat['peak_overpressure_baseline_corrected_time_ms']}` |"
        )
    lines.extend(["", "## Next Steps", ""])
    for step in report["recommended_next_steps"]:
        lines.append(f"- {step}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-path", default=str(DEFAULT_CSV))
    parser.add_argument("--peaks-csv", default=str(DEFAULT_PEAKS_CSV))
    parser.add_argument("--window-csv", default=str(DEFAULT_WINDOW_CSV))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"h2_fire_overpressure_reduced_exp002 VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"h2_fire_overpressure_reduced_exp002 PASS json={output_json} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
