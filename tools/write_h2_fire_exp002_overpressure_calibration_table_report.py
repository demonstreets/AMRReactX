#!/usr/bin/env python3
"""Write a schema-compatible EXP002 overpressure calibration target table."""

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
STATUS_PASS = "PASS-H2-FIRE-EXP002-OVERPRESSURE-CALIBRATION-TABLE"
STATUS_NOT_READY = "NOT_READY-H2-FIRE-EXP002-OVERPRESSURE-CALIBRATION-TABLE"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/h2_fire_exp002_overpressure_calibration_table_20260805")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "h2_fire_exp002_overpressure_calibration_table_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "h2_fire_exp002_overpressure_calibration_table_report.md"
DEFAULT_OUTPUT_CSV = DEFAULT_ROOT / "overpressure_metrics.csv"
DEFAULT_OUTPUT_METADATA = DEFAULT_ROOT / "calibration_metadata.exp002_overpressure_partial.json"
DEFAULT_OUTPUT_CHANNELS = DEFAULT_ROOT / "exp002_pressure_channel_targets.json"

EXP002_REDUCED = Path(
    "docs/codex_audit/evidence/h2_fire_overpressure_reduced_exp002_20260805/"
    "h2_fire_overpressure_reduced_exp002_report.json"
)
EXP002_BRIDGE = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_exp002_delayed_ignition_bridge_20260805/"
    "engineering_h2_fire_exp002_delayed_ignition_bridge_report.json"
)
METADATA_REPORT = Path(
    "docs/codex_audit/evidence/h2_fire_overpressure_dataverse_metadata_20260805/"
    "h2_fire_overpressure_dataverse_metadata_report.json"
)

CSV_COLUMNS = (
    "metric_id",
    "distance_m",
    "reference_overpressure_kpa",
    "tolerance_abs_kpa",
    "tolerance_rel",
    "source_basis",
)


class TableError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TableError(message)


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
        raise TableError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TableError(f"invalid JSON evidence {path}: {exc}") from exc
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
        raise TableError(f"{label} is not numeric: {value!r}") from exc
    require(math.isfinite(number), f"{label} is not finite")
    require(number > 0.0, f"{label} must be positive")
    return number


