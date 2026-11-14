#!/usr/bin/env python3
"""Write/verify strict master-plan real-CAD blocker update evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_TRIAGED = "TRIAGED-MASTER-PLAN-STRICT-REAL-CAD-ARTIFACTS-MISSING"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/master_plan_strict_real_cad_update_20260731")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "master_plan_strict_real_cad_update_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "master_plan_strict_real_cad_update_report.md"
DEFAULT_TRACEABILITY = Path(
    "docs/codex_audit/evidence/engineering_h2_master_plan_traceability_20260724/"
    "h2_master_plan_traceability_report.json"
)
DEFAULT_CLEANUP_PACKAGE = Path(
    "docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/"
    "real_cad_cleanup_package_report.json"
)
DEFAULT_INTAKE_PREFLIGHT = Path(
    "docs/codex_audit/evidence/engineering_h2_real_cad_intake_preflight_20260724/"
    "real_cad_intake_preflight_report.json"
)
DEFAULT_BOUNDARY_CONTRACT = Path(
    "docs/codex_audit/evidence/engineering_h2_real_cad_boundary_tag_contract_20260724/"
    "real_cad_boundary_tag_contract_report.json"
)
DEFAULT_HANDOFF_CONTRACT = Path(
    "docs/codex_audit/evidence/engineering_h2_real_cad_handoff_contract_20260805/"
    "real_cad_handoff_contract_report.json"
)
DEFAULT_NEGATIVE_SELFTEST = Path(
    "docs/codex_audit/evidence/engineering_h2_real_cad_guard_negative_selftest_20260807/"
    "real_cad_guard_negative_selftest_report.json"
)


class StrictRealCadError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise StrictRealCadError(message)


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
        raise StrictRealCadError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StrictRealCadError(f"invalid JSON evidence {path}: {exc}") from exc
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
    traceability_path = Path(args.traceability)
    cleanup_path = Path(args.cleanup_package)
    intake_path = Path(args.intake_preflight)
    boundary_path = Path(args.boundary_contract)
    handoff_path = Path(args.handoff_contract)
    negative_path = Path(args.negative_selftest)
    traceability = load_json(traceability_path)
    cleanup = load_json(cleanup_path)
    intake = load_json(intake_path)
    boundary = load_json(boundary_path)
    handoff = load_json(handoff_path)
    negative = load_json(negative_path)

    blockers = traceability.get("remaining_blockers", [])
    blocker_names = [b.get("blocker") for b in blockers if isinstance(b, dict)]
    real_cad_blocker_present = "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup" in blocker_names
    intake_summary = intake.get("summary", {}) if isinstance(intake.get("summary"), dict) else {}
    boundary_summary = boundary.get("summary", {}) if isinstance(boundary.get("summary"), dict) else {}
    handoff_summary = handoff.get("summary", {}) if isinstance(handoff.get("summary"), dict) else {}
    negative_summary = negative.get("summary", {}) if isinstance(negative.get("summary"), dict) else {}

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_TRIAGED,
        "summary": {
            "real_cad_blocker_present": real_cad_blocker_present,
            "cleanup_package_status": cleanup.get("status"),
            "intake_preflight_status": intake.get("status"),
            "boundary_contract_status": boundary.get("status"),
            "handoff_contract_status": handoff.get("status"),
            "handoff_contract_ready": handoff_summary.get("handoff_contract_ready"),
            "source_cad_file_count": intake_summary.get("source_cad_file_count"),
            "cleaned_geometry_file_count": intake_summary.get("cleaned_geometry_file_count"),
            "boundary_tag_count": boundary_summary.get("boundary_tag_count"),
            "cleanup_package_clears_blocker": intake_summary.get("cleanup_package_clears_blocker"),
            "boundary_contract_ready_for_credit": boundary_summary.get("ready_for_real_cad_bc_tagging_credit"),
            "negative_selftest_status": negative.get("status"),
            "negative_selftest_ready": negative_summary.get("real_cad_guard_negative_selftest_ready"),
            "negative_selftest_case_count": negative_summary.get("negative_case_count"),
            "negative_selftest_rejected_count": negative_summary.get("negative_rejected_count"),
            "negative_selftest_expected_fragment_seen_count": negative_summary.get("expected_fragment_seen_count"),
            "guards_synthetic_manifest": negative_summary.get("guards_synthetic_manifest"),
            "guards_missing_provenance": negative_summary.get("guards_missing_provenance"),
            "guards_source_hash_mismatch": negative_summary.get("guards_source_hash_mismatch"),
            "guards_large_layout_too_few_geometries": negative_summary.get("guards_large_layout_too_few_geometries"),
            "guards_data_room_bad_hash": negative_summary.get("guards_data_room_bad_hash"),
            "guards_cleanup_quality_false_check": negative_summary.get("guards_cleanup_quality_false_check"),
            "guards_boundary_placeholder": negative_summary.get("guards_boundary_placeholder"),
            "guards_boundary_missing_required_role": negative_summary.get("guards_boundary_missing_required_role"),
            "strict_real_cad_blocker_cleared": False,
            "strict_real_cad_next_actions": [
                "Provide controlled source CAD files with provenance and hashes.",
                "Validate the delivery against the real-CAD handoff contract before claiming strict credit.",
                "Run the existing real-CAD cleanup package workflow to produce cleaned geometry files.",
                "Populate repository-ingestable cleanup manifest, data-room index, and cleanup quality record.",
                "Provide boundary tag contract entries for inlet, outlet, walls, leak sources, obstacles, and monitoring regions.",
                "Regenerate cleanup package, intake preflight, boundary tag contract, production scorecard, and master-plan traceability reports.",
            ],
        },
        "missing_for_strict_credit": [
            "source CAD files",
            "cleaned geometry files",
            "cleanup manifest with source and cleaned geometry hashes",
            "data-room index/provenance records",
            "cleanup quality record",
            "boundary tag CSV/JSON entries for real geometry surfaces and leak/monitor regions",
            "large-layout coverage with at least three real geometries when claiming large-layout campaign credit",
        ],
        "evidence_files": [
            evidence_entry("master_plan_traceability_report", traceability_path),
            evidence_entry("real_cad_cleanup_package_report", cleanup_path),
            evidence_entry("real_cad_intake_preflight_report", intake_path),
            evidence_entry("real_cad_boundary_tag_contract_report", boundary_path),
            evidence_entry("real_cad_handoff_contract_report", handoff_path),
            evidence_entry("real_cad_guard_negative_selftest_report", negative_path),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_TRIAGED, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("real_cad_blocker_present") is True, "real CAD blocker not detected")
    require(summary.get("intake_preflight_status") == "PASS-H2-REAL-CAD-INTAKE-PREFLIGHT", "intake preflight should be verified")
    require(summary.get("cleanup_package_status") == "NOT_READY-H2-REAL-CAD-CLEANUP-PACKAGE", "cleanup package status changed")
    require(
        summary.get("boundary_contract_status") == "NOT_READY-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT",
        "boundary contract status changed",
    )
    require(
        summary.get("handoff_contract_status") == "PASS-H2-REAL-CAD-HANDOFF-CONTRACT",
        "handoff contract not ready",
    )
    require(summary.get("handoff_contract_ready") is True, "handoff contract ready flag missing")
    require(summary.get("source_cad_file_count") == 0, "unexpected source CAD files present")
    require(summary.get("cleaned_geometry_file_count") == 0, "unexpected cleaned geometry files present")
    require(
        summary.get("negative_selftest_status") == "PASS-H2-REAL-CAD-GUARD-NEGATIVE-SELFTEST",
        "negative selftest is not passing",
    )
    require(summary.get("negative_selftest_ready") is True, "negative selftest is not ready")
    require(summary.get("negative_selftest_case_count") == 8, "unexpected negative case count")
    require(summary.get("negative_selftest_rejected_count") == 8, "not all negative cases were rejected")
    require(summary.get("negative_selftest_expected_fragment_seen_count") == 8, "negative diagnostics changed")
    for key in (
        "guards_synthetic_manifest",
        "guards_missing_provenance",
        "guards_source_hash_mismatch",
        "guards_large_layout_too_few_geometries",
        "guards_data_room_bad_hash",
        "guards_cleanup_quality_false_check",
        "guards_boundary_placeholder",
        "guards_boundary_missing_required_role",
    ):
        require(summary.get(key) is True, f"{key} is not active")
    require(summary.get("strict_real_cad_blocker_cleared") is False, "strict real CAD blocker must remain open")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Strict Real-CAD Update",
        "",
        f"- Status: `{report['status']}`",
        f"- Cleanup package: `{s['cleanup_package_status']}`",
        f"- Intake preflight: `{s['intake_preflight_status']}`",
        f"- Boundary contract: `{s['boundary_contract_status']}`",
        f"- Handoff contract: `{s['handoff_contract_status']}`",
        f"- Source CAD files: `{s['source_cad_file_count']}`",
        f"- Cleaned geometry files: `{s['cleaned_geometry_file_count']}`",
        f"- Negative selftest: `{s['negative_selftest_status']}`",
        f"- Negative cases rejected: `{s['negative_selftest_rejected_count']}/{s['negative_selftest_case_count']}`",
        f"- Strict real-CAD blocker cleared: `{s['strict_real_cad_blocker_cleared']}`",
        "",
        "## Missing For Strict Credit",
        "",
    ]
    for item in report["missing_for_strict_credit"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Next Actions", ""])
    for item in s["strict_real_cad_next_actions"]:
        lines.append(f"- {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traceability", default=str(DEFAULT_TRACEABILITY))
    parser.add_argument("--cleanup-package", default=str(DEFAULT_CLEANUP_PACKAGE))
    parser.add_argument("--intake-preflight", default=str(DEFAULT_INTAKE_PREFLIGHT))
    parser.add_argument("--boundary-contract", default=str(DEFAULT_BOUNDARY_CONTRACT))
    parser.add_argument("--handoff-contract", default=str(DEFAULT_HANDOFF_CONTRACT))
    parser.add_argument("--negative-selftest", default=str(DEFAULT_NEGATIVE_SELFTEST))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"strict_real_cad_update VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"strict_real_cad_update PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
