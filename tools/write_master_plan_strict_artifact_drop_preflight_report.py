#!/usr/bin/env python3
"""Write/verify strict master-plan external artifact drop preflight evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_COMPLETE = "PASS-MASTER-PLAN-STRICT-ARTIFACT-DROP-PREFLIGHT-COMPLETE"
STATUS_AWAITING = "AWAITING-MASTER-PLAN-STRICT-ARTIFACT-DROP-PREFLIGHT-EXTERNAL-ARTIFACTS"
STATUS_NOT_READY = "NOT_READY-MASTER-PLAN-STRICT-ARTIFACT-DROP-PREFLIGHT"

DEFAULT_MANIFEST = Path(
    "docs/codex_audit/evidence/master_plan_strict_artifact_intake_manifest_20260731/"
    "master_plan_strict_artifact_intake_manifest_report.json"
)
DEFAULT_ROOT = Path("docs/codex_audit/evidence/master_plan_strict_artifact_drop_preflight_20260731")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "master_plan_strict_artifact_drop_preflight_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "master_plan_strict_artifact_drop_preflight_report.md"

PLACEHOLDER_MARKERS = (
    "<",
    "replace",
    "pending",
    "todo",
    "tbd",
    "placeholder",
    "fill in",
    "to be supplied",
)
TEMPLATE_MARKERS = ("_template.", "template_", "_template_")
CAD_EXTENSIONS = {".step", ".stp", ".stl", ".obj", ".iges", ".igs", ".brep", ".sat", ".x_t"}
CLEANED_GEOMETRY_EXTENSIONS = {".stl", ".step", ".stp", ".obj", ".brep"}


DOMAIN_SPECS: dict[str, dict[str, Any]] = {
    "external_plume": {
        "required_files": [
            "dataset_metadata.json",
            "sensor_coordinates.csv",
            "baffle_geometry.csv",
            "experimental_timeseries.csv",
        ],
        "optional_files": ["digitization_uncertainty_record.csv"],
        "template_files": [
            "dataset_metadata_template.json",
            "sensor_coordinates_template.csv",
            "baffle_geometry_template.csv",
            "experimental_timeseries_template.csv",
            "digitization_uncertainty_record_template.csv",
        ],
        "post_intake_primary_command": "python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py",
    },
    "real_cad": {
        "required_files": [
            "real_cad_cleanup_manifest.json",
            "real_cad_data_room_index.csv",
            "real_cad_cleanup_quality_record.csv",
            "real_cad_boundary_tags.csv",
        ],
        "required_file_groups": [
            {"name": "source_cad_files", "root": "source_cad", "extensions": CAD_EXTENSIONS},
            {"name": "cleaned_geometry_files", "root": "cleaned_geometry", "extensions": CLEANED_GEOMETRY_EXTENSIONS},
        ],
        "template_files": [
            "real_cad_cleanup_manifest_template.json",
            "real_cad_data_room_index_template.csv",
            "real_cad_cleanup_quality_record_template.csv",
            "real_cad_boundary_tags_template.csv",
            "real_cad_intake_checklist.csv",
        ],
        "post_intake_primary_command": "python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py",
    },
    "fire_calibration": {
        "required_files": [
            "calibration_metadata.json",
            "radiation_metrics.csv",
            "overpressure_metrics.csv",
            "fire_calibration_source_registry.csv",
        ],
        "optional_files": ["fire_calibration_digitization_uncertainty.csv"],
        "template_files": [
            "calibration_metadata_template.json",
            "radiation_metrics_template.csv",
            "overpressure_metrics_template.csv",
            "fire_calibration_source_registry_template.csv",
            "fire_calibration_digitization_uncertainty_template.csv",
            "fire_calibration_intake_checklist.csv",
        ],
        "post_intake_primary_command": "python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py",
    },
}


class DropPreflightError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise DropPreflightError(message)


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
        raise DropPreflightError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DropPreflightError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def text_has_placeholder(path: Path) -> bool:
    if path.stat().st_size > 2_000_000:
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False
    return any(marker in text for marker in PLACEHOLDER_MARKERS)


def csv_data_rows(path: Path) -> int | None:
    try:
        with path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
    except Exception:
        return None
    if not rows:
        return 0
    return max(0, len(rows) - 1)


def file_entry(path: Path, label: str) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "label": label,
        "path": str(path),
        "exists": path.is_file(),
    }
    if path.is_file():
        entry.update(
            {
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "placeholder_markers_present": text_has_placeholder(path),
                "looks_like_template": any(marker in path.name.lower() for marker in TEMPLATE_MARKERS),
            }
        )
        if path.suffix.lower() == ".csv":
            entry["csv_data_rows"] = csv_data_rows(path)
    return entry


def discover_group(root: Path, group: dict[str, Any]) -> dict[str, Any]:
    group_root = root / group["root"]
    files = []
    if group_root.is_dir():
        for path in sorted(group_root.rglob("*")):
            if path.is_file() and path.suffix.lower() in group["extensions"]:
                files.append(path)
    return {
        "name": group["name"],
        "root": str(group_root),
        "required": True,
        "file_count": len(files),
        "ready": len(files) > 0,
        "files": [file_entry(path, group["name"]) for path in files],
    }


def evaluate_domain(name: str, manifest_domain: dict[str, Any]) -> dict[str, Any]:
    spec = DOMAIN_SPECS[name]
    drop_root = Path(manifest_domain["drop_root"])
    required = [file_entry(drop_root / rel, rel) for rel in spec.get("required_files", [])]
    optional = [file_entry(drop_root / rel, rel) for rel in spec.get("optional_files", [])]
    templates = [file_entry(drop_root / rel, rel) for rel in spec.get("template_files", [])]
    groups = [discover_group(drop_root, group) for group in spec.get("required_file_groups", [])]

    missing_required = [entry["label"] for entry in required if not entry["exists"]]
    placeholder_required = [
        entry["label"]
        for entry in required
        if entry.get("exists") and entry.get("placeholder_markers_present")
    ]
    empty_required_csv = [
        entry["label"]
        for entry in required
        if entry.get("exists") and entry["path"].lower().endswith(".csv") and entry.get("csv_data_rows", 0) <= 0
    ]
    missing_groups = [group["name"] for group in groups if not group["ready"]]

    complete = not missing_required and not placeholder_required and not empty_required_csv and not missing_groups
    templates_available = all(entry["exists"] for entry in templates)
    return {
        "name": name,
        "status": "COMPLETE" if complete else "AWAITING_EXTERNAL_ARTIFACTS",
        "drop_root": str(drop_root),
        "blocker": manifest_domain.get("blocker"),
        "complete": complete,
        "templates_available": templates_available,
        "missing_required_artifacts": missing_required,
        "required_artifacts_with_placeholder_markers": placeholder_required,
        "required_csv_artifacts_without_data_rows": empty_required_csv,
        "missing_required_file_groups": missing_groups,
        "required_files": required,
        "optional_files": optional,
        "template_files": templates,
        "required_file_groups": groups,
        "post_intake_primary_command": spec["post_intake_primary_command"],
        "post_intake_commands": manifest_domain.get("post_intake_commands", []),
    }


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def build_report(manifest_path: Path) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    require(
        manifest.get("status") == "READY-MASTER-PLAN-STRICT-ARTIFACT-INTAKE-MANIFEST",
        "strict artifact intake manifest is not ready",
    )
    domains = manifest.get("intake_domains")
    require(isinstance(domains, dict), "manifest missing intake_domains")
    require(set(DOMAIN_SPECS).issubset(domains), "manifest missing required intake domains")

    domain_results = [evaluate_domain(name, domains[name]) for name in sorted(DOMAIN_SPECS)]
    complete_count = sum(1 for domain in domain_results if domain["complete"])
    awaiting_count = len(domain_results) - complete_count
    template_ready = all(domain["templates_available"] for domain in domain_results)
    status = STATUS_COMPLETE if complete_count == len(domain_results) else STATUS_AWAITING
    if not template_ready:
        status = STATUS_NOT_READY

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "ready_for_user_artifact_drop": template_ready,
        "strict_master_plan_external_artifacts_complete": complete_count == len(domain_results),
        "summary": {
            "domain_count": len(domain_results),
            "complete_domain_count": complete_count,
            "awaiting_external_artifact_domain_count": awaiting_count,
            "template_ready": template_ready,
            "strict_master_plan_complete_after_drop_preflight": complete_count == len(domain_results),
        },
        "domains": domain_results,
        "evidence_files": [
            evidence_entry("strict_artifact_intake_manifest_report", manifest_path),
        ],
    }


def validate_report(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_COMPLETE, STATUS_AWAITING, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("domain_count") == len(DOMAIN_SPECS), "unexpected domain count")
    domains = data.get("domains")
    require(isinstance(domains, list), "missing domains")
    require({domain.get("name") for domain in domains} == set(DOMAIN_SPECS), "unexpected domain set")
    for domain in domains:
        require(domain.get("templates_available") is True, f"templates missing for {domain.get('name')}")
        require(domain.get("status") in {"COMPLETE", "AWAITING_EXTERNAL_ARTIFACTS"}, "invalid domain status")
        require(domain.get("drop_root"), "missing drop_root")
    if data.get("status") == STATUS_COMPLETE:
        require(summary.get("complete_domain_count") == len(DOMAIN_SPECS), "complete status but not all domains complete")
    elif data.get("status") == STATUS_AWAITING:
        require(summary.get("awaiting_external_artifact_domain_count", 0) > 0, "awaiting status without awaiting domains")
        require(data.get("ready_for_user_artifact_drop") is True, "awaiting status must still be ready for user artifact drop")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Strict Artifact Drop Preflight",
        "",
        f"- Status: `{report['status']}`",
        f"- Ready for artifact drop: `{report['ready_for_user_artifact_drop']}`",
        f"- Complete domains: `{report['summary']['complete_domain_count']}/{report['summary']['domain_count']}`",
        "",
        "## Domains",
        "",
    ]
    for domain in report["domains"]:
        lines.extend(
            [
                f"### {domain['name']}",
                "",
                f"- Status: `{domain['status']}`",
                f"- Drop root: `{domain['drop_root']}`",
                f"- Missing required artifacts: `{', '.join(domain['missing_required_artifacts']) or 'none'}`",
                f"- Missing required file groups: `{', '.join(domain['missing_required_file_groups']) or 'none'}`",
                f"- Primary post-intake command: `{domain['post_intake_primary_command']}`",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--verify-json", type=Path)
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(args.verify_json)
        validate_report(data)
        print(f"master_plan_strict_artifact_drop_preflight VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args.manifest)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, args.output_md)
    print(f"master_plan_strict_artifact_drop_preflight PASS json={args.output_json} md={args.output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
