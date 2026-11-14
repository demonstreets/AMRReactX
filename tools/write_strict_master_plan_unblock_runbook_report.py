#!/usr/bin/env python3
"""Write/verify the strict master-plan unblock runbook report."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-STRICT-MASTER-PLAN-UNBLOCK-RUNBOOK"
STATUS_NOT_READY = "NOT_READY-STRICT-MASTER-PLAN-UNBLOCK-RUNBOOK"

RUNBOOK = Path("docs/codex_audit/strict_master_plan_unblock_runbook.md")
DEFAULT_ROOT = Path("docs/codex_audit/evidence/strict_master_plan_unblock_runbook_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "strict_master_plan_unblock_runbook_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "strict_master_plan_unblock_runbook_report.md"
STRICT_BLOCKER_MATRIX = Path(
    "docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/"
    "master_plan_strict_blocker_matrix_report.json"
)

REQUIRED_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}

REQUIRED_COMMANDS = [
    "bash tools/verify_master_plan_strict_blocker_matrix.sh",
    "bash tools/verify_master_plan_strict_external_source_update.sh",
    "bash tools/verify_master_plan_strict_real_cad_update.sh",
    "bash tools/verify_master_plan_strict_fire_calibration_update.sh",
    "python3 tools/write_dataverse_open_channel_amr_source_projection_contract_report.py",
    "bash tools/verify_dataverse_open_channel_amr_source_projection_contract.sh",
    "python3 tools/write_engineering_h2_external_artifact_operator_receipt_report.py",
    "python3 tools/write_engineering_h2_external_artifact_drop_validator.py",
    "python3 tools/write_engineering_h2_external_artifact_controlled_copy_report.py",
    "python3 tools/codex_print_strict_external_artifact_drop_index.py",
    "python3 tools/codex_print_strict_external_artifact_drop_index.py --json",
    "python3 tools/write_strict_external_evidence_receiving_pack_report.py",
    "bash tools/verify_strict_external_evidence_receiving_pack.sh",
    "python3 tools/write_strict_external_artifact_template_clone_selftest_report.py",
    "bash tools/verify_strict_external_artifact_template_clone_selftest.sh",
    "bash tools/verify_strict_artifact_drop_contract_preflight.sh",
    "python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py",
    "python3 tools/write_engineering_h2_sbepv5_external_dataset_report.py",
    "python3 tools/write_engineering_h2_sbepv5_literature_metric_preflight_report.py",
    "python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py",
    "python3 tools/write_engineering_h2_real_cad_boundary_tag_contract_report.py",
    "python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py",
    "python3 tools/write_engineering_h2_fire_calibration_dataset_report.py",
    "python3 tools/write_engineering_h2_fire_calibration_package_report.py",
    "bash tools/verify_master_plan_strict_artifact_intake_manifest.sh",
    "bash tools/verify_master_plan_strict_artifact_drop_preflight.sh",
    "bash tools/codex_verify_current_scope.sh",
    "bash tools/run_current_scope_release_refresh.sh",
]

REQUIRED_PATHS = [
    STRICT_BLOCKER_MATRIX,
    Path("docs/codex_audit/evidence/engineering_h2_external_evidence_intake_kit_20260724/templates/operator_receipt_template.json"),
    Path("docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812/strict_external_evidence_receiving_pack_report.json"),
    Path("docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812/strict_external_evidence_receiving_pack_report.md"),
    Path("docs/codex_audit/evidence/strict_external_artifact_template_clone_selftest_20260817/strict_external_artifact_template_clone_selftest_report.json"),
    Path("docs/codex_audit/evidence/strict_external_artifact_template_clone_selftest_20260817/strict_external_artifact_template_clone_selftest_report.md"),
    Path("docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/strict_external_artifact_drop_index_report.md"),
    Path("docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812/strict_external_artifact_drop_checklist_report.md"),
    Path("docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_contract_20260811/dataverse_open_channel_amr_source_projection_contract_report.json"),
    Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/dataset_metadata_template.json"),
    Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/sensors_template.csv"),
    Path("docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries_template.csv"),
    Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/source_cad/README.md"),
    Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest_template.json"),
    Path("docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_boundary_tags_template.csv"),
    Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata_template.json"),
    Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics_template.csv"),
    Path("docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics_template.csv"),
]


class UnblockRunbookError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UnblockRunbookError(message)


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
        raise UnblockRunbookError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise UnblockRunbookError(f"invalid JSON evidence {path}: {exc}") from exc
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


def build_report() -> dict[str, Any]:
    require(RUNBOOK.is_file(), f"missing runbook: {RUNBOOK}")
    text = RUNBOOK.read_text(encoding="utf-8")
    strict = load_json(STRICT_BLOCKER_MATRIX)
    open_blockers = set(strict.get("summary", {}).get("open_strict_blockers", []))

    missing_blockers = sorted(blocker for blocker in REQUIRED_BLOCKERS if blocker not in text)
    missing_commands = sorted(command for command in REQUIRED_COMMANDS if command not in text)
    missing_paths_in_runbook = sorted(str(path) for path in REQUIRED_PATHS if str(path) not in text)
    missing_files = sorted(str(path) for path in REQUIRED_PATHS if not path.is_file())
    missing_tools = []
    for command in REQUIRED_COMMANDS:
        parts = command.split()
        if len(parts) >= 2 and parts[0] in {"bash", "python3"} and parts[1].startswith("tools/"):
            tool = Path(parts[1])
            if not tool.is_file():
                missing_tools.append(str(tool))

    ready = (
        not missing_blockers
        and not missing_commands
        and not missing_paths_in_runbook
        and not missing_files
        and not missing_tools
        and open_blockers == REQUIRED_BLOCKERS
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "strict_master_plan_unblock_runbook_ready": ready,
            "runbook_path": str(RUNBOOK),
            "required_blocker_count": len(REQUIRED_BLOCKERS),
            "missing_blocker_count": len(missing_blockers),
            "required_command_count": len(REQUIRED_COMMANDS),
            "missing_command_count": len(missing_commands),
            "required_path_count": len(REQUIRED_PATHS),
            "missing_path_in_runbook_count": len(missing_paths_in_runbook),
            "missing_file_count": len(missing_files),
            "missing_tool_count": len(missing_tools),
            "strict_blocker_matrix_status": strict.get("status"),
            "strict_blocker_set_matches_expected": open_blockers == REQUIRED_BLOCKERS,
        },
        "findings": {
            "missing_blockers": missing_blockers,
            "missing_commands": missing_commands,
            "missing_paths_in_runbook": missing_paths_in_runbook,
            "missing_files": missing_files,
            "missing_tools": missing_tools,
        },
        "evidence_files": [
            evidence_entry("strict_master_plan_unblock_runbook", RUNBOOK),
            evidence_entry("master_plan_strict_blocker_matrix_report", STRICT_BLOCKER_MATRIX),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_master_plan_unblock_runbook_ready") is True, "strict unblock runbook is not ready")
    require(summary.get("missing_blocker_count") == 0, "runbook is missing strict blockers")
    require(summary.get("missing_command_count") == 0, "runbook is missing commands")
    require(summary.get("missing_path_in_runbook_count") == 0, "runbook is missing required paths")
    require(summary.get("missing_file_count") == 0, "required files are missing")
    require(summary.get("missing_tool_count") == 0, "required tools are missing")
    require(summary.get("strict_blocker_set_matches_expected") is True, "strict blocker set changed")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Strict Master-Plan Unblock Runbook Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Runbook: `{summary['runbook_path']}`",
        f"- Missing blockers: `{summary['missing_blocker_count']}`",
        f"- Missing commands: `{summary['missing_command_count']}`",
        f"- Missing paths in runbook: `{summary['missing_path_in_runbook_count']}`",
        f"- Missing files: `{summary['missing_file_count']}`",
        f"- Missing tools: `{summary['missing_tool_count']}`",
        f"- Strict blocker matrix: `{summary['strict_blocker_matrix_status']}`",
        f"- Strict blocker set matches expected: `{summary['strict_blocker_set_matches_expected']}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"strict_master_plan_unblock_runbook VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"strict_master_plan_unblock_runbook PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
