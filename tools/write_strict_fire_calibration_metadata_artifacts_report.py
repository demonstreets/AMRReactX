#!/usr/bin/env python3
"""Write/verify strict fire-calibration metadata and uncertainty artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-FIRE-CALIBRATION-METADATA-ARTIFACTS"

DEFAULT_OUTPUT_ROOT = Path("docs/codex_audit/evidence/strict_fire_calibration_metadata_artifacts_20260817")
DEFAULT_OUTPUT_JSON = DEFAULT_OUTPUT_ROOT / "strict_fire_calibration_metadata_artifacts_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_OUTPUT_ROOT / "strict_fire_calibration_metadata_artifacts_report.md"

METRIC_ARTIFACT_REPORT = Path(
    "docs/codex_audit/evidence/strict_fire_calibration_metric_artifacts_20260817/"
    "strict_fire_calibration_metric_artifacts_report.json"
)
RADIATION_REPORT = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_calibration_table_20260805/"
    "h2_fire_mdpi_radiation_calibration_table_report.json"
)
OVERPRESSURE_REPORT = Path(
    "docs/codex_audit/evidence/h2_fire_exp002_overpressure_calibration_table_20260805/"
    "h2_fire_exp002_overpressure_calibration_table_report.json"
)
METADATA_TARGET = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/"
    "dataset/calibration_metadata.json"
)
UNCERTAINTY_TARGET = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/"
    "dataset/fire_calibration_digitization_uncertainty.csv"
)

METADATA_REQUIRED_KEYS = {
    "case",
    "case_alignment",
    "dataset_type",
    "schema_version",
    "source",
    "source_type",
    "uncertainty",
}
UNCERTAINTY_HEADER = (
    "artifact",
    "source_basis",
    "method",
    "calibration_points_or_table",
    "estimated_uncertainty",
    "review_status",
)
PLACEHOLDER_MARKERS = ("<", "replace", "pending", "todo", "tbd", "placeholder", "fill in")


class MetadataArtifactError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MetadataArtifactError(message)


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
        raise MetadataArtifactError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MetadataArtifactError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": path.as_posix(),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_uncertainty_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(UNCERTAINTY_HEADER))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_uncertainty_csv(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"missing uncertainty CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        require(tuple(reader.fieldnames or ()) == UNCERTAINTY_HEADER, "uncertainty CSV header mismatch")
        rows = list(reader)
    require(rows, "uncertainty CSV is empty")
    return rows


def validate_no_placeholders(text: str, context: str) -> None:
    lowered = text.lower()
    hits = [marker for marker in PLACEHOLDER_MARKERS if marker in lowered]
    require(not hits, f"placeholder marker in {context}: {hits}")


def build_metadata(
    metric_summary: dict[str, Any],
    radiation_summary: dict[str, Any],
    overpressure_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "case": "engineering_h2_fire_consequence_metric_artifacts",
        "dataset_type": "h2_fire_consequence_calibration_agreement",
        "source_type": "literature_digitized",
        "source": {
            "title": "MDPI hydrogen jet-fire radiation anchors and Dataverse EXP002 overpressure anchors",
            "doi": "10.18710/X044QK",
            "url": "https://www.mdpi.com/2076-3417/14/16/7098",
            "notes": (
                "Radiation metrics use MDPI Applied Sciences 14(16):7098 anchors; "
                "overpressure metrics use DataverseNO DOI 10.18710/X044QK EXP002 reduced pressure channels. "
                "The two metric families are retained as partial strict artifacts and do not by themselves prove "
                "full fire calibration closure."
            ),
        },
        "case_alignment": {
            "fuel": True,
            "radiation_measurement_basis": True,
            "overpressure_measurement_basis": True,
            "release_or_cloud_mass": False,
            "ignition_or_burn_basis": False,
            "boundary_conditions": False,
        },
        "uncertainty": {
            "radiation": (
                f"{metric_summary['radiation_metric_count']} radiation anchors; tolerance_rel max "
                f"{radiation_summary['max_tolerance_rel']} from MDPI optimized multi-point-source residual guard."
            ),
            "overpressure": (
                f"{metric_summary['overpressure_metric_count']} overpressure anchors; tolerance_rel max "
                f"{overpressure_summary['max_tolerance_rel']} from reduced EXP002 pressure-channel guard."
            ),
        },
    }


def build_uncertainty_rows(
    radiation_summary: dict[str, Any],
    overpressure_summary: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "artifact": "radiation_metrics.csv",
            "source_basis": "MDPI Applied Sciences 14(16):7098 hydrogen jet-fire radiation anchors",
            "method": "literature table and anchor extraction",
            "calibration_points_or_table": f"{radiation_summary['radiation_metric_count']} radiation metric rows",
            "estimated_uncertainty": (
                f"max relative tolerance {radiation_summary['max_tolerance_rel']}; "
                "absolute tolerance stored per metric row"
            ),
            "review_status": "reviewed_partial_metric_artifact",
        },
        {
            "artifact": "overpressure_metrics.csv",
            "source_basis": "DataverseNO DOI 10.18710/X044QK EXP002 reduced pressure channels",
            "method": "baseline-corrected pressure-channel reduction",
            "calibration_points_or_table": f"{overpressure_summary['overpressure_metric_count']} overpressure metric rows",
            "estimated_uncertainty": (
                f"max relative tolerance {overpressure_summary['max_tolerance_rel']}; "
                "absolute tolerance stored per metric row"
            ),
            "review_status": "reviewed_partial_metric_artifact",
        },
    ]


def validate_metadata(data: dict[str, Any]) -> None:
    require(METADATA_REQUIRED_KEYS.issubset(data), "metadata required keys missing")
    require(data.get("schema_version") == 1, "metadata schema_version mismatch")
    require(data.get("dataset_type") == "h2_fire_consequence_calibration_agreement", "bad dataset_type")
    require(data.get("source_type") == "literature_digitized", "bad source_type")
    source = data.get("source")
    require(isinstance(source, dict), "metadata source is not an object")
    for key in ("title", "doi", "url", "notes"):
        value = source.get(key)
        require(isinstance(value, str) and value.strip(), f"metadata source missing {key}")
    alignment = data.get("case_alignment")
    require(isinstance(alignment, dict), "case_alignment is not an object")
    require(alignment.get("fuel") is True, "fuel alignment should be true")
    require(alignment.get("radiation_measurement_basis") is True, "radiation basis should be true")
    require(alignment.get("overpressure_measurement_basis") is True, "overpressure basis should be true")
    for key in ("release_or_cloud_mass", "ignition_or_burn_basis", "boundary_conditions"):
        require(alignment.get(key) is False, f"{key} must remain false for partial artifacts")
    uncertainty = data.get("uncertainty")
    require(isinstance(uncertainty, dict), "uncertainty is not an object")
    for key in ("radiation", "overpressure"):
        value = uncertainty.get(key)
        require(isinstance(value, str) and "tolerance" in value.lower(), f"uncertainty missing {key}")
    validate_no_placeholders(json.dumps(data, sort_keys=True), "calibration_metadata.json")


def validate_uncertainty_rows(rows: list[dict[str, str]]) -> None:
    require(len(rows) == 2, "unexpected uncertainty row count")
    artifacts = {row.get("artifact") for row in rows}
    require(artifacts == {"radiation_metrics.csv", "overpressure_metrics.csv"}, "unexpected uncertainty artifacts")
    for idx, row in enumerate(rows, 1):
        for key in UNCERTAINTY_HEADER:
            value = row.get(key, "").strip()
            require(value, f"row_{idx}_missing_{key}")
            validate_no_placeholders(value, f"uncertainty row {idx} {key}")
        require(row.get("review_status") == "reviewed_partial_metric_artifact", "bad review status")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    metric_artifact = load_json(Path(args.metric_artifact_report))
    radiation = load_json(Path(args.radiation_report))
    overpressure = load_json(Path(args.overpressure_report))
    metric_summary = metric_artifact.get("summary", {})
    radiation_summary = radiation.get("summary", {})
    overpressure_summary = overpressure.get("summary", {})

    require(metric_artifact.get("status") == "PASS-STRICT-FIRE-CALIBRATION-METRIC-ARTIFACTS", "metric artifacts not PASS")
    require(metric_summary.get("strict_fire_calibration_metric_artifacts_ready") is True, "metric artifacts not ready")
    require(metric_summary.get("ready_for_full_fire_calibration_ingestion") is False, "metric artifacts overclaim full ingestion")
    require(radiation.get("status") == "PASS-H2-FIRE-MDPI-RADIATION-CALIBRATION-TABLE", "radiation source not PASS")
    require(overpressure.get("status") == "PASS-H2-FIRE-EXP002-OVERPRESSURE-CALIBRATION-TABLE", "overpressure source not PASS")

    metadata_path = Path(args.metadata_target)
    uncertainty_path = Path(args.uncertainty_target)
    metadata = build_metadata(metric_summary, radiation_summary, overpressure_summary)
    uncertainty_rows = build_uncertainty_rows(radiation_summary, overpressure_summary)
    validate_metadata(metadata)
    validate_uncertainty_rows(uncertainty_rows)
    write_json(metadata_path, metadata)
    write_uncertainty_csv(uncertainty_path, uncertainty_rows)
    persisted_metadata = load_json(metadata_path)
    persisted_uncertainty_rows = read_uncertainty_csv(uncertainty_path)
    validate_metadata(persisted_metadata)
    validate_uncertainty_rows(persisted_uncertainty_rows)

    ready = (
        persisted_metadata == metadata
        and persisted_uncertainty_rows == uncertainty_rows
        and metric_summary.get("strict_completion_allowed") is False
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "strict fire calibration metadata and digitization uncertainty artifacts",
        "summary": {
            "strict_fire_calibration_metadata_artifacts_ready": ready,
            "calibration_metadata_path": metadata_path.as_posix(),
            "digitization_uncertainty_path": uncertainty_path.as_posix(),
            "metadata_case": metadata["case"],
            "uncertainty_row_count": len(uncertainty_rows),
            "radiation_uncertainty_recorded": True,
            "overpressure_uncertainty_recorded": True,
            "ready_for_full_fire_calibration_ingestion": False,
            "strict_fire_calibration_blocker_cleared": False,
            "strict_completion_allowed": False,
            "strict_master_plan_still_open": True,
        },
        "calibration_metadata": metadata,
        "digitization_uncertainty_rows": uncertainty_rows,
        "evidence_files": [
            evidence_entry("strict_fire_calibration_metric_artifacts", Path(args.metric_artifact_report)),
            evidence_entry("radiation_calibration_table_report", Path(args.radiation_report)),
            evidence_entry("overpressure_calibration_table_report", Path(args.overpressure_report)),
            evidence_entry("calibration_metadata_target", metadata_path),
            evidence_entry("digitization_uncertainty_target", uncertainty_path),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_fire_calibration_metadata_artifacts_ready") is True, "metadata artifacts not ready")
    require(summary.get("uncertainty_row_count") == 2, "unexpected uncertainty row count")
    require(summary.get("radiation_uncertainty_recorded") is True, "radiation uncertainty missing")
    require(summary.get("overpressure_uncertainty_recorded") is True, "overpressure uncertainty missing")
    require(summary.get("ready_for_full_fire_calibration_ingestion") is False, "metadata overclaims full ingestion")
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "metadata clears blocker")
    require(summary.get("strict_completion_allowed") is False, "metadata overclaims strict completion")
    require(summary.get("strict_master_plan_still_open") is True, "metadata overclaims strict closure")
    metadata = data.get("calibration_metadata")
    require(isinstance(metadata, dict), "missing calibration metadata")
    validate_metadata(metadata)
    rows = data.get("digitization_uncertainty_rows")
    require(isinstance(rows, list), "missing uncertainty rows")
    validate_uncertainty_rows(rows)
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict Fire Calibration Metadata Artifacts",
        "",
        f"- Status: `{report['status']}`",
        f"- Ready: `{summary['strict_fire_calibration_metadata_artifacts_ready']}`",
        f"- Metadata: `{summary['calibration_metadata_path']}`",
        f"- Digitization uncertainty: `{summary['digitization_uncertainty_path']}`",
        f"- Full fire calibration ingestion ready: `{summary['ready_for_full_fire_calibration_ingestion']}`",
        f"- Strict completion allowed: `{summary['strict_completion_allowed']}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metric-artifact-report", default=str(METRIC_ARTIFACT_REPORT))
    parser.add_argument("--radiation-report", default=str(RADIATION_REPORT))
    parser.add_argument("--overpressure-report", default=str(OVERPRESSURE_REPORT))
    parser.add_argument("--metadata-target", default=str(METADATA_TARGET))
    parser.add_argument("--uncertainty-target", default=str(UNCERTAINTY_TARGET))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data)
        print(f"strict_fire_calibration_metadata_artifacts VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0
    report = build_report(args)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_fire_calibration_metadata_artifacts PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
