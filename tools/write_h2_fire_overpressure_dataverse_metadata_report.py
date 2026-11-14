#!/usr/bin/env python3
"""Write/verify the DataverseNO ignited-H2 overpressure metadata report."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-FIRE-OVERPRESSURE-DATAVERSE-METADATA"
STATUS_NOT_READY = "NOT_READY-H2-FIRE-OVERPRESSURE-DATAVERSE-METADATA"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/h2_fire_overpressure_dataverse_metadata_20260805")
DEFAULT_API_JSON = DEFAULT_ROOT / "dataverse_dataset_api.json"
DEFAULT_README = DEFAULT_ROOT / "00_Readme.txt"
DEFAULT_XLSX = DEFAULT_ROOT / "Matrix_and_H2_flow_results.xlsx"
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "h2_fire_overpressure_dataverse_metadata_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "h2_fire_overpressure_dataverse_metadata_report.md"

EXPECTED_DATASET_DOI = "doi:10.18710/X044QK"
EXPECTED_README_MD5 = "709a0f899a6495722389484948bd18cf"
EXPECTED_XLSX_MD5 = "6c929ee530ac393ee8e76f6db2eff05c"


class MetadataReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MetadataReportError(message)


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
        raise MetadataReportError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MetadataReportError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    entry = {
        "label": label,
        "path": str(path),
        "sha256": hash_file(path, "sha256"),
        "size_bytes": path.stat().st_size,
    }
    if path.suffix.lower() in {".txt", ".xlsx"}:
        entry["md5"] = hash_file(path, "md5")
    return entry


def xlsx_rows(path: Path) -> list[list[str]]:
    ns = {
        "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    with zipfile.ZipFile(path) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall("a:si", ns):
                shared.append("".join(t.text or "" for t in si.findall(".//a:t", ns)))
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rid_to_target = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        sheet = workbook.find("a:sheets/a:sheet", ns)
        require(sheet is not None, "xlsx has no sheets")
        target = rid_to_target[sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
        worksheet = ET.fromstring(zf.read("xl/" + target.lstrip("/")))
        rows: list[list[str]] = []
        for row in worksheet.findall(".//a:sheetData/a:row", ns):
            values: list[str] = []
            for cell in row.findall("a:c", ns):
                cell_type = cell.attrib.get("t")
                value_node = cell.find("a:v", ns)
                value = "" if value_node is None or value_node.text is None else value_node.text
                if cell_type == "s" and value:
                    value = shared[int(value)]
                values.append(value)
            rows.append(values)
        return rows


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    api_path = Path(args.api_json)
    readme_path = Path(args.readme)
    xlsx_path = Path(args.xlsx)
    api = load_json(api_path)
    readme = readme_path.read_text(encoding="utf-8", errors="replace")
    rows = xlsx_rows(xlsx_path)

    latest = api.get("data", {}).get("latestVersion", {})
    files = latest.get("files", [])
    require(isinstance(files, list), "dataset API missing files list")
    file_entries = []
    for item in files:
        data_file = item.get("dataFile", {}) if isinstance(item, dict) else {}
        filename = data_file.get("filename", "")
        file_entries.append(
            {
                "id": data_file.get("id"),
                "filename": filename,
                "content_type": data_file.get("contentType"),
                "size_bytes": data_file.get("filesize"),
                "md5": data_file.get("md5"),
                "is_csv": filename.endswith(".csv"),
                "is_large_binary": filename.endswith(".zip"),
            }
        )

    csv_files = [item for item in file_entries if item["is_csv"]]
    zip_files = [item for item in file_entries if item["is_large_binary"]]
    xlsx_files = [item for item in file_entries if item["filename"] == "Matrix and H2 flow results.xlsx"]
    header = rows[1] if len(rows) > 1 else []
    experiment_rows = [row for row in rows[2:] if row and re.fullmatch(r"\d+", row[0] or "")]
    comments = [row[9] for row in experiment_rows if len(row) > 9 and row[9]]

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "summary": {
            "dataset_api_status": api.get("status"),
            "dataset_doi": EXPECTED_DATASET_DOI,
            "dataset_id": api.get("data", {}).get("id"),
            "file_count": len(file_entries),
            "csv_file_count": len(csv_files),
            "large_zip_file_count": len(zip_files),
            "readme_present": readme_path.is_file(),
            "readme_md5_matches_dataverse": hash_file(readme_path, "md5") == EXPECTED_README_MD5,
            "matrix_xlsx_present": xlsx_path.is_file(),
            "matrix_xlsx_md5_matches_dataverse": hash_file(xlsx_path, "md5") == EXPECTED_XLSX_MD5,
            "experiment_matrix_header": header,
            "experiment_matrix_row_count": len(experiment_rows),
            "pressure_sensor_count_from_readme": 4 if "Four piezoelectric pressure sensors" in readme else None,
            "overpressure_calibration_curve_from_readme": "1 V = -1 bar" if "1" in readme and "bar" in readme else "",
            "metadata_ready_for_reduced_case_selection": len(experiment_rows) >= 30 and len(csv_files) >= 30,
            "large_csv_download_required_for_strict_overpressure_credit": True,
            "strict_fire_calibration_blocker_cleared": False,
        },
        "files": file_entries,
        "experiment_matrix_preview": {
            "title": rows[0][0] if rows and rows[0] else "",
            "header": header,
            "first_five_experiments": experiment_rows[:5],
            "comment_values": comments,
        },
        "recommended_next_steps": [
            "Select one ignited experiment with no exclusion comment and a small CSV size for a reduced overpressure calibration scout.",
            "Download only the selected CSV into a dedicated evidence directory with MD5 verification.",
            "Extract pressure-sensor time-series columns, pressure conversion, ignition delay, obstacle distance, and mass-flow metadata.",
            "Build a reduced PeleC/PeleLMeX delayed-ignition validation case and compare peak overpressure/time-of-arrival against the selected experiment.",
        ],
        "evidence_files": [
            evidence_entry("dataverse_dataset_api_json", api_path),
            evidence_entry("dataverse_readme", readme_path),
            evidence_entry("dataverse_matrix_xlsx", xlsx_path),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "metadata report is not passing")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("dataset_api_status") == "OK", "Dataverse API status is not OK")
    require(summary.get("file_count") == 47, "unexpected Dataverse file count")
    require(summary.get("csv_file_count", 0) >= 30, "too few CSV files")
    require(summary.get("large_zip_file_count") == 6, "unexpected zip file count")
    require(summary.get("readme_present") is True, "README missing")
    require(summary.get("readme_md5_matches_dataverse") is True, "README md5 mismatch")
    require(summary.get("matrix_xlsx_present") is True, "matrix xlsx missing")
    require(summary.get("matrix_xlsx_md5_matches_dataverse") is True, "matrix xlsx md5 mismatch")
    require(summary.get("pressure_sensor_count_from_readme") == 4, "pressure sensor count not detected")
    require(summary.get("experiment_matrix_row_count", 0) >= 30, "experiment matrix has too few rows")
    require(summary.get("metadata_ready_for_reduced_case_selection") is True, "metadata not ready for case selection")
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "metadata report must not clear strict blocker")
    header = summary.get("experiment_matrix_header", [])
    for field in ["EXP Number", "Max Pressure [bar]", "Avg MFR [kg/s]", "Ignition place", "Obstacle distance from the nozzle [cm]"]:
        require(field in header, f"experiment matrix missing field: {field}")
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
        "# H2 Fire Overpressure Dataverse Metadata",
        "",
        f"- Status: `{report['status']}`",
        f"- Dataset DOI: `{summary['dataset_doi']}`",
        f"- File count: `{summary['file_count']}`",
        f"- CSV file count: `{summary['csv_file_count']}`",
        f"- Large zip file count: `{summary['large_zip_file_count']}`",
        f"- README MD5 matches Dataverse: `{summary['readme_md5_matches_dataverse']}`",
        f"- Matrix XLSX MD5 matches Dataverse: `{summary['matrix_xlsx_md5_matches_dataverse']}`",
        f"- Experiment matrix rows: `{summary['experiment_matrix_row_count']}`",
        f"- Pressure sensors detected in README: `{summary['pressure_sensor_count_from_readme']}`",
        f"- Strict fire calibration blocker cleared: `{summary['strict_fire_calibration_blocker_cleared']}`",
        "",
        "## Matrix Header",
        "",
        ", ".join(f"`{item}`" for item in summary["experiment_matrix_header"]),
        "",
        "## Next Steps",
        "",
    ]
    for step in report["recommended_next_steps"]:
        lines.append(f"- {step}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-json", default=str(DEFAULT_API_JSON))
    parser.add_argument("--readme", default=str(DEFAULT_README))
    parser.add_argument("--xlsx", default=str(DEFAULT_XLSX))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"h2_fire_overpressure_dataverse_metadata VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"h2_fire_overpressure_dataverse_metadata PASS json={output_json} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
