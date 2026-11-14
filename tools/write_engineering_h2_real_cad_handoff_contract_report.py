#!/usr/bin/env python3
"""Write a machine-checkable handoff contract for real-CAD artifact delivery."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-REAL-CAD-HANDOFF-CONTRACT"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_h2_real_cad_handoff_contract_20260805")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "real_cad_handoff_contract_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "real_cad_handoff_contract_report.md"

PACKAGE_ROOT = Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package")
CLEANUP_PACKAGE = Path(
    "docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/"
    "real_cad_cleanup_package_report.json"
)
INTAKE_PREFLIGHT = Path(
    "docs/codex_audit/evidence/engineering_h2_real_cad_intake_preflight_20260724/"
    "real_cad_intake_preflight_report.json"
)
BOUNDARY_CONTRACT = Path(
    "docs/codex_audit/evidence/engineering_h2_real_cad_boundary_tag_contract_20260724/"
    "real_cad_boundary_tag_contract_report.json"
)

REQUIRED_MANIFEST_KEYS = {
    "schema_version",
    "dataset_type",
    "campaign",
    "status",
    "synthetic",
    "cad_source_is_real",
    "source_type",
    "large_layout_campaign",
    "provenance",
    "geometries",
}
REQUIRED_PROVENANCE_KEYS = {
    "title",
    "owner_or_supplier",
    "drawing_or_package_id",
    "revision",
    "received_at_utc",
    "confidentiality",
}
REQUIRED_GEOMETRY_KEYS = {"label", "source_cad", "cleaned_geometry", "cleanup_checks"}
REQUIRED_DATA_ROOM_COLUMNS = {
    "file_role",
    "label",
    "relative_path",
    "sha256",
    "source_type",
    "revision",
    "owner_or_supplier",
}
REQUIRED_CLEANUP_QUALITY_COLUMNS = {
    "label",
    "units_declared",
    "watertight_or_closed_surface",
    "nondegenerate_elements",
    "positive_volume_or_area",
    "bbox_min_m",
    "bbox_max_m",
    "tool_or_method",
    "reviewer",
}
REQUIRED_BOUNDARY_COLUMNS = {
    "label",
    "patch_id",
    "bc_type",
    "face_selector",
    "normal_hint",
    "area_m2",
    "source_basis",
    "engineering_role",
    "reviewer",
}
REQUIRED_BOUNDARY_ROLES = {"wall_or_obstacle", "release_or_inlet", "outflow_or_vent"}


class HandoffContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HandoffContractError(message)


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
        raise HandoffContractError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HandoffContractError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {"label": label, "path": str(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def validate_manifest_template(path: Path) -> dict[str, Any]:
    manifest = load_json(path)
    missing = sorted(REQUIRED_MANIFEST_KEYS - set(manifest))
    require(not missing, f"manifest template missing keys: {missing}")
    provenance = manifest.get("provenance")
    require(isinstance(provenance, dict), "manifest provenance must be an object")
    missing_provenance = sorted(REQUIRED_PROVENANCE_KEYS - set(provenance))
    require(not missing_provenance, f"manifest provenance missing keys: {missing_provenance}")
    geometries = manifest.get("geometries")
    require(isinstance(geometries, list) and len(geometries) >= 3, "manifest template requires >=3 geometries")
    labels = []
    for idx, geometry in enumerate(geometries, 1):
        require(isinstance(geometry, dict), f"geometry {idx} must be an object")
        missing_geometry = sorted(REQUIRED_GEOMETRY_KEYS - set(geometry))
        require(not missing_geometry, f"geometry {idx} missing keys: {missing_geometry}")
        labels.append(str(geometry.get("label", "")).strip())
    require(all(labels) and len(set(labels)) == len(labels), "geometry labels must be nonempty and unique")
    return {"path": str(path), "geometry_label_count": len(labels), "geometry_labels": labels}


def validate_template_columns(path: Path, required: set[str]) -> dict[str, Any]:
    rows = read_csv_rows(path)
    require(rows, f"CSV template has no data rows: {path}")
    columns = {str(column) for column in rows[0].keys() if column is not None}
    missing = sorted(required - columns)
    require(not missing, f"{path} missing required columns: {missing}")
    return {"path": str(path), "column_count": len(columns), "columns": sorted(columns)}


def validate_boundary_template(path: Path) -> dict[str, Any]:
    rows = read_csv_rows(path)
    require(rows, "boundary tag template has no data rows")
    columns = set(rows[0].keys())
    missing = sorted(REQUIRED_BOUNDARY_COLUMNS - columns)
    require(not missing, f"boundary tag template missing columns: {missing}")
    roles = {str(row.get("engineering_role", "")).strip() for row in rows}
    missing_roles = sorted(REQUIRED_BOUNDARY_ROLES - roles)
    require(not missing_roles, f"boundary tag template missing required roles: {missing_roles}")
    return {"path": str(path), "row_count": len(rows), "roles": sorted(roles)}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    package_root = Path(args.package_root)
    cleanup_package = load_json(Path(args.cleanup_package))
    intake_preflight = load_json(Path(args.intake_preflight))
    boundary_contract = load_json(Path(args.boundary_contract))

    manifest_template = package_root / "real_cad_cleanup_manifest_template.json"
    data_room_template = package_root / "real_cad_data_room_index_template.csv"
    cleanup_quality_template = package_root / "real_cad_cleanup_quality_record_template.csv"
    boundary_template = package_root / "real_cad_boundary_tags_template.csv"
    checklist = package_root / "real_cad_intake_checklist.csv"

    checks = {
        "cleanup_package_template": validate_manifest_template(manifest_template),
        "data_room_index_template": validate_template_columns(data_room_template, REQUIRED_DATA_ROOM_COLUMNS),
        "cleanup_quality_template": validate_template_columns(cleanup_quality_template, REQUIRED_CLEANUP_QUALITY_COLUMNS),
        "boundary_tag_template": validate_boundary_template(boundary_template),
        "intake_checklist": validate_template_columns(checklist, {"item", "required_evidence", "production_rule"}),
    }
    require(cleanup_package.get("status") == "NOT_READY-H2-REAL-CAD-CLEANUP-PACKAGE", "cleanup should remain not ready")
    require(intake_preflight.get("status") == "PASS-H2-REAL-CAD-INTAKE-PREFLIGHT", "intake preflight not ready")
    require(
        boundary_contract.get("status") == "NOT_READY-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT",
        "boundary contract should remain not ready",
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "title": "Engineering H2 Real-CAD Handoff Contract",
        "status": STATUS_PASS,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "handoff_contract_ready": True,
            "manifest_template_ready": True,
            "data_room_index_template_ready": True,
            "cleanup_quality_template_ready": True,
            "boundary_tag_template_ready": True,
            "intake_checklist_ready": True,
            "source_cad_artifacts_present": False,
            "strict_real_cad_blocker_cleared": False,
        },
        "acceptance_contract": {
            "minimum_real_geometry_count": 3,
            "required_manifest_keys": sorted(REQUIRED_MANIFEST_KEYS),
            "required_provenance_keys": sorted(REQUIRED_PROVENANCE_KEYS),
            "required_data_room_columns": sorted(REQUIRED_DATA_ROOM_COLUMNS),
            "required_cleanup_quality_columns": sorted(REQUIRED_CLEANUP_QUALITY_COLUMNS),
            "required_boundary_tag_columns": sorted(REQUIRED_BOUNDARY_COLUMNS),
            "required_boundary_roles": sorted(REQUIRED_BOUNDARY_ROLES),
            "strict_credit_policy": "blocker remains open until controlled source CAD, cleaned geometry, quality records, and boundary tags validate together",
        },
        "template_checks": checks,
        "evidence_files": [
            evidence_entry("real_cad_cleanup_package_report", Path(args.cleanup_package)),
            evidence_entry("real_cad_intake_preflight_report", Path(args.intake_preflight)),
            evidence_entry("real_cad_boundary_tag_contract_report", Path(args.boundary_contract)),
            evidence_entry("real_cad_cleanup_manifest_template", manifest_template),
            evidence_entry("real_cad_data_room_index_template", data_room_template),
            evidence_entry("real_cad_cleanup_quality_record_template", cleanup_quality_template),
            evidence_entry("real_cad_boundary_tags_template", boundary_template),
            evidence_entry("real_cad_intake_checklist", checklist),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS_PASS, f"unexpected status: {data.get('status')}")
    summary = data.get("summary", {})
    require(isinstance(summary, dict), "summary missing")
    for key in (
        "handoff_contract_ready",
        "manifest_template_ready",
        "data_room_index_template_ready",
        "cleanup_quality_template_ready",
        "boundary_tag_template_ready",
        "intake_checklist_ready",
    ):
        require(summary.get(key) is True, f"{key} is not true")
    require(summary.get("source_cad_artifacts_present") is False, "source CAD artifacts overclaimed")
    require(summary.get("strict_real_cad_blocker_cleared") is False, "strict real CAD blocker overclaimed")
    contract = data.get("acceptance_contract", {})
    require(isinstance(contract, dict), "acceptance contract missing")
    require(contract.get("minimum_real_geometry_count") == 3, "minimum geometry count mismatch")
    require(set(contract.get("required_boundary_roles", [])) == REQUIRED_BOUNDARY_ROLES, "boundary roles mismatch")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Engineering H2 Real-CAD Handoff Contract",
        "",
        f"- Status: `{report['status']}`",
        f"- Handoff contract ready: `{s['handoff_contract_ready']}`",
        f"- Manifest template ready: `{s['manifest_template_ready']}`",
        f"- Data-room index template ready: `{s['data_room_index_template_ready']}`",
        f"- Cleanup-quality template ready: `{s['cleanup_quality_template_ready']}`",
        f"- Boundary-tag template ready: `{s['boundary_tag_template_ready']}`",
        f"- Strict real-CAD blocker cleared: `{s['strict_real_cad_blocker_cleared']}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(PACKAGE_ROOT))
    parser.add_argument("--cleanup-package", default=str(CLEANUP_PACKAGE))
    parser.add_argument("--intake-preflight", default=str(INTAKE_PREFLIGHT))
    parser.add_argument("--boundary-contract", default=str(BOUNDARY_CONTRACT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"real_cad_handoff_contract VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"real_cad_handoff_contract PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
