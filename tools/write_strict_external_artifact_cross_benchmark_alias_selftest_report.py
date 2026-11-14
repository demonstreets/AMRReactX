#!/usr/bin/env python3
"""Write/verify a strict negative selftest for cross-benchmark external artifact aliases."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-EXTERNAL-ARTIFACT-CROSS-BENCHMARK-ALIAS-SELFTEST"

DEFAULT_OUTPUT_ROOT = Path(
    "docs/codex_audit/evidence/strict_external_artifact_cross_benchmark_alias_selftest_20260817"
)
DEFAULT_OUTPUT_JSON = DEFAULT_OUTPUT_ROOT / "strict_external_artifact_cross_benchmark_alias_selftest_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_OUTPUT_ROOT / "strict_external_artifact_cross_benchmark_alias_selftest_report.md"

DEFAULT_RECEIVING_PACK = Path(
    "docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812/"
    "strict_external_evidence_receiving_pack_report.json"
)
DEFAULT_DROP_INDEX = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
    "strict_external_artifact_drop_index_report.json"
)
DATAVERSE_REFERENCE_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803")
DATAVERSE_GEOMETRY_ROOT = Path("docs/codex_audit/evidence/dataverse_open_channel_geometry_mapping_20260803")

TARGET_BENCHMARK_ID = "hysafe_sbepv5_d27"
SOURCE_BENCHMARK_ID = "dataverse_open_channel_h2"


class AliasSelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AliasSelftestError(message)


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
        raise AliasSelftestError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AliasSelftestError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def csv_header(path: Path) -> list[str]:
    try:
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            return next(reader)
    except FileNotFoundError as exc:
        raise AliasSelftestError(f"missing CSV evidence: {path}") from exc
    except StopIteration as exc:
        raise AliasSelftestError(f"empty CSV evidence: {path}") from exc


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": path.as_posix(),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def external_plume_targets(drop_index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    targets: dict[str, dict[str, Any]] = {}
    for domain in drop_index.get("domain_drop_index", []):
        if isinstance(domain, dict) and domain.get("domain") == "external_plume":
            for check in domain.get("checks", []):
                if isinstance(check, dict):
                    label = str(check.get("label", ""))
                    if label:
                        targets[label] = check
    return targets


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    receiving_pack_path = Path(args.receiving_pack)
    drop_index_path = Path(args.drop_index)
    receiving_pack = load_json(receiving_pack_path)
    drop_index = load_json(drop_index_path)
    require(
        receiving_pack.get("status") == "PASS-STRICT-EXTERNAL-EVIDENCE-RECEIVING-PACK",
        "receiving pack is not PASS",
    )
    require(
        drop_index.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX",
        "strict external artifact drop index is not PASS",
    )

    reference_metadata_path = DATAVERSE_REFERENCE_ROOT / "dataverse_reference_case_metadata.json"
    reference_timeseries_path = DATAVERSE_REFERENCE_ROOT / "dataverse_reference_timeseries_wide.csv"
    reference_report_path = DATAVERSE_REFERENCE_ROOT / "dataverse_open_channel_reference_package_report.json"
    geometry_metadata_path = DATAVERSE_GEOMETRY_ROOT / "dataverse_geometry_metadata.json"
    geometry_sensor_path = DATAVERSE_GEOMETRY_ROOT / "dataverse_sensor_coordinates.csv"

    reference_metadata = load_json(reference_metadata_path)
    geometry_metadata = load_json(geometry_metadata_path)
    reference_header = csv_header(reference_timeseries_path)
    geometry_header = csv_header(geometry_sensor_path)

    targets = external_plume_targets(drop_index)
    expected_targets = {
        "external_plume.dataset_metadata",
        "external_plume.sensor_coordinates",
        "external_plume.baffle_geometry",
        "external_plume.experimental_timeseries",
        "external_plume.digitization_uncertainty_record",
    }
    missing_targets = sorted(expected_targets - set(targets))
    require(not missing_targets, "receiving pack missing external plume targets: " + ",".join(missing_targets))

    dataverse_sensor_columns = [
        column for column in reference_header if column.startswith("sensor_") and column.endswith("_H2_vol_percent")
    ]
    sbepv5_gas_columns = [f"Gas{idx:02d}_vol_percent" for idx in range(1, 13)]
    dataverse_sensor_count = len(dataverse_sensor_columns)

    alias_cases = [
        {
            "case_id": "dataverse_metadata_as_sbepv5_dataset_metadata",
            "source_path": reference_metadata_path.as_posix(),
            "target_label": "external_plume.dataset_metadata",
            "decision": "REJECT",
            "reasons": [
                "source_raw_case_id_is_dataverse_not_hysafe_sbepv5_d27",
                "metadata_benchmark_id_not_equal_hysafe_sbepv5_d27",
                "source_dataset_doi_is_for_open_channel_dataverse_case",
            ],
        },
        {
            "case_id": "dataverse_sensor_coordinates_as_sbepv5_sensor_coordinates",
            "source_path": geometry_sensor_path.as_posix(),
            "target_label": "external_plume.sensor_coordinates",
            "decision": "REJECT",
            "reasons": [
                "sensor_coordinate_schema_missing_reliability_and_digitization_uncertainty_m",
                "source_sensor_layout_has_29_dataverse_sensors_not_12_sbepv5_gas_sensors",
                "coordinate_convention_and_article_doi_do_not_match_sbepv5_d27",
            ],
        },
        {
            "case_id": "dataverse_geometry_metadata_as_sbepv5_baffle_geometry",
            "source_path": geometry_metadata_path.as_posix(),
            "target_label": "external_plume.baffle_geometry",
            "decision": "REJECT",
            "reasons": [
                "source_contains_open_channel_dimensions_not_four_sbepv5_baffle_bounds",
                "no_baffle_id_or_per_baffle_min_max_columns",
                "known_obstacle_summary_explicitly_says_component_bounds_not_encoded",
            ],
        },
        {
            "case_id": "dataverse_timeseries_as_sbepv5_experimental_timeseries",
            "source_path": reference_timeseries_path.as_posix(),
            "target_label": "external_plume.experimental_timeseries",
            "decision": "REJECT",
            "reasons": [
                "timeseries_header_uses_sensor_nn_H2_vol_percent_not_Gas01_to_Gas12_vol_percent",
                "source_has_29_dataverse_sensor_columns_not_12_sbepv5_columns",
                "source_article_and_dataset_doi_are_not_sbepv5_d27",
            ],
        },
        {
            "case_id": "dataverse_reference_package_as_sbepv5_digitization_uncertainty_record",
            "source_path": reference_report_path.as_posix(),
            "target_label": "external_plume.digitization_uncertainty_record",
            "decision": "REJECT",
            "reasons": [
                "reference_package_report_is_not_a_digitization_uncertainty_csv",
                "no_per_artifact_method_axis_calibration_uncertainty_review_status_rows",
                "dataverse_machine_readable_source_does_not_document_sbepv5_curve_digitization",
            ],
        },
    ]

    target_paths = [Path(str(targets[label]["target_path"])) for label in sorted(expected_targets)]
    ready = (
        len(alias_cases) == 5
        and all(case["decision"] == "REJECT" for case in alias_cases)
        and dataverse_sensor_count == 29
        and all(column not in reference_header for column in sbepv5_gas_columns)
        and reference_metadata.get("article_doi") != "sbepv5_d27"
        and geometry_metadata.get("known_obstacle_summary", {}).get("strict_credit_gap")
        == "channel obstacle/component geometry still needs exact bounds before CFD mesh parity can be claimed"
    )

    evidence_files = [
        evidence_entry("strict_external_evidence_receiving_pack", receiving_pack_path),
        evidence_entry("strict_external_artifact_drop_index", drop_index_path),
        evidence_entry("dataverse_reference_case_metadata", reference_metadata_path),
        evidence_entry("dataverse_reference_timeseries_wide", reference_timeseries_path),
        evidence_entry("dataverse_open_channel_reference_package_report", reference_report_path),
        evidence_entry("dataverse_geometry_metadata", geometry_metadata_path),
        evidence_entry("dataverse_sensor_coordinates", geometry_sensor_path),
    ]

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "negative selftest preventing Dataverse open-channel evidence from satisfying SBEPV5 D27 strict plume artifacts",
        "summary": {
            "strict_external_artifact_cross_benchmark_alias_selftest_ready": ready,
            "source_benchmark_id": SOURCE_BENCHMARK_ID,
            "target_benchmark_id": TARGET_BENCHMARK_ID,
            "protected_domain": "external_plume",
            "alias_case_count": len(alias_cases),
            "alias_rejected_count": sum(1 for case in alias_cases if case["decision"] == "REJECT"),
            "alias_accepted_count": sum(1 for case in alias_cases if case["decision"] != "REJECT"),
            "dataverse_sensor_column_count": dataverse_sensor_count,
            "sbepv5_required_gas_column_count": len(sbepv5_gas_columns),
            "sbepv5_required_gas_columns_present_in_dataverse_timeseries": all(
                column in reference_header for column in sbepv5_gas_columns
            ),
            "protected_target_count": len(targets),
            "target_artifacts_currently_present_count": sum(1 for path in target_paths if path.is_file()),
            "does_not_create_or_copy_target_artifacts": True,
            "strict_completion_allowed": False,
            "strict_master_plan_still_open": True,
        },
        "alias_cases": alias_cases,
        "evidence_files": evidence_files,
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(
        summary.get("strict_external_artifact_cross_benchmark_alias_selftest_ready") is True,
        "cross-benchmark alias selftest is not ready",
    )
    require(summary.get("source_benchmark_id") == SOURCE_BENCHMARK_ID, "unexpected source benchmark")
    require(summary.get("target_benchmark_id") == TARGET_BENCHMARK_ID, "unexpected target benchmark")
    require(summary.get("protected_domain") == "external_plume", "unexpected protected domain")
    require(summary.get("alias_case_count") == 5, "unexpected alias case count")
    require(summary.get("alias_rejected_count") == 5, "not all alias cases were rejected")
    require(summary.get("alias_accepted_count") == 0, "one or more alias cases were accepted")
    require(summary.get("dataverse_sensor_column_count") == 29, "unexpected Dataverse sensor column count")
    require(summary.get("sbepv5_required_gas_column_count") == 12, "unexpected SBEPV5 gas column count")
    require(
        summary.get("sbepv5_required_gas_columns_present_in_dataverse_timeseries") is False,
        "Dataverse header unexpectedly satisfies SBEPV5 header",
    )
    require(summary.get("does_not_create_or_copy_target_artifacts") is True, "selftest may alter target artifacts")
    require(summary.get("strict_completion_allowed") is False, "selftest overclaims strict completion")
    require(summary.get("strict_master_plan_still_open") is True, "selftest overclaims strict closure")
    cases = data.get("alias_cases")
    require(isinstance(cases, list) and len(cases) == 5, "invalid alias case list")
    for case in cases:
        require(case.get("decision") == "REJECT", f"alias case not rejected: {case.get('case_id')}")
        require(case.get("reasons"), f"alias case missing reasons: {case.get('case_id')}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict External Artifact Cross-Benchmark Alias Selftest",
        "",
        f"- Status: `{report['status']}`",
        f"- Ready: `{summary['strict_external_artifact_cross_benchmark_alias_selftest_ready']}`",
        f"- Source benchmark: `{summary['source_benchmark_id']}`",
        f"- Target benchmark: `{summary['target_benchmark_id']}`",
        f"- Alias rejected/accepted: `{summary['alias_rejected_count']}/{summary['alias_accepted_count']}`",
        f"- Strict completion allowed by this selftest: `{summary['strict_completion_allowed']}`",
        "",
        "## Rejected Aliases",
        "",
    ]
    for case in report["alias_cases"]:
        lines.append(f"- `{case['case_id']}` -> `{case['target_label']}`: `{case['decision']}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receiving-pack", default=str(DEFAULT_RECEIVING_PACK))
    parser.add_argument("--drop-index", default=str(DEFAULT_DROP_INDEX))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data)
        print(
            "strict_external_artifact_cross_benchmark_alias_selftest "
            f"VERIFY-PASS json={args.verify_json} status={data['status']}"
        )
        return 0

    report = build_report(args)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(
        "strict_external_artifact_cross_benchmark_alias_selftest "
        f"PASS json={output_json} md={output_md} status={report['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
