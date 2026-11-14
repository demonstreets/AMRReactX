#!/usr/bin/env python3
"""Write/verify the strict master-plan artifact intake manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_READY = "READY-MASTER-PLAN-STRICT-ARTIFACT-INTAKE-MANIFEST"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/master_plan_strict_artifact_intake_manifest_20260731")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "master_plan_strict_artifact_intake_manifest_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "master_plan_strict_artifact_intake_manifest_report.md"
DEFAULT_MATRIX = Path(
    "docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/"
    "master_plan_strict_blocker_matrix_report.json"
)

TEMPLATE_FILES = {
    "external_plume": [
        Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata_template.json"),
        Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates_template.csv"),
        Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry_template.csv"),
        Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries_template.csv"),
        Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/digitization_uncertainty_record_template.csv"),
    ],
    "real_cad": [
        Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest_template.json"),
        Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index_template.csv"),
        Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record_template.csv"),
        Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_boundary_tags_template.csv"),
        Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_intake_checklist.csv"),
    ],
    "fire_calibration": [
        Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata_template.json"),
        Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics_template.csv"),
        Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics_template.csv"),
        Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_digitization_uncertainty_template.csv"),
        Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_source_registry_template.csv"),
        Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_intake_checklist.csv"),
    ],
}


class IntakeManifestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise IntakeManifestError(message)


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
        raise IntakeManifestError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise IntakeManifestError(f"invalid JSON evidence {path}: {exc}") from exc
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


def template_entries(domain: str) -> list[dict[str, Any]]:
    return [evidence_entry(f"{domain}_template", path) for path in TEMPLATE_FILES[domain]]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    matrix_path = Path(args.strict_blocker_matrix)
    matrix = load_json(matrix_path)

    intake_domains = {
        "external_plume": {
            "blocker": "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
            "drop_root": "docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset",
            "required_artifacts": [
                "dataset_metadata.json",
                "sensor_coordinates.csv",
                "baffle_geometry.csv",
                "experimental_timeseries.csv",
                "digitization_uncertainty_record.csv if digitized plots are used",
            ],
            "post_intake_commands": [
                "python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py",
                "python3 tools/write_engineering_h2_sbepv5_external_dataset_report.py",
                "python3 tools/write_engineering_h2_external_plume_benchmark_readiness.py",
                "python3 tools/write_engineering_production_scorecard.py",
                "python3 tools/write_engineering_h2_master_plan_traceability_report.py",
            ],
        },
        "real_cad": {
            "blocker": "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
            "drop_root": "docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package",
            "required_artifacts": [
                "source_cad/* real source CAD files",
                "cleaned_geometry/* cleaned STL/STEP geometry files",
                "real_cad_cleanup_manifest.json",
                "real_cad_data_room_index.csv",
                "real_cad_cleanup_quality_record.csv",
                "real_cad_boundary_tags.csv",
            ],
            "post_intake_commands": [
                "python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py",
                "python3 tools/write_engineering_h2_real_cad_intake_preflight_report.py",
                "python3 tools/write_engineering_h2_real_cad_boundary_tag_contract_report.py",
                "python3 tools/write_engineering_production_scorecard.py",
                "python3 tools/write_engineering_h2_master_plan_traceability_report.py",
            ],
        },
        "fire_calibration": {
            "blocker": "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
            "drop_root": "docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset",
            "required_artifacts": [
                "calibration_metadata.json",
                "radiation_metrics.csv",
                "overpressure_metrics.csv",
                "fire_calibration_source_registry.csv",
                "fire_calibration_digitization_uncertainty.csv if digitized plots are used",
            ],
            "post_intake_commands": [
                "python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py",
                "python3 tools/write_engineering_h2_fire_calibration_package_report.py",
                "python3 tools/write_engineering_h2_fire_calibration_dataset_report.py",
                "python3 tools/write_engineering_production_scorecard.py",
                "python3 tools/write_engineering_h2_master_plan_traceability_report.py",
            ],
        },
    }

    evidence_files = [evidence_entry("strict_blocker_matrix_report", matrix_path)]
    for domain in TEMPLATE_FILES:
        evidence_files.extend(template_entries(domain))

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_READY,
        "summary": {
            "strict_blocker_matrix_status": matrix.get("status"),
            "open_strict_blocker_count": matrix.get("summary", {}).get("open_strict_blocker_count"),
            "intake_domain_count": len(intake_domains),
            "template_file_count": sum(len(paths) for paths in TEMPLATE_FILES.values()),
            "artifact_intake_ready": True,
            "strict_master_plan_complete_after_manifest": False,
        },
        "intake_domains": intake_domains,
        "evidence_files": evidence_files,
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_READY, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_blocker_matrix_status") == "TRIAGED-MASTER-PLAN-STRICT-BLOCKER-MATRIX", "matrix not ready")
    require(summary.get("open_strict_blocker_count") == 3, "open strict blocker count changed")
    require(summary.get("intake_domain_count") == 3, "intake domain count changed")
    require(summary.get("template_file_count") == 16, "template file count changed")
    require(summary.get("artifact_intake_ready") is True, "artifact intake manifest not ready")
    require(summary.get("strict_master_plan_complete_after_manifest") is False, "manifest should not clear strict master plan")
    domains = data.get("intake_domains")
    require(isinstance(domains, dict), "missing intake_domains")
    require(set(domains) == {"external_plume", "real_cad", "fire_calibration"}, "unexpected intake domain set")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Strict Artifact Intake Manifest",
        "",
        f"- Status: `{report['status']}`",
        f"- Intake domains: `{s['intake_domain_count']}`",
        f"- Template files verified: `{s['template_file_count']}`",
        f"- Open strict blockers: `{s['open_strict_blocker_count']}`",
        "",
    ]
    for name, domain in report["intake_domains"].items():
        lines.extend([
            f"## {name}",
            "",
            f"- Blocker: `{domain['blocker']}`",
            f"- Drop root: `{domain['drop_root']}`",
            "- Required artifacts:",
        ])
        for item in domain["required_artifacts"]:
            lines.append(f"  - {item}")
        lines.append("- Post-intake commands:")
        for cmd in domain["post_intake_commands"]:
            lines.append(f"  - `{cmd}`")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict-blocker-matrix", default=str(DEFAULT_MATRIX))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"strict_artifact_intake_manifest VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"strict_artifact_intake_manifest PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
