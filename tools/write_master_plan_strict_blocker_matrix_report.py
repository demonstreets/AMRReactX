#!/usr/bin/env python3
"""Write/verify the strict master-plan blocker matrix."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_TRIAGED = "TRIAGED-MASTER-PLAN-STRICT-BLOCKER-MATRIX"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "master_plan_strict_blocker_matrix_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "master_plan_strict_blocker_matrix_report.md"
DEFAULT_TRACEABILITY = Path(
    "docs/codex_audit/evidence/engineering_h2_master_plan_traceability_20260724/"
    "h2_master_plan_traceability_report.json"
)
DEFAULT_EXTERNAL = Path(
    "docs/codex_audit/evidence/master_plan_strict_external_source_update_20260731/"
    "master_plan_strict_external_source_update_report.json"
)
DEFAULT_REAL_CAD = Path(
    "docs/codex_audit/evidence/master_plan_strict_real_cad_update_20260731/"
    "master_plan_strict_real_cad_update_report.json"
)
DEFAULT_FIRE = Path(
    "docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731/"
    "master_plan_strict_fire_calibration_update_report.json"
)

EXPECTED_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}


class MatrixError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MatrixError(message)


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
        raise MatrixError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MatrixError(f"invalid JSON evidence {path}: {exc}") from exc
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
    paths = {
        "traceability": Path(args.traceability),
        "external_plume_update": Path(args.external_plume_update),
        "real_cad_update": Path(args.real_cad_update),
        "fire_calibration_update": Path(args.fire_calibration_update),
    }
    reports = {name: load_json(path) for name, path in paths.items()}
    blockers = reports["traceability"].get("remaining_blockers", [])
    blocker_map = {
        item.get("blocker"): item
        for item in blockers
        if isinstance(item, dict)
    }

    external = reports["external_plume_update"]
    real_cad = reports["real_cad_update"]
    fire = reports["fire_calibration_update"]

    matrix = [
        {
            "blocker": "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
            "domain": "external_plume_shape_reference",
            "update_status": external.get("status"),
            "cleared": external.get("summary", {}).get("strict_external_plume_blocker_cleared"),
            "next_actions": external.get("summary", {}).get("strict_external_plume_next_actions", []),
            "missing_for_strict_credit": external.get("missing_for_strict_credit", []),
            "failed_quality_gates": blocker_map.get(
                "reference_agreement_is_threshold_only_not_external_plume_shape_dataset", {}
            ).get("failed_quality_gates", []),
        },
        {
            "blocker": "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
            "domain": "real_cad_cleanup",
            "update_status": real_cad.get("status"),
            "cleared": real_cad.get("summary", {}).get("strict_real_cad_blocker_cleared"),
            "next_actions": real_cad.get("summary", {}).get("strict_real_cad_next_actions", []),
            "missing_for_strict_credit": real_cad.get("missing_for_strict_credit", []),
            "failed_quality_gates": blocker_map.get(
                "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup", {}
            ).get("failed_quality_gates", []),
        },
        {
            "blocker": "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
            "domain": "calibrated_fire_radiation_overpressure",
            "update_status": fire.get("status"),
            "cleared": fire.get("summary", {}).get("strict_fire_calibration_blocker_cleared"),
            "next_actions": fire.get("summary", {}).get("strict_fire_calibration_next_actions", []),
            "missing_for_strict_credit": fire.get("missing_for_strict_credit", []),
            "failed_quality_gates": blocker_map.get(
                "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure", {}
            ).get("failed_quality_gates", []),
        },
    ]

    open_blockers = [item for item in matrix if item["cleared"] is not True]
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_TRIAGED,
        "summary": {
            "strict_master_plan_complete": False,
            "traceability_status": reports["traceability"].get("status"),
            "expected_blocker_count": len(EXPECTED_BLOCKERS),
            "traceability_blocker_count": len(blocker_map),
            "matrix_blocker_count": len(matrix),
            "open_strict_blocker_count": len(open_blockers),
            "open_strict_blockers": [item["blocker"] for item in open_blockers],
            "all_strict_blockers_have_update_reports": all(item["update_status"] for item in matrix),
            "all_strict_blockers_triaged": all(str(item["update_status"]).startswith("TRIAGED-") for item in matrix),
        },
        "blocker_matrix": matrix,
        "evidence_files": [evidence_entry(name, path) for name, path in paths.items()],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_TRIAGED, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("strict_master_plan_complete") is False, "strict master plan should remain incomplete")
    require(summary.get("traceability_status") == "NOT_READY-H2-MASTER-PLAN-TRACEABILITY", "traceability status changed")
    require(summary.get("expected_blocker_count") == 3, "expected blocker count changed")
    require(summary.get("matrix_blocker_count") == 3, "matrix blocker count changed")
    require(summary.get("open_strict_blocker_count") == 3, "strict blockers should remain open")
    require(summary.get("all_strict_blockers_have_update_reports") is True, "missing strict update report")
    require(summary.get("all_strict_blockers_triaged") is True, "strict blockers not all triaged")
    blockers = {item.get("blocker") for item in data.get("blocker_matrix", []) if isinstance(item, dict)}
    require(blockers == EXPECTED_BLOCKERS, "unexpected blocker set")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Strict Master-Plan Blocker Matrix",
        "",
        f"- Status: `{report['status']}`",
        f"- Traceability status: `{s['traceability_status']}`",
        f"- Open strict blockers: `{s['open_strict_blocker_count']}`",
        f"- All update reports present: `{s['all_strict_blockers_have_update_reports']}`",
        "",
        "## Blockers",
        "",
    ]
    for item in report["blocker_matrix"]:
        lines.extend([
            f"### {item['domain']}",
            "",
            f"- Blocker: `{item['blocker']}`",
            f"- Update status: `{item['update_status']}`",
            f"- Cleared: `{item['cleared']}`",
            "- Missing for strict credit:",
        ])
        for missing in item["missing_for_strict_credit"]:
            lines.append(f"  - {missing}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traceability", default=str(DEFAULT_TRACEABILITY))
    parser.add_argument("--external-plume-update", default=str(DEFAULT_EXTERNAL))
    parser.add_argument("--real-cad-update", default=str(DEFAULT_REAL_CAD))
    parser.add_argument("--fire-calibration-update", default=str(DEFAULT_FIRE))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"strict_blocker_matrix VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"strict_blocker_matrix PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
