#!/usr/bin/env python3
"""Write/verify strict fire-calibration radiation and overpressure metric artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-FIRE-CALIBRATION-METRIC-ARTIFACTS"

DEFAULT_OUTPUT_ROOT = Path("docs/codex_audit/evidence/strict_fire_calibration_metric_artifacts_20260817")
DEFAULT_OUTPUT_JSON = DEFAULT_OUTPUT_ROOT / "strict_fire_calibration_metric_artifacts_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_OUTPUT_ROOT / "strict_fire_calibration_metric_artifacts_report.md"

SOURCE_REGISTRY_REPORT = Path(
    "docs/codex_audit/evidence/strict_fire_calibration_source_registry_artifact_20260817/"
    "strict_fire_calibration_source_registry_artifact_report.json"
)
RADIATION_REPORT = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_calibration_table_20260805/"
    "h2_fire_mdpi_radiation_calibration_table_report.json"
)
RADIATION_SOURCE = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_calibration_table_20260805/radiation_metrics.csv"
)
OVERPRESSURE_REPORT = Path(
    "docs/codex_audit/evidence/h2_fire_exp002_overpressure_calibration_table_20260805/"
    "h2_fire_exp002_overpressure_calibration_table_report.json"
)
OVERPRESSURE_SOURCE = Path(
    "docs/codex_audit/evidence/h2_fire_exp002_overpressure_calibration_table_20260805/overpressure_metrics.csv"
)
RADIATION_TARGET = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/"
    "dataset/radiation_metrics.csv"
)
OVERPRESSURE_TARGET = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/"
    "dataset/overpressure_metrics.csv"
)

RADIATION_HEADER = (
    "metric_id",
    "distance_m",
    "reference_flux_w_m2",
    "tolerance_abs_w_m2",
    "tolerance_rel",
    "source_basis",
)
OVERPRESSURE_HEADER = (
    "metric_id",
    "distance_m",
    "reference_overpressure_kpa",
    "tolerance_abs_kpa",
    "tolerance_rel",
    "source_basis",
)
PLACEHOLDER_MARKERS = ("<", "replace", "pending", "todo", "tbd", "placeholder", "fill in")


class MetricArtifactError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MetricArtifactError(message)


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
        raise MetricArtifactError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MetricArtifactError(f"invalid JSON evidence {path}: {exc}") from exc
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


def copy_artifact(source: Path, target: Path) -> None:
    require(source.is_file(), f"missing source artifact: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def read_metric_csv(path: Path, header: tuple[str, ...]) -> list[dict[str, str]]:
    require(path.is_file(), f"missing metric CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        require(tuple(reader.fieldnames or ()) == header, f"metric CSV header mismatch: {path}")
        rows = list(reader)
    require(rows, f"metric CSV is empty: {path}")
    return rows


def validate_metric_rows(
    rows: list[dict[str, str]],
    *,
    value_key: str,
    tolerance_key: str,
    expected_count: int,
) -> dict[str, Any]:
    ids: set[str] = set()
    values: list[float] = []
    tolerances: list[float] = []
    rel_tolerances: list[float] = []
    gaps: list[str] = []
    for idx, row in enumerate(rows, 1):
        metric_id = row.get("metric_id", "").strip()
        if not metric_id:
            gaps.append(f"row_{idx}_missing_metric_id")
        if metric_id in ids:
            gaps.append(f"duplicate_metric_id:{metric_id}")
        ids.add(metric_id)
        source_basis = row.get("source_basis", "").strip()
        if not source_basis:
            gaps.append(f"row_{idx}_missing_source_basis")
        text = " ".join(row.get(key, "") for key in row).lower()
        if any(marker in text for marker in PLACEHOLDER_MARKERS):
            gaps.append(f"row_{idx}_placeholder_marker")
        for key in ("distance_m", value_key, tolerance_key, "tolerance_rel"):
            try:
                number = float(row.get(key, ""))
            except ValueError:
                gaps.append(f"row_{idx}_invalid_{key}")
                continue
            if number <= 0.0:
                gaps.append(f"row_{idx}_nonpositive_{key}")
            if key == value_key:
                values.append(number)
            elif key == tolerance_key:
                tolerances.append(number)
            elif key == "tolerance_rel":
                rel_tolerances.append(number)
    require(len(rows) == expected_count, f"unexpected metric row count: {len(rows)}")
    require(not gaps, "metric validation gaps: " + ",".join(gaps))
    return {
        "row_count": len(rows),
        "min_reference_value": min(values),
        "max_reference_value": max(values),
        "max_abs_tolerance": max(tolerances),
        "max_rel_tolerance": max(rel_tolerances),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    registry_report = load_json(Path(args.source_registry_report))
    radiation_report = load_json(Path(args.radiation_report))
    overpressure_report = load_json(Path(args.overpressure_report))

    require(
        registry_report.get("status") == "PASS-STRICT-FIRE-CALIBRATION-SOURCE-REGISTRY-ARTIFACT",
        "source registry artifact is not PASS",
    )
    require(
        registry_report.get("summary", {}).get("registry_is_source_list_not_calibration_dataset") is True,
        "source registry overclaimed calibration dataset",
    )
    require(
        radiation_report.get("status") == "PASS-H2-FIRE-MDPI-RADIATION-CALIBRATION-TABLE",
        "radiation calibration table is not PASS",
    )
    require(
        overpressure_report.get("status") == "PASS-H2-FIRE-EXP002-OVERPRESSURE-CALIBRATION-TABLE",
        "overpressure calibration table is not PASS",
    )
    require(radiation_report.get("summary", {}).get("radiation_metrics_csv_ready") is True, "radiation CSV not ready")
    require(
        overpressure_report.get("summary", {}).get("overpressure_metrics_csv_ready") is True,
        "overpressure CSV not ready",
    )
    require(
        radiation_report.get("summary", {}).get("ready_for_full_fire_calibration_ingestion") is False,
        "radiation report unexpectedly claims full ingestion readiness",
    )
    require(
        overpressure_report.get("summary", {}).get("ready_for_full_fire_calibration_ingestion") is False,
        "overpressure report unexpectedly claims full ingestion readiness",
    )

    radiation_source = Path(args.radiation_source)
    overpressure_source = Path(args.overpressure_source)
    radiation_target = Path(args.radiation_target)
    overpressure_target = Path(args.overpressure_target)
    copy_artifact(radiation_source, radiation_target)
    copy_artifact(overpressure_source, overpressure_target)
    require(sha256_file(radiation_source) == sha256_file(radiation_target), "radiation target hash differs from source")
    require(
        sha256_file(overpressure_source) == sha256_file(overpressure_target),
        "overpressure target hash differs from source",
    )

    radiation_rows = read_metric_csv(radiation_target, RADIATION_HEADER)
    overpressure_rows = read_metric_csv(overpressure_target, OVERPRESSURE_HEADER)
    radiation_summary = validate_metric_rows(
        radiation_rows,
        value_key="reference_flux_w_m2",
        tolerance_key="tolerance_abs_w_m2",
        expected_count=4,
    )
    overpressure_summary = validate_metric_rows(
        overpressure_rows,
        value_key="reference_overpressure_kpa",
        tolerance_key="tolerance_abs_kpa",
        expected_count=4,
    )
    ready = (
        radiation_summary["row_count"] == 4
        and overpressure_summary["row_count"] == 4
        and radiation_report.get("summary", {}).get("ready_for_cfd_radiation_comparison") is True
        and overpressure_report.get("summary", {}).get("ready_for_cfd_pressure_sensor_comparison") is True
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "strict fire calibration metric CSV artifacts",
        "summary": {
            "strict_fire_calibration_metric_artifacts_ready": ready,
            "radiation_metrics_path": radiation_target.as_posix(),
            "radiation_metric_count": radiation_summary["row_count"],
            "overpressure_metrics_path": overpressure_target.as_posix(),
            "overpressure_metric_count": overpressure_summary["row_count"],
            "radiation_source_hash_matches_target": True,
            "overpressure_source_hash_matches_target": True,
            "calibration_metadata_still_required": True,
            "digitization_uncertainty_still_required": True,
            "ready_for_full_fire_calibration_ingestion": False,
            "strict_fire_calibration_blocker_cleared": False,
            "strict_completion_allowed": False,
            "strict_master_plan_still_open": True,
        },
        "radiation_metrics": radiation_rows,
        "overpressure_metrics": overpressure_rows,
        "evidence_files": [
            evidence_entry("strict_fire_calibration_source_registry_artifact", Path(args.source_registry_report)),
            evidence_entry("radiation_calibration_table_report", Path(args.radiation_report)),
            evidence_entry("radiation_metrics_source", radiation_source),
            evidence_entry("radiation_metrics_target", radiation_target),
            evidence_entry("overpressure_calibration_table_report", Path(args.overpressure_report)),
            evidence_entry("overpressure_metrics_source", overpressure_source),
            evidence_entry("overpressure_metrics_target", overpressure_target),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_fire_calibration_metric_artifacts_ready") is True, "metric artifacts not ready")
    require(summary.get("radiation_metric_count") == 4, "unexpected radiation metric count")
    require(summary.get("overpressure_metric_count") == 4, "unexpected overpressure metric count")
    require(summary.get("radiation_source_hash_matches_target") is True, "radiation source/target mismatch")
    require(summary.get("overpressure_source_hash_matches_target") is True, "overpressure source/target mismatch")
    require(summary.get("calibration_metadata_still_required") is True, "metadata requirement overclaimed")
    require(summary.get("digitization_uncertainty_still_required") is True, "digitization uncertainty overclaimed")
    require(
        summary.get("ready_for_full_fire_calibration_ingestion") is False,
        "metric artifacts overclaim full ingestion",
    )
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "metric artifacts cleared blocker")
    require(summary.get("strict_completion_allowed") is False, "metric artifacts overclaim strict completion")
    require(summary.get("strict_master_plan_still_open") is True, "metric artifacts overclaim strict closure")
    radiation_rows = data.get("radiation_metrics")
    overpressure_rows = data.get("overpressure_metrics")
    require(isinstance(radiation_rows, list), "invalid radiation metrics")
    require(isinstance(overpressure_rows, list), "invalid overpressure metrics")
    validate_metric_rows(
        radiation_rows,
        value_key="reference_flux_w_m2",
        tolerance_key="tolerance_abs_w_m2",
        expected_count=4,
    )
    validate_metric_rows(
        overpressure_rows,
        value_key="reference_overpressure_kpa",
        tolerance_key="tolerance_abs_kpa",
        expected_count=4,
    )
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict Fire Calibration Metric Artifacts",
        "",
        f"- Status: `{report['status']}`",
        f"- Ready: `{summary['strict_fire_calibration_metric_artifacts_ready']}`",
        f"- Radiation metrics: `{summary['radiation_metric_count']}`",
        f"- Overpressure metrics: `{summary['overpressure_metric_count']}`",
        f"- Full fire calibration ingestion ready: `{summary['ready_for_full_fire_calibration_ingestion']}`",
        f"- Strict completion allowed: `{summary['strict_completion_allowed']}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-registry-report", default=str(SOURCE_REGISTRY_REPORT))
    parser.add_argument("--radiation-report", default=str(RADIATION_REPORT))
    parser.add_argument("--radiation-source", default=str(RADIATION_SOURCE))
    parser.add_argument("--radiation-target", default=str(RADIATION_TARGET))
    parser.add_argument("--overpressure-report", default=str(OVERPRESSURE_REPORT))
    parser.add_argument("--overpressure-source", default=str(OVERPRESSURE_SOURCE))
    parser.add_argument("--overpressure-target", default=str(OVERPRESSURE_TARGET))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()
    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data)
        print(f"strict_fire_calibration_metric_artifacts VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0
    report = build_report(args)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_fire_calibration_metric_artifacts PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
