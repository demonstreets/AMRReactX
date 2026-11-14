#!/usr/bin/env python3
"""Validate any present strict external-artifact drops against template contracts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT"
STATUS_NOT_READY = "NOT_READY-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_artifact_drop_contract_preflight_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_artifact_drop_contract_preflight_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_artifact_drop_contract_preflight_report.md"

STRICT_DROP_PREFLIGHT = Path(
    "docs/codex_audit/evidence/master_plan_strict_artifact_drop_preflight_20260731/"
    "master_plan_strict_artifact_drop_preflight_report.json"
)
STRICT_TEMPLATE_LINT = Path(
    "docs/codex_audit/evidence/strict_artifact_template_lint_20260803/"
    "strict_artifact_template_lint_report.json"
)

DROP_ROOTS = {
    "external_plume": Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset"),
    "real_cad": Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package"),
    "fire_calibration": Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset"),
}

JSON_CONTRACTS: dict[str, tuple[str, Path, set[str]]] = {
    "external_plume.dataset_metadata": (
        "external_plume",
        DROP_ROOTS["external_plume"] / "dataset_metadata.json",
        {"benchmark_id", "case_alignment", "digitization", "digitized_dataset_sha256", "original_dataset_sha256", "schema_version", "source"},
    ),
    "real_cad.real_cad_cleanup_manifest": (
        "real_cad",
        DROP_ROOTS["real_cad"] / "real_cad_cleanup_manifest.json",
        {"cad_source_is_real", "campaign", "dataset_type", "geometries", "large_layout_campaign", "provenance", "schema_version", "source_type", "status", "synthetic"},
    ),
    "fire_calibration.calibration_metadata": (
        "fire_calibration",
        DROP_ROOTS["fire_calibration"] / "calibration_metadata.json",
        {"case", "case_alignment", "dataset_type", "schema_version", "source", "source_type", "uncertainty"},
    ),
}

CSV_CONTRACTS: dict[str, tuple[str, Path, list[str], bool]] = {
    "external_plume.sensor_coordinates": (
        "external_plume",
        DROP_ROOTS["external_plume"] / "sensor_coordinates.csv",
        ["sensor_id", "x_m", "y_m", "z_m", "reliability", "source_basis", "digitization_uncertainty_m"],
        True,
    ),
    "external_plume.baffle_geometry": (
        "external_plume",
        DROP_ROOTS["external_plume"] / "baffle_geometry.csv",
        ["baffle_id", "x_min_m", "x_max_m", "y_min_m", "y_max_m", "z_min_m", "z_max_m", "source_basis", "digitization_uncertainty_m"],
        True,
    ),
    "external_plume.experimental_timeseries": (
        "external_plume",
        DROP_ROOTS["external_plume"] / "experimental_timeseries.csv",
        ["time_s", "Gas01_vol_percent", "Gas02_vol_percent", "Gas03_vol_percent", "Gas04_vol_percent", "Gas05_vol_percent", "Gas06_vol_percent", "Gas07_vol_percent", "Gas08_vol_percent", "Gas09_vol_percent", "Gas10_vol_percent", "Gas11_vol_percent", "Gas12_vol_percent"],
        True,
    ),
    "external_plume.digitization_uncertainty_record": (
        "external_plume",
        DROP_ROOTS["external_plume"] / "digitization_uncertainty_record.csv",
        ["artifact", "source_basis", "method", "axis_or_geometry_calibration", "estimated_uncertainty", "review_status"],
        False,
    ),
    "real_cad.real_cad_data_room_index": (
        "real_cad",
        DROP_ROOTS["real_cad"] / "real_cad_data_room_index.csv",
        ["file_role", "label", "relative_path", "sha256", "source_type", "revision", "owner_or_supplier", "notes"],
        True,
    ),
    "real_cad.real_cad_cleanup_quality_record": (
        "real_cad",
        DROP_ROOTS["real_cad"] / "real_cad_cleanup_quality_record.csv",
        ["label", "units_declared", "watertight_or_closed_surface", "nondegenerate_elements", "positive_volume_or_area", "bbox_min_m", "bbox_max_m", "tool_or_method", "reviewer"],
        True,
    ),
    "real_cad.real_cad_boundary_tags": (
        "real_cad",
        DROP_ROOTS["real_cad"] / "real_cad_boundary_tags.csv",
        ["label", "patch_id", "bc_type", "face_selector", "normal_hint", "area_m2", "source_basis", "engineering_role", "reviewer"],
        True,
    ),
    "fire_calibration.radiation_metrics": (
        "fire_calibration",
        DROP_ROOTS["fire_calibration"] / "radiation_metrics.csv",
        ["metric_id", "distance_m", "reference_flux_w_m2", "tolerance_abs_w_m2", "tolerance_rel", "source_basis"],
        True,
    ),
    "fire_calibration.overpressure_metrics": (
        "fire_calibration",
        DROP_ROOTS["fire_calibration"] / "overpressure_metrics.csv",
        ["metric_id", "distance_m", "reference_overpressure_kpa", "tolerance_abs_kpa", "tolerance_rel", "source_basis"],
        True,
    ),
    "fire_calibration.fire_calibration_source_registry": (
        "fire_calibration",
        DROP_ROOTS["fire_calibration"] / "fire_calibration_source_registry.csv",
        ["family", "candidate_id", "title", "url_or_doi", "selected_for_calibration", "required_digitization"],
        True,
    ),
    "fire_calibration.fire_calibration_digitization_uncertainty": (
        "fire_calibration",
        DROP_ROOTS["fire_calibration"] / "fire_calibration_digitization_uncertainty.csv",
        ["artifact", "source_basis", "method", "calibration_points_or_table", "estimated_uncertainty", "review_status"],
        False,
    ),
}


class DropContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DropContractError(message)


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
        raise DropContractError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DropContractError(f"invalid JSON evidence {path}: {exc}") from exc
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


def json_duplicate_keys(path: Path) -> bool:
    duplicate = False

    def object_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        nonlocal duplicate
        seen: set[str] = set()
        for key, _ in pairs:
            if key in seen:
                duplicate = True
            seen.add(key)
        return dict(pairs)

    json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=object_hook)
    return duplicate


def validate_json_artifact(label: str, domain: str, path: Path, required_keys: set[str]) -> dict[str, Any]:
    if not path.exists():
        return {
            "label": label,
            "domain": domain,
            "path": str(path),
            "kind": "json",
            "present": False,
            "ready": True,
            "reason": "awaiting_external_artifact",
        }
    errors: list[str] = []
    try:
        data = load_json(path)
    except DropContractError as exc:
        return {
            "label": label,
            "domain": domain,
            "path": str(path),
            "kind": "json",
            "present": True,
            "ready": False,
            "errors": [str(exc)],
        }
    missing = sorted(required_keys - set(data))
    if missing:
        errors.append(f"missing required keys: {', '.join(missing)}")
    try:
        if json_duplicate_keys(path):
            errors.append("duplicate JSON keys detected")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON: {exc}")
    return {
        "label": label,
        "domain": domain,
        "path": str(path),
        "kind": "json",
        "present": True,
        "ready": not errors,
        "required_keys": sorted(required_keys),
        "actual_keys": sorted(data),
        "errors": errors,
        "sha256": sha256_file(path),
    }


def validate_csv_artifact(label: str, domain: str, path: Path, expected_header: list[str], required: bool) -> dict[str, Any]:
    if not path.exists():
        return {
            "label": label,
            "domain": domain,
            "path": str(path),
            "kind": "csv",
            "present": False,
            "required": required,
            "ready": True,
            "reason": "awaiting_external_artifact" if required else "optional_artifact_absent",
        }
    errors: list[str] = []
    try:
        with path.open(newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.reader(fh))
    except Exception as exc:  # pragma: no cover - defensive for external files
        return {
            "label": label,
            "domain": domain,
            "path": str(path),
            "kind": "csv",
            "present": True,
            "required": required,
            "ready": False,
            "errors": [f"invalid CSV: {exc}"],
        }
    header = rows[0] if rows else []
    duplicate_columns = sorted({column for column in header if header.count(column) > 1})
    blank_columns = [index for index, column in enumerate(header) if not column.strip()]
    if header != expected_header:
        errors.append("header does not match expected template contract")
    if duplicate_columns:
        errors.append(f"duplicate columns: {', '.join(duplicate_columns)}")
    if blank_columns:
        errors.append(f"blank column indices: {', '.join(map(str, blank_columns))}")
    if required and len(rows) <= 1:
        errors.append("required CSV has no data rows")
    return {
        "label": label,
        "domain": domain,
        "path": str(path),
        "kind": "csv",
        "present": True,
        "required": required,
        "ready": not errors,
        "expected_header": expected_header,
        "actual_header": header,
        "row_count": len(rows),
        "data_row_count": max(0, len(rows) - 1),
        "errors": errors,
        "sha256": sha256_file(path),
    }


def build_report() -> dict[str, Any]:
    drop = load_json(STRICT_DROP_PREFLIGHT)
    template_lint = load_json(STRICT_TEMPLATE_LINT)
    require(
        drop.get("status")
        in {
            "AWAITING-MASTER-PLAN-STRICT-ARTIFACT-DROP-PREFLIGHT-EXTERNAL-ARTIFACTS",
            "PASS-MASTER-PLAN-STRICT-ARTIFACT-DROP-PREFLIGHT-COMPLETE",
        },
        "strict artifact drop preflight is not ready",
    )
    require(template_lint.get("status") == "PASS-STRICT-ARTIFACT-TEMPLATE-LINT", "strict template lint is not ready")

    checks = [
        validate_json_artifact(label, domain, path, required_keys)
        for label, (domain, path, required_keys) in JSON_CONTRACTS.items()
    ]
    checks.extend(
        validate_csv_artifact(label, domain, path, expected_header, required)
        for label, (domain, path, expected_header, required) in CSV_CONTRACTS.items()
    )

    present = [check for check in checks if check["present"]]
    invalid = [check for check in present if not check["ready"]]
    domains = {
        name: {
            "drop_root": str(root),
            "present_contract_artifact_count": sum(1 for check in present if check["domain"] == name),
            "invalid_contract_artifact_count": sum(1 for check in invalid if check["domain"] == name),
        }
        for name, root in DROP_ROOTS.items()
    }
    ready = len(invalid) == 0
    evidence_files = [
        evidence_entry("strict_artifact_drop_preflight", STRICT_DROP_PREFLIGHT),
        evidence_entry("strict_artifact_template_lint", STRICT_TEMPLATE_LINT),
    ]
    for check in present:
        evidence_files.append(evidence_entry(check["label"], Path(check["path"])))

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "strict_artifact_drop_contract_preflight_ready": ready,
            "drop_preflight_status": drop.get("status"),
            "template_lint_status": template_lint.get("status"),
            "contract_check_count": len(checks),
            "present_contract_artifact_count": len(present),
            "invalid_present_artifact_count": len(invalid),
            "awaiting_missing_artifact_count": len(checks) - len(present),
        },
        "domains": domains,
        "checks": checks,
        "invalid_checks": invalid,
        "evidence_files": evidence_files,
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_artifact_drop_contract_preflight_ready") is True, "drop contract preflight is not ready")
    require(summary.get("template_lint_status") == "PASS-STRICT-ARTIFACT-TEMPLATE-LINT", "template lint not ready")
    require(summary.get("contract_check_count") == 14, "unexpected contract check count")
    require(summary.get("invalid_present_artifact_count") == 0, "invalid present artifacts found")
    for check in data.get("checks", []):
        require(isinstance(check, dict), "invalid check entry")
        require(check.get("ready") is True, f"drop artifact contract failed: {check.get('label')}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict Artifact Drop Contract Preflight",
        "",
        f"- Status: `{report['status']}`",
        f"- Contract checks: `{summary['contract_check_count']}`",
        f"- Present contract artifacts: `{summary['present_contract_artifact_count']}`",
        f"- Invalid present artifacts: `{summary['invalid_present_artifact_count']}`",
        f"- Awaiting missing artifacts: `{summary['awaiting_missing_artifact_count']}`",
        "",
        "## Domains",
        "",
    ]
    for name, domain in report["domains"].items():
        lines.append(
            f"- `{name}` present=`{domain['present_contract_artifact_count']}` "
            f"invalid=`{domain['invalid_contract_artifact_count']}` root=`{domain['drop_root']}`"
        )
    lines.extend(["", "## Checks", ""])
    for check in report["checks"]:
        state = "present" if check["present"] else "awaiting"
        lines.append(f"- `{check['label']}` `{check['kind']}` {state} ready=`{check['ready']}`")
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
        print(f"strict_artifact_drop_contract_preflight VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_artifact_drop_contract_preflight PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
