#!/usr/bin/env python3
"""Write a schema-compatible radiation target table from recorded MDPI jet-fire anchors."""

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
STATUS_PASS = "PASS-H2-FIRE-MDPI-RADIATION-CALIBRATION-TABLE"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/h2_fire_mdpi_radiation_calibration_table_20260805")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "h2_fire_mdpi_radiation_calibration_table_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "h2_fire_mdpi_radiation_calibration_table_report.md"
DEFAULT_OUTPUT_CSV = DEFAULT_ROOT / "radiation_metrics.csv"
DEFAULT_OUTPUT_METADATA = DEFAULT_ROOT / "calibration_metadata.mdpi_radiation_partial.json"
DEFAULT_OUTPUT_ANCHORS = DEFAULT_ROOT / "mdpi_radiation_anchor_targets.json"

LITERATURE_PREFLIGHT = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_calibration_literature_metric_preflight_20260724/"
    "fire_calibration_literature_metric_preflight_report.json"
)
PUBLIC_TRIAGE = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_calibration_public_source_triage_20260724/"
    "fire_calibration_public_source_triage_report.json"
)
FIRE_CONSEQUENCE = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/"
    "fire_consequence_metrics_report.json"
)

CSV_COLUMNS = (
    "metric_id",
    "distance_m",
    "reference_flux_w_m2",
    "tolerance_abs_w_m2",
    "tolerance_rel",
    "source_basis",
)


class RadiationTableError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RadiationTableError(message)


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
        raise RadiationTableError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RadiationTableError(f"invalid JSON evidence {path}: {exc}") from exc
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


