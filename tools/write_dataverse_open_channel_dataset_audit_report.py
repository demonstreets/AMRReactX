#!/usr/bin/env python3
"""Write/verify DataverseNO open-channel H2 dispersion dataset audit evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = "PASS-DATAVERSE-OPEN-CHANNEL-H2-DATASET-AUDIT"
STATUS_NOT_READY = "NOT_READY-DATAVERSE-OPEN-CHANNEL-H2-DATASET-AUDIT"

DATASET_DOI = "10.23642/USN.26117989"
DATASET_API_URL = f"https://dataverse.no/api/datasets/:persistentId?persistentId=doi:{DATASET_DOI}"
FILE_API_URL = "https://dataverse.no/api/access/datafile/:persistentId?persistentId={persistent_id}"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_dataset_20260803")
DEFAULT_METADATA = Path("docs/codex_audit/evidence/dataverse_probe_20260803/dataverse_dataset_metadata.json")
DEFAULT_RAW_DIR = DEFAULT_ROOT / "raw"
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "dataverse_open_channel_dataset_audit_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "dataverse_open_channel_dataset_audit_report.md"

REQUIRED_CSV_COLUMNS = (
    "flow time [s]",
    "filling pressure [bar]",
    "h2 sensor time",
)
MASS_FLOW_COLUMNS = ("mass flow meter 1 [g/s]", "mass flow meter 2 [g/s]")


class DataverseAuditError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DataverseAuditError(message)


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
        raise DataverseAuditError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DataverseAuditError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def ensure_metadata(path: Path, download_metadata: bool) -> None:
    if path.is_file():
        return
    require(download_metadata, f"metadata is missing and --download-metadata was not set: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(DATASET_API_URL, timeout=120) as response:
        payload = response.read()
    path.write_bytes(payload)


def latest_version(metadata: dict[str, Any]) -> dict[str, Any]:
    require(metadata.get("status") == "OK", "Dataverse metadata status is not OK")
    data = metadata.get("data")
    require(isinstance(data, dict), "Dataverse metadata data object missing")
    latest = data.get("latestVersion")
    require(isinstance(latest, dict), "Dataverse latestVersion object missing")
    require(latest.get("versionState") == "RELEASED", "Dataverse dataset is not RELEASED")
    return latest


def citation_fields(latest: dict[str, Any]) -> dict[str, Any]:
    blocks = latest.get("metadataBlocks")
    require(isinstance(blocks, dict), "Dataverse metadataBlocks missing")
    citation = blocks.get("citation")
    require(isinstance(citation, dict), "Dataverse citation block missing")
    fields = citation.get("fields")
    require(isinstance(fields, list), "Dataverse citation fields missing")
    out: dict[str, Any] = {}
    for field in fields:
        if isinstance(field, dict) and "typeName" in field:
            out[str(field["typeName"])] = field.get("value")
    return out


def file_records(latest: dict[str, Any]) -> list[dict[str, Any]]:
    files = latest.get("files")
    require(isinstance(files, list) and files, "Dataverse file list missing")
    records: list[dict[str, Any]] = []
    for item in files:
        require(isinstance(item, dict), "Dataverse file row is not an object")
        data_file = item.get("dataFile")
        require(isinstance(data_file, dict), "Dataverse dataFile row missing")
        filename = str(data_file.get("filename", ""))
        persistent_id = str(data_file.get("persistentId", ""))
        md5 = str(data_file.get("md5", ""))
        size = int(data_file.get("filesize", 0))
        require(filename, "Dataverse file missing filename")
        require(persistent_id.startswith("doi:"), f"Dataverse file missing persistent id: {filename}")
        require(len(md5) == 32, f"Dataverse file missing MD5: {filename}")
        require(size > 0, f"Dataverse file missing positive size: {filename}")
        records.append(
            {
                "filename": filename,
                "persistent_id": persistent_id,
                "md5": md5,
                "size_bytes": size,
            }
        )
    return sorted(records, key=lambda row: row["filename"])


def download_file(record: dict[str, Any], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    url = FILE_API_URL.format(persistent_id=record["persistent_id"])
    with urllib.request.urlopen(url, timeout=300) as response, tmp.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    if md5_file(tmp) != record["md5"]:
        tmp.unlink(missing_ok=True)
        raise DataverseAuditError(f"downloaded MD5 mismatch: {record['filename']}")
    tmp.replace(target)


def inspect_zip_csv(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing raw zip: {path}")
    require(zipfile.is_zipfile(path), f"not a valid zip file: {path}")
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        csv_names = [name for name in names if name.lower().endswith(".csv")]
        jpeg_names = [name for name in names if name.lower().endswith((".jpeg", ".jpg"))]
        require(len(csv_names) == 1, f"expected one CSV in {path.name}, found {len(csv_names)}")
        csv_payload = zf.read(csv_names[0])
    text = csv_payload.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration as exc:
        raise DataverseAuditError(f"empty CSV in {path.name}") from exc
    row_count = 0
    for row in reader:
        if row:
            row_count += 1
    sensor_columns = [col for col in header if "h2 concentration" in col.lower()]
    missing_required = [col for col in REQUIRED_CSV_COLUMNS if col not in header]
    mass_flow_columns_present = [col for col in MASS_FLOW_COLUMNS if col in header]
    if not mass_flow_columns_present:
        missing_required.append("mass flow meter 1 [g/s] or mass flow meter 2 [g/s]")
    return {
        "zip_member_count": len(names),
        "csv_member": csv_names[0],
        "jpeg_member_count": len(jpeg_names),
        "csv_size_bytes": len(csv_payload),
        "csv_column_count": len(header),
        "csv_data_row_count": row_count,
        "required_columns_present": not missing_required,
        "missing_required_columns": missing_required,
        "mass_flow_columns_present": mass_flow_columns_present,
        "h2_concentration_sensor_column_count": len(sensor_columns),
        "sensor_columns": sensor_columns,
    }


def audit_records(records: list[dict[str, Any]], raw_dir: Path, download_missing: bool) -> list[dict[str, Any]]:
    audited: list[dict[str, Any]] = []
    for record in records:
        path = raw_dir / record["filename"]
        if not path.is_file() and download_missing:
            download_file(record, path)
        present = path.is_file()
        row = dict(record)
        row["path"] = str(path)
        row["present"] = present
        row["md5_verified"] = False
        row["zip_csv_audit"] = None
        row["ready"] = False
        row["gaps"] = []
        if not present:
            row["gaps"].append("raw_file_missing")
        else:
            actual_md5 = md5_file(path)
            row["actual_md5"] = actual_md5
            row["actual_size_bytes"] = path.stat().st_size
            row["md5_verified"] = actual_md5 == record["md5"]
            if not row["md5_verified"]:
                row["gaps"].append("md5_mismatch")
            if path.stat().st_size != record["size_bytes"]:
                row["gaps"].append("size_mismatch")
            if path.suffix.lower() == ".zip" and row["md5_verified"]:
                zip_audit = inspect_zip_csv(path)
                row["zip_csv_audit"] = zip_audit
                if not zip_audit["required_columns_present"]:
                    row["gaps"].append("csv_required_columns_missing")
                if zip_audit["h2_concentration_sensor_column_count"] != 29:
                    row["gaps"].append("csv_h2_sensor_column_count_not_29")
                if int(zip_audit["csv_data_row_count"]) <= 0:
                    row["gaps"].append("csv_has_no_data_rows")
        row["ready"] = not row["gaps"]
        audited.append(row)
    return audited


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    metadata_path = Path(args.metadata)
    raw_dir = Path(args.raw_dir)
    ensure_metadata(metadata_path, args.download_metadata)
    metadata = load_json(metadata_path)
    latest = latest_version(metadata)
    fields = citation_fields(latest)
    records = file_records(latest)
    audited = audit_records(records, raw_dir, args.download_missing)
    present = [row for row in audited if row["present"]]
    ready = [row for row in audited if row["ready"]]
    zip_rows = [row for row in ready if str(row["filename"]).lower().endswith(".zip")]
    sensor_counts = sorted(
        {
            int(row["zip_csv_audit"]["h2_concentration_sensor_column_count"])
            for row in zip_rows
            if isinstance(row.get("zip_csv_audit"), dict)
        }
    )
    status = STATUS_PASS if len(ready) == len(audited) and sensor_counts == [29] else STATUS_NOT_READY
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "dataset": {
            "title": fields.get("title"),
            "doi": DATASET_DOI,
            "api_url": DATASET_API_URL,
            "version_state": latest.get("versionState"),
            "release_time": latest.get("releaseTime"),
            "license": "CC BY 4.0",
        },
        "summary": {
            "metadata_present": True,
            "expected_file_count": len(records),
            "present_file_count": len(present),
            "md5_verified_file_count": sum(1 for row in audited if row["md5_verified"]),
            "ready_file_count": len(ready),
            "missing_file_count": sum(1 for row in audited if not row["present"]),
            "zip_file_count": sum(1 for row in audited if str(row["filename"]).lower().endswith(".zip")),
            "zip_csv_audited_file_count": len(zip_rows),
            "sensor_column_counts_seen": sensor_counts,
            "all_expected_files_ready": len(ready) == len(audited),
            "all_ready_zip_csvs_have_29_h2_sensor_columns": sensor_counts == [29] and bool(zip_rows),
            "clears_external_plume_reference_blocker": False,
        },
        "files": audited,
        "evidence_files": [evidence_entry("dataverse_dataset_metadata", metadata_path)]
        + [evidence_entry(row["filename"], Path(row["path"])) for row in audited if row["present"]],
        "limitations": [
            "This audit verifies raw public Dataverse files and CSV column structure.",
            "It does not map sensor coordinates or channel geometry into the repository comparison schema.",
            "It does not run CFD/reference agreement scoring and therefore does not clear the external plume blocker.",
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    dataset = data.get("dataset")
    require(isinstance(dataset, dict), "missing dataset")
    require(dataset.get("doi") == DATASET_DOI, "unexpected dataset DOI")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(int(summary.get("expected_file_count", 0)) >= 20, "expected file count too small")
    require(summary.get("clears_external_plume_reference_blocker") is False, "raw audit cannot clear plume blocker")
    if data.get("status") == STATUS_PASS:
        require(summary.get("all_expected_files_ready") is True, "PASS report has incomplete files")
        require(
            summary.get("all_ready_zip_csvs_have_29_h2_sensor_columns") is True,
            "PASS report lacks 29-sensor CSV confirmation",
        )
    files = data.get("files")
    require(isinstance(files, list) and files, "missing file audit rows")
    for row in files:
        require(isinstance(row, dict), "file audit row is not an object")
        require(str(row.get("filename", "")).strip(), "file audit row missing filename")
        if row.get("ready") is True:
            require(row.get("md5_verified") is True, f"ready file is not MD5 verified: {row.get('filename')}")
            zip_audit = row.get("zip_csv_audit")
            if str(row.get("filename", "")).lower().endswith(".zip"):
                require(isinstance(zip_audit, dict), f"ready zip lacks CSV audit: {row.get('filename')}")
                require(
                    zip_audit.get("h2_concentration_sensor_column_count") == 29,
                    f"ready zip does not have 29 sensor columns: {row.get('filename')}",
                )
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# DataverseNO Open-Channel H2 Dataset Audit",
        "",
        f"- Status: `{report['status']}`",
        f"- DOI: `{report['dataset']['doi']}`",
        f"- Expected files: `{summary['expected_file_count']}`",
        f"- Present files: `{summary['present_file_count']}`",
        f"- MD5 verified files: `{summary['md5_verified_file_count']}`",
        f"- Ready files: `{summary['ready_file_count']}`",
        f"- ZIP CSV audited files: `{summary['zip_csv_audited_file_count']}`",
        f"- Sensor column counts seen: `{summary['sensor_column_counts_seen']}`",
        f"- Clears external plume blocker: `{summary['clears_external_plume_reference_blocker']}`",
        "",
        "## Files",
        "",
        "| File | Present | MD5 | Ready | Sensor Columns | Rows |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["files"]:
        zip_audit = row.get("zip_csv_audit") if isinstance(row.get("zip_csv_audit"), dict) else {}
        lines.append(
            "| `{}` | `{}` | `{}` | `{}` | `{}` | `{}` |".format(
                row["filename"],
                row["present"],
                row["md5_verified"],
                row["ready"],
                zip_audit.get("h2_concentration_sensor_column_count", ""),
                zip_audit.get("csv_data_row_count", ""),
            )
        )
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--download-metadata", action="store_true")
    parser.add_argument("--download-missing", action="store_true")
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(
                "dataverse_open_channel_dataset_audit VERIFY-PASS "
                f"json={args.verify_json} status={data['status']} "
                f"ready={data['summary']['ready_file_count']}/{data['summary']['expected_file_count']}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        write_json(out_json, report)
        write_markdown(report, out_md)
        print(
            "dataverse_open_channel_dataset_audit PASS "
            f"json={out_json} md={out_md} status={report['status']} "
            f"ready={report['summary']['ready_file_count']}/{report['summary']['expected_file_count']}"
        )
        return 0
    except DataverseAuditError as exc:
        print(f"dataverse_open_channel_dataset_audit FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
