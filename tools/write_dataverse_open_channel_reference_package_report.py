#!/usr/bin/env python3
"""Write/verify a standardized DataverseNO open-channel H2 reference package."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = "PASS-DATAVERSE-OPEN-CHANNEL-H2-REFERENCE-PACKAGE"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_reference_package_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_reference_package_report.md"
DEFAULT_LONG_CSV = DEFAULT_ROOT / "dataverse_reference_timeseries_long.csv"
DEFAULT_WIDE_CSV = DEFAULT_ROOT / "dataverse_reference_timeseries_wide.csv"
DEFAULT_RELEASE_CSV = DEFAULT_ROOT / "dataverse_reference_release_profile.csv"
DEFAULT_CASE_METADATA_JSON = DEFAULT_ROOT / "dataverse_reference_case_metadata.json"
DEFAULT_RAW_DIR = Path("docs/codex_audit/evidence/dataverse_open_channel_dataset_20260803/raw")
DEFAULT_TIMESERIES_INDEX = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_timeseries_index_20260803/"
    "dataverse_open_channel_timeseries_index_report.json"
)
DEFAULT_GEOMETRY_MAPPING = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_geometry_mapping_20260803/"
    "dataverse_open_channel_geometry_mapping_report.json"
)

DATASET_DOI = "10.23642/USN.26117989"
ARTICLE_DOI = "10.1016/j.jlp.2025.105669"
LFL_H2_VOL_PERCENT = 4.0


class ReferencePackageError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReferencePackageError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReferencePackageError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReferencePackageError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def as_float(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return math.nan
    return out if math.isfinite(out) else math.nan


def sensor_id_from_column(column: str) -> int:
    text = column.lower().replace("sensor", "").replace("h2 concentration [%]", "").strip()
    try:
        return int(text)
    except ValueError as exc:
        raise ReferencePackageError(f"cannot parse sensor ID from column: {column}") from exc


def select_case(index: dict[str, Any], case_id: str | None) -> dict[str, Any]:
    case_rows = [row for row in index.get("case_rows", []) if isinstance(row, dict)]
    require(case_rows, "time-series index case rows missing")
    if case_id:
        normalized = case_id[:-4] if case_id.endswith(".zip") else case_id
        for row in case_rows:
            filename = str(row.get("filename", ""))
            if filename == case_id or filename[:-4] == normalized:
                return row
        raise ReferencePackageError(f"requested case not found in time-series index: {case_id}")
    candidates = [row for row in index.get("recommended_validation_candidates", []) if isinstance(row, dict)]
    require(candidates, "time-series index recommended candidates missing")
    return candidates[0]


def case_map_by_raw_id(mapping: dict[str, Any]) -> dict[str, str]:
    rows = mapping.get("case_map")
    require(isinstance(rows, list) and rows, "geometry mapping case map missing")
    out: dict[str, str] = {}
    for row in rows:
        if isinstance(row, dict):
            out[str(row.get("raw_case_id"))] = str(row.get("article_test_id"))
    require(len(out) == 22, f"expected 22 Dataverse case mappings, found {len(out)}")
    return out


def sensor_rows_by_id(mapping: dict[str, Any]) -> dict[int, dict[str, Any]]:
    rows = mapping.get("sensor_rows")
    require(isinstance(rows, list) and rows, "geometry mapping sensor rows missing")
    out: dict[int, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict):
            sensor_id = int(row["sensor_id"])
            out[sensor_id] = row
    require(len(out) == 29, f"expected 29 sensor rows, found {len(out)}")
    require(set(out) == set(range(1, 16)) | set(range(17, 31)), "sensor ID set mismatch")
    return out


def read_raw_csv(raw_zip: Path, expected_md5: str) -> tuple[str, list[str], list[dict[str, str]]]:
    require(raw_zip.is_file(), f"missing raw Dataverse ZIP: {raw_zip}")
    actual_md5 = md5_file(raw_zip)
    require(actual_md5 == expected_md5, f"raw ZIP MD5 mismatch: {raw_zip}")
    with zipfile.ZipFile(raw_zip) as zf:
        csv_members = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        require(len(csv_members) == 1, f"expected one CSV in {raw_zip.name}, found {len(csv_members)}")
        text = zf.read(csv_members[0]).decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    header = reader.fieldnames or []
    rows = [row for row in reader if row]
    require(rows, f"CSV has no data rows in {raw_zip.name}")
    return csv_members[0], header, rows


def write_reference_tables(
    *,
    raw_rows: list[dict[str, str]],
    sensor_rows: dict[int, dict[str, Any]],
    sensor_columns: list[str],
    flow_column: str,
    long_csv: Path,
    wide_csv: Path,
    release_csv: Path,
) -> dict[str, Any]:
    long_csv.parent.mkdir(parents=True, exist_ok=True)
    sensor_ids = sorted(sensor_rows)
    sensor_column_by_id = {sensor_id_from_column(column): column for column in sensor_columns}
    require(set(sensor_column_by_id) == set(sensor_ids), "raw CSV sensor columns do not match geometry mapping IDs")

    row_count = 0
    sensor_record_count = 0
    time_start = math.inf
    time_end = -math.inf
    h2_peak_vol_percent = -math.inf
    h2_peak_sensor_id = -1
    h2_min_vol_percent = math.inf
    lfl_sensor_ids: set[int] = set()
    flow_max = -math.inf
    flow_sum = 0.0
    flow_count = 0
    pressure_max = -math.inf

    long_fields = [
        "time",
        "sensor_id",
        "X(H2)",
        "X_H2_clipped_nonnegative",
        "H2_vol_percent",
        "x_m",
        "y_m",
        "z_m",
        "above_lfl",
        "raw_column",
    ]
    wide_fields = (
        ["time_s"]
        + [f"sensor_{sensor_id:02d}_X_H2" for sensor_id in sensor_ids]
        + [f"sensor_{sensor_id:02d}_H2_vol_percent" for sensor_id in sensor_ids]
    )
    release_fields = [
        "row_index",
        "flow_time_s",
        "h2_sensor_time_s",
        "filling_pressure_bar",
        "mass_flow_g_s",
        "mass_flow_kg_s",
        "mass_flow_column",
    ]

    with long_csv.open("w", newline="", encoding="utf-8") as long_fh, wide_csv.open(
        "w", newline="", encoding="utf-8"
    ) as wide_fh, release_csv.open("w", newline="", encoding="utf-8") as release_fh:
        long_writer = csv.DictWriter(long_fh, fieldnames=long_fields)
        wide_writer = csv.DictWriter(wide_fh, fieldnames=wide_fields)
        release_writer = csv.DictWriter(release_fh, fieldnames=release_fields)
        long_writer.writeheader()
        wide_writer.writeheader()
        release_writer.writeheader()

        for row_index, row in enumerate(raw_rows):
            time_s = as_float(row.get("h2 sensor time"))
            flow_time_s = as_float(row.get("flow time [s]"))
            pressure_bar = as_float(row.get("filling pressure [bar]"))
            flow_g_s = as_float(row.get(flow_column))
            if math.isfinite(flow_g_s):
                flow_max = max(flow_max, flow_g_s)
                flow_sum += flow_g_s
                flow_count += 1
            if math.isfinite(pressure_bar):
                pressure_max = max(pressure_max, pressure_bar)
            release_writer.writerow(
                {
                    "row_index": row_index,
                    "flow_time_s": flow_time_s,
                    "h2_sensor_time_s": time_s,
                    "filling_pressure_bar": pressure_bar,
                    "mass_flow_g_s": flow_g_s,
                    "mass_flow_kg_s": flow_g_s / 1000.0 if math.isfinite(flow_g_s) else "",
                    "mass_flow_column": flow_column,
                }
            )
            if not math.isfinite(time_s):
                continue

            row_count += 1
            time_start = min(time_start, time_s)
            time_end = max(time_end, time_s)

            wide_row: dict[str, Any] = {"time_s": time_s}
            for sensor_id in sensor_ids:
                column = sensor_column_by_id[sensor_id]
                h2_vol_percent = as_float(row.get(column))
                require(math.isfinite(h2_vol_percent), f"invalid H2 value for sensor {sensor_id} at row {row_index}")
                x_h2 = h2_vol_percent / 100.0
                sensor = sensor_rows[sensor_id]
                above_lfl = h2_vol_percent >= LFL_H2_VOL_PERCENT
                if above_lfl:
                    lfl_sensor_ids.add(sensor_id)
                if h2_vol_percent > h2_peak_vol_percent:
                    h2_peak_vol_percent = h2_vol_percent
                    h2_peak_sensor_id = sensor_id
                h2_min_vol_percent = min(h2_min_vol_percent, h2_vol_percent)
                long_writer.writerow(
                    {
                        "time": time_s,
                        "sensor_id": sensor_id,
                        "X(H2)": x_h2,
                        "X_H2_clipped_nonnegative": max(0.0, x_h2),
                        "H2_vol_percent": h2_vol_percent,
                        "x_m": sensor["x_m"],
                        "y_m": sensor["y_m"],
                        "z_m": sensor["z_m"],
                        "above_lfl": str(above_lfl).lower(),
                        "raw_column": column,
                    }
                )
                wide_row[f"sensor_{sensor_id:02d}_X_H2"] = x_h2
                wide_row[f"sensor_{sensor_id:02d}_H2_vol_percent"] = h2_vol_percent
                sensor_record_count += 1
            wide_writer.writerow(wide_row)

    return {
        "sensor_time_sample_count": row_count,
        "sensor_record_count": sensor_record_count,
        "sensor_count": len(sensor_ids),
        "time_start_s": time_start,
        "time_end_s": time_end,
        "duration_s": time_end - time_start,
        "flow_column": flow_column,
        "flow_max_g_s": flow_max,
        "flow_mean_g_s": flow_sum / flow_count if flow_count else None,
        "pressure_max_bar": pressure_max,
        "h2_min_vol_percent": h2_min_vol_percent,
        "h2_peak_vol_percent": h2_peak_vol_percent,
        "h2_peak_x_h2": h2_peak_vol_percent / 100.0,
        "h2_peak_sensor_id": h2_peak_sensor_id,
        "lfl_sensor_count": len(lfl_sensor_ids),
        "lfl_sensor_ids": sorted(lfl_sensor_ids),
    }


def write_case_metadata(path: Path, metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    timeseries_index_path = Path(args.timeseries_index_report)
    geometry_mapping_path = Path(args.geometry_mapping_report)
    raw_dir = Path(args.raw_dir)
    long_csv = Path(args.long_csv)
    wide_csv = Path(args.wide_csv)
    release_csv = Path(args.release_csv)
    case_metadata_json = Path(args.case_metadata_json)

    index = load_json(timeseries_index_path)
    mapping = load_json(geometry_mapping_path)
    require(
        index.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-TIMESERIES-INDEX",
        "Dataverse time-series index is not PASS",
    )
    require(
        mapping.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-GEOMETRY-MAPPING",
        "Dataverse geometry mapping is not PASS",
    )
    selected = select_case(index, args.case_id)
    raw_filename = str(selected["filename"])
    raw_case_id = raw_filename[:-4] if raw_filename.endswith(".zip") else raw_filename
    article_test_id = case_map_by_raw_id(mapping).get(raw_case_id)
    require(article_test_id, f"article test ID missing for {raw_case_id}")
    sensors = sensor_rows_by_id(mapping)
    raw_zip = raw_dir / raw_filename
    csv_member, header, raw_rows = read_raw_csv(raw_zip, str(selected["md5"]))
    sensor_columns = [column for column in header if "h2 concentration" in column.lower()]
    require(len(sensor_columns) == 29, f"expected 29 H2 sensor columns, found {len(sensor_columns)}")
    flow_columns = [column for column in selected.get("flow_columns", []) if column in header]
    require(flow_columns, f"selected case flow columns are absent from raw CSV: {selected.get('flow_columns')}")

    table_summary = write_reference_tables(
        raw_rows=raw_rows,
        sensor_rows=sensors,
        sensor_columns=sensor_columns,
        flow_column=flow_columns[0],
        long_csv=long_csv,
        wide_csv=wide_csv,
        release_csv=release_csv,
    )
    peak_delta = abs(float(table_summary["h2_peak_vol_percent"]) - float(selected["h2_peak_vol_percent"]))
    case_metadata = {
        "schema_version": 1,
        "dataset_doi": DATASET_DOI,
        "article_doi": ARTICLE_DOI,
        "raw_zip_filename": raw_filename,
        "raw_case_id": raw_case_id,
        "article_test_id": article_test_id,
        "raw_zip_md5": md5_file(raw_zip),
        "raw_csv_member": csv_member,
        "selected_by": "time-series-index top ranked strong plume candidate" if not args.case_id else "explicit --case-id",
        "candidate_reason": selected.get("candidate_reason"),
        "coordinate_convention": "x width across channel, y from closed end to open end, z vertical",
        "units": {
            "X(H2)": "volume fraction from raw H2 concentration percent divided by 100",
            "H2_vol_percent": "raw experimental hydrogen concentration percent",
            "mass_flow_g_s": "raw Dataverse mass flow in grams per second",
            "filling_pressure_bar": "raw Dataverse filling pressure in bar",
        },
        "table_summary": table_summary,
        "source_reports": {
            "timeseries_index_report": str(timeseries_index_path),
            "geometry_mapping_report": str(geometry_mapping_path),
        },
        "limitations": [
            "This package standardizes one experimental reference case for downstream CFD sensor-time-history scoring.",
            "It does not generate a CFD mesh or simulation input deck for the Dataverse channel.",
            "It does not run CFD/reference agreement scoring and therefore does not clear the strict plume blocker.",
        ],
    }
    write_case_metadata(case_metadata_json, case_metadata)

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "dataset_doi": DATASET_DOI,
        "article_doi": ARTICLE_DOI,
        "summary": {
            "selected_case_filename": raw_filename,
            "raw_case_id": raw_case_id,
            "article_test_id": article_test_id,
            "raw_csv_member": csv_member,
            "raw_row_count": len(raw_rows),
            "sensor_time_sample_count": table_summary["sensor_time_sample_count"],
            "sensor_count": table_summary["sensor_count"],
            "sensor_record_count": table_summary["sensor_record_count"],
            "flow_column": table_summary["flow_column"],
            "duration_s": table_summary["duration_s"],
            "h2_peak_vol_percent": table_summary["h2_peak_vol_percent"],
            "h2_peak_x_h2": table_summary["h2_peak_x_h2"],
            "h2_peak_sensor_id": table_summary["h2_peak_sensor_id"],
            "index_peak_h2_vol_percent": selected["h2_peak_vol_percent"],
            "peak_delta_abs_vol_percent": peak_delta,
            "lfl_sensor_count": table_summary["lfl_sensor_count"],
            "ready_for_reference_signal_sampling": True,
            "ready_for_cfd_reference_agreement_scoring": False,
            "clears_external_plume_reference_blocker": False,
        },
        "outputs": {
            "long_timeseries_csv": str(long_csv),
            "wide_timeseries_csv": str(wide_csv),
            "release_profile_csv": str(release_csv),
            "case_metadata_json": str(case_metadata_json),
        },
        "selected_candidate": selected,
        "case_metadata": case_metadata,
        "evidence_files": [
            evidence_entry("dataverse_timeseries_index", timeseries_index_path),
            evidence_entry("dataverse_geometry_mapping", geometry_mapping_path),
            evidence_entry("dataverse_raw_zip", raw_zip),
            evidence_entry("reference_long_timeseries_csv", long_csv),
            evidence_entry("reference_wide_timeseries_csv", wide_csv),
            evidence_entry("reference_release_profile_csv", release_csv),
            evidence_entry("reference_case_metadata_json", case_metadata_json),
        ],
        "limitations": [
            "This report proves reference signal packaging, not CFD validation agreement.",
            "The raw experimental CSV contains small negative concentration readings from measurement noise; X(H2) preserves the raw converted signal and X_H2_clipped_nonnegative is provided for nonnegative-only consumers.",
            "The strict external plume blocker remains open until CFD sensor samples are compared against this reference package with accepted metrics.",
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, "invalid status")
    require(data.get("dataset_doi") == DATASET_DOI, "dataset DOI mismatch")
    require(data.get("article_doi") == ARTICLE_DOI, "article DOI mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("selected_case_filename") == "23_FFI_P101_T00031.zip", "default selected case drifted")
    require(summary.get("article_test_id") == "test-08-1", "article test ID mismatch for default case")
    require(int(summary.get("raw_row_count", 0)) > 1000, "raw row count too small")
    require(int(summary.get("sensor_time_sample_count", 0)) >= 500, "sensor time sample count too small")
    require(int(summary.get("sensor_count", 0)) == 29, "sensor count mismatch")
    require(
        int(summary.get("sensor_record_count", 0))
        == int(summary.get("sensor_time_sample_count", 0)) * int(summary.get("sensor_count", 0)),
        "sensor record count mismatch",
    )
    require(float(summary.get("duration_s", 0.0)) >= 120.0, "reference duration too short")
    require(float(summary.get("h2_peak_x_h2", 0.0)) >= 0.10, "reference peak X(H2) too small")
    require(float(summary.get("peak_delta_abs_vol_percent", 1.0)) <= 1.0e-9, "peak value disagrees with index")
    require(int(summary.get("lfl_sensor_count", 0)) >= 3, "too few sensors above LFL")
    require(summary.get("ready_for_reference_signal_sampling") is True, "reference signal sampling is not ready")
    require(
        summary.get("ready_for_cfd_reference_agreement_scoring") is False,
        "reference package should not claim CFD scoring readiness",
    )
    require(summary.get("clears_external_plume_reference_blocker") is False, "reference package cannot clear blocker")
    outputs = data.get("outputs")
    require(isinstance(outputs, dict), "outputs missing")
    for key in ("long_timeseries_csv", "wide_timeseries_csv", "release_profile_csv", "case_metadata_json"):
        path = Path(str(outputs.get(key, "")))
        require(path.is_file(), f"missing output {key}: {path}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# DataverseNO Open-Channel H2 Reference Package",
        "",
        f"- Status: `{report['status']}`",
        f"- Selected case: `{s['selected_case_filename']}` / `{s['article_test_id']}`",
        f"- Raw rows: `{s['raw_row_count']}`",
        f"- Sensor time samples: `{s['sensor_time_sample_count']}`",
        f"- Sensor records: `{s['sensor_record_count']}`",
        f"- Duration s: `{s['duration_s']}`",
        f"- Peak H2 vol percent: `{s['h2_peak_vol_percent']}` at sensor `{s['h2_peak_sensor_id']}`",
        f"- LFL sensor count: `{s['lfl_sensor_count']}`",
        f"- Ready for reference signal sampling: `{s['ready_for_reference_signal_sampling']}`",
        f"- Ready for CFD/reference agreement scoring: `{s['ready_for_cfd_reference_agreement_scoring']}`",
        f"- Clears external plume blocker: `{s['clears_external_plume_reference_blocker']}`",
        "",
        "## Outputs",
        "",
    ]
    for label, output in report["outputs"].items():
        lines.append(f"- {label}: `{output}`")
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeseries-index-report", default=str(DEFAULT_TIMESERIES_INDEX))
    parser.add_argument("--geometry-mapping-report", default=str(DEFAULT_GEOMETRY_MAPPING))
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR))
    parser.add_argument("--case-id")
    parser.add_argument("--long-csv", default=str(DEFAULT_LONG_CSV))
    parser.add_argument("--wide-csv", default=str(DEFAULT_WIDE_CSV))
    parser.add_argument("--release-csv", default=str(DEFAULT_RELEASE_CSV))
    parser.add_argument("--case-metadata-json", default=str(DEFAULT_CASE_METADATA_JSON))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(
                "dataverse_open_channel_reference_package VERIFY-PASS "
                f"json={args.verify_json} status={data['status']} "
                f"case={data['summary']['selected_case_filename']} records={data['summary']['sensor_record_count']}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, out_md)
        print(
            "dataverse_open_channel_reference_package PASS "
            f"json={out_json} md={out_md} status={report['status']} "
            f"case={report['summary']['selected_case_filename']} records={report['summary']['sensor_record_count']}"
        )
        return 0
    except ReferencePackageError as exc:
        print(f"dataverse_open_channel_reference_package FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
