#!/usr/bin/env python3
"""Lint strict external-artifact intake templates at content level."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-ARTIFACT-TEMPLATE-LINT"
STATUS_NOT_READY = "NOT_READY-STRICT-ARTIFACT-TEMPLATE-LINT"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_artifact_template_lint_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_artifact_template_lint_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_artifact_template_lint_report.md"

STRICT_INTAKE_MANIFEST = Path(
    "docs/codex_audit/evidence/master_plan_strict_artifact_intake_manifest_20260731/"
    "master_plan_strict_artifact_intake_manifest_report.json"
)

JSON_CONTRACTS: dict[str, tuple[Path, set[str]]] = {
    "external_plume_metadata": (
        Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata_template.json"),
        {"benchmark_id", "case_alignment", "digitization", "digitized_dataset_sha256", "original_dataset_sha256", "schema_version", "source"},
    ),
    "real_cad_cleanup_manifest": (
        Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest_template.json"),
        {"cad_source_is_real", "campaign", "dataset_type", "geometries", "large_layout_campaign", "provenance", "schema_version", "source_type", "status", "synthetic"},
    ),
    "fire_calibration_metadata": (
        Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata_template.json"),
        {"case", "case_alignment", "dataset_type", "schema_version", "source", "source_type", "uncertainty"},
    ),
}

CSV_CONTRACTS: dict[str, tuple[Path, list[str]]] = {
    "external_plume_sensor_coordinates": (
        Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates_template.csv"),
        ["sensor_id", "x_m", "y_m", "z_m", "reliability", "source_basis", "digitization_uncertainty_m"],
    ),
    "external_plume_baffle_geometry": (
        Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry_template.csv"),
        ["baffle_id", "x_min_m", "x_max_m", "y_min_m", "y_max_m", "z_min_m", "z_max_m", "source_basis", "digitization_uncertainty_m"],
    ),
    "external_plume_experimental_timeseries": (
        Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries_template.csv"),
        ["time_s", "Gas01_vol_percent", "Gas02_vol_percent", "Gas03_vol_percent", "Gas04_vol_percent", "Gas05_vol_percent", "Gas06_vol_percent", "Gas07_vol_percent", "Gas08_vol_percent", "Gas09_vol_percent", "Gas10_vol_percent", "Gas11_vol_percent", "Gas12_vol_percent"],
    ),
    "external_plume_digitization_uncertainty": (
        Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/digitization_uncertainty_record_template.csv"),
        ["artifact", "source_basis", "method", "axis_or_geometry_calibration", "estimated_uncertainty", "review_status"],
    ),
    "real_cad_data_room_index": (
        Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index_template.csv"),
        ["file_role", "label", "relative_path", "sha256", "source_type", "revision", "owner_or_supplier", "notes"],
    ),
    "real_cad_cleanup_quality_record": (
        Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record_template.csv"),
        ["label", "units_declared", "watertight_or_closed_surface", "nondegenerate_elements", "positive_volume_or_area", "bbox_min_m", "bbox_max_m", "tool_or_method", "reviewer"],
    ),
    "real_cad_boundary_tags": (
        Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_boundary_tags_template.csv"),
        ["label", "patch_id", "bc_type", "face_selector", "normal_hint", "area_m2", "source_basis", "engineering_role", "reviewer"],
    ),
    "real_cad_intake_checklist": (
        Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_intake_checklist.csv"),
        ["item", "required_evidence", "production_rule"],
    ),
    "fire_calibration_radiation_metrics": (
        Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics_template.csv"),
        ["metric_id", "distance_m", "reference_flux_w_m2", "tolerance_abs_w_m2", "tolerance_rel", "source_basis"],
    ),
    "fire_calibration_overpressure_metrics": (
        Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics_template.csv"),
        ["metric_id", "distance_m", "reference_overpressure_kpa", "tolerance_abs_kpa", "tolerance_rel", "source_basis"],
    ),
    "fire_calibration_digitization_uncertainty": (
        Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_digitization_uncertainty_template.csv"),
        ["artifact", "source_basis", "method", "calibration_points_or_table", "estimated_uncertainty", "review_status"],
    ),
    "fire_calibration_source_registry": (
        Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_source_registry_template.csv"),
        ["family", "candidate_id", "title", "url_or_doi", "selected_for_calibration", "required_digitization"],
    ),
    "fire_calibration_intake_checklist": (
        Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_intake_checklist.csv"),
        ["item", "required_evidence", "production_rule"],
    ),
}


class TemplateLintError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TemplateLintError(message)


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
        raise TemplateLintError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TemplateLintError(f"invalid JSON evidence {path}: {exc}") from exc
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


def lint_json_template(label: str, path: Path, required_keys: set[str]) -> dict[str, Any]:
    data = load_json(path)
    keys = set(data)
    missing = sorted(required_keys - keys)
    duplicate_keys = False
    try:
        def object_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            nonlocal duplicate_keys
            seen: set[str] = set()
            for key, _ in pairs:
                if key in seen:
                    duplicate_keys = True
                seen.add(key)
            return dict(pairs)

        json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=object_hook)
    except json.JSONDecodeError:
        duplicate_keys = True
    return {
        "label": label,
        "path": str(path),
        "kind": "json",
        "required_keys": sorted(required_keys),
        "actual_keys": sorted(keys),
        "missing_required_keys": missing,
        "has_schema_version": "schema_version" in keys,
        "duplicate_keys_detected": duplicate_keys,
        "ready": not missing and "schema_version" in keys and not duplicate_keys,
        "sha256": sha256_file(path),
    }


def lint_csv_template(label: str, path: Path, expected_header: list[str]) -> dict[str, Any]:
    require(path.is_file(), f"missing CSV template: {path}")
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    header = rows[0] if rows else []
    duplicate_columns = sorted({column for column in header if header.count(column) > 1})
    blank_columns = [index for index, column in enumerate(header) if not column.strip()]
    ready = header == expected_header and not duplicate_columns and not blank_columns and len(rows) >= 1
    return {
        "label": label,
        "path": str(path),
        "kind": "csv",
        "expected_header": expected_header,
        "actual_header": header,
        "row_count": len(rows),
        "duplicate_columns": duplicate_columns,
        "blank_column_indices": blank_columns,
        "header_matches_expected": header == expected_header,
        "ready": ready,
        "sha256": sha256_file(path),
    }


def build_report() -> dict[str, Any]:
    intake = load_json(STRICT_INTAKE_MANIFEST)
    evidence_files = [evidence_entry("strict_artifact_intake_manifest", STRICT_INTAKE_MANIFEST)]

    json_templates = [
        lint_json_template(label, path, required_keys)
        for label, (path, required_keys) in JSON_CONTRACTS.items()
    ]
    csv_templates = [
        lint_csv_template(label, path, expected_header)
        for label, (path, expected_header) in CSV_CONTRACTS.items()
    ]
    for label, (path, _) in JSON_CONTRACTS.items():
        evidence_files.append(evidence_entry(label, path))
    for label, (path, _) in CSV_CONTRACTS.items():
        evidence_files.append(evidence_entry(label, path))

    templates = json_templates + csv_templates
    failing = [template for template in templates if not template["ready"]]
    ready = (
        intake.get("status") == "READY-MASTER-PLAN-STRICT-ARTIFACT-INTAKE-MANIFEST"
        and len(json_templates) == 3
        and len(csv_templates) == 13
        and not failing
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "strict_artifact_template_lint_ready": ready,
            "intake_manifest_status": intake.get("status"),
            "json_template_count": len(json_templates),
            "csv_template_count": len(csv_templates),
            "template_count": len(templates),
            "failing_template_count": len(failing),
        },
        "templates": templates,
        "failing_templates": failing,
        "evidence_files": evidence_files,
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_artifact_template_lint_ready") is True, "template lint is not ready")
    require(summary.get("intake_manifest_status") == "READY-MASTER-PLAN-STRICT-ARTIFACT-INTAKE-MANIFEST", "intake manifest not ready")
    require(summary.get("json_template_count") == 3, "unexpected JSON template count")
    require(summary.get("csv_template_count") == 13, "unexpected CSV template count")
    require(summary.get("template_count") == 16, "unexpected template count")
    require(summary.get("failing_template_count") == 0, "one or more templates failed lint")
    for template in data.get("templates", []):
        require(isinstance(template, dict), "invalid template entry")
        require(template.get("ready") is True, f"template not ready: {template.get('path')}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict Artifact Template Lint",
        "",
        f"- Status: `{report['status']}`",
        f"- JSON templates: `{summary['json_template_count']}`",
        f"- CSV templates: `{summary['csv_template_count']}`",
        f"- Failing templates: `{summary['failing_template_count']}`",
        "",
        "## Templates",
        "",
    ]
    for template in report["templates"]:
        if template["kind"] == "json":
            detail = f"keys={len(template['actual_keys'])}"
        else:
            detail = f"columns={len(template['actual_header'])} rows={template['row_count']}"
        lines.append(f"- `{template['label']}` `{template['kind']}` ready=`{template['ready']}` {detail}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"strict_artifact_template_lint VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_artifact_template_lint PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
