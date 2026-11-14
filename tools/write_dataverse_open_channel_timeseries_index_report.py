#!/usr/bin/env python3
"""Write/verify DataverseNO open-channel H2 time-series index evidence."""
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
STATUS = "PASS-DATAVERSE-OPEN-CHANNEL-H2-TIMESERIES-INDEX"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_timeseries_index_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_timeseries_index_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_timeseries_index_report.md"
DEFAULT_DATASET_AUDIT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_dataset_20260803/"
    "dataverse_open_channel_dataset_audit_report.json"
)
DEFAULT_RAW_DIR = Path("docs/codex_audit/evidence/dataverse_open_channel_dataset_20260803/raw")

MASS_FLOW_COLUMNS = ("mass flow meter 1 [g/s]", "mass flow meter 2 [g/s]")
LFL_H2_VOL_PERCENT = 4.0
STRONG_PLUME_PEAK_VOL_PERCENT = 10.0


class TimeseriesIndexError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TimeseriesIndexError(message)


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
        raise TimeseriesIndexError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TimeseriesIndexError(f"invalid JSON evidence {path}: {exc}") from exc
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


def sensor_id_from_column(column: str) -> str:
    text = column.lower().replace("sensor", "").replace("h2 concentration [%]", "").strip()
    return text


def inspect_zip(path: Path, expected_md5: str) -> dict[str, Any]:
    require(path.is_file(), f"missing raw ZIP: {path}")
    actual_md5 = md5_file(path)
    require(actual_md5 == expected_md5, f"MD5 mismatch for {path}")
    with zipfile.ZipFile(path) as zf:
        csv_names = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        require(len(csv_names) == 1, f"expected one CSV in {path.name}, found {len(csv_names)}")
        text = zf.read(csv_names[0]).decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    header = reader.fieldnames or []
    flow_columns = [column for column in MASS_FLOW_COLUMNS if column in header]
    sensor_columns = [column for column in header if "h2 concentration" in column.lower()]
    require(flow_columns, f"no supported mass-flow column in {path.name}")
    require("filling pressure [bar]" in header, f"pressure column missing in {path.name}")
    require("h2 sensor time" in header, f"H2 sensor time column missing in {path.name}")
    require(len(sensor_columns) == 29, f"expected 29 H2 sensor columns in {path.name}, found {len(sensor_columns)}")

    row_count = 0
    time_start = math.inf
    time_end = -math.inf
    flow_max = -math.inf
    flow_mean_accum = 0.0
    flow_mean_count = 0
    pressure_max = -math.inf
    h2_max = -math.inf
    peak_sensor_column = ""
    peak_sensor_values: dict[str, float] = {column: -math.inf for column in sensor_columns}
    lfl_sensor_ids: set[str] = set()

    for row in reader:
        if not row:
            continue
        row_count += 1
        time_value = as_float(row.get("h2 sensor time"))
        if math.isfinite(time_value):
            time_start = min(time_start, time_value)
            time_end = max(time_end, time_value)
        for flow_column in flow_columns:
            flow_value = as_float(row.get(flow_column))
            if math.isfinite(flow_value):
                flow_max = max(flow_max, flow_value)
                flow_mean_accum += flow_value
                flow_mean_count += 1
        pressure_value = as_float(row.get("filling pressure [bar]"))
        if math.isfinite(pressure_value):
            pressure_max = max(pressure_max, pressure_value)
        for sensor_column in sensor_columns:
            h2_value = as_float(row.get(sensor_column))
            if not math.isfinite(h2_value):
                continue
            if h2_value > peak_sensor_values[sensor_column]:
                peak_sensor_values[sensor_column] = h2_value
            if h2_value >= LFL_H2_VOL_PERCENT:
                lfl_sensor_ids.add(sensor_id_from_column(sensor_column))
            if h2_value > h2_max:
                h2_max = h2_value
                peak_sensor_column = sensor_column

    require(row_count > 0, f"CSV has no data rows in {path.name}")
    require(math.isfinite(time_start) and math.isfinite(time_end), f"time range missing in {path.name}")
    require(math.isfinite(flow_max), f"flow signal missing in {path.name}")
    require(math.isfinite(pressure_max), f"pressure signal missing in {path.name}")
    require(math.isfinite(h2_max), f"H2 signal missing in {path.name}")
    peak_sensor_top5 = sorted(
        (
            {
                "sensor_column": column,
                "sensor_id": sensor_id_from_column(column),
                "peak_h2_vol_percent": value,
            }
            for column, value in peak_sensor_values.items()
            if math.isfinite(value)
        ),
        key=lambda item: float(item["peak_h2_vol_percent"]),
        reverse=True,
    )[:5]
    duration = time_end - time_start
    strong_candidate = h2_max >= STRONG_PLUME_PEAK_VOL_PERCENT and len(lfl_sensor_ids) >= 3 and duration >= 120.0
    return {
        "filename": path.name,
        "path": str(path),
        "md5": actual_md5,
        "csv_member": csv_names[0],
        "row_count": row_count,
        "time_start_s": time_start,
        "time_end_s": time_end,
        "duration_s": duration,
        "flow_columns": flow_columns,
        "flow_max_g_s": flow_max,
        "flow_mean_g_s": flow_mean_accum / flow_mean_count if flow_mean_count else None,
        "pressure_max_bar": pressure_max,
        "sensor_column_count": len(sensor_columns),
        "h2_peak_vol_percent": h2_max,
        "h2_peak_sensor_column": peak_sensor_column,
        "h2_peak_sensor_id": sensor_id_from_column(peak_sensor_column),
        "lfl_sensor_count": len(lfl_sensor_ids),
        "lfl_sensor_ids": sorted(lfl_sensor_ids, key=lambda item: int(item)),
        "peak_sensor_top5": peak_sensor_top5,
        "strong_plume_candidate": strong_candidate,
        "candidate_reason": (
            "peak>=10vol%, >=3 sensors above LFL, duration>=120s"
            if strong_candidate
            else "does not satisfy strong plume candidate thresholds"
        ),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    dataset_audit_path = Path(args.dataset_audit_report)
    raw_dir = Path(args.raw_dir)
    dataset_audit = load_json(dataset_audit_path)
    require(
        dataset_audit.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-DATASET-AUDIT",
        "Dataverse raw dataset audit is not PASS",
    )
    files = dataset_audit.get("files")
    require(isinstance(files, list) and files, "Dataverse raw dataset file rows missing")
    zip_records = [
        row
        for row in files
        if isinstance(row, dict) and str(row.get("filename", "")).lower().endswith(".zip")
    ]
    require(len(zip_records) >= 20, "Dataverse ZIP record count is too small")
    case_rows = [
        inspect_zip(raw_dir / str(row["filename"]), str(row["md5"]))
        for row in sorted(zip_records, key=lambda item: str(item["filename"]))
    ]
    candidate_rows = [row for row in case_rows if row["strong_plume_candidate"]]
    ranked_candidates = sorted(
        candidate_rows,
        key=lambda item: (float(item["h2_peak_vol_percent"]), int(item["lfl_sensor_count"]), float(item["duration_s"])),
        reverse=True,
    )
    flow_meter_counts: dict[str, int] = {}
    for row in case_rows:
        for flow_column in row["flow_columns"]:
            flow_meter_counts[flow_column] = flow_meter_counts.get(flow_column, 0) + 1
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "dataset_audit_report": str(dataset_audit_path),
        "raw_dir": str(raw_dir),
        "summary": {
            "zip_case_count": len(case_rows),
            "strong_plume_candidate_count": len(candidate_rows),
            "flow_meter_counts": flow_meter_counts,
            "sensor_column_counts_seen": sorted({row["sensor_column_count"] for row in case_rows}),
            "max_h2_peak_vol_percent": max(float(row["h2_peak_vol_percent"]) for row in case_rows),
            "max_lfl_sensor_count": max(int(row["lfl_sensor_count"]) for row in case_rows),
            "time_end_max_s": max(float(row["time_end_s"]) for row in case_rows),
            "ready_for_case_selection": len(candidate_rows) >= 3,
            "clears_external_plume_reference_blocker": False,
        },
        "recommended_validation_candidates": ranked_candidates[:8],
        "case_rows": case_rows,
        "evidence_files": [evidence_entry("dataverse_raw_dataset_audit", dataset_audit_path)],
        "limitations": [
            "This report indexes reference time-series signals and validation candidates.",
            "It does not provide sensor coordinates or channel/obstacle geometry mapping.",
            "It does not run CFD/reference agreement scoring and therefore does not clear the external plume blocker.",
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(int(summary.get("zip_case_count", 0)) >= 20, "zip case count too small")
    require(int(summary.get("strong_plume_candidate_count", 0)) >= 3, "too few strong plume candidates")
    require(summary.get("sensor_column_counts_seen") == [29], "sensor column counts are not uniformly 29")
    require(float(summary.get("max_h2_peak_vol_percent", 0.0)) >= 10.0, "no strong H2 peak found")
    require(summary.get("ready_for_case_selection") is True, "case selection is not ready")
    require(summary.get("clears_external_plume_reference_blocker") is False, "timeseries index cannot clear blocker")
    candidates = data.get("recommended_validation_candidates")
    require(isinstance(candidates, list) and len(candidates) >= 3, "recommended candidates missing")
    for row in candidates:
        require(isinstance(row, dict), "candidate row is not an object")
        require(row.get("strong_plume_candidate") is True, f"recommended weak candidate: {row.get('filename')}")
        require(int(row.get("sensor_column_count", 0)) == 29, f"candidate missing 29 sensors: {row.get('filename')}")
    case_rows = data.get("case_rows")
    require(isinstance(case_rows, list) and len(case_rows) == int(summary["zip_case_count"]), "case rows mismatch")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# DataverseNO Open-Channel H2 Time-Series Index",
        "",
        f"- Status: `{report['status']}`",
        f"- ZIP cases: `{summary['zip_case_count']}`",
        f"- Strong plume candidates: `{summary['strong_plume_candidate_count']}`",
        f"- Flow meter counts: `{summary['flow_meter_counts']}`",
        f"- Sensor column counts seen: `{summary['sensor_column_counts_seen']}`",
        f"- Max H2 peak vol percent: `{summary['max_h2_peak_vol_percent']}`",
        f"- Ready for case selection: `{summary['ready_for_case_selection']}`",
        f"- Clears external plume blocker: `{summary['clears_external_plume_reference_blocker']}`",
        "",
        "## Recommended Validation Candidates",
        "",
        "| File | Peak H2 vol % | Peak Sensor | LFL Sensors | Duration s | Flow Columns |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["recommended_validation_candidates"]:
        lines.append(
            "| `{}` | `{:.6g}` | `{}` | `{}` | `{:.6g}` | `{}` |".format(
                row["filename"],
                row["h2_peak_vol_percent"],
                row["h2_peak_sensor_id"],
                row["lfl_sensor_count"],
                row["duration_s"],
                ", ".join(row["flow_columns"]),
            )
        )
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-audit-report", default=str(DEFAULT_DATASET_AUDIT))
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(
                "dataverse_open_channel_timeseries_index VERIFY-PASS "
                f"json={args.verify_json} status={data['status']} "
                f"candidates={data['summary']['strong_plume_candidate_count']}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, out_md)
        print(
            "dataverse_open_channel_timeseries_index PASS "
            f"json={out_json} md={out_md} status={report['status']} "
            f"candidates={report['summary']['strong_plume_candidate_count']}"
        )
        return 0
    except TimeseriesIndexError as exc:
        print(f"dataverse_open_channel_timeseries_index FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
