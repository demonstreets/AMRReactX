#!/usr/bin/env python3
"""Write/verify a strict audit separating SBEPV5 D27 plume needs from Dataverse plume evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-EXTERNAL-PLUME-SOURCE-SEPARATION-AUDIT"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_external_plume_source_separation_audit_20260817")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_external_plume_source_separation_audit_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_external_plume_source_separation_audit_report.md"

PUBLIC_TRIAGE = Path(
    "docs/codex_audit/evidence/engineering_h2_external_plume_public_source_triage_20260724/"
    "external_plume_public_source_triage_report.json"
)
SBEPV5_INGESTION = Path(
    "docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/"
    "sbepv5_d27_dataset_ingestion_report.json"
)
DATAVERSE_REFERENCE = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/"
    "dataverse_open_channel_reference_package_report.json"
)
DATAVERSE_METADATA = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/"
    "dataverse_reference_case_metadata.json"
)
CROSS_BENCHMARK_ALIAS = Path(
    "docs/codex_audit/evidence/strict_external_artifact_cross_benchmark_alias_selftest_20260817/"
    "strict_external_artifact_cross_benchmark_alias_selftest_report.json"
)
DROP_INDEX = Path(
    "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
    "strict_external_artifact_drop_index_report.json"
)
RECEIVING_PACK = Path(
    "docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812/"
    "strict_external_evidence_receiving_pack_report.json"
)


class SourceSeparationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceSeparationError(message)


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
        raise SourceSeparationError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SourceSeparationError(f"invalid JSON evidence {path}: {exc}") from exc
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


def external_plume_checks(drop_index: dict[str, Any]) -> list[dict[str, Any]]:
    for domain in drop_index.get("domain_drop_index", []):
        if isinstance(domain, dict) and domain.get("domain") == "external_plume":
            checks = domain.get("checks", [])
            require(isinstance(checks, list), "external plume checks are not a list")
            return [check for check in checks if isinstance(check, dict)]
    raise SourceSeparationError("external plume domain missing from drop index")


def build_report(_: argparse.Namespace) -> dict[str, Any]:
    public_triage = load_json(PUBLIC_TRIAGE)
    sbepv5_ingestion = load_json(SBEPV5_INGESTION)
    dataverse_reference = load_json(DATAVERSE_REFERENCE)
    dataverse_metadata = load_json(DATAVERSE_METADATA)
    cross_alias = load_json(CROSS_BENCHMARK_ALIAS)
    drop_index = load_json(DROP_INDEX)
    receiving_pack = load_json(RECEIVING_PACK)

    checks = external_plume_checks(drop_index)
    target_paths = [Path(str(check["target_path"])) for check in checks if check.get("target_path")]
    target_present_count = sum(1 for path in target_paths if path.is_file())

    source_findings = [
        {
            "source_family": "sbepv5_d27_public_literature",
            "benchmark_id": "hysafe_sbepv5_d27",
            "machine_readable_timeseries_available_locally": False,
            "strict_artifact_credit_allowed": False,
            "reason": "public sources identify the D27 case and figures, but no accepted local Excel/CSV source for Gas01..Gas12 time histories is present",
            "representative_urls": [
                "https://publikationen.bibliothek.kit.edu/230068969",
                "https://www.researchgate.net/publication/311396790_Results_of_the_HySafe_CFD_Validation_Benchmark_SBEPV5",
                "https://www.h2knowledgecentre.com/content/conference289",
                "https://www.slideserve.com/nilson/results-of-the-hysafe-cfd-validation-benchmark-sbepv5-powerpoint-ppt-presentation",
            ],
        },
        {
            "source_family": "dataverse_open_channel_h2",
            "benchmark_id": "dataverse_open_channel_h2",
            "machine_readable_timeseries_available_locally": True,
            "strict_artifact_credit_allowed": False,
            "reason": "Dataverse provides a machine-readable open-channel dataset, but it has 29 sensor_* columns and is not the HySafe SBEPV5 D27 Gas01..Gas12 benchmark",
            "representative_urls": [
                "https://dataverse.no/dataset.xhtml?persistentId=doi:10.23642/USN.26117989",
                "https://figshare.com/articles/dataset/Experimental_Data_of_Hydrogen_Dispersion_in_an_Open-ended_Rectangular_Channel/26117989",
            ],
        },
    ]

    searched_queries = [
        '"23_FFI_P101_T00031" SBEPV5 D27',
        '"HySafe" "SBEPV5" "D27" "Excel" hydrogen concentration',
        '"SBEPV5" "D27" "Gas01(%)"',
    ]

    receiving_summary = receiving_pack.get("summary", {})
    receiving_required_count = receiving_summary.get("required_file_count")
    receiving_present_count = receiving_summary.get("present_file_count")
    receiving_missing_count = receiving_summary.get("missing_file_count")

    ready = (
        public_triage.get("status") == "PASS-H2-EXTERNAL-PLUME-PUBLIC-SOURCE-TRIAGE"
        and public_triage.get("clears_reference_data_blocker") is False
        and sbepv5_ingestion.get("status") == "NOT_READY-SBEPV5-D27-DATASET-INGESTION"
        and str(dataverse_reference.get("status", "")).startswith("PASS-DATAVERSE-OPEN-CHANNEL")
        and str(dataverse_reference.get("status", "")).endswith("REFERENCE-PACKAGE")
        and dataverse_metadata.get("dataset_doi") == "10.23642/USN.26117989"
        and cross_alias.get("summary", {}).get("alias_rejected_count") == 5
        and cross_alias.get("summary", {}).get("alias_accepted_count") == 0
        and receiving_required_count == 14
        and isinstance(receiving_present_count, int)
        and isinstance(receiving_missing_count, int)
        and receiving_present_count + receiving_missing_count == receiving_required_count
        and receiving_missing_count > 0
        and receiving_summary.get("strict_completion_allowed") is False
        and target_present_count == 0
        and len(checks) == 5
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS,
        "scope": "strict external plume source separation and public-search audit",
        "summary": {
            "strict_external_plume_source_separation_audit_ready": ready,
            "sbepv5_public_sources_identified": True,
            "sbepv5_machine_readable_timeseries_available_locally": False,
            "dataverse_machine_readable_timeseries_available_locally": True,
            "dataverse_usable_as_sbepv5_strict_credit": False,
            "cross_benchmark_alias_guard_ready": cross_alias.get("summary", {}).get(
                "strict_external_artifact_cross_benchmark_alias_selftest_ready"
            ),
            "external_plume_target_count": len(checks),
            "external_plume_target_present_count": target_present_count,
            "strict_external_artifacts_required": receiving_required_count,
            "strict_external_artifacts_present": receiving_present_count,
            "strict_external_artifacts_missing": receiving_missing_count,
            "strict_completion_allowed": False,
            "strict_master_plan_still_open": True,
        },
        "searched_queries": searched_queries,
        "source_findings": source_findings,
        "evidence_files": [
            evidence_entry("external_plume_public_source_triage", PUBLIC_TRIAGE),
            evidence_entry("sbepv5_d27_dataset_ingestion", SBEPV5_INGESTION),
            evidence_entry("dataverse_open_channel_reference_package", DATAVERSE_REFERENCE),
            evidence_entry("dataverse_reference_case_metadata", DATAVERSE_METADATA),
            evidence_entry("strict_cross_benchmark_alias_selftest", CROSS_BENCHMARK_ALIAS),
            evidence_entry("strict_external_artifact_drop_index", DROP_INDEX),
            evidence_entry("strict_external_evidence_receiving_pack", RECEIVING_PACK),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_PASS, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(
        summary.get("strict_external_plume_source_separation_audit_ready") is True,
        "source separation audit is not ready",
    )
    require(summary.get("sbepv5_public_sources_identified") is True, "SBEPV5 public sources not identified")
    require(
        summary.get("sbepv5_machine_readable_timeseries_available_locally") is False,
        "SBEPV5 machine-readable data unexpectedly available",
    )
    require(
        summary.get("dataverse_machine_readable_timeseries_available_locally") is True,
        "Dataverse machine-readable data not available",
    )
    require(summary.get("dataverse_usable_as_sbepv5_strict_credit") is False, "Dataverse overcredited as SBEPV5")
    require(summary.get("cross_benchmark_alias_guard_ready") is True, "cross-benchmark alias guard not ready")
    require(summary.get("external_plume_target_count") == 5, "unexpected external plume target count")
    require(summary.get("external_plume_target_present_count") == 0, "external plume target count changed")
    require(summary.get("strict_external_artifacts_required") == 14, "strict required count changed")
    require(
        isinstance(summary.get("strict_external_artifacts_present"), int),
        "strict present count is not an integer",
    )
    require(
        isinstance(summary.get("strict_external_artifacts_missing"), int),
        "strict missing count is not an integer",
    )
    require(
        summary.get("strict_external_artifacts_present") + summary.get("strict_external_artifacts_missing") == 14,
        "strict present/missing counts do not sum to required total",
    )
    require(summary.get("strict_external_artifacts_missing") > 0, "strict missing count unexpectedly cleared")
    require(summary.get("strict_completion_allowed") is False, "audit overclaims strict completion")
    require(summary.get("strict_master_plan_still_open") is True, "audit overclaims strict closure")
    require(len(data.get("searched_queries", [])) >= 3, "searched query audit too short")
    findings = data.get("source_findings")
    require(isinstance(findings, list) and len(findings) == 2, "invalid source findings")
    for finding in findings:
        require(finding.get("strict_artifact_credit_allowed") is False, "source finding overcredits strict artifact")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(entry["path"])
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict External Plume Source Separation Audit",
        "",
        f"- Status: `{report['status']}`",
        f"- Ready: `{summary['strict_external_plume_source_separation_audit_ready']}`",
        f"- SBEPV5 machine-readable data local: `{summary['sbepv5_machine_readable_timeseries_available_locally']}`",
        f"- Dataverse machine-readable data local: `{summary['dataverse_machine_readable_timeseries_available_locally']}`",
        f"- Dataverse usable as SBEPV5 strict credit: `{summary['dataverse_usable_as_sbepv5_strict_credit']}`",
        f"- External plume targets present: `{summary['external_plume_target_present_count']}/{summary['external_plume_target_count']}`",
        "",
        "## Source Findings",
        "",
    ]
    for finding in report["source_findings"]:
        lines.append(
            f"- `{finding['source_family']}` machine_readable=`{finding['machine_readable_timeseries_available_locally']}` "
            f"strict_credit=`{finding['strict_artifact_credit_allowed']}`"
        )
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
        validate_report(data)
        print(f"strict_external_plume_source_separation_audit VERIFY-PASS json={args.verify_json} status={data['status']}")
        return 0

    report = build_report(args)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_external_plume_source_separation_audit PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