def finite_positive(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RadiationTableError(f"{label} is not numeric: {value!r}") from exc
    require(math.isfinite(number), f"{label} is not finite")
    require(number > 0.0, f"{label} must be positive")
    return number


def find_anchor(preflight: dict[str, Any], metric_id: str) -> dict[str, Any]:
    for anchor in preflight.get("metric_anchors", []):
        if anchor.get("metric_id") == metric_id:
            return anchor
    raise RadiationTableError(f"missing radiation metric anchor: {metric_id}")


def build_rows(preflight: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    require(
        preflight.get("status") == "PASS-H2-FIRE-CALIBRATION-LITERATURE-METRIC-PREFLIGHT",
        "literature preflight is not ready",
    )
    flux_anchor = find_anchor(preflight, "mdpi_jet_fire_reference_flux_bounds")
    error_anchor = find_anchor(preflight, "mdpi_jet_fire_model_error_anchor")
    values = flux_anchor["values"]
    max_error_percent = finite_positive(error_anchor["values"]["max_error_percent"], "max model error percent")
    tolerance_rel = max(0.25, min(0.5, max_error_percent / 100.0 * 2.0))

    raw_targets = [
        (
            "mdpi_jet_fire_1p5mm_0p6mpa_0p23m",
            0.23,
            values["flux_w_m2_1p5mm_0p6mpa_0p23m"],
            "1.5 mm leak diameter, 0.6 MPa, radial distance 0.23 m",
        ),
        (
            "mdpi_jet_fire_1p5mm_0p6mpa_0p50m",
            0.50,
            values["flux_w_m2_1p5mm_0p6mpa_0p50m"],
            "1.5 mm leak diameter, 0.6 MPa, radial distance 0.50 m",
        ),
        (
            "mdpi_jet_fire_max_1p2mm_0p23m",
            0.23,
            values["max_flux_w_m2_at_0p23m_1p2mm"],
            "maximum reported heat flux at 0.23 m for 1.2 mm leak diameter",
        ),
        (
            "mdpi_jet_fire_max_2p0mm_0p23m",
            0.23,
            values["max_flux_w_m2_at_0p23m_2p0mm"],
            "maximum reported heat flux at 0.23 m for 2.0 mm leak diameter",
        ),
    ]

    rows: list[dict[str, str]] = []
    details: list[dict[str, Any]] = []
    for metric_id, distance_m, flux, basis in raw_targets:
        flux_w_m2 = finite_positive(flux, metric_id)
        tolerance_abs = max(50.0, flux_w_m2 * tolerance_rel)
        source_basis = (
            "MDPI Applied Sciences 14(16):7098 hydrogen jet-fire radiation anchor; "
            f"{basis}; tolerance uses 2x reported max optimized multi-point-source error "
            f"({max_error_percent}%)."
        )
        rows.append(
            {
                "metric_id": metric_id,
                "distance_m": f"{distance_m:.12g}",
                "reference_flux_w_m2": f"{flux_w_m2:.12g}",
                "tolerance_abs_w_m2": f"{tolerance_abs:.12g}",
                "tolerance_rel": f"{tolerance_rel:.12g}",
                "source_basis": source_basis,
            }
        )
        details.append(
            {
                "metric_id": metric_id,
                "distance_m": distance_m,
                "reference_flux_w_m2": flux_w_m2,
                "tolerance_abs_w_m2": tolerance_abs,
                "tolerance_rel": tolerance_rel,
                "source_id": flux_anchor["source_id"],
                "source_basis": basis,
            }
        )
    return rows, details


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_sidecars(
    preflight: dict[str, Any],
    public_triage: dict[str, Any],
    rows: list[dict[str, str]],
    details: list[dict[str, Any]],
    metadata_path: Path,
    anchors_path: Path,
) -> None:
    candidates = {
        item["id"]: item for item in public_triage.get("radiation_candidates", []) if isinstance(item, dict)
    }
    mdpi_source = candidates.get("mdpi_jet_fire_2024", {})
    metadata = {
        "schema_version": 1,
        "dataset_type": "h2_fire_mdpi_radiation_calibration_partial",
        "case": "MDPI hydrogen jet-fire radiation anchors",
        "source_type": "experimental_public_literature",
        "source": {
            "title": mdpi_source.get(
                "title",
                "Study on Thermal Radiation Characteristics and the Multi-Point Source Model of Hydrogen Jet Fire",
            ),
            "url": mdpi_source.get("url", "https://www.mdpi.com/2076-3417/14/16/7098"),
            "source_id": "mdpi_jet_fire_2024",
        },
        "case_parameters": {
            "radial_distance_m_values": sorted({float(row["distance_m"]) for row in rows}),
            "metric_count": len(rows),
            "source_preflight_status": preflight.get("status"),
        },
        "strict_credit": {
            "clears_fire_consequence_blocker": False,
            "reason": "Radiation targets are repository-formatted, but case-aligned CFD radiation agreement and EXP002 pressure agreement are not complete.",
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    anchors_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "row_count": len(rows),
                "csv_columns": list(CSV_COLUMNS),
                "radiation_targets": details,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    preflight = load_json(Path(args.literature_preflight))
    public_triage = load_json(Path(args.public_triage))
    fire_consequence = load_json(Path(args.fire_consequence))
    require(public_triage.get("status") == "PASS-H2-FIRE-CALIBRATION-PUBLIC-SOURCE-TRIAGE", "public triage not ready")
    require(fire_consequence.get("status") == "PASS-SCREENING", "screening fire consequence report not ready")

    rows, details = build_rows(preflight)
    out_csv = Path(args.output_csv)
    out_metadata = Path(args.output_metadata)
    out_anchors = Path(args.output_anchors)
    write_csv(rows, out_csv)
    write_sidecars(preflight, public_triage, rows, details, out_metadata, out_anchors)

    values = [finite_positive(row["reference_flux_w_m2"], row["metric_id"]) for row in rows]
    report = {
        "schema_version": SCHEMA_VERSION,
        "title": "H2 Fire MDPI Radiation Calibration Table",
        "status": STATUS_PASS,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "radiation_metrics_csv_ready": True,
            "radiation_metric_count": len(rows),
            "csv_columns": list(CSV_COLUMNS),
            "reference_flux_w_m2_range": [min(values), max(values)],
            "max_tolerance_rel": max(float(row["tolerance_rel"]) for row in rows),
            "source_metric_anchor_status": preflight.get("status"),
            "source_public_triage_status": public_triage.get("status"),
            "strict_fire_calibration_blocker_cleared": False,
            "ready_for_cfd_radiation_comparison": True,
            "ready_for_full_fire_calibration_ingestion": False,
        },
        "limitations": [
            "This table promotes recorded MDPI radiation anchors into the repository schema; it is not a CFD radiation agreement result.",
            "The rows are a partial radiation target set and do not include full experiment-specific radiometer time histories.",
            "Strict fire credit still requires case-aligned CFD radiation comparison and EXP002 pressure comparison.",
        ],
        "output_files": {
            "radiation_metrics_csv": str(out_csv),
            "partial_metadata_json": str(out_metadata),
            "anchor_targets_json": str(out_anchors),
        },
        "evidence_files": [
            evidence_entry("literature_metric_preflight", Path(args.literature_preflight)),
            evidence_entry("public_source_triage", Path(args.public_triage)),
            evidence_entry("fire_consequence_screening", Path(args.fire_consequence)),
            evidence_entry("radiation_metrics_csv", out_csv),
            evidence_entry("partial_metadata_json", out_metadata),
            evidence_entry("anchor_targets_json", out_anchors),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_csv(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"missing radiation CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    require(len(rows) >= 4, f"expected at least four radiation rows, got {len(rows)}")
    require(all(col in rows[0] for col in CSV_COLUMNS), "radiation CSV missing required columns")
    metric_ids = set()
    for row in rows:
        metric_id = row["metric_id"].strip()
        require(metric_id and metric_id not in metric_ids, f"invalid duplicate metric id {metric_id!r}")
        metric_ids.add(metric_id)
        finite_positive(row["distance_m"], f"{metric_id} distance_m")
        finite_positive(row["reference_flux_w_m2"], f"{metric_id} reference_flux_w_m2")
        finite_positive(row["tolerance_abs_w_m2"], f"{metric_id} tolerance_abs_w_m2")
        tol_rel = finite_positive(row["tolerance_rel"], f"{metric_id} tolerance_rel")
        require(tol_rel <= 0.75, f"{metric_id} tolerance_rel too wide")
        require(row["source_basis"].strip(), f"{metric_id} missing source_basis")
    return rows


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS_PASS, f"status is not pass: {data.get('status')}")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("radiation_metrics_csv_ready") is True, "radiation CSV not ready")
    require(summary.get("radiation_metric_count") >= 4, "radiation metric count too small")
    require(summary.get("source_metric_anchor_status") == "PASS-H2-FIRE-CALIBRATION-LITERATURE-METRIC-PREFLIGHT", "metric anchor source not ready")
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "strict fire blocker overclaimed")
    require(summary.get("ready_for_cfd_radiation_comparison") is True, "CFD radiation comparison readiness missing")
    require(summary.get("ready_for_full_fire_calibration_ingestion") is False, "full ingestion overclaimed")
    validate_csv(Path(data["output_files"]["radiation_metrics_csv"]))
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# H2 Fire MDPI Radiation Calibration Table",
        "",
        f"- Status: `{report['status']}`",
        f"- Radiation metrics: `{s['radiation_metric_count']}`",
        f"- Reference flux range W/m2: `{s['reference_flux_w_m2_range']}`",
        f"- Strict fire calibration blocker cleared: `{s['strict_fire_calibration_blocker_cleared']}`",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in report["limitations"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--literature-preflight", default=str(LITERATURE_PREFLIGHT))
    parser.add_argument("--public-triage", default=str(PUBLIC_TRIAGE))
    parser.add_argument("--fire-consequence", default=str(FIRE_CONSEQUENCE))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--output-metadata", default=str(DEFAULT_OUTPUT_METADATA))
    parser.add_argument("--output-anchors", default=str(DEFAULT_OUTPUT_ANCHORS))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"h2_fire_mdpi_radiation_calibration_table VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"h2_fire_mdpi_radiation_calibration_table PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