def build_rows(exp002: dict[str, Any], bridge: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    require(exp002.get("status") == "PASS-H2-FIRE-OVERPRESSURE-REDUCED-EXP002", "EXP002 reduced report not ready")
    require(bridge.get("status") == "PASS-H2-FIRE-EXP002-DELAYED-IGNITION-BRIDGE", "EXP002 bridge not ready")
    summary = exp002["summary"]
    require(summary.get("source_csv_md5_matches_dataverse") is True, "EXP002 CSV MD5 is not verified")
    channels = exp002["csv_scan"]["pressure_channels"]
    require(isinstance(channels, dict) and len(channels) == 4, "EXP002 pressure channel count is not four")

    distance_m = finite_positive(
        exp002["experiment_matrix_row"]["Obstacle distance from the nozzle [cm]"], "obstacle distance cm"
    ) / 100.0
    rows: list[dict[str, str]] = []
    details: list[dict[str, Any]] = []
    for channel_id in sorted(channels, key=lambda text: int(text)):
        channel = channels[channel_id]
        peak_bar = finite_positive(
            channel["peak_overpressure_baseline_corrected_bar"],
            f"channel {channel_id} peak overpressure bar",
        )
        peak_kpa = peak_bar * 100.0
        tolerance_abs_kpa = max(0.25, peak_kpa * 0.5)
        metric_id = f"exp002_pressure_channel_{channel_id}"
        source_basis = (
            "DataverseNO doi:10.18710/X044QK EXP002 "
            f"Ign_pipe_geom_EXP_002.csv {channel['name']}; "
            "1 V = -1 bar calibration; baseline-corrected peak. "
            "distance_m records nozzle-to-obstacle distance, not sensor radial distance."
        )
        rows.append(
            {
                "metric_id": metric_id,
                "distance_m": f"{distance_m:.12g}",
                "reference_overpressure_kpa": f"{peak_kpa:.12g}",
                "tolerance_abs_kpa": f"{tolerance_abs_kpa:.12g}",
                "tolerance_rel": "0.5",
                "source_basis": source_basis,
            }
        )
        details.append(
            {
                "metric_id": metric_id,
                "channel_id": int(channel_id),
                "channel_name": channel["name"],
                "reference_overpressure_bar": peak_bar,
                "reference_overpressure_kpa": peak_kpa,
                "peak_time_ms": finite_positive(
                    channel["peak_overpressure_baseline_corrected_time_ms"],
                    f"channel {channel_id} peak time ms",
                ),
                "pretrigger_baseline_v": channel["pretrigger_baseline_v"],
                "distance_m_is_obstacle_distance_not_sensor_distance": True,
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
    exp002: dict[str, Any],
    bridge: dict[str, Any],
    rows: list[dict[str, str]],
    channel_details: list[dict[str, Any]],
    metadata_path: Path,
    channels_path: Path,
) -> None:
    exp_row = exp002["experiment_matrix_row"]
    metadata = {
        "schema_version": 1,
        "dataset_type": "h2_fire_exp002_overpressure_calibration_partial",
        "case": "DataverseNO EXP002 hydrogen delayed ignition overpressure",
        "source_type": "experimental_public_dataverse",
        "source": {
            "title": "Hydrogen jet fire/delayed ignition overpressure EXP002",
            "doi": exp002["summary"]["source_dataset_doi"],
            "file": exp002["summary"]["source_csv_filename"],
            "source_csv_md5_matches_dataverse": exp002["summary"]["source_csv_md5_matches_dataverse"],
        },
        "case_parameters": {
            "avg_mfr_kg_s": exp_row["Avg MFR [kg/s]"],
            "max_mfr_kg_s": exp_row["Max MFR [kg/s]"],
            "h2_release_time_s": exp_row["H2 release time [s]"],
            "ignition_delay_time_s": exp_row["Ignition delay time [s]"],
            "obstacle_distance_from_nozzle_m": exp_row["Obstacle distance from the nozzle [cm]"] / 100.0,
            "ignition_place": exp_row["Ignition place"],
        },
        "bridge_evidence": {
            "status": bridge["status"],
            "timed_ignition_energy_conservation_ready": bridge["checks"]["cuda_energy_conservation_pass"]
            and bridge["checks"]["cpu_mpi_energy_conservation_pass"],
            "cpu_gpu_delayed_ignition_parity_ready": bridge["checks"]["cpu_gpu_delayed_ignition_parity_pass"],
        },
        "strict_credit": {
            "clears_fire_consequence_blocker": False,
            "reason": "Overpressure targets are repository-formatted, but CFD pressure-sensor agreement and radiation calibration are not complete.",
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    channels_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "row_count": len(rows),
                "csv_columns": list(CSV_COLUMNS),
                "channel_targets": channel_details,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    exp002 = load_json(Path(args.exp002_reduced))
    bridge = load_json(Path(args.exp002_bridge))
    metadata_report = load_json(Path(args.metadata_report))
    require(metadata_report.get("status") == "PASS-H2-FIRE-OVERPRESSURE-DATAVERSE-METADATA", "metadata report not ready")

    rows, channel_details = build_rows(exp002, bridge)
    out_csv = Path(args.output_csv)
    out_metadata = Path(args.output_metadata)
    out_channels = Path(args.output_channels)
    write_csv(rows, out_csv)
    write_sidecars(exp002, bridge, rows, channel_details, out_metadata, out_channels)

    values = [finite_positive(row["reference_overpressure_kpa"], row["metric_id"]) for row in rows]
    report = {
        "schema_version": SCHEMA_VERSION,
        "title": "H2 Fire EXP002 Overpressure Calibration Table",
        "status": STATUS_PASS,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "overpressure_metrics_csv_ready": True,
            "overpressure_metric_count": len(rows),
            "csv_columns": list(CSV_COLUMNS),
            "reference_overpressure_kpa_range": [min(values), max(values)],
            "max_tolerance_rel": max(float(row["tolerance_rel"]) for row in rows),
            "source_csv_md5_matches_dataverse": exp002["summary"]["source_csv_md5_matches_dataverse"],
            "exp002_peak_corrected_overpressure_bar": exp002["summary"]["peak_corrected_overpressure_bar"],
            "distance_m_field_is_obstacle_distance_not_sensor_distance": True,
            "strict_fire_calibration_blocker_cleared": False,
            "ready_for_cfd_pressure_sensor_comparison": True,
            "ready_for_full_fire_calibration_ingestion": False,
        },
        "limitations": [
            "This table promotes EXP002 measured overpressure targets into the repository schema; it does not include CFD pressure-sensor agreement.",
            "distance_m records the known nozzle-to-obstacle distance because sensor coordinates are not yet mapped.",
            "Radiation calibration metrics are still absent, so strict fire-consequence credit remains blocked.",
        ],
        "output_files": {
            "overpressure_metrics_csv": str(out_csv),
            "partial_metadata_json": str(out_metadata),
            "channel_targets_json": str(out_channels),
        },
        "evidence_files": [
            evidence_entry("exp002_reduced_report", Path(args.exp002_reduced)),
            evidence_entry("exp002_delayed_ignition_bridge", Path(args.exp002_bridge)),
            evidence_entry("metadata_report", Path(args.metadata_report)),
            evidence_entry("overpressure_metrics_csv", out_csv),
            evidence_entry("partial_metadata_json", out_metadata),
            evidence_entry("channel_targets_json", out_channels),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_csv(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"missing overpressure CSV: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    require(len(rows) == 4, f"expected four EXP002 pressure rows, got {len(rows)}")
    require(all(col in rows[0] for col in CSV_COLUMNS), "overpressure CSV missing required columns")
    metric_ids = set()
    for row in rows:
        metric_id = row["metric_id"].strip()
        require(metric_id and metric_id not in metric_ids, f"invalid duplicate metric id {metric_id!r}")
        metric_ids.add(metric_id)
        finite_positive(row["distance_m"], f"{metric_id} distance_m")
        finite_positive(row["reference_overpressure_kpa"], f"{metric_id} reference_overpressure_kpa")
        finite_positive(row["tolerance_abs_kpa"], f"{metric_id} tolerance_abs_kpa")
        tol_rel = finite_positive(row["tolerance_rel"], f"{metric_id} tolerance_rel")
        require(tol_rel <= 0.75, f"{metric_id} tolerance_rel too wide")
        require(row["source_basis"].strip(), f"{metric_id} missing source_basis")
    return rows


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch")
    require(data.get("status") == STATUS_PASS, f"status is not pass: {data.get('status')}")
    summary = data.get("summary")
    require(isinstance(summary, dict), "summary missing")
    require(summary.get("overpressure_metrics_csv_ready") is True, "overpressure CSV not ready")
    require(summary.get("overpressure_metric_count") == 4, "metric count mismatch")
    require(summary.get("source_csv_md5_matches_dataverse") is True, "source CSV MD5 not verified")
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "strict fire blocker overclaimed")
    require(summary.get("ready_for_cfd_pressure_sensor_comparison") is True, "CFD comparison readiness missing")
    require(summary.get("ready_for_full_fire_calibration_ingestion") is False, "full ingestion overclaimed")
    csv_path = Path(data["output_files"]["overpressure_metrics_csv"])
    rows = validate_csv(csv_path)
    peak_kpa = max(float(row["reference_overpressure_kpa"]) for row in rows)
    require(
        math.isclose(peak_kpa / 100.0, float(summary["exp002_peak_corrected_overpressure_bar"]), rel_tol=1.0e-12),
        "CSV peak does not match EXP002 reduced report peak",
    )
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# H2 Fire EXP002 Overpressure Calibration Table",
        "",
        f"- Status: `{report['status']}`",
        f"- Overpressure metrics: `{s['overpressure_metric_count']}`",
        f"- Reference overpressure range kPa: `{s['reference_overpressure_kpa_range']}`",
        f"- Strict fire calibration blocker cleared: `{s['strict_fire_calibration_blocker_cleared']}`",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in report["limitations"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exp002-reduced", default=str(EXP002_REDUCED))
    parser.add_argument("--exp002-bridge", default=str(EXP002_BRIDGE))
    parser.add_argument("--metadata-report", default=str(METADATA_REPORT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--output-metadata", default=str(DEFAULT_OUTPUT_METADATA))
    parser.add_argument("--output-channels", default=str(DEFAULT_OUTPUT_CHANNELS))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"h2_fire_exp002_overpressure_calibration_table VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"h2_fire_exp002_overpressure_calibration_table PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
