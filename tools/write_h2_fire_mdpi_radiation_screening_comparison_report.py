#!/usr/bin/env python3
"""Quantify the current screening radiation model against MDPI heat-flux targets.

This is deliberately a screening comparison, not a strict calibrated CFD
agreement claim. It uses the existing H2 fire consequence screening radiative
power and evaluates it at the MDPI target radiometer distances so the current
gap is numerical and reproducible.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_QUANTIFIED = "QUANTIFIED-H2-FIRE-MDPI-RADIATION-SCREENING-NOT-PASSING"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/h2_fire_mdpi_radiation_screening_comparison_20260805")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "h2_fire_mdpi_radiation_screening_comparison_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "h2_fire_mdpi_radiation_screening_comparison_report.md"
DEFAULT_OUTPUT_CSV = DEFAULT_ROOT / "mdpi_radiation_screening_comparison.csv"

RADIATION_TABLE = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_calibration_table_20260805/"
    "h2_fire_mdpi_radiation_calibration_table_report.json"
)
FIRE_CONSEQUENCE = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/"
    "fire_consequence_metrics_report.json"
)


class ScreeningComparisonError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScreeningComparisonError(message)


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


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
        raise ScreeningComparisonError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ScreeningComparisonError(f"invalid JSON evidence {path}: {exc}") from exc
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


def read_radiation_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    output_files = report.get("output_files")
    require(isinstance(output_files, dict), "radiation table missing output_files")
    csv_path = Path(str(output_files.get("radiation_metrics_csv", "")))
    require(csv_path.is_file(), f"missing radiation metrics CSV: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as fh:
        raw_rows = list(csv.DictReader(fh))
    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        metric_id = row.get("metric_id")
        require(isinstance(metric_id, str) and metric_id, "radiation row missing metric_id")
        try:
            distance = float(row["distance_m"])
            reference = float(row["reference_flux_w_m2"])
            tol_abs = float(row["tolerance_abs_w_m2"])
            tol_rel = float(row["tolerance_rel"])
        except (KeyError, ValueError) as exc:
            raise ScreeningComparisonError(f"invalid radiation row for {metric_id}: {exc}") from exc
        require(distance > 0.0 and reference > 0.0 and tol_abs > 0.0 and tol_rel > 0.0, "invalid radiation values")
        rows.append(
            {
                "metric_id": metric_id,
                "distance_m": distance,
                "reference_flux_w_m2": reference,
                "tolerance_abs_w_m2": tol_abs,
                "tolerance_rel": tol_rel,
                "source_basis": row.get("source_basis", ""),
            }
        )
    require(len(rows) >= 4, f"expected at least four MDPI radiation rows, got {len(rows)}")
    return rows


def point_source_flux(power_w: float, distance_m: float) -> float:
    return power_w / (4.0 * math.pi * distance_m * distance_m)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    radiation_table_path = Path(args.radiation_table)
    fire_consequence_path = Path(args.fire_consequence)
    output_csv = Path(args.output_csv)

    radiation_table = load_json(radiation_table_path)
    fire_consequence = load_json(fire_consequence_path)
    require(
        radiation_table.get("status") == "PASS-H2-FIRE-MDPI-RADIATION-CALIBRATION-TABLE",
        "MDPI radiation table is not ready",
    )
    require(fire_consequence.get("status") == "PASS-SCREENING", "fire consequence report must remain screening-only")
    fire_summary = fire_consequence.get("summary", {})
    require(isinstance(fire_summary, dict), "fire consequence summary missing")

    source_power = fire_summary.get("source_limited_radiative_power_w")
    cloud_power = fire_summary.get("cloud_average_radiative_power_w")
    require(finite(source_power) and float(source_power) > 0.0, "source radiative power missing")
    require(finite(cloud_power) and float(cloud_power) > 0.0, "cloud-average radiative power missing")
    source_power = float(source_power)
    cloud_power = float(cloud_power)

    rows = read_radiation_rows(radiation_table)
    comparisons: list[dict[str, Any]] = []
    for row in rows:
        distance = float(row["distance_m"])
        reference = float(row["reference_flux_w_m2"])
        source_flux = point_source_flux(source_power, distance)
        cloud_flux = point_source_flux(cloud_power, distance)
        abs_error = abs(source_flux - reference)
        rel_error = abs_error / reference
        passed = abs_error <= float(row["tolerance_abs_w_m2"]) or rel_error <= float(row["tolerance_rel"])
        comparisons.append(
            {
                **row,
                "screening_source_limited_flux_w_m2": source_flux,
                "screening_cloud_average_flux_w_m2": cloud_flux,
                "source_limited_abs_error_w_m2": abs_error,
                "source_limited_rel_error": rel_error,
                "source_limited_to_reference_ratio": source_flux / reference,
                "passed": passed,
            }
        )

    pass_count = sum(1 for item in comparisons if item["passed"])
    ratios = [float(item["source_limited_to_reference_ratio"]) for item in comparisons]
    report = {
        "schema_version": SCHEMA_VERSION,
        "title": "H2 Fire MDPI Radiation Screening Comparison",
        "status": STATUS_QUANTIFIED,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "screening_comparison_executed": True,
            "mdpi_radiation_metric_count": len(comparisons),
            "screening_metric_pass_count": pass_count,
            "screening_metric_fail_count": len(comparisons) - pass_count,
            "all_screening_metrics_passed": pass_count == len(comparisons),
            "case_aligned_cfd_radiation_agreement": False,
            "current_outputs_sufficient_for_mdpi_radiation_agreement": False,
            "strict_fire_calibration_blocker_cleared": False,
            "source_limited_radiative_power_w": source_power,
            "cloud_average_radiative_power_w": cloud_power,
            "min_source_limited_to_reference_ratio": min(ratios),
            "max_source_limited_to_reference_ratio": max(ratios),
        },
        "comparison_basis": {
            "simulation_basis": "existing engineering H2 fire consequence screening point-source flux",
            "reference_basis": "MDPI radiation calibration target table",
            "screening_flux_formula": "radiative_power_w / (4*pi*distance_m^2)",
            "strict_credit_policy": "does not clear strict fire calibration blocker without case-aligned CFD radiation and EXP002 pressure agreement",
        },
        "comparisons": comparisons,
        "output_files": {
            "comparison_csv": str(output_csv),
        },
        "limitations": [
            "This uses a screening point-source flux, not a resolved flame radiation model.",
            "The current engineering H2 scenario is not case-aligned to each MDPI nozzle diameter and pressure.",
            "This report quantifies the current gap and intentionally does not clear strict fire calibration credit.",
        ],
        "evidence_files": [
            evidence_entry("mdpi_radiation_table", radiation_table_path),
            evidence_entry("fire_consequence_screening", fire_consequence_path),
            evidence_entry("radiation_metrics_csv", Path(radiation_table["output_files"]["radiation_metrics_csv"])),
        ],
    }
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    write_comparison_csv(comparisons, output_csv)
    report["evidence_files"].append(evidence_entry("comparison_csv", output_csv))
    validate_report(report, verify_hashes=False)
    return report


def write_comparison_csv(comparisons: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "metric_id",
        "distance_m",
        "reference_flux_w_m2",
        "tolerance_abs_w_m2",
        "tolerance_rel",
        "screening_source_limited_flux_w_m2",
        "screening_cloud_average_flux_w_m2",
        "source_limited_abs_error_w_m2",
        "source_limited_rel_error",
        "source_limited_to_reference_ratio",
        "passed",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for item in comparisons:
            writer.writerow({key: item[key] for key in fields})


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    require(data.get("status") == STATUS_QUANTIFIED, f"unexpected status: {data.get('status')}")
    summary = data.get("summary", {})
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("screening_comparison_executed") is True, "screening comparison not executed")
    require(summary.get("mdpi_radiation_metric_count", 0) >= 4, "too few MDPI radiation metrics")
    require(summary.get("screening_metric_fail_count", 0) >= 1, "screening comparison unexpectedly has no failures")
    require(summary.get("all_screening_metrics_passed") is False, "screening comparison overclaimed all-pass")
    require(summary.get("case_aligned_cfd_radiation_agreement") is False, "case-aligned CFD agreement overclaimed")
    require(
        summary.get("current_outputs_sufficient_for_mdpi_radiation_agreement") is False,
        "MDPI radiation output sufficiency overclaimed",
    )
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "strict fire blocker overclaimed")
    comparisons = data.get("comparisons")
    require(isinstance(comparisons, list) and len(comparisons) >= 4, "comparisons missing")
    for item in comparisons:
        require(isinstance(item, dict), "invalid comparison item")
        for key in (
            "distance_m",
            "reference_flux_w_m2",
            "screening_source_limited_flux_w_m2",
            "source_limited_abs_error_w_m2",
            "source_limited_rel_error",
            "source_limited_to_reference_ratio",
        ):
            require(finite(item.get(key)), f"non-finite comparison value: {key}")
        require(item.get("passed") is False, "current screening item unexpectedly passed")
    output_files = data.get("output_files", {})
    require(isinstance(output_files, dict), "output_files missing")
    csv_path = Path(str(output_files.get("comparison_csv", "")))
    require(csv_path.is_file(), f"comparison CSV missing: {csv_path}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# H2 Fire MDPI Radiation Screening Comparison",
        "",
        f"- Status: `{report['status']}`",
        f"- Screening comparison executed: `{s['screening_comparison_executed']}`",
        f"- MDPI radiation metrics: `{s['mdpi_radiation_metric_count']}`",
        f"- Screening pass/fail: `{s['screening_metric_pass_count']}/{s['screening_metric_fail_count']}`",
        f"- Strict fire blocker cleared: `{s['strict_fire_calibration_blocker_cleared']}`",
        "",
        "## Comparison",
        "",
        "| Metric | Distance m | Reference W/m2 | Screening W/m2 | Relative error | Passed |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in report["comparisons"]:
        lines.append(
            f"| `{item['metric_id']}` | {item['distance_m']:.3g} | {item['reference_flux_w_m2']:.8e} | "
            f"{item['screening_source_limited_flux_w_m2']:.8e} | {item['source_limited_rel_error']:.8e} | "
            f"`{item['passed']}` |"
        )
    lines += ["", "## Limitations", ""]
    for item in report["limitations"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--radiation-table", default=str(RADIATION_TABLE))
    parser.add_argument("--fire-consequence", default=str(FIRE_CONSEQUENCE))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(
            "h2_fire_mdpi_radiation_screening_comparison VERIFY-PASS "
            f"json={args.verify_json} status={data.get('status')}"
        )
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"h2_fire_mdpi_radiation_screening_comparison PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
