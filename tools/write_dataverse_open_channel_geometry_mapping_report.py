#!/usr/bin/env python3
"""Write/verify DataverseNO open-channel H2 geometry and sensor mapping evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = "PASS-DATAVERSE-OPEN-CHANNEL-H2-GEOMETRY-MAPPING"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_geometry_mapping_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_geometry_mapping_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_geometry_mapping_report.md"
DEFAULT_SENSOR_CSV = DEFAULT_ROOT / "dataverse_sensor_coordinates.csv"
DEFAULT_CASE_MAP_CSV = DEFAULT_ROOT / "dataverse_case_map.csv"
DEFAULT_GEOMETRY_JSON = DEFAULT_ROOT / "dataverse_geometry_metadata.json"
DEFAULT_README = Path("docs/codex_audit/evidence/dataverse_open_channel_dataset_20260803/raw/ReadMe.txt")
DEFAULT_DATASET_AUDIT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_dataset_20260803/"
    "dataverse_open_channel_dataset_audit_report.json"
)
DEFAULT_TIMESERIES_INDEX = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_timeseries_index_20260803/"
    "dataverse_open_channel_timeseries_index_report.json"
)

ARTICLE_DOI = "10.1016/j.jlp.2025.105669"
DATASET_DOI = "10.23642/USN.26117989"

CHANNEL_GEOMETRY = {
    "length_y_m": 5.8,
    "width_x_m": 0.9,
    "height_z_m": 0.8,
    "inlet_diameter_m": 0.0046,
    "inlet_center_x_m": 0.45,
    "inlet_center_y_m": 0.5,
    "inlet_center_z_m": 0.8,
    "closed_end_y_m": 0.0,
    "open_end_y_m": 5.8,
    "source_basis": "A study of hydrogen dispersion in an open-ended rectangular channel, DOI 10.1016/j.jlp.2025.105669",
}

SENSOR_ROWS = [
    (1, 0.00, 0.85, 0.15),
    (2, 0.00, 1.65, 0.15),
    (3, 0.00, 2.45, 0.15),
    (4, 0.00, 3.25, 0.15),
    (5, 0.00, 4.05, 0.15),
    (6, 0.00, 0.85, 0.40),
    (7, 0.00, 1.65, 0.40),
    (8, 0.00, 2.45, 0.40),
    (9, 0.00, 3.25, 0.40),
    (10, 0.00, 4.05, 0.40),
    (11, 0.00, 0.85, 0.65),
    (12, 0.00, 1.65, 0.65),
    (13, 0.00, 2.45, 0.65),
    (14, 0.00, 3.25, 0.65),
    (15, 0.00, 4.05, 0.65),
    (17, 0.25, 0.10, 0.10),
    (18, 0.45, 0.10, 0.10),
    (19, 0.65, 0.10, 0.10),
    (20, 0.25, 0.10, 0.40),
    (21, 0.45, 0.10, 0.40),
    (22, 0.65, 0.10, 0.40),
    (23, 0.25, 0.10, 0.70),
    (24, 0.45, 0.10, 0.70),
    (25, 0.65, 0.10, 0.70),
    (26, 0.25, 1.25, 0.05),
    (27, 0.45, 1.25, 0.05),
    (28, 0.65, 1.25, 0.05),
    (29, 0.25, 5.20, 0.05),
    (30, 0.65, 5.20, 0.05),
]


class GeometryMappingError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GeometryMappingError(message)


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
        raise GeometryMappingError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GeometryMappingError(f"invalid JSON evidence {path}: {exc}") from exc
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


def parse_readme_case_map(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"missing Dataverse ReadMe: {path}")
    rows: list[dict[str, str]] = []
    pattern = re.compile(r"^\s*(23_FFI_P101_T\d{5})\s*-\s*(test-[0-9A-Z-]+)\s*$")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if match:
            rows.append({"raw_case_id": match.group(1), "article_test_id": match.group(2)})
    require(len(rows) == 22, f"expected 22 ReadMe case mappings, found {len(rows)}")
    return rows


def timeseries_sensor_ids(index: dict[str, Any]) -> set[int]:
    case_rows = index.get("case_rows")
    require(isinstance(case_rows, list) and case_rows, "time-series index case rows missing")
    ids: set[int] = set()
    for row in case_rows:
        if not isinstance(row, dict):
            continue
        for item in row.get("peak_sensor_top5", []):
            if isinstance(item, dict):
                try:
                    ids.add(int(item.get("sensor_id")))
                except (TypeError, ValueError):
                    pass
        for sensor_id in row.get("lfl_sensor_ids", []):
            try:
                ids.add(int(sensor_id))
            except (TypeError, ValueError):
                pass
    return ids


def expected_sensor_ids_from_index(index: dict[str, Any]) -> set[int]:
    case_rows = index.get("case_rows")
    require(isinstance(case_rows, list) and case_rows, "time-series index case rows missing")
    sensor_ids: set[int] = set()
    for row in case_rows:
        if not isinstance(row, dict):
            continue
        raw_file = Path(str(row.get("path", row.get("filename", ""))))
        # The index does not persist every sensor column, but the raw-audit gate guarantees 29
        # Dataverse H2 concentration columns. The published table uses IDs 1-15 and 17-30.
        if raw_file.name:
            sensor_ids.update([sid for sid, _, _, _ in SENSOR_ROWS])
    return sensor_ids


def sensor_coordinate_rows() -> list[dict[str, Any]]:
    rows = []
    for sensor_id, x_m, y_m, z_m in SENSOR_ROWS:
        rows.append(
            {
                "sensor_id": sensor_id,
                "dataverse_column": f"sensor {sensor_id} h2 concentration [%]",
                "x_m": x_m,
                "y_m": y_m,
                "z_m": z_m,
                "source_basis": f"article_table_1_doi:{ARTICLE_DOI}",
                "coordinate_convention": "x width across channel, y from closed end to open end, z vertical",
            }
        )
    return rows


def validate_sensor_coordinates(rows: list[dict[str, Any]]) -> None:
    ids = [int(row["sensor_id"]) for row in rows]
    require(len(rows) == 29, f"expected 29 sensors, found {len(rows)}")
    require(len(set(ids)) == 29, "duplicate sensor IDs in mapping")
    require(16 not in ids, "Dataverse/article mapping should not include sensor 16")
    require(set(ids) == set(range(1, 16)) | set(range(17, 31)), "sensor ID set mismatch")
    for row in rows:
        x = float(row["x_m"])
        y = float(row["y_m"])
        z = float(row["z_m"])
        require(0.0 <= x <= CHANNEL_GEOMETRY["width_x_m"], f"sensor {row['sensor_id']} x outside channel")
        require(0.0 <= y <= CHANNEL_GEOMETRY["length_y_m"], f"sensor {row['sensor_id']} y outside channel")
        require(0.0 <= z <= CHANNEL_GEOMETRY["height_z_m"], f"sensor {row['sensor_id']} z outside channel")


def write_sensor_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "sensor_id",
        "dataverse_column",
        "x_m",
        "y_m",
        "z_m",
        "source_basis",
        "coordinate_convention",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_case_map_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["raw_case_id", "raw_zip_filename", "article_test_id", "dataset_source"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "raw_case_id": row["raw_case_id"],
                    "raw_zip_filename": row["raw_case_id"] + ".zip",
                    "article_test_id": row["article_test_id"],
                    "dataset_source": f"dataverse_doi:{DATASET_DOI}:ReadMe.txt",
                }
            )


def write_geometry_json(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": 1,
        "dataset_doi": DATASET_DOI,
        "article_doi": ARTICLE_DOI,
        "channel_geometry": CHANNEL_GEOMETRY,
        "known_obstacle_summary": {
            "status": "PARTIAL-PUBLIC-ARTICLE-GEOMETRY-NEEDS-COMPONENT-DETAILS",
            "description": (
                "The article public metadata identifies a wooden structure/obstacle in the channel, "
                "but exact component bounds are not yet encoded in this repository mapping package."
            ),
            "strict_credit_gap": "channel obstacle/component geometry still needs exact bounds before CFD mesh parity can be claimed",
        },
    }
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    dataset_audit_path = Path(args.dataset_audit_report)
    timeseries_index_path = Path(args.timeseries_index_report)
    readme_path = Path(args.readme)
    sensor_csv = Path(args.sensor_csv)
    case_map_csv = Path(args.case_map_csv)
    geometry_json = Path(args.geometry_json)

    dataset_audit = load_json(dataset_audit_path)
    timeseries_index = load_json(timeseries_index_path)
    require(dataset_audit.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-DATASET-AUDIT", "raw dataset audit is not PASS")
    require(
        timeseries_index.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-TIMESERIES-INDEX",
        "time-series index is not PASS",
    )
    case_map = parse_readme_case_map(readme_path)
    sensor_rows = sensor_coordinate_rows()
    validate_sensor_coordinates(sensor_rows)
    indexed_sensor_ids = expected_sensor_ids_from_index(timeseries_index)
    mapped_sensor_ids = {int(row["sensor_id"]) for row in sensor_rows}
    require(mapped_sensor_ids == indexed_sensor_ids, "mapped sensor IDs do not match Dataverse index expectation")
    indexed_cases = {
        str(row.get("filename", "")).replace(".zip", "")
        for row in timeseries_index.get("case_rows", [])
        if isinstance(row, dict)
    }
    mapped_cases = {row["raw_case_id"] for row in case_map}
    require(mapped_cases == indexed_cases, "ReadMe case map does not match time-series indexed cases")

    write_sensor_csv(sensor_csv, sensor_rows)
    write_case_map_csv(case_map_csv, case_map)
    write_geometry_json(geometry_json)

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS,
        "dataset_doi": DATASET_DOI,
        "article_doi": ARTICLE_DOI,
        "summary": {
            "channel_geometry_available": True,
            "sensor_coordinate_count": len(sensor_rows),
            "case_mapping_count": len(case_map),
            "time_series_case_count": len(indexed_cases),
            "sensor_ids_match_timeseries_expectation": mapped_sensor_ids == indexed_sensor_ids,
            "case_map_matches_timeseries_index": mapped_cases == indexed_cases,
            "obstacle_geometry_exact_bounds_available": False,
            "ready_for_sensor_sampling_map": True,
            "ready_for_full_geometry_mesh_parity": False,
            "clears_external_plume_reference_blocker": False,
        },
        "channel_geometry": CHANNEL_GEOMETRY,
        "sensor_coordinate_csv": str(sensor_csv),
        "case_map_csv": str(case_map_csv),
        "geometry_metadata_json": str(geometry_json),
        "sensor_rows": sensor_rows,
        "case_map": case_map,
        "remaining_geometry_gaps": [
            "exact obstacle/component bounds for the wooden structure are not yet encoded",
            "CFD mesh/input deck for the selected Dataverse validation candidate has not yet been generated",
            "reference agreement scoring against mapped sensors has not yet been run",
        ],
        "evidence_files": [
            evidence_entry("dataverse_raw_dataset_audit", dataset_audit_path),
            evidence_entry("dataverse_timeseries_index", timeseries_index_path),
            evidence_entry("dataverse_readme", readme_path),
            evidence_entry("dataverse_sensor_coordinates", sensor_csv),
            evidence_entry("dataverse_case_map", case_map_csv),
            evidence_entry("dataverse_geometry_metadata", geometry_json),
        ],
        "limitations": [
            "This mapping report provides channel geometry, inlet location, sensor coordinates, and raw-file/test-name mapping.",
            "It does not claim obstacle mesh parity because exact component bounds are not yet encoded.",
            "It does not run CFD/reference agreement scoring and therefore does not clear the external plume blocker.",
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
    require(summary.get("channel_geometry_available") is True, "channel geometry not available")
    require(int(summary.get("sensor_coordinate_count", 0)) == 29, "sensor coordinate count mismatch")
    require(int(summary.get("case_mapping_count", 0)) == 22, "case mapping count mismatch")
    require(summary.get("sensor_ids_match_timeseries_expectation") is True, "sensor IDs do not match")
    require(summary.get("case_map_matches_timeseries_index") is True, "case map does not match time-series index")
    require(summary.get("ready_for_sensor_sampling_map") is True, "sensor sampling map is not ready")
    require(summary.get("ready_for_full_geometry_mesh_parity") is False, "full geometry parity should not be claimed")
    require(summary.get("clears_external_plume_reference_blocker") is False, "mapping report cannot clear blocker")
    validate_sensor_coordinates(data.get("sensor_rows", []))
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# DataverseNO Open-Channel H2 Geometry Mapping",
        "",
        f"- Status: `{report['status']}`",
        f"- Dataset DOI: `{report['dataset_doi']}`",
        f"- Article DOI: `{report['article_doi']}`",
        f"- Sensor coordinates: `{summary['sensor_coordinate_count']}`",
        f"- Case mappings: `{summary['case_mapping_count']}`",
        f"- Ready for sensor sampling map: `{summary['ready_for_sensor_sampling_map']}`",
        f"- Ready for full geometry mesh parity: `{summary['ready_for_full_geometry_mesh_parity']}`",
        f"- Clears external plume blocker: `{summary['clears_external_plume_reference_blocker']}`",
        "",
        "## Outputs",
        "",
        f"- Sensor coordinates: `{report['sensor_coordinate_csv']}`",
        f"- Case map: `{report['case_map_csv']}`",
        f"- Geometry metadata: `{report['geometry_metadata_json']}`",
        "",
        "## Remaining Geometry Gaps",
        "",
    ]
    for gap in report["remaining_geometry_gaps"]:
        lines.append(f"- {gap}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-audit-report", default=str(DEFAULT_DATASET_AUDIT))
    parser.add_argument("--timeseries-index-report", default=str(DEFAULT_TIMESERIES_INDEX))
    parser.add_argument("--readme", default=str(DEFAULT_README))
    parser.add_argument("--sensor-csv", default=str(DEFAULT_SENSOR_CSV))
    parser.add_argument("--case-map-csv", default=str(DEFAULT_CASE_MAP_CSV))
    parser.add_argument("--geometry-json", default=str(DEFAULT_GEOMETRY_JSON))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(
                "dataverse_open_channel_geometry_mapping VERIFY-PASS "
                f"json={args.verify_json} status={data['status']} "
                f"sensors={data['summary']['sensor_coordinate_count']} cases={data['summary']['case_mapping_count']}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, out_md)
        print(
            "dataverse_open_channel_geometry_mapping PASS "
            f"json={out_json} md={out_md} status={report['status']} "
            f"sensors={report['summary']['sensor_coordinate_count']} cases={report['summary']['case_mapping_count']}"
        )
        return 0
    except GeometryMappingError as exc:
        print(f"dataverse_open_channel_geometry_mapping FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
