#!/usr/bin/env python3
"""Write/verify candidate public sources for strict H2 fire consequence calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-FIRE-CALIBRATION-CANDIDATE-SOURCES-20260805"
STATUS_NOT_READY = "NOT_READY-H2-FIRE-CALIBRATION-CANDIDATE-SOURCES-20260805"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/h2_fire_calibration_candidate_sources_20260805")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "h2_fire_calibration_candidate_sources_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "h2_fire_calibration_candidate_sources_report.md"
DEFAULT_OVERPRESSURE_METADATA = Path(
    "docs/codex_audit/evidence/h2_fire_overpressure_dataverse_metadata_20260805/"
    "h2_fire_overpressure_dataverse_metadata_report.json"
)
DEFAULT_OVERPRESSURE_REDUCED_EXP002 = Path(
    "docs/codex_audit/evidence/h2_fire_overpressure_reduced_exp002_20260805/"
    "h2_fire_overpressure_reduced_exp002_report.json"
)


SOURCES: list[dict[str, Any]] = [
    {
        "id": "dataverse_no_ignited_h2_jets_overpressure_2026",
        "family": "overpressure",
        "title": "Replication data for: Laboratory-Scale Experiments on Ignited Hydrogen Jets: Flame Acceleration and Overpressure Analysis",
        "persistent_id": "doi:10.18710/X044QK",
        "url": "https://dataverse.no/dataset.xhtml?persistentId=doi%3A10.18710%2FX044QK",
        "publication_date": "2026-02-12",
        "license": "CC0 1.0",
        "public_access": True,
        "machine_download_candidate": True,
        "reported_measurements": [
            "high-speed imaging",
            "pressure sensors",
            "flame acceleration",
            "overpressure development",
            "obstacle/nozzle spacing effects",
        ],
        "known_files": [
            {"name": "00_Readme.txt", "size": "6.6 KB", "md5": "709a0f899a6495722389484948bd18cf"},
            {"name": "Ign_pipe_geom_EXP_001.csv", "size": "393.1 MB", "md5": "76f57dd1efaf3f20acd8572785ddbccf"},
            {"name": "Ign_pipe_geom_EXP_002.csv", "size": "387.6 MB", "md5": "f0e95dc5a2f1c6a1f98cb266f8360dcc"},
            {"name": "Ign_pipe_geom_EXP_003.csv", "size": "393.9 MB", "md5": "c44b1920cb828c206c00892d65391aa4"},
        ],
        "strict_use": "Candidate for overpressure/time-of-arrival calibration of delayed ignition hydrogen jets with obstacles.",
        "remaining_work": [
            "Download readme and at least one pressure CSV through the Dataverse API without exceeding disk budget.",
            "Map CSV headers to pressure sensor positions, ignition timing, obstacle spacing, and release mass-flow metadata.",
            "Build a reduced validation case aligned with one experiment before strict overpressure credit.",
        ],
    },
    {
        "id": "hysafe_inclined_large_scale_h2_jet_flame_radiation_2026",
        "family": "radiation",
        "title": "Thermal Radiation Of Inclined Large Scale Hydrogen Jet Flames",
        "persistent_id": "doi:10.58895/hysafe.27",
        "url": "https://hysafejournal.org/articles/10.58895/hysafe.27",
        "publication_date": "2026-02-13",
        "license": "CC BY 4.0",
        "public_access": True,
        "machine_download_candidate": False,
        "reported_measurements": [
            "incident thermal radiation",
            "infrared flame shape",
            "OH* flame shape",
            "surface emissive power",
            "radiant heat fraction",
            "constant mass-flow hydrogen jet releases",
        ],
        "known_ranges": {
            "mass_flow_kg_s": "0.0125-0.175",
            "orifice_diameter_m": "0.03",
            "radiant_heat_fraction": "0.031-0.043",
            "SEP_IR_kW_m2": "10-16",
            "SEP_OH_kW_m2": "40-80",
        },
        "strict_use": "Candidate radiation metric anchor for large-scale open-field hydrogen jet fires.",
        "remaining_work": [
            "Extract machine-readable tables or contact/source supplemental data for sensor positions and measured heat flux values.",
            "Record wind, inclination, mass-flow, flame-geometry, and radiometer uncertainty fields.",
            "Build a radiation agreement contract once measured flux tables are repository-ingestable.",
        ],
    },
]


class CandidateSourcesError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateSourcesError(message)


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
        raise CandidateSourcesError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CandidateSourcesError(f"invalid JSON evidence {path}: {exc}") from exc
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


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    overpressure_metadata = load_json(Path(args.overpressure_metadata))
    overpressure_reduced_exp002 = load_json(Path(args.overpressure_reduced_exp002))
    overpressure_summary = overpressure_metadata.get("summary", {})
    reduced_summary = overpressure_reduced_exp002.get("summary", {})
    require(isinstance(overpressure_summary, dict), "overpressure metadata report missing summary")
    require(isinstance(reduced_summary, dict), "overpressure reduced EXP002 report missing summary")
    families = {source["family"] for source in SOURCES}
    ready = {"radiation", "overpressure"}.issubset(families)
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "candidate_source_count": len(SOURCES),
            "radiation_candidate_available": "radiation" in families,
            "overpressure_candidate_available": "overpressure" in families,
            "both_metric_families_have_public_candidates": {"radiation", "overpressure"}.issubset(families),
            "overpressure_dataverse_metadata_status": overpressure_metadata.get("status"),
            "overpressure_dataverse_metadata_ready": overpressure_metadata.get("status") == "PASS-H2-FIRE-OVERPRESSURE-DATAVERSE-METADATA",
            "overpressure_experiment_matrix_row_count": overpressure_summary.get("experiment_matrix_row_count"),
            "overpressure_pressure_sensor_count": overpressure_summary.get("pressure_sensor_count_from_readme"),
            "overpressure_reduced_exp002_status": overpressure_reduced_exp002.get("status"),
            "overpressure_reduced_exp002_ready": overpressure_reduced_exp002.get("status") == "PASS-H2-FIRE-OVERPRESSURE-REDUCED-EXP002",
            "overpressure_reduced_exp002_row_count": reduced_summary.get("row_count"),
            "overpressure_reduced_exp002_ready_for_validation_case": reduced_summary.get("ready_for_reduced_validation_case"),
            "repository_ingestable_calibration_package_ready": False,
            "strict_fire_calibration_blocker_cleared": False,
        },
        "sources": SOURCES,
        "strict_credit_gap": [
            "No downloaded, hashed, repository-ingestable radiation calibration table is present yet.",
            "No downloaded, hashed, repository-ingestable overpressure calibration table is present yet.",
            "No case alignment file links the candidate measurements to a PeleC/PeleLMeX fire-consequence validation case yet.",
        ],
        "evidence_files": [
            evidence_entry("overpressure_dataverse_metadata", Path(args.overpressure_metadata)),
            evidence_entry("overpressure_reduced_exp002", Path(args.overpressure_reduced_exp002)),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "candidate source report is not passing")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("candidate_source_count") >= 2, "too few candidate sources")
    require(summary.get("radiation_candidate_available") is True, "radiation candidate missing")
    require(summary.get("overpressure_candidate_available") is True, "overpressure candidate missing")
    require(summary.get("both_metric_families_have_public_candidates") is True, "not all metric families have candidates")
    require(summary.get("overpressure_dataverse_metadata_ready") is True, "overpressure Dataverse metadata not ready")
    require(summary.get("overpressure_experiment_matrix_row_count", 0) >= 30, "overpressure experiment matrix too small")
    require(summary.get("overpressure_pressure_sensor_count") == 4, "overpressure pressure sensor count not detected")
    require(summary.get("overpressure_reduced_exp002_ready") is True, "overpressure reduced EXP002 report not ready")
    require(summary.get("overpressure_reduced_exp002_row_count") == 5000004, "overpressure reduced EXP002 row count mismatch")
    require(
        summary.get("overpressure_reduced_exp002_ready_for_validation_case") is True,
        "overpressure reduced EXP002 not ready for validation case",
    )
    require(summary.get("repository_ingestable_calibration_package_ready") is False, "candidate report should not claim package readiness")
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "candidate report should not clear strict blocker")
    sources = data.get("sources")
    require(isinstance(sources, list), "missing sources")
    source_ids = {item.get("id") for item in sources if isinstance(item, dict)}
    require("dataverse_no_ignited_h2_jets_overpressure_2026" in source_ids, "missing DataverseNO overpressure source")
    require("hysafe_inclined_large_scale_h2_jet_flame_radiation_2026" in source_ids, "missing HySafe radiation source")
    for item in sources:
        require(item.get("public_access") is True, f"source is not public: {item.get('id')}")
        require(item.get("persistent_id"), f"source missing persistent id: {item.get('id')}")
        require(item.get("url"), f"source missing URL: {item.get('id')}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"sha256 mismatch for {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# H2 Fire Calibration Candidate Sources",
        "",
        f"- Status: `{report['status']}`",
        f"- Candidate sources: `{summary['candidate_source_count']}`",
        f"- Radiation candidate available: `{summary['radiation_candidate_available']}`",
        f"- Overpressure candidate available: `{summary['overpressure_candidate_available']}`",
        f"- Overpressure Dataverse metadata ready: `{summary['overpressure_dataverse_metadata_ready']}`",
        f"- Overpressure experiment matrix rows: `{summary['overpressure_experiment_matrix_row_count']}`",
        f"- Overpressure reduced EXP002 ready: `{summary['overpressure_reduced_exp002_ready']}`",
        f"- Repository-ingestable package ready: `{summary['repository_ingestable_calibration_package_ready']}`",
        f"- Strict blocker cleared: `{summary['strict_fire_calibration_blocker_cleared']}`",
        "",
        "| Source | Family | Persistent ID | Public | Machine Download Candidate |",
        "|---|---|---|---:|---:|",
    ]
    for source in report["sources"]:
        lines.append(
            f"| {source['title']} | `{source['family']}` | `{source['persistent_id']}` | "
            f"`{source['public_access']}` | `{source['machine_download_candidate']}` |"
        )
    lines.extend(["", "## Strict Credit Gap", ""])
    for gap in report["strict_credit_gap"]:
        lines.append(f"- {gap}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_JSON), help="output JSON report path")
    parser.add_argument("--markdown", default=str(DEFAULT_OUTPUT_MD), help="output Markdown report path")
    parser.add_argument("--overpressure-metadata", default=str(DEFAULT_OVERPRESSURE_METADATA))
    parser.add_argument("--overpressure-reduced-exp002", default=str(DEFAULT_OVERPRESSURE_REDUCED_EXP002))
    parser.add_argument("--verify-json", help="verify an existing JSON report instead of writing one")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"h2_fire_calibration_candidate_sources VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, Path(args.markdown))
    print(f"h2_fire_calibration_candidate_sources PASS json={output} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
