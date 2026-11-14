#!/usr/bin/env python3
"""Write/verify negative selftests for the engineering H2 real-CAD guard rails."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(TOOL_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT / "tools"))

from write_engineering_campaign_manifest import (  # noqa: E402
    ManifestError,
    REAL_CAD_DATASET_TYPE,
    validate_real_cad_cleanup_manifest,
)
from write_engineering_h2_real_cad_boundary_tag_contract_report import (  # noqa: E402
    validate_boundary_tags,
)
from write_engineering_h2_real_cad_intake_preflight_report import (  # noqa: E402
    RealCadIntakePreflightError,
    validate_cleanup_quality_record,
    validate_data_room_index,
)


SCHEMA_VERSION = 1
STATUS = "PASS-H2-REAL-CAD-GUARD-NEGATIVE-SELFTEST"
DEFAULT_ROOT = Path("docs/codex_audit/evidence/engineering_h2_real_cad_guard_negative_selftest_20260807")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "real_cad_guard_negative_selftest_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "real_cad_guard_negative_selftest_report.md"
DEFAULT_FIXTURE_ROOT = DEFAULT_ROOT / "fixtures"
CAMPAIGN = "engineering-h2-production-full"

CLEANUP_PACKAGE_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/"
    "real_cad_cleanup_package_report.json"
)
INTAKE_PREFLIGHT_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_real_cad_intake_preflight_20260724/"
    "real_cad_intake_preflight_report.json"
)
BOUNDARY_CONTRACT_REPORT = Path(
    "docs/codex_audit/evidence/engineering_h2_real_cad_boundary_tag_contract_20260724/"
    "real_cad_boundary_tag_contract_report.json"
)
STRICT_REAL_CAD_UPDATE_REPORT = Path(
    "docs/codex_audit/evidence/master_plan_strict_real_cad_update_20260731/"
    "master_plan_strict_real_cad_update_report.json"
)


class RealCadGuardSelftestError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RealCadGuardSelftestError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    return {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RealCadGuardSelftestError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RealCadGuardSelftestError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def write_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def base_provenance() -> dict[str, str]:
    return {
        "title": "Guard fixture CAD package",
        "owner_or_supplier": "guard-fixture-owner",
        "drawing_or_package_id": "GUARD-CAD-001",
        "revision": "A",
        "received_at_utc": "2026-08-07T00:00:00Z",
        "confidentiality": "internal_guard_fixture",
    }


def make_geometry(root: Path, label: str, offset: float) -> dict[str, Any]:
    source = write_file(root / "source_cad" / f"{label}.step", f"ISO-10303-21; HEADER; DATA; /* {label} */ ENDSEC;\n")
    cleaned = write_file(root / "cleaned_geometry" / f"{label}.stl", f"solid {label}\nendsolid {label}\n")
    return {
        "label": label,
        "source_cad": {"path": str(source), "sha256": sha256_file(source)},
        "cleaned_geometry": {"path": str(cleaned), "sha256": sha256_file(cleaned)},
        "cleanup_checks": {
            "units_declared": True,
            "watertight_or_closed_surface": True,
            "nondegenerate_elements": True,
            "positive_volume_or_area": True,
            "bbox_min_m": [offset, 0.0, 0.0],
            "bbox_max_m": [offset + 1.0, 1.0, 1.0],
        },
    }


def make_manifest(root: Path, labels: list[str] | None = None) -> Path:
    labels = labels or ["tank_001", "pipe_rack_001", "bund_wall_001"]
    geometries = [make_geometry(root, label, float(idx) * 2.0) for idx, label in enumerate(labels)]
    data = {
        "schema_version": 1,
        "dataset_type": REAL_CAD_DATASET_TYPE,
        "campaign": CAMPAIGN,
        "status": "PASS",
        "synthetic": False,
        "cad_source_is_real": True,
        "source_type": "owner_operator_cad",
        "large_layout_campaign": True,
        "provenance": base_provenance(),
        "geometries": geometries,
    }
    path = root / "real_cad_cleanup_manifest.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def mutate_json(path: Path, mutator: Callable[[dict[str, Any]], None]) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    mutator(data)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_data_room_index(path: Path, bad_hash: bool = False) -> Path:
    rows = [
        ["file_role", "label", "relative_path", "sha256", "source_type", "revision", "owner_or_supplier", "notes"],
    ]
    for label in ["tank_001", "pipe_rack_001", "bund_wall_001"]:
        good_hash = "a" * 64
        rows.append(["source_cad", label, f"source_cad/{label}.step", "bad" if bad_hash else good_hash, "owner_operator_cad", "A", "owner", "source"])
        rows.append(["cleaned_geometry", label, f"cleaned_geometry/{label}.stl", good_hash, "derived_cleanup", "A", "owner", "cleaned"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)
    return path


def write_cleanup_quality(path: Path, false_check: bool = False) -> Path:
    rows = [
        [
            "label",
            "units_declared",
            "watertight_or_closed_surface",
            "nondegenerate_elements",
            "positive_volume_or_area",
            "bbox_min_m",
            "bbox_max_m",
            "tool_or_method",
            "reviewer",
        ],
    ]
    for label in ["tank_001", "pipe_rack_001", "bund_wall_001"]:
        rows.append([label, "true", "false" if false_check else "true", "true", "true", "[0,0,0]", "[1,1,1]", "guard-tool", "reviewer"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)
    return path


def write_boundary_tags(path: Path, placeholder: bool = False, missing_release: bool = False) -> Path:
    rows = [
        ["label", "patch_id", "bc_type", "face_selector", "normal_hint", "area_m2", "source_basis", "engineering_role", "reviewer"],
        ["tank_001", "tank_wall", "no_slip_wall", "cad_named_face:tank", "0,0,1", "10.0", "face-id", "wall_or_obstacle", "<reviewer>" if placeholder else "reviewer"],
        ["pipe_rack_001", "pipe_release", "inlet", "cad_named_face:nozzle", "1,0,0", "0.1", "face-id", "wall_or_obstacle" if missing_release else "release_or_inlet", "reviewer"],
        ["bund_wall_001", "domain_out", "outlet", "domain_plane:x_hi", "1,0,0", "100.0", "domain", "outflow_or_vent", "reviewer"],
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)
    return path


def expect_exception(case_name: str, expected_fragment: str, fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - this is a negative selftest harness.
        diagnostic = str(exc)
        return {
            "case": case_name,
            "rejected": True,
            "expected_fragment": expected_fragment,
            "expected_fragment_seen": expected_fragment in diagnostic,
            "diagnostic": diagnostic[:500],
        }
    return {
        "case": case_name,
        "rejected": False,
        "expected_fragment": expected_fragment,
        "expected_fragment_seen": False,
        "diagnostic": "unexpectedly accepted",
    }


def expect_invalid_boundary(case_name: str, expected_fragment: str, tags: Path, cleanup_package: dict[str, Any]) -> dict[str, Any]:
    valid, summary, gaps = validate_boundary_tags(tags, cleanup_package)
    text = ";".join(gaps)
    return {
        "case": case_name,
        "rejected": valid is False,
        "expected_fragment": expected_fragment,
        "expected_fragment_seen": expected_fragment in text,
        "diagnostic": text[:500],
        "summary": summary,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    fixture_root = Path(args.fixture_root)
    if fixture_root.exists():
        shutil.rmtree(fixture_root)
    fixture_root.mkdir(parents=True, exist_ok=True)

    cleanup = load_json(CLEANUP_PACKAGE_REPORT)
    intake = load_json(INTAKE_PREFLIGHT_REPORT)
    boundary = load_json(BOUNDARY_CONTRACT_REPORT)
    strict = load_json(STRICT_REAL_CAD_UPDATE_REPORT)

    positive_controls = [
        {
            "case": "default_cleanup_package_does_not_clear_blocker",
            "passed": cleanup.get("status") == "NOT_READY-H2-REAL-CAD-CLEANUP-PACKAGE"
            and cleanup.get("clears_real_cad_cleanup_blocker") is False,
        },
        {
            "case": "default_boundary_contract_does_not_clear_credit",
            "passed": boundary.get("status") == "NOT_READY-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT"
            and boundary.get("ready_for_real_cad_bc_tagging_credit") is False,
        },
        {
            "case": "strict_real_cad_update_keeps_blocker_open",
            "passed": strict.get("status") == "TRIAGED-MASTER-PLAN-STRICT-REAL-CAD-ARTIFACTS-MISSING"
            and strict.get("summary", {}).get("strict_real_cad_blocker_cleared") is False,
        },
    ]

    manifest_synthetic = make_manifest(fixture_root / "synthetic_manifest")
    mutate_json(manifest_synthetic, lambda data: data.__setitem__("synthetic", True))
    manifest_missing_provenance = make_manifest(fixture_root / "missing_provenance")
    mutate_json(manifest_missing_provenance, lambda data: data["provenance"].pop("revision"))
    manifest_bad_hash = make_manifest(fixture_root / "bad_hash")
    mutate_json(manifest_bad_hash, lambda data: data["geometries"][0]["source_cad"].__setitem__("sha256", "0" * 64))
    manifest_too_few = make_manifest(fixture_root / "too_few_geometries", ["tank_001"])

    data_room_bad_hash = write_data_room_index(fixture_root / "data_room_bad_hash" / "real_cad_data_room_index.csv", bad_hash=True)
    cleanup_quality_false = write_cleanup_quality(
        fixture_root / "cleanup_quality_false" / "real_cad_cleanup_quality_record.csv",
        false_check=True,
    )
    valid_manifest = make_manifest(fixture_root / "boundary_fixture")
    cleanup_package_for_boundary = {"validation_summary": validate_real_cad_cleanup_manifest(valid_manifest, CAMPAIGN)}
    boundary_placeholder = write_boundary_tags(fixture_root / "boundary_placeholder" / "real_cad_boundary_tags.csv", placeholder=True)
    boundary_missing_release = write_boundary_tags(
        fixture_root / "boundary_missing_release" / "real_cad_boundary_tags.csv",
        missing_release=True,
    )

    negative_cases = [
        expect_exception(
            "manifest_synthetic_true",
            "non-synthetic",
            lambda: validate_real_cad_cleanup_manifest(manifest_synthetic, CAMPAIGN),
        ),
        expect_exception(
            "manifest_missing_provenance_revision",
            "provenance.revision",
            lambda: validate_real_cad_cleanup_manifest(manifest_missing_provenance, CAMPAIGN),
        ),
        expect_exception(
            "manifest_source_hash_mismatch",
            "hash mismatch",
            lambda: validate_real_cad_cleanup_manifest(manifest_bad_hash, CAMPAIGN),
        ),
        expect_exception(
            "manifest_large_layout_too_few_geometries",
            "at least three geometries",
            lambda: validate_real_cad_cleanup_manifest(manifest_too_few, CAMPAIGN),
        ),
        expect_exception(
            "data_room_index_bad_sha256",
            "invalid sha256",
            lambda: validate_data_room_index(data_room_bad_hash),
        ),
        expect_exception(
            "cleanup_quality_false_watertight",
            "cleanup check must be true",
            lambda: validate_cleanup_quality_record(cleanup_quality_false),
        ),
        expect_invalid_boundary(
            "boundary_tags_placeholder_reviewer",
            "placeholder_marker",
            boundary_placeholder,
            cleanup_package_for_boundary,
        ),
        expect_invalid_boundary(
            "boundary_tags_missing_release_role",
            "missing_release_or_inlet_role",
            boundary_missing_release,
            cleanup_package_for_boundary,
        ),
    ]

    expected_fragment_seen_count = sum(1 for case in negative_cases if case["expected_fragment_seen"])
    rejected_count = sum(1 for case in negative_cases if case["rejected"])
    failed_negative_count = len(negative_cases) - rejected_count
    ready = (
        all(control["passed"] for control in positive_controls)
        and rejected_count == len(negative_cases)
        and expected_fragment_seen_count == len(negative_cases)
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUS if ready else "NOT_READY-H2-REAL-CAD-GUARD-NEGATIVE-SELFTEST",
        "summary": {
            "real_cad_guard_negative_selftest_ready": ready,
            "positive_control_count": len(positive_controls),
            "positive_control_pass_count": sum(1 for control in positive_controls if control["passed"]),
            "negative_case_count": len(negative_cases),
            "negative_rejected_count": rejected_count,
            "failed_negative_count": failed_negative_count,
            "expected_fragment_seen_count": expected_fragment_seen_count,
            "guards_synthetic_manifest": negative_cases[0]["rejected"],
            "guards_missing_provenance": negative_cases[1]["rejected"],
            "guards_source_hash_mismatch": negative_cases[2]["rejected"],
            "guards_large_layout_too_few_geometries": negative_cases[3]["rejected"],
            "guards_data_room_bad_hash": negative_cases[4]["rejected"],
            "guards_cleanup_quality_false_check": negative_cases[5]["rejected"],
            "guards_boundary_placeholder": negative_cases[6]["rejected"],
            "guards_boundary_missing_required_role": negative_cases[7]["rejected"],
            "strict_real_cad_blocker_cleared": False,
        },
        "positive_controls": positive_controls,
        "negative_cases": negative_cases,
        "fixture_root": str(fixture_root),
        "evidence_files": [
            evidence_entry("real_cad_cleanup_package_report", CLEANUP_PACKAGE_REPORT),
            evidence_entry("real_cad_intake_preflight_report", INTAKE_PREFLIGHT_REPORT),
            evidence_entry("real_cad_boundary_tag_contract_report", BOUNDARY_CONTRACT_REPORT),
            evidence_entry("strict_real_cad_update_report", STRICT_REAL_CAD_UPDATE_REPORT),
            evidence_entry("synthetic_manifest_fixture", manifest_synthetic),
            evidence_entry("missing_provenance_fixture", manifest_missing_provenance),
            evidence_entry("bad_hash_fixture", manifest_bad_hash),
            evidence_entry("too_few_geometries_fixture", manifest_too_few),
            evidence_entry("data_room_bad_hash_fixture", data_room_bad_hash),
            evidence_entry("cleanup_quality_false_fixture", cleanup_quality_false),
            evidence_entry("boundary_placeholder_fixture", boundary_placeholder),
            evidence_entry("boundary_missing_release_fixture", boundary_missing_release),
        ],
        "limitations": [
            "This is a guard selftest. It does not provide real source CAD or clear the strict real-CAD blocker.",
            "Positive controls only prove the default reports remain non-claiming until controlled real CAD is supplied.",
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS, f"unexpected status: {data.get('status')}")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("real_cad_guard_negative_selftest_ready") is True, "negative selftest not ready")
    require(summary.get("positive_control_pass_count") == summary.get("positive_control_count") == 3, "positive controls failed")
    require(summary.get("negative_case_count") == 8, "unexpected negative case count")
    require(summary.get("negative_rejected_count") == 8, "not all negative cases were rejected")
    require(summary.get("failed_negative_count") == 0, "some negative cases were accepted")
    require(summary.get("expected_fragment_seen_count") == 8, "not all expected diagnostics were seen")
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
    require(summary.get("strict_real_cad_blocker_cleared") is False, "negative selftest must not clear blocker")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Engineering H2 Real-CAD Guard Negative Selftest",
        "",
        f"- Status: `{report['status']}`",
        f"- Positive controls: `{s['positive_control_pass_count']}/{s['positive_control_count']}`",
        f"- Negative cases rejected: `{s['negative_rejected_count']}/{s['negative_case_count']}`",
        f"- Expected diagnostics seen: `{s['expected_fragment_seen_count']}/{s['negative_case_count']}`",
        f"- Strict real-CAD blocker cleared: `{s['strict_real_cad_blocker_cleared']}`",
        "",
        "## Negative Cases",
        "",
    ]
    for case in report["negative_cases"]:
        lines.append(
            f"- `{case['case']}`: rejected `{case['rejected']}`, expected diagnostic `{case['expected_fragment_seen']}`"
        )
    lines += ["", "## Limitations", ""]
    for item in report["limitations"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-root", default=str(DEFAULT_FIXTURE_ROOT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args(argv)
    try:
        if args.verify_json:
            data = load_json(Path(args.verify_json))
            validate_report(data, verify_hashes=True)
            print(f"engineering_h2_real_cad_guard_negative_selftest VERIFY-PASS json={args.verify_json} status={data.get('status')}")
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(report, out_md)
        print(f"engineering_h2_real_cad_guard_negative_selftest PASS json={out_json} md={out_md} status={report['status']}")
        return 0
    except RealCadGuardSelftestError as exc:
        print(f"engineering_h2_real_cad_guard_negative_selftest FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
