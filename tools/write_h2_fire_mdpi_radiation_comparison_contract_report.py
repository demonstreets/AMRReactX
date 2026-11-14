#!/usr/bin/env python3
"""Write an acceptance contract for MDPI radiation CFD comparison."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-H2-FIRE-MDPI-RADIATION-COMPARISON-CONTRACT"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/h2_fire_mdpi_radiation_comparison_contract_20260805")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "h2_fire_mdpi_radiation_comparison_contract_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "h2_fire_mdpi_radiation_comparison_contract_report.md"

RADIATION_TABLE = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_calibration_table_20260805/"
    "h2_fire_mdpi_radiation_calibration_table_report.json"
)
FIRE_CONSEQUENCE = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/"
    "fire_consequence_metrics_report.json"
)
STRICT_FIRE_UPDATE = Path(
    "docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731/"
    "master_plan_strict_fire_calibration_update_report.json"
)


class ContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


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
        raise ContractError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON evidence {path}: {exc}") from exc
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


def read_radiation_rows(report: dict[str, Any]) -> list[dict[str, str]]:
    csv_path = Path(report["output_files"]["radiation_metrics_csv"])
    require(csv_path.is_file(), f"missing radiation CSV: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    require(len(rows) >= 4, f"expected at least four MDPI radiation rows, got {len(rows)}")
    return rows


def screening_flux_distances(summary: dict[str, object]) -> list[float]:
    distances: list[float] = []
    pattern = re.compile(r"^screening_flux_at_(?P<distance>[0-9]+)m_w_m2$")
    for key in summary:
        match = pattern.match(key)
        if match:
            distances.append(float(match.group("distance")))
    return sorted(distances)


def build_report(args: argparse.Namespace) -> dict[str, object]:
    radiation_table = load_json(Path(args.radiation_table))
    fire_consequence = load_json(Path(args.fire_consequence))
    strict_fire = load_json(Path(args.strict_fire_update))
    require(
        radiation_table.get("status") == "PASS-H2-FIRE-MDPI-RADIATION-CALIBRATION-TABLE",
        "MDPI radiation table not ready",
    )
    require(fire_consequence.get("status") == "PASS-SCREENING", "fire consequence screening report not ready")
    require(strict_fire.get("summary", {}).get("strict_fire_calibration_blocker_cleared") is False, "strict fire overclaimed")

    rows = read_radiation_rows(radiation_table)
    target_distances = sorted({float(row["distance_m"]) for row in rows})
    fire_summary = fire_consequence.get("summary", {})
    require(isinstance(fire_summary, dict), "fire consequence summary missing")
    available_distances = screening_flux_distances(fire_summary)
    missing_direct_distances = [distance for distance in target_distances if distance not in available_distances]

    acceptance_contract = {
        "required_reference_metrics": [row["metric_id"] for row in rows],
        "required_reference_metric_count": len(rows),
        "required_cfd_outputs": [
            "case_aligned_radiative_heat_flux_w_m2_at_each_mdpi_radiometer_distance",
            "release_pressure_or_mass_flow_matching_target_case",
            "orifice_diameter_matching_target_case",
            "radiometer_distance_and_height_mapping",
            "radiation_model_basis_and_radiative_fraction",
        ],
        "acceptance_criteria": {
            "all_radiation_metrics_present": True,
            "flux_tolerance_source": "per-row tolerance_abs_w_m2 and tolerance_rel in radiation_metrics.csv",
            "no_nan_inf_solver_abort": True,
            "cpu_or_gpu_parallel_run_required": True,
            "strict_credit_requires_exp002_pressure_comparison_too": True,
        },
    }

    current_gap = {
        "current_fire_consequence_is_screening_only": True,
        "current_fire_consequence_available_flux_distances_m": available_distances,
        "mdpi_target_distances_m": target_distances,
        "mdpi_target_distances_missing_from_screening_report_m": missing_direct_distances,
        "current_cfd_radiation_comparison_executed": False,
        "current_outputs_sufficient_for_mdpi_radiation_agreement": False,
        "strict_fire_calibration_blocker_cleared": False,
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "title": "H2 Fire MDPI Radiation Comparison Acceptance Contract",
        "status": STATUS_PASS,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "mdpi_radiation_table_ready": True,
            "mdpi_radiation_metric_count": len(rows),
            "radiation_comparison_contract_ready": True,
            "current_cfd_radiation_comparison_executed": False,
            "current_outputs_sufficient_for_mdpi_radiation_agreement": False,
            "strict_fire_calibration_blocker_cleared": False,
        },
        "acceptance_contract": acceptance_contract,
        "current_gap": current_gap,
        "limitations": [
            "This is an acceptance contract and preflight, not an MDPI CFD radiation agreement result.",
            "The current fire consequence report is screening-only and does not provide direct 0.23 m / 0.50 m MDPI radiometer comparisons.",
            "Strict fire credit still requires case-aligned CFD radiation comparison and EXP002 pressure comparison.",
        ],
        "evidence_files": [
            evidence_entry("radiation_table_report", Path(args.radiation_table)),
            evidence_entry("fire_consequence_screening", Path(args.fire_consequence)),
            evidence_entry("strict_fire_update", Path(args.strict_fire_update)),
            evidence_entry("radiation_metrics_csv", Path(radiation_table["output_files"]["radiation_metrics_csv"])),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, object], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS_PASS, f"status is not pass: {data.get('status')}")
    summary = data.get("summary", {})
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("mdpi_radiation_table_ready") is True, "radiation table not ready")
    require(summary.get("mdpi_radiation_metric_count") >= 4, "radiation metric count too small")
    require(summary.get("radiation_comparison_contract_ready") is True, "contract not ready")
    require(summary.get("current_cfd_radiation_comparison_executed") is False, "radiation comparison overclaimed")
    require(summary.get("current_outputs_sufficient_for_mdpi_radiation_agreement") is False, "radiation agreement overclaimed")
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "strict fire blocker overclaimed")
    current_gap = data.get("current_gap", {})
    require(isinstance(current_gap, dict), "current_gap missing")
    require(current_gap.get("current_fire_consequence_is_screening_only") is True, "screening-only gap not detected")
    require(current_gap.get("current_outputs_sufficient_for_mdpi_radiation_agreement") is False, "output sufficiency overclaimed")
    require(len(data.get("acceptance_contract", {}).get("required_reference_metrics", [])) >= 4, "contract missing radiation metrics")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, object], path: Path) -> None:
    summary = report["summary"]
    current_gap = report["current_gap"]
    lines = [
        "# H2 Fire MDPI Radiation Comparison Acceptance Contract",
        "",
        f"- Status: `{report['status']}`",
        f"- MDPI radiation metrics: `{summary['mdpi_radiation_metric_count']}`",
        f"- Contract ready: `{summary['radiation_comparison_contract_ready']}`",
        f"- CFD comparison executed: `{summary['current_cfd_radiation_comparison_executed']}`",
        f"- Strict fire blocker cleared: `{summary['strict_fire_calibration_blocker_cleared']}`",
        "",
        "## Current Gap",
        "",
        f"- Screening flux distances m: `{current_gap['current_fire_consequence_available_flux_distances_m']}`",
        f"- MDPI target distances m: `{current_gap['mdpi_target_distances_m']}`",
        f"- Missing direct target distances m: `{current_gap['mdpi_target_distances_missing_from_screening_report_m']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--radiation-table", default=str(RADIATION_TABLE))
    parser.add_argument("--fire-consequence", default=str(FIRE_CONSEQUENCE))
    parser.add_argument("--strict-fire-update", default=str(STRICT_FIRE_UPDATE))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"h2_fire_mdpi_radiation_comparison_contract VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"h2_fire_mdpi_radiation_comparison_contract PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
