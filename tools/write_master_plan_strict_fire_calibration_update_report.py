#!/usr/bin/env python3
"""Write/verify strict master-plan fire calibration blocker update evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_TRIAGED = "TRIAGED-MASTER-PLAN-STRICT-FIRE-CALIBRATION-PARTIAL-DATA-BRIDGED"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "master_plan_strict_fire_calibration_update_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "master_plan_strict_fire_calibration_update_report.md"
DEFAULT_TRACEABILITY = Path(
    "docs/codex_audit/evidence/engineering_h2_master_plan_traceability_20260724/"
    "h2_master_plan_traceability_report.json"
)
DEFAULT_PUBLIC_TRIAGE = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_calibration_public_source_triage_20260724/"
    "fire_calibration_public_source_triage_report.json"
)
DEFAULT_INGESTION = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/"
    "fire_calibration_dataset_ingestion_report.json"
)
DEFAULT_DIGITIZATION = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/"
    "fire_calibration_digitization_preflight_report.json"
)
DEFAULT_LITERATURE = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_calibration_literature_metric_preflight_20260724/"
    "fire_calibration_literature_metric_preflight_report.json"
)
DEFAULT_PACKAGE = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_calibration_package_20260723/"
    "fire_calibration_package_report.json"
)
DEFAULT_DATASET = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_20260723/"
    "fire_calibration_dataset_report.json"
)
DEFAULT_CANDIDATES_20260805 = Path(
    "docs/codex_audit/evidence/h2_fire_calibration_candidate_sources_20260805/"
    "h2_fire_calibration_candidate_sources_report.json"
)
DEFAULT_EXP002_REDUCED = Path(
    "docs/codex_audit/evidence/h2_fire_overpressure_reduced_exp002_20260805/"
    "h2_fire_overpressure_reduced_exp002_report.json"
)
DEFAULT_EXP002_BRIDGE = Path(
    "docs/codex_audit/evidence/engineering_h2_fire_exp002_delayed_ignition_bridge_20260805/"
    "engineering_h2_fire_exp002_delayed_ignition_bridge_report.json"
)
DEFAULT_EXP002_OVERPRESSURE_TABLE = Path(
    "docs/codex_audit/evidence/h2_fire_exp002_overpressure_calibration_table_20260805/"
    "h2_fire_exp002_overpressure_calibration_table_report.json"
)
DEFAULT_EXP002_PRESSURE_CONTRACT = Path(
    "docs/codex_audit/evidence/h2_fire_exp002_pressure_comparison_contract_20260805/"
    "h2_fire_exp002_pressure_comparison_contract_report.json"
)
DEFAULT_EXP002_PRESSURE_CFD_PROXY = Path(
    "docs/codex_audit/evidence/h2_fire_exp002_pressure_cfd_proxy_20260805/"
    "h2_fire_exp002_pressure_cfd_proxy_report.json"
)
DEFAULT_PLOTFILE_SENSOR_SAMPLING_CONTRACT = Path(
    "docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_contract_20260807/"
    "h2_fire_plotfile_sensor_sampling_contract_report.json"
)
DEFAULT_PLOTFILE_SENSOR_SAMPLING_NEGATIVE_SELFTEST = Path(
    "docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/"
    "h2_fire_plotfile_sensor_sampling_negative_selftest_report.json"
)
DEFAULT_MDPI_RADIATION_TABLE = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_calibration_table_20260805/"
    "h2_fire_mdpi_radiation_calibration_table_report.json"
)
DEFAULT_MDPI_RADIATION_CONTRACT = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_comparison_contract_20260805/"
    "h2_fire_mdpi_radiation_comparison_contract_report.json"
)
DEFAULT_MDPI_RADIATION_SCREENING_COMPARISON = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_screening_comparison_20260805/"
    "h2_fire_mdpi_radiation_screening_comparison_report.json"
)
DEFAULT_MDPI_RADIATION_CFD_PROXY = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_cfd_proxy_20260805/"
    "h2_fire_mdpi_radiation_cfd_proxy_report.json"
)
DEFAULT_MDPI_RADIATION_INTEGRATED_CFD_PROXY = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_integrated_cfd_proxy_20260807/"
    "h2_fire_mdpi_radiation_integrated_cfd_proxy_report.json"
)


class StrictFireError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise StrictFireError(message)


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
        raise StrictFireError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StrictFireError(f"invalid JSON evidence {path}: {exc}") from exc
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
        "public_triage": Path(args.public_triage),
        "ingestion": Path(args.ingestion),
        "digitization": Path(args.digitization),
        "literature": Path(args.literature),
        "package": Path(args.package),
        "dataset": Path(args.dataset),
        "candidate_sources_20260805": Path(args.candidate_sources_20260805),
        "exp002_reduced_overpressure": Path(args.exp002_reduced),
        "exp002_delayed_ignition_bridge": Path(args.exp002_bridge),
        "exp002_overpressure_calibration_table": Path(args.exp002_overpressure_table),
        "exp002_pressure_comparison_contract": Path(args.exp002_pressure_contract),
        "exp002_pressure_cfd_proxy": Path(args.exp002_pressure_cfd_proxy),
        "plotfile_sensor_sampling_contract": Path(args.plotfile_sensor_sampling_contract),
        "plotfile_sensor_sampling_negative_selftest": Path(args.plotfile_sensor_sampling_negative_selftest),
        "mdpi_radiation_calibration_table": Path(args.mdpi_radiation_table),
        "mdpi_radiation_comparison_contract": Path(args.mdpi_radiation_contract),
        "mdpi_radiation_screening_comparison": Path(args.mdpi_radiation_screening_comparison),
        "mdpi_radiation_cfd_proxy": Path(args.mdpi_radiation_cfd_proxy),
        "mdpi_radiation_integrated_cfd_proxy": Path(args.mdpi_radiation_integrated_cfd_proxy),
    }
    reports = {name: load_json(path) for name, path in paths.items()}
    blockers = reports["traceability"].get("remaining_blockers", [])
    blocker_names = [b.get("blocker") for b in blockers if isinstance(b, dict)]
    fire_blocker_present = (
        "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure" in blocker_names
    )
    public_summary = reports["public_triage"].get("summary", {}) if isinstance(reports["public_triage"].get("summary"), dict) else {}
    digitization_summary = reports["digitization"].get("summary", {}) if isinstance(reports["digitization"].get("summary"), dict) else {}
    literature_summary = reports["literature"].get("summary", {}) if isinstance(reports["literature"].get("summary"), dict) else {}
    candidate_summary = (
        reports["candidate_sources_20260805"].get("summary", {})
        if isinstance(reports["candidate_sources_20260805"].get("summary"), dict)
        else {}
    )
    exp002_summary = (
        reports["exp002_reduced_overpressure"].get("summary", {})
        if isinstance(reports["exp002_reduced_overpressure"].get("summary"), dict)
        else {}
    )
    bridge_checks = (
        reports["exp002_delayed_ignition_bridge"].get("checks", {})
        if isinstance(reports["exp002_delayed_ignition_bridge"].get("checks"), dict)
        else {}
    )
    bridge_targets = (
        reports["exp002_delayed_ignition_bridge"].get("exp002_targets", {})
        if isinstance(reports["exp002_delayed_ignition_bridge"].get("exp002_targets"), dict)
        else {}
    )
    overpressure_table_summary = (
        reports["exp002_overpressure_calibration_table"].get("summary", {})
        if isinstance(reports["exp002_overpressure_calibration_table"].get("summary"), dict)
        else {}
    )
    pressure_contract_summary = (
        reports["exp002_pressure_comparison_contract"].get("summary", {})
        if isinstance(reports["exp002_pressure_comparison_contract"].get("summary"), dict)
        else {}
    )
    pressure_cfd_proxy_summary = (
        reports["exp002_pressure_cfd_proxy"].get("summary", {})
        if isinstance(reports["exp002_pressure_cfd_proxy"].get("summary"), dict)
        else {}
    )
    sensor_sampling_summary = (
        reports["plotfile_sensor_sampling_contract"].get("summary", {})
        if isinstance(reports["plotfile_sensor_sampling_contract"].get("summary"), dict)
        else {}
    )
    sensor_sampling_negative_summary = (
        reports["plotfile_sensor_sampling_negative_selftest"].get("summary", {})
        if isinstance(reports["plotfile_sensor_sampling_negative_selftest"].get("summary"), dict)
        else {}
    )
    radiation_table_summary = (
        reports["mdpi_radiation_calibration_table"].get("summary", {})
        if isinstance(reports["mdpi_radiation_calibration_table"].get("summary"), dict)
        else {}
    )
    radiation_contract_summary = (
        reports["mdpi_radiation_comparison_contract"].get("summary", {})
        if isinstance(reports["mdpi_radiation_comparison_contract"].get("summary"), dict)
        else {}
    )
    radiation_screening_summary = (
        reports["mdpi_radiation_screening_comparison"].get("summary", {})
        if isinstance(reports["mdpi_radiation_screening_comparison"].get("summary"), dict)
        else {}
    )
    radiation_cfd_proxy_summary = (
        reports["mdpi_radiation_cfd_proxy"].get("summary", {})
        if isinstance(reports["mdpi_radiation_cfd_proxy"].get("summary"), dict)
        else {}
    )
    radiation_integrated_proxy_summary = (
        reports["mdpi_radiation_integrated_cfd_proxy"].get("summary", {})
        if isinstance(reports["mdpi_radiation_integrated_cfd_proxy"].get("summary"), dict)
        else {}
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_TRIAGED,
        "summary": {
            "fire_calibration_blocker_present": fire_blocker_present,
            "public_source_triage_status": reports["public_triage"].get("status"),
            "dataset_ingestion_status": reports["ingestion"].get("status"),
            "digitization_preflight_status": reports["digitization"].get("status"),
            "literature_metric_preflight_status": reports["literature"].get("status"),
            "calibration_package_status": reports["package"].get("status"),
            "calibration_dataset_status": reports["dataset"].get("status"),
            "radiation_candidate_available": public_summary.get("radiation_candidate_available"),
            "overpressure_candidate_available": public_summary.get("overpressure_candidate_available"),
            "candidate_sources_20260805_status": reports["candidate_sources_20260805"].get("status"),
            "candidate_sources_20260805_radiation_available": candidate_summary.get("radiation_candidate_available"),
            "candidate_sources_20260805_overpressure_available": candidate_summary.get("overpressure_candidate_available"),
            "candidate_sources_20260805_both_metric_families_available": candidate_summary.get("both_metric_families_have_public_candidates"),
            "candidate_sources_20260805_repository_package_ready": candidate_summary.get("repository_ingestable_calibration_package_ready"),
            "exp002_reduced_overpressure_status": reports["exp002_reduced_overpressure"].get("status"),
            "exp002_source_csv_md5_verified": exp002_summary.get("source_csv_md5_matches_dataverse"),
            "exp002_pressure_channel_count": exp002_summary.get("pressure_channel_count"),
            "exp002_peak_corrected_overpressure_bar": exp002_summary.get("peak_corrected_overpressure_bar"),
            "exp002_ready_for_reduced_validation_case": exp002_summary.get("ready_for_reduced_validation_case"),
            "exp002_delayed_ignition_bridge_status": reports["exp002_delayed_ignition_bridge"].get("status"),
            "exp002_bridge_energy_conservation_ready": (
                bridge_checks.get("cuda_energy_conservation_pass") is True
                and bridge_checks.get("cpu_mpi_energy_conservation_pass") is True
            ),
            "exp002_bridge_cpu_gpu_parity_ready": bridge_checks.get("cpu_gpu_delayed_ignition_parity_pass"),
            "exp002_bridge_pressure_targets_available": bridge_checks.get("pressure_targets_available"),
            "exp002_bridge_ignition_delay_time_s": bridge_targets.get("ignition_delay_time_s"),
            "exp002_bridge_obstacle_distance_from_nozzle_m": bridge_targets.get("obstacle_distance_from_nozzle_m"),
            "exp002_overpressure_calibration_table_status": reports["exp002_overpressure_calibration_table"].get("status"),
            "exp002_overpressure_metric_count": overpressure_table_summary.get("overpressure_metric_count"),
            "exp002_overpressure_metrics_csv_ready": overpressure_table_summary.get("overpressure_metrics_csv_ready"),
            "exp002_overpressure_table_ready_for_cfd_pressure_sensor_comparison": overpressure_table_summary.get(
                "ready_for_cfd_pressure_sensor_comparison"
            ),
            "exp002_overpressure_table_ready_for_full_fire_calibration_ingestion": overpressure_table_summary.get(
                "ready_for_full_fire_calibration_ingestion"
            ),
            "exp002_pressure_comparison_contract_status": reports["exp002_pressure_comparison_contract"].get("status"),
            "exp002_pressure_comparison_contract_ready": pressure_contract_summary.get(
                "pressure_comparison_contract_ready"
            ),
            "exp002_cfd_pressure_sensor_comparison_executed": pressure_contract_summary.get(
                "current_cfd_pressure_sensor_comparison_executed"
            ),
            "exp002_cfd_outputs_sufficient_for_pressure_agreement": pressure_contract_summary.get(
                "current_outputs_sufficient_for_exp002_pressure_agreement"
            ),
            "exp002_pressure_cfd_proxy_status": reports["exp002_pressure_cfd_proxy"].get("status"),
            "exp002_pressure_cfd_proxy_extracted": pressure_cfd_proxy_summary.get("pressure_proxy_extracted"),
            "exp002_pressure_cfd_proxy_cpu_gpu_parity_passed": pressure_cfd_proxy_summary.get(
                "cpu_gpu_pressure_proxy_parity_passed"
            ),
            "exp002_pressure_cfd_proxy_cpu_gpu_rel_diff": pressure_cfd_proxy_summary.get(
                "cpu_gpu_peak_abs_pressure_rel_diff"
            ),
            "exp002_pressure_cfd_proxy_case_aligned_agreement": pressure_cfd_proxy_summary.get(
                "case_aligned_pressure_sensor_agreement"
            ),
            "plotfile_sensor_sampling_contract_status": reports["plotfile_sensor_sampling_contract"].get("status"),
            "plotfile_sensor_sampling_contract_ready": sensor_sampling_summary.get(
                "plotfile_sensor_sampling_contract_ready"
            ),
            "plotfile_sensor_sampling_pressure_timeseries_path_ready": sensor_sampling_summary.get(
                "pressure_sensor_timeseries_path_ready"
            ),
            "plotfile_sensor_sampling_uses_synthetic_sensor_coordinates": sensor_sampling_summary.get(
                "uses_synthetic_sensor_coordinates"
            ),
            "plotfile_sensor_sampling_sampling_mode": sensor_sampling_summary.get("sampling_mode"),
            "plotfile_sensor_sampling_linear_interpolation_used": sensor_sampling_summary.get(
                "linear_interpolation_used"
            ),
            "plotfile_sensor_sampling_uses_non_cell_center_sensor_coordinates": sensor_sampling_summary.get(
                "uses_non_cell_center_sensor_coordinates"
            ),
            "plotfile_sensor_sampling_row_count": sensor_sampling_summary.get("row_count"),
            "plotfile_sensor_sampling_current_outputs_sufficient_for_exp002_pressure_agreement": sensor_sampling_summary.get(
                "current_outputs_sufficient_for_exp002_pressure_agreement"
            ),
            "plotfile_sensor_sampling_case_aligned_pressure_sensor_agreement": sensor_sampling_summary.get(
                "case_aligned_pressure_sensor_agreement"
            ),
            "plotfile_sensor_sampling_strict_fire_calibration_blocker_cleared": sensor_sampling_summary.get(
                "strict_fire_calibration_blocker_cleared"
            ),
            "plotfile_sensor_sampling_negative_selftest_status": reports[
                "plotfile_sensor_sampling_negative_selftest"
            ].get("status"),
            "plotfile_sensor_sampling_negative_selftest_ready": sensor_sampling_negative_summary.get(
                "negative_selftest_ready"
            ),
            "plotfile_sensor_sampling_negative_case_count": sensor_sampling_negative_summary.get(
                "negative_case_count"
            ),
            "plotfile_sensor_sampling_negative_refused_count": sensor_sampling_negative_summary.get(
                "negative_refused_count"
            ),
            "plotfile_sensor_sampling_negative_failed_count": sensor_sampling_negative_summary.get(
                "failed_negative_count"
            ),
            "plotfile_sensor_sampling_negative_strict_fire_calibration_blocker_cleared": sensor_sampling_negative_summary.get(
                "strict_fire_calibration_blocker_cleared"
            ),
            "mdpi_radiation_calibration_table_status": reports["mdpi_radiation_calibration_table"].get("status"),
            "mdpi_radiation_metric_count": radiation_table_summary.get("radiation_metric_count"),
            "mdpi_radiation_metrics_csv_ready": radiation_table_summary.get("radiation_metrics_csv_ready"),
            "mdpi_radiation_table_ready_for_cfd_radiation_comparison": radiation_table_summary.get(
                "ready_for_cfd_radiation_comparison"
            ),
            "mdpi_radiation_table_ready_for_full_fire_calibration_ingestion": radiation_table_summary.get(
                "ready_for_full_fire_calibration_ingestion"
            ),
            "mdpi_radiation_comparison_contract_status": reports["mdpi_radiation_comparison_contract"].get("status"),
            "mdpi_radiation_comparison_contract_ready": radiation_contract_summary.get(
                "radiation_comparison_contract_ready"
            ),
            "mdpi_cfd_radiation_comparison_executed": radiation_contract_summary.get(
                "current_cfd_radiation_comparison_executed"
            ),
            "mdpi_cfd_outputs_sufficient_for_radiation_agreement": radiation_contract_summary.get(
                "current_outputs_sufficient_for_mdpi_radiation_agreement"
            ),
            "mdpi_radiation_screening_comparison_status": reports["mdpi_radiation_screening_comparison"].get("status"),
            "mdpi_radiation_screening_comparison_executed": radiation_screening_summary.get(
                "screening_comparison_executed"
            ),
            "mdpi_radiation_screening_metric_pass_count": radiation_screening_summary.get(
                "screening_metric_pass_count"
            ),
            "mdpi_radiation_screening_metric_fail_count": radiation_screening_summary.get(
                "screening_metric_fail_count"
            ),
            "mdpi_radiation_screening_all_metrics_passed": radiation_screening_summary.get(
                "all_screening_metrics_passed"
            ),
            "mdpi_radiation_screening_min_source_reference_ratio": radiation_screening_summary.get(
                "min_source_limited_to_reference_ratio"
            ),
            "mdpi_radiation_screening_max_source_reference_ratio": radiation_screening_summary.get(
                "max_source_limited_to_reference_ratio"
            ),
            "mdpi_radiation_cfd_proxy_status": reports["mdpi_radiation_cfd_proxy"].get("status"),
            "mdpi_radiation_cfd_proxy_extracted": radiation_cfd_proxy_summary.get("cfd_proxy_extracted"),
            "mdpi_radiation_cfd_proxy_cpu_gpu_parity_passed": radiation_cfd_proxy_summary.get(
                "cpu_gpu_proxy_parity_passed"
            ),
            "mdpi_radiation_cfd_proxy_cpu_gpu_rel_diff": radiation_cfd_proxy_summary.get(
                "cpu_gpu_proxy_radiative_power_rel_diff"
            ),
            "mdpi_radiation_cfd_proxy_agreement_fail_count": radiation_cfd_proxy_summary.get(
                "proxy_agreement_fail_count"
            ),
            "mdpi_radiation_integrated_cfd_proxy_status": reports["mdpi_radiation_integrated_cfd_proxy"].get("status"),
            "mdpi_radiation_integrated_cfd_proxy_extracted": radiation_integrated_proxy_summary.get(
                "integrated_cfd_proxy_extracted"
            ),
            "mdpi_radiation_integrated_cfd_proxy_plotfile_count": radiation_integrated_proxy_summary.get(
                "plotfile_count"
            ),
            "mdpi_radiation_integrated_cfd_proxy_virtual_radiometer_flux_generated": radiation_integrated_proxy_summary.get(
                "virtual_radiometer_flux_generated"
            ),
            "mdpi_radiation_integrated_cfd_proxy_peak_radiative_power_w": radiation_integrated_proxy_summary.get(
                "peak_integrated_radiative_power_w"
            ),
            "mdpi_radiation_integrated_cfd_proxy_agreement_fail_count": radiation_integrated_proxy_summary.get(
                "agreement_fail_count"
            ),
            "mdpi_radiation_integrated_cfd_proxy_case_aligned_agreement": radiation_integrated_proxy_summary.get(
                "case_aligned_cfd_radiation_agreement"
            ),
            "mdpi_radiation_integrated_cfd_proxy_outputs_sufficient_for_mdpi_agreement": radiation_integrated_proxy_summary.get(
                "current_outputs_sufficient_for_mdpi_radiation_agreement"
            ),
            "mdpi_radiation_integrated_cfd_proxy_strict_fire_calibration_blocker_cleared": radiation_integrated_proxy_summary.get(
                "strict_fire_calibration_blocker_cleared"
            ),
            "radiation_metric_anchor_available": literature_summary.get("radiation_metric_anchor_available"),
            "overpressure_metric_anchor_available": literature_summary.get("overpressure_metric_anchor_available"),
            "radiation_metrics_available": digitization_summary.get("radiation_metrics_available"),
            "overpressure_metrics_available": digitization_summary.get("overpressure_metrics_available"),
            "strict_fire_calibration_blocker_cleared": False,
            "strict_fire_calibration_next_actions": [
                "Replace the synthetic plotfile sensor-sampling CSV with exact EXP002 sensor coordinates once available.",
                "Run a case-aligned CFD radiation comparison against the MDPI radiation target table.",
                "Run an EXP002-aligned CFD pressure-sensor comparison and require peak overpressure plus arrival-time acceptance before clearing strict fire credit.",
                "Run the existing dataset ingestion, package, dataset builder, production scorecard, and master-plan traceability reports after calibrated tables exist.",
            ],
        },
        "missing_for_strict_credit": [
            "CFD radiation comparison against MDPI heat-flux targets",
            "exact EXP002 sensor coordinates plus CFD pressure-sensor comparison against EXP002 peak overpressure and arrival time",
            "case alignment records linking measurements to simulated engineering scenarios",
            "uncertainty/provenance fields sufficient for calibrated radiation and overpressure agreement",
        ],
        "evidence_files": [evidence_entry(name, path) for name, path in paths.items()],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_TRIAGED, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("fire_calibration_blocker_present") is True, "fire calibration blocker not detected")
    require(summary.get("public_source_triage_status") == "PASS-H2-FIRE-CALIBRATION-PUBLIC-SOURCE-TRIAGE", "public triage not ready")
    require(summary.get("digitization_preflight_status") == "PASS-H2-FIRE-CALIBRATION-DIGITIZATION-PREFLIGHT", "digitization preflight not ready")
    require(
        summary.get("literature_metric_preflight_status") == "PASS-H2-FIRE-CALIBRATION-LITERATURE-METRIC-PREFLIGHT",
        "literature metric preflight not ready",
    )
    require(
        summary.get("dataset_ingestion_status") == "NOT_READY-H2-FIRE-CALIBRATION-DATASET-INGESTION",
        "dataset ingestion status changed",
    )
    require(summary.get("calibration_package_status") == "NOT_READY-H2-FIRE-CALIBRATION-PACKAGE", "package status changed")
    require(summary.get("calibration_dataset_status") == "NOT_READY-H2-FIRE-CALIBRATION-DATASET", "dataset status changed")
    require(summary.get("radiation_candidate_available") is True, "radiation source candidate missing")
    require(summary.get("overpressure_candidate_available") is True, "overpressure source candidate missing")
    require(
        summary.get("candidate_sources_20260805_status") == "PASS-H2-FIRE-CALIBRATION-CANDIDATE-SOURCES-20260805",
        "2026 candidate source report not ready",
    )
    require(
        summary.get("candidate_sources_20260805_both_metric_families_available") is True,
        "2026 candidate source report does not cover both metric families",
    )
    require(
        summary.get("candidate_sources_20260805_repository_package_ready") is False,
        "2026 candidate source report should not claim repository package readiness",
    )
    require(
        summary.get("exp002_reduced_overpressure_status") == "PASS-H2-FIRE-OVERPRESSURE-REDUCED-EXP002",
        "EXP002 reduced overpressure report not ready",
    )
    require(summary.get("exp002_source_csv_md5_verified") is True, "EXP002 source CSV MD5 not verified")
    require(summary.get("exp002_pressure_channel_count") == 4, "EXP002 pressure channel count mismatch")
    require(
        isinstance(summary.get("exp002_peak_corrected_overpressure_bar"), (int, float))
        and summary.get("exp002_peak_corrected_overpressure_bar") > 0.0,
        "EXP002 peak corrected overpressure missing",
    )
    require(
        summary.get("exp002_ready_for_reduced_validation_case") is True,
        "EXP002 is not ready for reduced validation case",
    )
    require(
        summary.get("exp002_delayed_ignition_bridge_status")
        == "PASS-H2-FIRE-EXP002-DELAYED-IGNITION-BRIDGE",
        "EXP002 delayed ignition bridge not ready",
    )
    require(summary.get("exp002_bridge_energy_conservation_ready") is True, "EXP002 bridge energy not ready")
    require(summary.get("exp002_bridge_cpu_gpu_parity_ready") is True, "EXP002 bridge CPU/GPU parity not ready")
    require(summary.get("exp002_bridge_pressure_targets_available") is True, "EXP002 bridge pressure targets missing")
    require(
        summary.get("exp002_overpressure_calibration_table_status")
        == "PASS-H2-FIRE-EXP002-OVERPRESSURE-CALIBRATION-TABLE",
        "EXP002 overpressure calibration table not ready",
    )
    require(summary.get("exp002_overpressure_metric_count") == 4, "EXP002 overpressure metric count mismatch")
    require(summary.get("exp002_overpressure_metrics_csv_ready") is True, "EXP002 overpressure CSV not ready")
    require(
        summary.get("exp002_overpressure_table_ready_for_cfd_pressure_sensor_comparison") is True,
        "EXP002 overpressure table not ready for CFD comparison",
    )
    require(
        summary.get("exp002_overpressure_table_ready_for_full_fire_calibration_ingestion") is False,
        "EXP002 overpressure table overclaimed full ingestion readiness",
    )
    require(
        summary.get("exp002_pressure_comparison_contract_status")
        == "PASS-H2-FIRE-EXP002-PRESSURE-COMPARISON-CONTRACT",
        "EXP002 pressure comparison contract not ready",
    )
    require(
        summary.get("exp002_pressure_comparison_contract_ready") is True,
        "EXP002 pressure comparison contract ready flag missing",
    )
    require(
        summary.get("exp002_cfd_pressure_sensor_comparison_executed") is False,
        "EXP002 CFD pressure comparison overclaimed",
    )
    require(
        summary.get("exp002_cfd_outputs_sufficient_for_pressure_agreement") is False,
        "EXP002 CFD pressure output sufficiency overclaimed",
    )
    require(
        summary.get("exp002_pressure_cfd_proxy_status") == "PASS-H2-FIRE-EXP002-PRESSURE-CFD-PROXY",
        "EXP002 pressure CFD proxy not ready",
    )
    require(summary.get("exp002_pressure_cfd_proxy_extracted") is True, "EXP002 pressure CFD proxy not extracted")
    require(
        summary.get("exp002_pressure_cfd_proxy_cpu_gpu_parity_passed") is True,
        "EXP002 pressure CFD proxy CPU/GPU parity failed",
    )
    require(
        summary.get("exp002_pressure_cfd_proxy_case_aligned_agreement") is False,
        "EXP002 pressure CFD proxy overclaimed case-aligned agreement",
    )
    require(
        summary.get("plotfile_sensor_sampling_contract_status") == "PASS-H2-FIRE-PLOTFILE-SENSOR-SAMPLING-CONTRACT",
        "plotfile sensor sampling contract not ready",
    )
    require(
        summary.get("plotfile_sensor_sampling_contract_ready") is True,
        "plotfile sensor sampling ready flag missing",
    )
    require(
        summary.get("plotfile_sensor_sampling_pressure_timeseries_path_ready") is True,
        "plotfile pressure time-series extraction path missing",
    )
    require(
        summary.get("plotfile_sensor_sampling_uses_synthetic_sensor_coordinates") is True,
        "plotfile sensor sampling must disclose synthetic sensor coordinates",
    )
    require(summary.get("plotfile_sensor_sampling_sampling_mode") == "linear", "plotfile sensor sampling mode changed")
    require(
        summary.get("plotfile_sensor_sampling_linear_interpolation_used") is True,
        "plotfile sensor sampling did not exercise linear interpolation",
    )
    require(
        summary.get("plotfile_sensor_sampling_uses_non_cell_center_sensor_coordinates") is True,
        "plotfile sensor sampling did not exercise non-cell-center coordinates",
    )
    require(summary.get("plotfile_sensor_sampling_row_count") == 8, "plotfile sensor sampling row count changed")
    require(
        summary.get("plotfile_sensor_sampling_current_outputs_sufficient_for_exp002_pressure_agreement") is False,
        "plotfile sensor sampling overclaimed EXP002 pressure output sufficiency",
    )
    require(
        summary.get("plotfile_sensor_sampling_case_aligned_pressure_sensor_agreement") is False,
        "plotfile sensor sampling overclaimed case-aligned pressure agreement",
    )
    require(
        summary.get("plotfile_sensor_sampling_strict_fire_calibration_blocker_cleared") is False,
        "plotfile sensor sampling overclaimed strict blocker clearance",
    )
    require(
        summary.get("plotfile_sensor_sampling_negative_selftest_status")
        == "PASS-H2-FIRE-PLOTFILE-SENSOR-SAMPLING-NEGATIVE-SELFTEST",
        "plotfile sensor sampling negative selftest not ready",
    )
    require(
        summary.get("plotfile_sensor_sampling_negative_selftest_ready") is True,
        "plotfile sensor sampling negative selftest ready flag missing",
    )
    require(summary.get("plotfile_sensor_sampling_negative_case_count") == 8, "negative selftest case count changed")
    require(summary.get("plotfile_sensor_sampling_negative_refused_count") == 8, "not all negative selftest cases refused")
    require(summary.get("plotfile_sensor_sampling_negative_failed_count") == 0, "negative selftest has failing cases")
    require(
        summary.get("plotfile_sensor_sampling_negative_strict_fire_calibration_blocker_cleared") is False,
        "plotfile sensor sampling negative selftest overclaimed strict blocker clearance",
    )
    require(
        summary.get("mdpi_radiation_calibration_table_status")
        == "PASS-H2-FIRE-MDPI-RADIATION-CALIBRATION-TABLE",
        "MDPI radiation calibration table not ready",
    )
    require(summary.get("mdpi_radiation_metric_count") >= 4, "MDPI radiation metric count too small")
    require(summary.get("mdpi_radiation_metrics_csv_ready") is True, "MDPI radiation CSV not ready")
    require(
        summary.get("mdpi_radiation_table_ready_for_cfd_radiation_comparison") is True,
        "MDPI radiation table not ready for CFD radiation comparison",
    )
    require(
        summary.get("mdpi_radiation_table_ready_for_full_fire_calibration_ingestion") is False,
        "MDPI radiation table overclaimed full ingestion readiness",
    )
    require(
        summary.get("mdpi_radiation_comparison_contract_status")
        == "PASS-H2-FIRE-MDPI-RADIATION-COMPARISON-CONTRACT",
        "MDPI radiation comparison contract not ready",
    )
    require(
        summary.get("mdpi_radiation_comparison_contract_ready") is True,
        "MDPI radiation comparison contract ready flag missing",
    )
    require(
        summary.get("mdpi_cfd_radiation_comparison_executed") is False,
        "MDPI CFD radiation comparison overclaimed",
    )
    require(
        summary.get("mdpi_cfd_outputs_sufficient_for_radiation_agreement") is False,
        "MDPI CFD radiation output sufficiency overclaimed",
    )
    require(
        summary.get("mdpi_radiation_screening_comparison_status")
        == "QUANTIFIED-H2-FIRE-MDPI-RADIATION-SCREENING-NOT-PASSING",
        "MDPI radiation screening comparison not quantified",
    )
    require(
        summary.get("mdpi_radiation_screening_comparison_executed") is True,
        "MDPI radiation screening comparison not executed",
    )
    require(
        isinstance(summary.get("mdpi_radiation_screening_metric_fail_count"), int)
        and summary.get("mdpi_radiation_screening_metric_fail_count") >= 1,
        "MDPI radiation screening comparison did not expose any failing metric",
    )
    require(
        summary.get("mdpi_radiation_screening_all_metrics_passed") is False,
        "MDPI radiation screening comparison overclaimed all-pass",
    )
    require(
        summary.get("mdpi_radiation_cfd_proxy_status") == "PASS-H2-FIRE-MDPI-RADIATION-CFD-PROXY",
        "MDPI radiation CFD proxy not ready",
    )
    require(summary.get("mdpi_radiation_cfd_proxy_extracted") is True, "MDPI radiation CFD proxy not extracted")
    require(
        summary.get("mdpi_radiation_cfd_proxy_cpu_gpu_parity_passed") is True,
        "MDPI radiation CFD proxy CPU/GPU parity failed",
    )
    require(
        isinstance(summary.get("mdpi_radiation_cfd_proxy_agreement_fail_count"), int)
        and summary.get("mdpi_radiation_cfd_proxy_agreement_fail_count") >= 4,
        "MDPI radiation CFD proxy should not claim agreement",
    )
    require(
        summary.get("mdpi_radiation_integrated_cfd_proxy_status")
        == "PASS-H2-FIRE-MDPI-RADIATION-INTEGRATED-CFD-PROXY",
        "MDPI integrated radiation CFD proxy not ready",
    )
    require(
        summary.get("mdpi_radiation_integrated_cfd_proxy_extracted") is True,
        "MDPI integrated radiation CFD proxy not extracted",
    )
    require(
        isinstance(summary.get("mdpi_radiation_integrated_cfd_proxy_plotfile_count"), int)
        and summary.get("mdpi_radiation_integrated_cfd_proxy_plotfile_count") >= 3,
        "MDPI integrated radiation CFD proxy plotfile count too small",
    )
    require(
        summary.get("mdpi_radiation_integrated_cfd_proxy_virtual_radiometer_flux_generated") is True,
        "MDPI integrated radiation virtual radiometer flux missing",
    )
    require(
        isinstance(summary.get("mdpi_radiation_integrated_cfd_proxy_peak_radiative_power_w"), (int, float))
        and summary.get("mdpi_radiation_integrated_cfd_proxy_peak_radiative_power_w") > 0.0,
        "MDPI integrated radiation proxy peak power not positive",
    )
    require(
        isinstance(summary.get("mdpi_radiation_integrated_cfd_proxy_agreement_fail_count"), int)
        and summary.get("mdpi_radiation_integrated_cfd_proxy_agreement_fail_count") >= 4,
        "MDPI integrated radiation proxy should not claim agreement",
    )
    require(
        summary.get("mdpi_radiation_integrated_cfd_proxy_case_aligned_agreement") is False,
        "MDPI integrated radiation proxy overclaimed case-aligned agreement",
    )
    require(
        summary.get("mdpi_radiation_integrated_cfd_proxy_outputs_sufficient_for_mdpi_agreement") is False,
        "MDPI integrated radiation proxy overclaimed output sufficiency",
    )
    require(
        summary.get("mdpi_radiation_integrated_cfd_proxy_strict_fire_calibration_blocker_cleared") is False,
        "MDPI integrated radiation proxy overclaimed strict blocker clearance",
    )
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "strict fire blocker must remain open")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Strict Fire Calibration Update",
        "",
        f"- Status: `{report['status']}`",
        f"- Public-source triage: `{s['public_source_triage_status']}`",
        f"- Digitization preflight: `{s['digitization_preflight_status']}`",
        f"- Literature metric preflight: `{s['literature_metric_preflight_status']}`",
        f"- 2026 candidate sources: `{s['candidate_sources_20260805_status']}`",
        f"- EXP002 reduced overpressure: `{s['exp002_reduced_overpressure_status']}`",
        f"- EXP002 delayed-ignition bridge: `{s['exp002_delayed_ignition_bridge_status']}`",
        f"- EXP002 peak corrected overpressure: `{s['exp002_peak_corrected_overpressure_bar']}` bar",
        f"- EXP002 bridge energy conservation ready: `{s['exp002_bridge_energy_conservation_ready']}`",
        f"- EXP002 bridge CPU/GPU parity ready: `{s['exp002_bridge_cpu_gpu_parity_ready']}`",
        f"- EXP002 overpressure calibration table: `{s['exp002_overpressure_calibration_table_status']}`",
        f"- EXP002 overpressure metric count: `{s['exp002_overpressure_metric_count']}`",
        f"- EXP002 pressure comparison contract: `{s['exp002_pressure_comparison_contract_status']}`",
        f"- EXP002 CFD pressure comparison executed: `{s['exp002_cfd_pressure_sensor_comparison_executed']}`",
        f"- EXP002 pressure CFD proxy: `{s['exp002_pressure_cfd_proxy_status']}`",
        f"- EXP002 pressure CFD proxy CPU/GPU parity: `{s['exp002_pressure_cfd_proxy_cpu_gpu_parity_passed']}`",
        f"- Plotfile sensor sampling contract: `{s['plotfile_sensor_sampling_contract_status']}`",
        f"- Plotfile pressure time-series path ready: `{s['plotfile_sensor_sampling_pressure_timeseries_path_ready']}`",
        f"- Plotfile sensor sampling uses synthetic coordinates: `{s['plotfile_sensor_sampling_uses_synthetic_sensor_coordinates']}`",
        f"- Plotfile sensor sampling mode: `{s['plotfile_sensor_sampling_sampling_mode']}`",
        f"- Plotfile sensor sampling linear interpolation: `{s['plotfile_sensor_sampling_linear_interpolation_used']}`",
        f"- Plotfile sensor sampling non-cell-center coordinates: `{s['plotfile_sensor_sampling_uses_non_cell_center_sensor_coordinates']}`",
        f"- Plotfile sensor sampling negative selftest: `{s['plotfile_sensor_sampling_negative_selftest_status']}`",
        f"- Plotfile sensor sampling negative cases refused: `{s['plotfile_sensor_sampling_negative_refused_count']}/{s['plotfile_sensor_sampling_negative_case_count']}`",
        f"- MDPI radiation calibration table: `{s['mdpi_radiation_calibration_table_status']}`",
        f"- MDPI radiation metric count: `{s['mdpi_radiation_metric_count']}`",
        f"- MDPI radiation comparison contract: `{s['mdpi_radiation_comparison_contract_status']}`",
        f"- MDPI CFD radiation comparison executed: `{s['mdpi_cfd_radiation_comparison_executed']}`",
        f"- MDPI radiation screening comparison: `{s['mdpi_radiation_screening_comparison_status']}`",
        f"- MDPI radiation screening pass/fail: `{s['mdpi_radiation_screening_metric_pass_count']}/{s['mdpi_radiation_screening_metric_fail_count']}`",
        f"- MDPI radiation CFD proxy: `{s['mdpi_radiation_cfd_proxy_status']}`",
        f"- MDPI radiation CFD proxy CPU/GPU parity: `{s['mdpi_radiation_cfd_proxy_cpu_gpu_parity_passed']}`",
        f"- MDPI integrated radiation CFD proxy: `{s['mdpi_radiation_integrated_cfd_proxy_status']}`",
        f"- MDPI integrated radiation plotfiles: `{s['mdpi_radiation_integrated_cfd_proxy_plotfile_count']}`",
        f"- MDPI integrated radiation virtual flux generated: `{s['mdpi_radiation_integrated_cfd_proxy_virtual_radiometer_flux_generated']}`",
        f"- Dataset ingestion: `{s['dataset_ingestion_status']}`",
        f"- Package: `{s['calibration_package_status']}`",
        f"- Dataset: `{s['calibration_dataset_status']}`",
        f"- Strict fire calibration blocker cleared: `{s['strict_fire_calibration_blocker_cleared']}`",
        "",
        "## Missing For Strict Credit",
        "",
    ]
    for item in report["missing_for_strict_credit"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Next Actions", ""])
    for item in s["strict_fire_calibration_next_actions"]:
        lines.append(f"- {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traceability", default=str(DEFAULT_TRACEABILITY))
    parser.add_argument("--public-triage", default=str(DEFAULT_PUBLIC_TRIAGE))
    parser.add_argument("--ingestion", default=str(DEFAULT_INGESTION))
    parser.add_argument("--digitization", default=str(DEFAULT_DIGITIZATION))
    parser.add_argument("--literature", default=str(DEFAULT_LITERATURE))
    parser.add_argument("--package", default=str(DEFAULT_PACKAGE))
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--candidate-sources-20260805", default=str(DEFAULT_CANDIDATES_20260805))
    parser.add_argument("--exp002-reduced", default=str(DEFAULT_EXP002_REDUCED))
    parser.add_argument("--exp002-bridge", default=str(DEFAULT_EXP002_BRIDGE))
    parser.add_argument("--exp002-overpressure-table", default=str(DEFAULT_EXP002_OVERPRESSURE_TABLE))
    parser.add_argument("--exp002-pressure-contract", default=str(DEFAULT_EXP002_PRESSURE_CONTRACT))
    parser.add_argument("--exp002-pressure-cfd-proxy", default=str(DEFAULT_EXP002_PRESSURE_CFD_PROXY))
    parser.add_argument("--plotfile-sensor-sampling-contract", default=str(DEFAULT_PLOTFILE_SENSOR_SAMPLING_CONTRACT))
    parser.add_argument("--plotfile-sensor-sampling-negative-selftest", default=str(DEFAULT_PLOTFILE_SENSOR_SAMPLING_NEGATIVE_SELFTEST))
    parser.add_argument("--mdpi-radiation-table", default=str(DEFAULT_MDPI_RADIATION_TABLE))
    parser.add_argument("--mdpi-radiation-contract", default=str(DEFAULT_MDPI_RADIATION_CONTRACT))
    parser.add_argument("--mdpi-radiation-screening-comparison", default=str(DEFAULT_MDPI_RADIATION_SCREENING_COMPARISON))
    parser.add_argument("--mdpi-radiation-cfd-proxy", default=str(DEFAULT_MDPI_RADIATION_CFD_PROXY))
    parser.add_argument("--mdpi-radiation-integrated-cfd-proxy", default=str(DEFAULT_MDPI_RADIATION_INTEGRATED_CFD_PROXY))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"strict_fire_calibration_update VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"strict_fire_calibration_update PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
