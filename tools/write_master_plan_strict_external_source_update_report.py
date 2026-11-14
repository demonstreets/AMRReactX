#!/usr/bin/env python3
"""Write/verify strict master-plan external source update evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_TRIAGED = "TRIAGED-MASTER-PLAN-STRICT-EXTERNAL-SOURCES-PUBLIC-DATA-INCOMPLETE"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/master_plan_strict_external_source_update_20260731")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "master_plan_strict_external_source_update_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "master_plan_strict_external_source_update_report.md"
DEFAULT_TRACEABILITY = Path(
    "docs/codex_audit/evidence/engineering_h2_master_plan_traceability_20260724/"
    "h2_master_plan_traceability_report.json"
)
DATAVERSE_METADATA = Path("docs/codex_audit/evidence/dataverse_probe_20260803/dataverse_dataset_metadata.json")
DATAVERSE_SAMPLE_ZIP = Path("docs/codex_audit/evidence/dataverse_probe_20260803/sample/23_FFI_P101_T00003.zip")
DATAVERSE_SAMPLE_ZIP_LISTING = Path(
    "docs/codex_audit/evidence/dataverse_probe_20260803/sample/23_FFI_P101_T00003_zip_listing.txt"
)
DATAVERSE_FULL_AUDIT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_dataset_20260803/"
    "dataverse_open_channel_dataset_audit_report.json"
)
DATAVERSE_TIMESERIES_INDEX = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_timeseries_index_20260803/"
    "dataverse_open_channel_timeseries_index_report.json"
)
DATAVERSE_GEOMETRY_MAPPING = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_geometry_mapping_20260803/"
    "dataverse_open_channel_geometry_mapping_report.json"
)
DATAVERSE_REFERENCE_PACKAGE = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/"
    "dataverse_open_channel_reference_package_report.json"
)
DATAVERSE_AGREEMENT_CONTRACT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_agreement_contract_20260803/"
    "dataverse_open_channel_agreement_contract_report.json"
)
DATAVERSE_CFD_SCOUT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_cfd_scout_mpi_cuda_20260803/"
    "dataverse_open_channel_cfd_scout_report.json"
)
DATAVERSE_CFD_AGREEMENT_ATTEMPT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_cfd_agreement_window_mpi_cuda_20260803/"
    "dataverse_open_channel_cfd_agreement_attempt_report.json"
)
DATAVERSE_CFD_45S_AGREEMENT_ATTEMPT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_window_mpi_cuda_20260803/"
    "dataverse_open_channel_cfd_agreement_attempt_report.json"
)
DATAVERSE_CFD_120S_AGREEMENT_ATTEMPT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_cfd_120s_peak_window_mpi_cuda_20260804/"
    "dataverse_open_channel_cfd_agreement_attempt_report.json"
)
DATAVERSE_120S_CALIBRATION_DIAGNOSIS = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_120s_calibration_diagnosis_20260804/"
    "dataverse_open_channel_120s_calibration_diagnosis_report.json"
)
DATAVERSE_45S_CALIBRATION_R005_Z08 = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_45s_calibration_r005_z08_screen_20260804/"
    "dataverse_open_channel_45s_calibration_r005_z08_screen_report.json"
)
DATAVERSE_45S_CALIBRATION_SWEEP = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_45s_calibration_sweep_20260804/"
    "dataverse_open_channel_45s_calibration_sweep_report.json"
)
DATAVERSE_PHYSICS_ALIGNMENT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_physics_alignment_20260804/"
    "dataverse_open_channel_physics_alignment_report.json"
)
DATAVERSE_ORIFICE_VELOCITY_SCOUT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_orifice_velocity_scout_mpi_cuda_20260805/"
    "dataverse_open_channel_orifice_velocity_scout_report.json"
)
DATAVERSE_OPEN_BOUNDARY_SCOUT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_scout_mpi_cuda_20260805/"
    "dataverse_open_channel_open_boundary_scout_report.json"
)
DATAVERSE_OPEN_BOUNDARY_ORIFICE_EXTENDED_01S = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_01s_mpi_cuda_20260805/"
    "dataverse_open_channel_open_boundary_orifice_velocity_extended_01s_report.json"
)
DATAVERSE_OPEN_BOUNDARY_ORIFICE_EXTENDED_1S = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_mpi_cuda_20260805/"
    "dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_report.json"
)
DATAVERSE_OPEN_BOUNDARY_ORIFICE_EXTENDED_2S = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_mpi_cuda_20260807/"
    "dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_screen_report.json"
)
DATAVERSE_REFINED_SOURCE_PROJECTION_PROBE = Path(
    "docs/codex_audit/evidence/dataverse_refined_source_projection_probe_mpi_cuda_20260807/"
    "dataverse_refined_source_projection_probe_report.json"
)
DATAVERSE_FULL_CHANNEL_REFINED_SOURCE_DX025_PROBE = Path(
    "docs/codex_audit/evidence/dataverse_full_channel_refined_source_dx025_probe_mpi_cuda_20260807/"
    "dataverse_full_channel_refined_source_dx025_probe_report.json"
)
DATAVERSE_FULL_CHANNEL_REFINED_SOURCE_DX025_500STEP = Path(
    "docs/codex_audit/evidence/dataverse_full_channel_refined_source_dx025_500step_mpi_cuda_20260807/"
    "dataverse_full_channel_refined_source_dx025_500step_report.json"
)
DATAVERSE_FULL_CHANNEL_REFINED_SOURCE_DX025_1000STEP_DT5EM6 = Path(
    "docs/codex_audit/evidence/dataverse_full_channel_refined_source_dx025_1000step_dt5em6_mpi_cuda_20260807/"
    "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_report.json"
)
DATAVERSE_AMR_SOURCE_PROJECTION_CONTRACT = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_contract_20260811/"
    "dataverse_open_channel_amr_source_projection_contract_report.json"
)
DATAVERSE_AMR_SOURCE_PROJECTION_IMPLEMENTATION = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_implementation_20260811/"
    "dataverse_open_channel_amr_source_projection_implementation_report.json"
)
DATAVERSE_LONG_WINDOW_RECONCILIATION = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_long_window_reconciliation_20260811/"
    "dataverse_open_channel_long_window_reconciliation_report.json"
)

SOURCES = [
    {
        "label": "ResearchGate full-text mirror of Results of the HySafe CFD Validation Benchmark SBEPV5",
        "url": "https://www.researchgate.net/publication/311396790_Results_of_the_HySafe_CFD_Validation_Benchmark_SBEPV5",
        "finding": (
            "Provides SBEPV5/D27 geometry, release period, nozzle diameter, exit velocity, flow rate, "
            "jet location, sensor reliability notes, and plotted concentration histories. It also states "
            "that the available benchmark dataset consisted of MS Excel transient concentration recordings "
            "for 12 monitor locations over the first 120 s."
        ),
        "machine_readable_timeseries_found": False,
    },
    {
        "label": "KITopen bibliographic record for Results of the HySafe CFD validation benchmark SBEPV5",
        "url": "https://publikationen.bibliothek.kit.edu/230068969",
        "finding": "Confirms the 2007 ICHS publication metadata for the SBEPV5 benchmark paper.",
        "machine_readable_timeseries_found": False,
    },
    {
        "label": "Hydrogen Knowledge Centre record for Results of the HySafe CFD Validation Benchmark SBEPV5",
        "url": "https://www.h2knowledgecentre.com/content/conference289",
        "finding": (
            "Confirms the benchmark paper, publication context, and a PDF supplement/presentation entry; "
            "no public machine-readable concentration time-series file was identified from the record."
        ),
        "machine_readable_timeseries_found": False,
    },
    {
        "label": "DataverseNO dataset: Experimental Data of Hydrogen Dispersion in an Open-ended Rectangular Channel",
        "url": "https://doi.org/10.23642/USN.26117989",
        "finding": (
            "Open CC-BY-4.0 hydrogen dispersion experiment dataset with downloadable ZIP/CSV files. "
            "Server-side probe confirmed released Dataverse metadata, per-file persistent IDs and MD5 hashes, "
            "and a downloaded sample CSV containing mass-flow, pressure, H2 sensor time, and 29 H2 concentration columns."
        ),
        "machine_readable_timeseries_found": True,
    },
]


class StrictSourceError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise StrictSourceError(message)


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
        raise StrictSourceError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StrictSourceError(f"invalid JSON evidence {path}: {exc}") from exc
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


def dataverse_latest_version(metadata: dict[str, Any]) -> dict[str, Any]:
    data = metadata.get("data")
    require(isinstance(data, dict), "Dataverse metadata data object missing")
    latest = data.get("latestVersion")
    require(isinstance(latest, dict), "Dataverse latestVersion object missing")
    return latest


def dataverse_citation_fields(latest: dict[str, Any]) -> dict[str, Any]:
    blocks = latest.get("metadataBlocks")
    require(isinstance(blocks, dict), "Dataverse metadataBlocks missing")
    citation = blocks.get("citation")
    require(isinstance(citation, dict), "Dataverse citation block missing")
    fields = citation.get("fields")
    require(isinstance(fields, list), "Dataverse citation fields missing")
    out: dict[str, Any] = {}
    for field in fields:
        if isinstance(field, dict) and "typeName" in field:
            out[str(field["typeName"])] = field.get("value")
    return out


def inspect_dataverse_sample_zip(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing Dataverse sample zip: {path}")
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        csv_names = [name for name in names if name.lower().endswith(".csv")]
        require(len(csv_names) == 1, f"expected one CSV in sample zip, found {len(csv_names)}")
        raw = zf.read(csv_names[0])
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    sensor_columns = [col for col in header if "h2 concentration" in col.lower()]
    require("flow time [s]" in header, "Dataverse sample CSV missing flow time column")
    require("mass flow meter 1 [g/s]" in header, "Dataverse sample CSV missing mass-flow column")
    require("filling pressure [bar]" in header, "Dataverse sample CSV missing pressure column")
    require("h2 sensor time" in header, "Dataverse sample CSV missing H2 sensor time column")
    require(len(sensor_columns) == 29, f"expected 29 H2 concentration sensor columns, found {len(sensor_columns)}")
    return {
        "zip_member_count": len(names),
        "csv_member": csv_names[0],
        "csv_size_bytes": len(raw),
        "csv_column_count": len(header),
        "h2_concentration_sensor_column_count": len(sensor_columns),
        "required_columns_present": True,
        "sensor_columns": sensor_columns,
    }


def build_dataverse_summary() -> dict[str, Any]:
    metadata = load_json(DATAVERSE_METADATA)
    require(metadata.get("status") == "OK", "Dataverse metadata status is not OK")
    latest = dataverse_latest_version(metadata)
    fields = dataverse_citation_fields(latest)
    files = latest.get("files")
    require(isinstance(files, list) and files, "Dataverse file list missing")
    sample_md5 = None
    file_rows = []
    total_size = 0
    for item in files:
        require(isinstance(item, dict), "Dataverse file row is not an object")
        data_file = item.get("dataFile")
        require(isinstance(data_file, dict), "Dataverse dataFile row missing")
        filename = str(data_file.get("filename", ""))
        persistent_id = str(data_file.get("persistentId", ""))
        md5 = str(data_file.get("md5", ""))
        size = int(data_file.get("filesize", 0))
        total_size += size
        if filename == "23_FFI_P101_T00003.zip":
            sample_md5 = md5
        file_rows.append(
            {
                "filename": filename,
                "persistent_id": persistent_id,
                "md5": md5,
                "size_bytes": size,
            }
        )
    require(sample_md5, "Dataverse sample file metadata missing")
    require(hashlib.md5(DATAVERSE_SAMPLE_ZIP.read_bytes()).hexdigest() == sample_md5, "Dataverse sample zip MD5 mismatch")
    return {
        "dataset_title": fields.get("title"),
        "dataset_doi": "10.23642/USN.26117989",
        "license": "CC BY 4.0",
        "version_state": latest.get("versionState"),
        "release_time": latest.get("releaseTime"),
        "file_count": len(files),
        "total_size_bytes": total_size,
        "metadata_file_present": True,
        "sample_zip_md5_verified": True,
        "sample_zip": inspect_dataverse_sample_zip(DATAVERSE_SAMPLE_ZIP),
        "first_files": file_rows[:5],
    }


def build_dataverse_full_audit_summary() -> dict[str, Any]:
    audit = load_json(DATAVERSE_FULL_AUDIT)
    require(
        audit.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-DATASET-AUDIT",
        "Dataverse full dataset audit is not PASS",
    )
    summary = audit.get("summary")
    require(isinstance(summary, dict), "Dataverse full dataset audit summary missing")
    require(summary.get("all_expected_files_ready") is True, "Dataverse full dataset audit does not have all files ready")
    require(
        summary.get("all_ready_zip_csvs_have_29_h2_sensor_columns") is True,
        "Dataverse full dataset audit lacks 29-sensor CSV confirmation",
    )
    return {
        "status": audit.get("status"),
        "expected_file_count": summary.get("expected_file_count"),
        "present_file_count": summary.get("present_file_count"),
        "md5_verified_file_count": summary.get("md5_verified_file_count"),
        "ready_file_count": summary.get("ready_file_count"),
        "zip_csv_audited_file_count": summary.get("zip_csv_audited_file_count"),
        "sensor_column_counts_seen": summary.get("sensor_column_counts_seen"),
        "all_expected_files_ready": summary.get("all_expected_files_ready"),
        "all_ready_zip_csvs_have_29_h2_sensor_columns": summary.get(
            "all_ready_zip_csvs_have_29_h2_sensor_columns"
        ),
    }


def build_dataverse_timeseries_index_summary() -> dict[str, Any]:
    index = load_json(DATAVERSE_TIMESERIES_INDEX)
    require(
        index.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-TIMESERIES-INDEX",
        "Dataverse time-series index is not PASS",
    )
    summary = index.get("summary")
    require(isinstance(summary, dict), "Dataverse time-series index summary missing")
    require(int(summary.get("zip_case_count", 0)) >= 20, "Dataverse time-series index zip case count too small")
    require(int(summary.get("strong_plume_candidate_count", 0)) >= 3, "Dataverse time-series index has too few candidates")
    require(summary.get("sensor_column_counts_seen") == [29], "Dataverse time-series index sensor counts mismatch")
    candidates = index.get("recommended_validation_candidates")
    require(isinstance(candidates, list) and len(candidates) >= 3, "Dataverse recommended candidates missing")
    return {
        "status": index.get("status"),
        "zip_case_count": summary.get("zip_case_count"),
        "strong_plume_candidate_count": summary.get("strong_plume_candidate_count"),
        "flow_meter_counts": summary.get("flow_meter_counts"),
        "sensor_column_counts_seen": summary.get("sensor_column_counts_seen"),
        "max_h2_peak_vol_percent": summary.get("max_h2_peak_vol_percent"),
        "max_lfl_sensor_count": summary.get("max_lfl_sensor_count"),
        "time_end_max_s": summary.get("time_end_max_s"),
        "ready_for_case_selection": summary.get("ready_for_case_selection"),
        "top_candidate_filenames": [str(item.get("filename")) for item in candidates[:5]],
    }


def build_dataverse_geometry_mapping_summary() -> dict[str, Any]:
    mapping = load_json(DATAVERSE_GEOMETRY_MAPPING)
    require(
        mapping.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-GEOMETRY-MAPPING",
        "Dataverse geometry mapping is not PASS",
    )
    summary = mapping.get("summary")
    require(isinstance(summary, dict), "Dataverse geometry mapping summary missing")
    require(int(summary.get("sensor_coordinate_count", 0)) == 29, "Dataverse geometry mapping sensor count mismatch")
    require(int(summary.get("case_mapping_count", 0)) == 22, "Dataverse geometry mapping case count mismatch")
    require(summary.get("ready_for_sensor_sampling_map") is True, "Dataverse sensor sampling map is not ready")
    require(
        summary.get("ready_for_full_geometry_mesh_parity") is False,
        "Dataverse geometry mapping should not claim full mesh parity",
    )
    return {
        "status": mapping.get("status"),
        "sensor_coordinate_count": summary.get("sensor_coordinate_count"),
        "case_mapping_count": summary.get("case_mapping_count"),
        "channel_geometry_available": summary.get("channel_geometry_available"),
        "ready_for_sensor_sampling_map": summary.get("ready_for_sensor_sampling_map"),
        "ready_for_full_geometry_mesh_parity": summary.get("ready_for_full_geometry_mesh_parity"),
        "obstacle_geometry_exact_bounds_available": summary.get("obstacle_geometry_exact_bounds_available"),
        "sensor_coordinate_csv": mapping.get("sensor_coordinate_csv"),
        "case_map_csv": mapping.get("case_map_csv"),
        "geometry_metadata_json": mapping.get("geometry_metadata_json"),
    }


def build_dataverse_reference_package_summary() -> dict[str, Any]:
    package = load_json(DATAVERSE_REFERENCE_PACKAGE)
    require(
        package.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-REFERENCE-PACKAGE",
        "Dataverse reference package is not PASS",
    )
    summary = package.get("summary")
    require(isinstance(summary, dict), "Dataverse reference package summary missing")
    require(summary.get("selected_case_filename") == "23_FFI_P101_T00031.zip", "Dataverse selected case drifted")
    require(summary.get("article_test_id") == "test-08-1", "Dataverse article test ID mismatch")
    require(int(summary.get("raw_row_count", 0)) > 1000, "Dataverse reference row count too small")
    require(int(summary.get("sensor_time_sample_count", 0)) >= 500, "Dataverse sensor sample count too small")
    require(int(summary.get("sensor_count", 0)) == 29, "Dataverse reference sensor count mismatch")
    require(
        int(summary.get("sensor_record_count", 0)) == int(summary.get("sensor_time_sample_count", 0)) * 29,
        "Dataverse reference sensor records mismatch",
    )
    require(float(summary.get("h2_peak_x_h2", 0.0)) >= 0.10, "Dataverse reference peak X(H2) too small")
    require(summary.get("ready_for_reference_signal_sampling") is True, "Dataverse reference sampling is not ready")
    require(
        summary.get("ready_for_cfd_reference_agreement_scoring") is False,
        "Dataverse reference package should not claim CFD scoring readiness",
    )
    outputs = package.get("outputs")
    require(isinstance(outputs, dict), "Dataverse reference package outputs missing")
    return {
        "status": package.get("status"),
        "selected_case_filename": summary.get("selected_case_filename"),
        "raw_case_id": summary.get("raw_case_id"),
        "article_test_id": summary.get("article_test_id"),
        "raw_row_count": summary.get("raw_row_count"),
        "sensor_time_sample_count": summary.get("sensor_time_sample_count"),
        "sensor_count": summary.get("sensor_count"),
        "sensor_record_count": summary.get("sensor_record_count"),
        "duration_s": summary.get("duration_s"),
        "h2_peak_x_h2": summary.get("h2_peak_x_h2"),
        "h2_peak_vol_percent": summary.get("h2_peak_vol_percent"),
        "h2_peak_sensor_id": summary.get("h2_peak_sensor_id"),
        "lfl_sensor_count": summary.get("lfl_sensor_count"),
        "ready_for_reference_signal_sampling": summary.get("ready_for_reference_signal_sampling"),
        "ready_for_cfd_reference_agreement_scoring": summary.get("ready_for_cfd_reference_agreement_scoring"),
        "long_timeseries_csv": outputs.get("long_timeseries_csv"),
        "wide_timeseries_csv": outputs.get("wide_timeseries_csv"),
        "release_profile_csv": outputs.get("release_profile_csv"),
        "case_metadata_json": outputs.get("case_metadata_json"),
    }


def build_dataverse_agreement_contract_summary() -> dict[str, Any]:
    contract = load_json(DATAVERSE_AGREEMENT_CONTRACT)
    require(
        contract.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-AGREEMENT-CONTRACT",
        "Dataverse agreement contract is not PASS",
    )
    summary = contract.get("summary")
    require(isinstance(summary, dict), "Dataverse agreement contract summary missing")
    require(summary.get("selected_case_filename") == "23_FFI_P101_T00031.zip", "Dataverse agreement case drifted")
    require(summary.get("article_test_id") == "test-08-1", "Dataverse agreement article test ID mismatch")
    require(int(summary.get("agreement_sensor_count", 0)) == 29, "Dataverse agreement sensor count mismatch")
    require(summary.get("all_sensors_passed") is True, "Dataverse agreement contract selftest did not pass")
    require(
        summary.get("ready_for_cfd_reference_agreement_scoring") is True,
        "Dataverse agreement contract is not ready for CFD scoring",
    )
    require(summary.get("selftest_mode") is True, "Dataverse agreement contract should be in selftest mode")
    require(summary.get("production_agreement_completed") is False, "Dataverse production agreement should remain incomplete")
    require(
        summary.get("clears_external_plume_reference_blocker") is False,
        "Dataverse agreement selftest must not clear external plume blocker",
    )
    return {
        "status": contract.get("status"),
        "mode": contract.get("mode"),
        "selected_case_filename": summary.get("selected_case_filename"),
        "article_test_id": summary.get("article_test_id"),
        "agreement_sensor_count": summary.get("agreement_sensor_count"),
        "agreement_lfl_sensor_count": summary.get("agreement_lfl_sensor_count"),
        "peak_pass_count": summary.get("peak_pass_count"),
        "nrmse_pass_count": summary.get("nrmse_pass_count"),
        "arrival_pass_count": summary.get("arrival_pass_count"),
        "max_peak_rel_error_seen": summary.get("max_peak_rel_error_seen"),
        "max_nrmse_seen": summary.get("max_nrmse_seen"),
        "max_arrival_abs_error_s_seen": summary.get("max_arrival_abs_error_s_seen"),
        "ready_for_cfd_reference_agreement_scoring": summary.get("ready_for_cfd_reference_agreement_scoring"),
        "production_agreement_completed": summary.get("production_agreement_completed"),
        "clears_external_plume_reference_blocker": summary.get("clears_external_plume_reference_blocker"),
    }


def build_dataverse_cfd_scout_summary() -> dict[str, Any]:
    scout = load_json(DATAVERSE_CFD_SCOUT)
    require(
        scout.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
        "Dataverse CFD scout is not PASS",
    )
    summary = scout.get("summary")
    require(isinstance(summary, dict), "Dataverse CFD scout summary missing")
    require(int(summary.get("mpi_rank_count", 0)) == 2, "Dataverse CFD scout MPI rank count mismatch")
    require(summary.get("cuda_initialized") is True, "Dataverse CFD scout CUDA not initialized")
    require(int(summary.get("plotfile_count", 0)) >= 5, "Dataverse CFD scout plotfile count too small")
    require(int(summary.get("sensor_count", 0)) == 29, "Dataverse CFD scout sensor count mismatch")
    require(int(summary.get("sensor_timeseries_rows", 0)) >= 145, "Dataverse CFD scout sensor rows too small")
    require(summary.get("plume_observation_status") == "PASS-H2-PLUME-OBSERVATION", "Dataverse CFD scout plume observation not PASS")
    require(summary.get("agreement_attempt_status") == "failed_expected_for_short_scout", "Dataverse CFD scout agreement attempt status mismatch")
    require(summary.get("production_agreement_completed") is False, "Dataverse CFD scout should not complete production agreement")
    require(summary.get("ready_for_longer_dataverse_cfd_campaign") is True, "Dataverse CFD scout does not prepare longer campaign")
    require(summary.get("clears_external_plume_reference_blocker") is False, "Dataverse CFD scout cannot clear blocker")
    return {
        "status": scout.get("status"),
        "mpi_rank_count": summary.get("mpi_rank_count"),
        "cuda_initialized": summary.get("cuda_initialized"),
        "plotfile_count": summary.get("plotfile_count"),
        "sensor_count": summary.get("sensor_count"),
        "sensor_timeseries_rows": summary.get("sensor_timeseries_rows"),
        "time_end_s": summary.get("time_end_s"),
        "mass_ratio_final": summary.get("mass_ratio_final"),
        "max_yh2": summary.get("max_yh2"),
        "agreement_attempt_status": summary.get("agreement_attempt_status"),
        "production_agreement_completed": summary.get("production_agreement_completed"),
        "ready_for_longer_dataverse_cfd_campaign": summary.get("ready_for_longer_dataverse_cfd_campaign"),
        "clears_external_plume_reference_blocker": summary.get("clears_external_plume_reference_blocker"),
    }


def build_dataverse_cfd_agreement_attempt_summary() -> dict[str, Any]:
    attempt = load_json(DATAVERSE_CFD_AGREEMENT_ATTEMPT)
    require(
        attempt.get("status") == "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
        "Dataverse CFD agreement attempt status is not the expected quantified non-passing state",
    )
    summary = attempt.get("summary")
    require(isinstance(summary, dict), "Dataverse CFD agreement attempt summary missing")
    require(summary.get("agreement_attempt_quantified") is True, "Dataverse agreement attempt is not quantified")
    require(int(summary.get("sensor_count", 0)) == 29, "Dataverse agreement attempt sensor count mismatch")
    require(int(summary.get("common_sample_count_min", 0)) >= 2, "Dataverse agreement attempt has too few common samples")
    require(float(summary.get("simulation_time_end_s", 0.0)) >= 1.999, "Dataverse agreement attempt did not reach 2 s")
    require(summary.get("production_agreement_completed") is False, "Dataverse agreement attempt should not complete production agreement")
    require(summary.get("clears_external_plume_reference_blocker") is False, "Dataverse agreement attempt should not clear blocker")
    return {
        "status": attempt.get("status"),
        "sensor_count": summary.get("sensor_count"),
        "common_sample_count_min": summary.get("common_sample_count_min"),
        "common_sample_count_max": summary.get("common_sample_count_max"),
        "failed_sensor_count": summary.get("failed_sensor_count"),
        "peak_pass_count": summary.get("peak_pass_count"),
        "nrmse_pass_count": summary.get("nrmse_pass_count"),
        "arrival_pass_count": summary.get("arrival_pass_count"),
        "simulation_time_end_s": summary.get("simulation_time_end_s"),
        "simulation_max_yh2": summary.get("simulation_max_yh2"),
        "simulation_mass_ratio_final": summary.get("simulation_mass_ratio_final"),
        "production_agreement_completed": summary.get("production_agreement_completed"),
        "clears_external_plume_reference_blocker": summary.get("clears_external_plume_reference_blocker"),
    }


def build_dataverse_cfd_45s_agreement_attempt_summary() -> dict[str, Any]:
    attempt = load_json(DATAVERSE_CFD_45S_AGREEMENT_ATTEMPT)
    require(
        attempt.get("status") == "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
        "Dataverse 45s CFD agreement attempt status is not the expected quantified non-passing state",
    )
    summary = attempt.get("summary")
    require(isinstance(summary, dict), "Dataverse 45s CFD agreement attempt summary missing")
    require(summary.get("agreement_attempt_quantified") is True, "Dataverse 45s agreement attempt is not quantified")
    require(int(summary.get("sensor_count", 0)) == 29, "Dataverse 45s agreement attempt sensor count mismatch")
    require(int(summary.get("common_sample_count_min", 0)) >= 60, "Dataverse 45s agreement attempt has too few common samples")
    require(float(summary.get("simulation_time_end_s", 0.0)) >= 44.9, "Dataverse 45s agreement attempt did not reach 45 s")
    require(int(summary.get("nrmse_pass_count", 0)) >= 20, "Dataverse 45s agreement attempt NRMSE regression")
    require(summary.get("production_agreement_completed") is False, "Dataverse 45s attempt should not complete production agreement")
    require(summary.get("clears_external_plume_reference_blocker") is False, "Dataverse 45s attempt should not clear blocker")
    return {
        "status": attempt.get("status"),
        "sensor_count": summary.get("sensor_count"),
        "common_sample_count_min": summary.get("common_sample_count_min"),
        "common_sample_count_max": summary.get("common_sample_count_max"),
        "failed_sensor_count": summary.get("failed_sensor_count"),
        "peak_pass_count": summary.get("peak_pass_count"),
        "nrmse_pass_count": summary.get("nrmse_pass_count"),
        "arrival_pass_count": summary.get("arrival_pass_count"),
        "simulation_time_end_s": summary.get("simulation_time_end_s"),
        "simulation_max_yh2": summary.get("simulation_max_yh2"),
        "simulation_mass_ratio_final": summary.get("simulation_mass_ratio_final"),
        "production_agreement_completed": summary.get("production_agreement_completed"),
        "clears_external_plume_reference_blocker": summary.get("clears_external_plume_reference_blocker"),
    }


def build_dataverse_cfd_120s_agreement_attempt_summary() -> dict[str, Any]:
    attempt = load_json(DATAVERSE_CFD_120S_AGREEMENT_ATTEMPT)
    require(
        attempt.get("status") == "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
        "Dataverse 120s CFD agreement attempt status is not the expected quantified non-passing state",
    )
    summary = attempt.get("summary")
    require(isinstance(summary, dict), "Dataverse 120s CFD agreement attempt summary missing")
    require(summary.get("agreement_attempt_quantified") is True, "Dataverse 120s agreement attempt is not quantified")
    require(int(summary.get("sensor_count", 0)) == 29, "Dataverse 120s agreement attempt sensor count mismatch")
    require(int(summary.get("common_sample_count_min", 0)) >= 180, "Dataverse 120s agreement attempt has too few common samples")
    require(float(summary.get("simulation_time_end_s", 0.0)) >= 119.9, "Dataverse 120s agreement attempt did not reach 120 s")
    require(abs(float(summary.get("simulation_mass_ratio_final", 0.0)) - 1.0) <= 1.0e-12, "Dataverse 120s agreement attempt mass ratio regressed")
    require(float(summary.get("simulation_max_yh2", 0.0)) >= 0.9, "Dataverse 120s agreement attempt did not sustain a strong H2 plume")
    require(int(summary.get("peak_pass_count", 0)) >= 2, "Dataverse 120s agreement attempt peak pass count regressed")
    require(int(summary.get("arrival_pass_count", 0)) >= 6, "Dataverse 120s agreement attempt arrival pass count regressed")
    require(summary.get("production_agreement_completed") is False, "Dataverse 120s attempt should not complete production agreement")
    require(summary.get("clears_external_plume_reference_blocker") is False, "Dataverse 120s attempt should not clear blocker")
    return {
        "status": attempt.get("status"),
        "sensor_count": summary.get("sensor_count"),
        "common_sample_count_min": summary.get("common_sample_count_min"),
        "common_sample_count_max": summary.get("common_sample_count_max"),
        "failed_sensor_count": summary.get("failed_sensor_count"),
        "peak_pass_count": summary.get("peak_pass_count"),
        "nrmse_pass_count": summary.get("nrmse_pass_count"),
        "arrival_pass_count": summary.get("arrival_pass_count"),
        "simulation_time_end_s": summary.get("simulation_time_end_s"),
        "simulation_max_yh2": summary.get("simulation_max_yh2"),
        "simulation_mass_ratio_final": summary.get("simulation_mass_ratio_final"),
        "production_agreement_completed": summary.get("production_agreement_completed"),
        "clears_external_plume_reference_blocker": summary.get("clears_external_plume_reference_blocker"),
    }


def build_dataverse_120s_calibration_diagnosis_summary() -> dict[str, Any]:
    diagnosis = load_json(DATAVERSE_120S_CALIBRATION_DIAGNOSIS)
    require(
        diagnosis.get("status") == "DIAGNOSED-DATAVERSE-OPEN-CHANNEL-H2-120S-CALIBRATION-GAPS",
        "Dataverse 120s calibration diagnosis status mismatch",
    )
    summary = diagnosis.get("summary")
    require(isinstance(summary, dict), "Dataverse 120s calibration diagnosis summary missing")
    require(float(summary.get("source_radius_ratio", 0.0)) > 10.0, "Dataverse 120s source-radius diagnosis missing")
    require(abs(float(summary.get("source_center_z_offset_m", 0.0))) >= 0.05, "Dataverse 120s source-height diagnosis missing")
    require(summary.get("ready_for_next_calibration_sweep") is True, "Dataverse 120s next calibration sweep not ready")
    require(summary.get("strict_external_plume_blocker_cleared") is False, "Dataverse 120s diagnosis must not clear blocker")
    return {
        "status": diagnosis.get("status"),
        "source_radius_ratio": summary.get("source_radius_ratio"),
        "source_area_ratio": summary.get("source_area_ratio"),
        "source_center_z_offset_m": summary.get("source_center_z_offset_m"),
        "minimum_active_radius_at_reference_source_on_current_grid_m": summary.get(
            "minimum_active_radius_at_reference_source_on_current_grid_m"
        ),
        "severe_peak_error_count": summary.get("severe_peak_error_count"),
        "severe_peak_overprediction_count": summary.get("severe_peak_overprediction_count"),
        "severe_peak_underprediction_count": summary.get("severe_peak_underprediction_count"),
        "infinite_arrival_error_count": summary.get("infinite_arrival_error_count"),
        "ready_for_next_calibration_sweep": summary.get("ready_for_next_calibration_sweep"),
        "strict_external_plume_blocker_cleared": summary.get("strict_external_plume_blocker_cleared"),
    }


def build_dataverse_45s_calibration_r005_z08_summary() -> dict[str, Any]:
    screen = load_json(DATAVERSE_45S_CALIBRATION_R005_Z08)
    require(
        screen.get("status") == "SCREENED-DATAVERSE-OPEN-CHANNEL-H2-45S-CALIBRATION-R005-Z08-NOT-PROMOTED",
        "Dataverse 45s calibration r005 z08 status mismatch",
    )
    summary = screen.get("summary")
    require(isinstance(summary, dict), "Dataverse 45s calibration r005 z08 summary missing")
    require(summary.get("candidate_stable") is True, "Dataverse 45s calibration candidate not stable")
    require(summary.get("promote_to_120s_peak_window") is False, "Dataverse 45s calibration candidate should not be promoted")
    require(summary.get("strict_external_plume_blocker_cleared") is False, "Dataverse 45s calibration screen must not clear blocker")
    return {
        "status": screen.get("status"),
        "candidate_peak_pass_count": summary.get("candidate_peak_pass_count"),
        "candidate_nrmse_pass_count": summary.get("candidate_nrmse_pass_count"),
        "candidate_arrival_pass_count": summary.get("candidate_arrival_pass_count"),
        "baseline_peak_pass_count": summary.get("baseline_peak_pass_count"),
        "baseline_nrmse_pass_count": summary.get("baseline_nrmse_pass_count"),
        "baseline_arrival_pass_count": summary.get("baseline_arrival_pass_count"),
        "promote_to_120s_peak_window": summary.get("promote_to_120s_peak_window"),
        "ready_for_next_calibration_screen": summary.get("ready_for_next_calibration_screen"),
    }


def build_dataverse_45s_calibration_sweep_summary() -> dict[str, Any]:
    sweep = load_json(DATAVERSE_45S_CALIBRATION_SWEEP)
    require(
        sweep.get("status") == "SCREENED-DATAVERSE-OPEN-CHANNEL-H2-45S-CALIBRATION-SWEEP-NO-PROMOTION",
        "Dataverse 45s calibration sweep status mismatch",
    )
    summary = sweep.get("summary")
    require(isinstance(summary, dict), "Dataverse 45s calibration sweep summary missing")
    require(int(summary.get("stable_case_count", 0)) == 3, "Dataverse 45s calibration sweep stable case count mismatch")
    require(int(summary.get("promoted_case_count", -1)) == 0, "Dataverse 45s calibration sweep unexpectedly promoted a case")
    require(summary.get("strict_external_plume_blocker_cleared") is False, "Dataverse 45s calibration sweep must not clear blocker")
    require(summary.get("ready_for_next_calibration_screen") is True, "Dataverse 45s calibration sweep next screen not ready")
    return {
        "status": sweep.get("status"),
        "case_count": summary.get("case_count"),
        "stable_case_count": summary.get("stable_case_count"),
        "promoted_case_count": summary.get("promoted_case_count"),
        "best_case_label": summary.get("best_case_label"),
        "best_case_combined_pass_count": summary.get("best_case_combined_pass_count"),
        "ready_for_next_calibration_screen": summary.get("ready_for_next_calibration_screen"),
    }


def build_dataverse_physics_alignment_summary() -> dict[str, Any]:
    alignment = load_json(DATAVERSE_PHYSICS_ALIGNMENT)
    require(
        alignment.get("status") == "DIAGNOSED-DATAVERSE-OPEN-CHANNEL-H2-PHYSICS-ALIGNMENT-GAPS",
        "Dataverse physics alignment status mismatch",
    )
    summary = alignment.get("summary")
    require(isinstance(summary, dict), "Dataverse physics alignment summary missing")
    require(float(summary.get("equivalent_orifice_velocity_m_s", 0.0)) > 100.0, "Dataverse equivalent orifice velocity missing")
    require(float(summary.get("equivalent_to_baseline_velocity_ratio", 0.0)) > 100.0, "Dataverse velocity-ratio diagnosis missing")
    require(int(summary.get("current_grid_active_cell_count_for_experimental_radius", -1)) == 0, "Dataverse experimental-radius active-cell diagnosis missing")
    require(summary.get("ready_for_orifice_velocity_scout") is True, "Dataverse orifice-velocity scout readiness missing")
    require(summary.get("ready_for_refined_source_projection") is True, "Dataverse refined projection readiness missing")
    require(summary.get("strict_external_plume_blocker_cleared") is False, "Dataverse physics alignment must not clear blocker")
    return {
        "status": alignment.get("status"),
        "experimental_orifice_diameter_m": summary.get("experimental_orifice_diameter_m"),
        "equivalent_orifice_velocity_m_s": summary.get("equivalent_orifice_velocity_m_s"),
        "baseline_numerical_leak_velocity_m_s": summary.get("baseline_numerical_leak_velocity_m_s"),
        "equivalent_to_baseline_velocity_ratio": summary.get("equivalent_to_baseline_velocity_ratio"),
        "baseline_to_experiment_radius_ratio": summary.get("baseline_to_experiment_radius_ratio"),
        "active_cell_count_for_experimental_radius": summary.get("current_grid_active_cell_count_for_experimental_radius"),
        "active_cell_count_for_baseline_radius": summary.get("current_grid_active_cell_count_for_baseline_radius"),
        "ready_for_orifice_velocity_scout": summary.get("ready_for_orifice_velocity_scout"),
        "ready_for_refined_source_projection": summary.get("ready_for_refined_source_projection"),
    }


def build_dataverse_orifice_velocity_scout_summary() -> dict[str, Any]:
    scout = load_json(DATAVERSE_ORIFICE_VELOCITY_SCOUT)
    require(
        scout.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
        "Dataverse orifice-velocity scout is not PASS",
    )
    summary = scout.get("summary")
    require(isinstance(summary, dict), "Dataverse orifice-velocity scout summary missing")
    require(int(summary.get("mpi_rank_count", 0)) == 2, "Dataverse orifice-velocity scout MPI rank count mismatch")
    require(summary.get("cuda_initialized") is True, "Dataverse orifice-velocity scout CUDA not initialized")
    require(int(summary.get("plotfile_count", 0)) >= 5, "Dataverse orifice-velocity scout plotfile count too small")
    require(int(summary.get("sensor_count", 0)) == 29, "Dataverse orifice-velocity scout sensor count mismatch")
    require(int(summary.get("sensor_timeseries_rows", 0)) >= 145, "Dataverse orifice-velocity scout sensor rows too small")
    require(abs(float(summary.get("mass_ratio_final", 0.0)) - 1.0) <= 1.0e-12, "Dataverse orifice-velocity scout mass ratio regressed")
    require(float(summary.get("max_yh2", 0.0)) > 0.0, "Dataverse orifice-velocity scout H2 plume missing")
    require(summary.get("agreement_attempt_status") == "failed_expected_for_short_scout", "Dataverse orifice-velocity scout agreement status mismatch")
    return {
        "status": scout.get("status"),
        "mpi_rank_count": summary.get("mpi_rank_count"),
        "cuda_initialized": summary.get("cuda_initialized"),
        "plotfile_count": summary.get("plotfile_count"),
        "sensor_timeseries_rows": summary.get("sensor_timeseries_rows"),
        "time_end_s": summary.get("time_end_s"),
        "mass_ratio_final": summary.get("mass_ratio_final"),
        "max_yh2": summary.get("max_yh2"),
        "agreement_attempt_status": summary.get("agreement_attempt_status"),
        "ready_for_longer_dataverse_cfd_campaign": summary.get("ready_for_longer_dataverse_cfd_campaign"),
    }


def build_dataverse_open_boundary_scout_summary() -> dict[str, Any]:
    scout = load_json(DATAVERSE_OPEN_BOUNDARY_SCOUT)
    require(
        scout.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
        "Dataverse open-boundary scout is not PASS",
    )
    summary = scout.get("summary")
    require(isinstance(summary, dict), "Dataverse open-boundary scout summary missing")
    require(int(summary.get("mpi_rank_count", 0)) == 2, "Dataverse open-boundary scout MPI rank count mismatch")
    require(summary.get("cuda_initialized") is True, "Dataverse open-boundary scout CUDA not initialized")
    require(int(summary.get("plotfile_count", 0)) >= 5, "Dataverse open-boundary scout plotfile count too small")
    require(int(summary.get("sensor_count", 0)) == 29, "Dataverse open-boundary scout sensor count mismatch")
    require(int(summary.get("sensor_timeseries_rows", 0)) >= 145, "Dataverse open-boundary scout sensor rows too small")
    require(abs(float(summary.get("mass_ratio_final", 0.0)) - 1.0) <= 1.0e-12, "Dataverse open-boundary scout mass ratio regressed")
    require(float(summary.get("max_yh2", 0.0)) > 0.0, "Dataverse open-boundary scout H2 plume missing")
    require(summary.get("agreement_attempt_status") == "failed_expected_for_short_scout", "Dataverse open-boundary scout agreement status mismatch")
    return {
        "status": scout.get("status"),
        "mpi_rank_count": summary.get("mpi_rank_count"),
        "cuda_initialized": summary.get("cuda_initialized"),
        "plotfile_count": summary.get("plotfile_count"),
        "sensor_timeseries_rows": summary.get("sensor_timeseries_rows"),
        "time_end_s": summary.get("time_end_s"),
        "mass_ratio_final": summary.get("mass_ratio_final"),
        "max_yh2": summary.get("max_yh2"),
        "agreement_attempt_status": summary.get("agreement_attempt_status"),
        "ready_for_longer_dataverse_cfd_campaign": summary.get("ready_for_longer_dataverse_cfd_campaign"),
    }


def build_dataverse_open_boundary_orifice_extended_01s_summary() -> dict[str, Any]:
    run = load_json(DATAVERSE_OPEN_BOUNDARY_ORIFICE_EXTENDED_01S)
    require(
        run.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
        "Dataverse open-boundary 0.1s extended run is not PASS",
    )
    summary = run.get("summary")
    require(isinstance(summary, dict), "Dataverse open-boundary 0.1s summary missing")
    require(int(summary.get("mpi_rank_count", 0)) == 2, "Dataverse open-boundary 0.1s MPI rank count mismatch")
    require(summary.get("cuda_initialized") is True, "Dataverse open-boundary 0.1s CUDA not initialized")
    require(int(summary.get("plotfile_count", 0)) >= 11, "Dataverse open-boundary 0.1s plotfile count too small")
    require(int(summary.get("sensor_count", 0)) == 29, "Dataverse open-boundary 0.1s sensor count mismatch")
    require(int(summary.get("sensor_timeseries_rows", 0)) >= 319, "Dataverse open-boundary 0.1s sensor rows too small")
    require(abs(float(summary.get("time_end_s", 0.0)) - 0.1) <= 1.0e-12, "Dataverse open-boundary 0.1s did not reach expected time")
    require(abs(float(summary.get("mass_ratio_final", 0.0)) - 1.0) <= 1.0e-12, "Dataverse open-boundary 0.1s mass ratio regressed")
    require(float(summary.get("max_yh2", 0.0)) > 0.02, "Dataverse open-boundary 0.1s H2 plume too weak")
    require(float(summary.get("downstream_fraction", 0.0)) > 0.95, "Dataverse open-boundary 0.1s plume did not advect downstream")
    require(summary.get("agreement_attempt_status") == "failed_expected_for_short_scout", "Dataverse open-boundary 0.1s agreement status mismatch")
    return {
        "status": run.get("status"),
        "mpi_rank_count": summary.get("mpi_rank_count"),
        "cuda_initialized": summary.get("cuda_initialized"),
        "plotfile_count": summary.get("plotfile_count"),
        "sensor_timeseries_rows": summary.get("sensor_timeseries_rows"),
        "time_end_s": summary.get("time_end_s"),
        "mass_ratio_final": summary.get("mass_ratio_final"),
        "max_yh2": summary.get("max_yh2"),
        "downstream_fraction": summary.get("downstream_fraction"),
        "agreement_attempt_status": summary.get("agreement_attempt_status"),
    }


def build_dataverse_open_boundary_orifice_extended_1s_summary() -> dict[str, Any]:
    run = load_json(DATAVERSE_OPEN_BOUNDARY_ORIFICE_EXTENDED_1S)
    require(
        run.get("status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
        "Dataverse open-boundary 1.0s extended run is not PASS",
    )
    summary = run.get("summary")
    require(isinstance(summary, dict), "Dataverse open-boundary 1.0s summary missing")
    require(int(summary.get("mpi_rank_count", 0)) == 2, "Dataverse open-boundary 1.0s MPI rank count mismatch")
    require(summary.get("cuda_initialized") is True, "Dataverse open-boundary 1.0s CUDA not initialized")
    require(int(summary.get("plotfile_count", 0)) >= 11, "Dataverse open-boundary 1.0s plotfile count too small")
    require(int(summary.get("sensor_count", 0)) == 29, "Dataverse open-boundary 1.0s sensor count mismatch")
    require(int(summary.get("sensor_timeseries_rows", 0)) >= 319, "Dataverse open-boundary 1.0s sensor rows too small")
    require(abs(float(summary.get("time_end_s", 0.0)) - 1.0) <= 1.0e-12, "Dataverse open-boundary 1.0s did not reach expected time")
    require(abs(float(summary.get("mass_ratio_final", 0.0)) - 1.0) <= 1.0e-12, "Dataverse open-boundary 1.0s mass ratio regressed")
    require(float(summary.get("max_yh2", 0.0)) > 0.015, "Dataverse open-boundary 1.0s H2 plume too weak")
    require(float(summary.get("downstream_fraction", 0.0)) > 0.99, "Dataverse open-boundary 1.0s plume did not advect downstream")
    require(summary.get("agreement_attempt_status") == "failed_expected_for_short_scout", "Dataverse open-boundary 1.0s agreement status mismatch")
    return {
        "status": run.get("status"),
        "mpi_rank_count": summary.get("mpi_rank_count"),
        "cuda_initialized": summary.get("cuda_initialized"),
        "plotfile_count": summary.get("plotfile_count"),
        "sensor_timeseries_rows": summary.get("sensor_timeseries_rows"),
        "time_end_s": summary.get("time_end_s"),
        "mass_ratio_final": summary.get("mass_ratio_final"),
        "max_yh2": summary.get("max_yh2"),
        "downstream_fraction": summary.get("downstream_fraction"),
        "agreement_attempt_status": summary.get("agreement_attempt_status"),
    }


def build_dataverse_open_boundary_orifice_extended_2s_summary() -> dict[str, Any]:
    run = load_json(DATAVERSE_OPEN_BOUNDARY_ORIFICE_EXTENDED_2S)
    require(
        run.get("status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-OPEN-BOUNDARY-ORIFICE-EXTENDED-2S-MPI-CUDA",
        "Dataverse open-boundary 2.0s extended screen is not PASS",
    )
    summary = run.get("summary")
    require(isinstance(summary, dict), "Dataverse open-boundary 2.0s summary missing")
    require(int(summary.get("mpi_rank_count", 0)) == 2, "Dataverse open-boundary 2.0s MPI rank count mismatch")
    require(summary.get("cuda_initialized") is True, "Dataverse open-boundary 2.0s CUDA not initialized")
    require(int(summary.get("plotfile_count", 0)) >= 21, "Dataverse open-boundary 2.0s plotfile count too small")
    require(int(summary.get("sensor_timeseries_rows", 0)) >= 609, "Dataverse open-boundary 2.0s sensor rows too small")
    require(abs(float(summary.get("time_end_s", 0.0)) - 2.0) <= 1.0e-12, "Dataverse open-boundary 2.0s did not reach expected time")
    require(0.75 <= float(summary.get("mass_ratio_final", 0.0)) <= 1.05, "Dataverse open-boundary 2.0s mass ratio outside open-boundary screen range")
    require(float(summary.get("max_yh2", 0.0)) > 0.015, "Dataverse open-boundary 2.0s H2 plume too weak")
    require(float(summary.get("downstream_fraction", 0.0)) > 0.99, "Dataverse open-boundary 2.0s plume did not advect downstream")
    require(summary.get("run_log_has_no_abort_nan_or_cuda_error") is True, "Dataverse open-boundary 2.0s runtime log regressed")
    require(
        summary.get("clears_external_plume_reference_blocker") is False,
        "Dataverse open-boundary 2.0s must not clear strict external plume blocker",
    )
    require(summary.get("strict_blocker_still_open") is True, "Dataverse open-boundary 2.0s strict blocker state mismatch")
    return {
        "status": run.get("status"),
        "mpi_rank_count": summary.get("mpi_rank_count"),
        "cuda_initialized": summary.get("cuda_initialized"),
        "plotfile_count": summary.get("plotfile_count"),
        "sensor_timeseries_rows": summary.get("sensor_timeseries_rows"),
        "time_end_s": summary.get("time_end_s"),
        "mass_ratio_final": summary.get("mass_ratio_final"),
        "max_yh2": summary.get("max_yh2"),
        "downstream_fraction": summary.get("downstream_fraction"),
        "run_log_has_no_abort_nan_or_cuda_error": summary.get("run_log_has_no_abort_nan_or_cuda_error"),
        "clears_external_plume_reference_blocker": summary.get("clears_external_plume_reference_blocker"),
        "strict_blocker_still_open": summary.get("strict_blocker_still_open"),
    }


def build_dataverse_refined_source_projection_probe_summary() -> dict[str, Any]:
    run = load_json(DATAVERSE_REFINED_SOURCE_PROJECTION_PROBE)
    require(
        run.get("status") == "PASS-DATAVERSE-REFINED-SOURCE-PROJECTION-PROBE-MPI-CUDA",
        "Dataverse refined source projection probe is not PASS",
    )
    summary = run.get("summary")
    require(isinstance(summary, dict), "Dataverse refined source projection summary missing")
    require(summary.get("refined_source_projection_probe_ready") is True, "refined source projection probe not ready")
    require(int(summary.get("mpi_rank_count", 0)) == 2, "refined source projection MPI rank count mismatch")
    require(summary.get("cuda_initialized") is True, "refined source projection CUDA not initialized")
    require(summary.get("run_log_has_no_abort_nan_or_cuda_error") is True, "refined source projection runtime log regressed")
    require(all(abs(float(v) - 0.0125) <= 1.0e-12 for v in summary.get("dx_m", [])), "refined source projection dx mismatch")
    require(abs(float(summary.get("leak_radius_m", 0.0)) - 0.0023) <= 1.0e-15, "refined source projection leak radius mismatch")
    require(float(summary.get("center_alignment_error_cells", 1.0)) <= 1.0e-12, "refined source projection source is not cell-centered")
    require(summary.get("active_volume_equals_single_cell") is True, "refined source projection active volume is not one cell")
    require(float(summary.get("source_cfl", 1.0)) < 0.01, "refined source projection source CFL too large")
    require(summary.get("clears_external_plume_reference_blocker") is False, "refined source projection must not clear strict blocker")
    require(summary.get("strict_blocker_still_open") is True, "refined source projection strict blocker state mismatch")
    return {
        "status": run.get("status"),
        "mpi_rank_count": summary.get("mpi_rank_count"),
        "cuda_initialized": summary.get("cuda_initialized"),
        "run_log_has_no_abort_nan_or_cuda_error": summary.get("run_log_has_no_abort_nan_or_cuda_error"),
        "n_cell": summary.get("n_cell"),
        "dx_m": summary.get("dx_m"),
        "leak_radius_m": summary.get("leak_radius_m"),
        "experimental_orifice_radius_m": summary.get("experimental_orifice_radius_m"),
        "equivalent_orifice_velocity_m_s": summary.get("equivalent_orifice_velocity_m_s"),
        "active_volume_m3": summary.get("active_volume_m3"),
        "single_cell_volume_m3": summary.get("single_cell_volume_m3"),
        "active_volume_equals_single_cell": summary.get("active_volume_equals_single_cell"),
        "source_cfl": summary.get("source_cfl"),
        "time_end_s": summary.get("time_end_s"),
        "validation_max_yh2": summary.get("validation_max_yh2"),
        "clears_external_plume_reference_blocker": summary.get("clears_external_plume_reference_blocker"),
        "strict_blocker_still_open": summary.get("strict_blocker_still_open"),
    }


def build_dataverse_full_channel_refined_source_dx025_probe_summary() -> dict[str, Any]:
    run = load_json(DATAVERSE_FULL_CHANNEL_REFINED_SOURCE_DX025_PROBE)
    require(
        run.get("status") == "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-PROBE-MPI-CUDA",
        "Dataverse full-channel refined-source dx=0.025 probe is not PASS",
    )
    summary = run.get("summary")
    require(isinstance(summary, dict), "Dataverse full-channel refined-source summary missing")
    require(summary.get("full_channel_refined_source_dx025_probe_ready") is True, "full-channel refined-source probe not ready")
    require(int(summary.get("mpi_rank_count", 0)) == 2, "full-channel refined-source MPI rank count mismatch")
    require(summary.get("cuda_initialized") is True, "full-channel refined-source CUDA not initialized")
    require(summary.get("run_log_has_no_abort_nan_or_cuda_error") is True, "full-channel refined-source runtime log regressed")
    require(summary.get("full_dataverse_domain") is True, "full-channel refined-source did not use full Dataverse domain")
    require(all(abs(float(v) - 0.025) <= 1.0e-12 for v in summary.get("dx_m", [])), "full-channel refined-source dx mismatch")
    require(abs(float(summary.get("leak_radius_m", 0.0)) - 0.0023) <= 1.0e-15, "full-channel refined-source leak radius mismatch")
    require(summary.get("active_volume_equals_single_cell") is True, "full-channel refined-source active volume is not one cell")
    require(float(summary.get("source_cfl", 1.0)) < 0.05, "full-channel refined-source source CFL too large")
    require(float(summary.get("validation_max_yh2", 0.0)) > 0.0, "full-channel refined-source plume missing")
    require(summary.get("clears_external_plume_reference_blocker") is False, "full-channel refined-source must not clear strict blocker")
    require(summary.get("strict_blocker_still_open") is True, "full-channel refined-source strict blocker state mismatch")
    return {
        "status": run.get("status"),
        "mpi_rank_count": summary.get("mpi_rank_count"),
        "cuda_initialized": summary.get("cuda_initialized"),
        "run_log_has_no_abort_nan_or_cuda_error": summary.get("run_log_has_no_abort_nan_or_cuda_error"),
        "full_dataverse_domain": summary.get("full_dataverse_domain"),
        "n_cell": summary.get("n_cell"),
        "dx_m": summary.get("dx_m"),
        "leak_radius_m": summary.get("leak_radius_m"),
        "experimental_orifice_radius_m": summary.get("experimental_orifice_radius_m"),
        "equivalent_orifice_velocity_m_s": summary.get("equivalent_orifice_velocity_m_s"),
        "active_volume_m3": summary.get("active_volume_m3"),
        "single_cell_volume_m3": summary.get("single_cell_volume_m3"),
        "active_volume_equals_single_cell": summary.get("active_volume_equals_single_cell"),
        "source_cfl": summary.get("source_cfl"),
        "time_end_s": summary.get("time_end_s"),
        "validation_max_yh2": summary.get("validation_max_yh2"),
        "clears_external_plume_reference_blocker": summary.get("clears_external_plume_reference_blocker"),
        "strict_blocker_still_open": summary.get("strict_blocker_still_open"),
    }


def build_dataverse_full_channel_refined_source_dx025_500step_summary() -> dict[str, Any]:
    run = load_json(DATAVERSE_FULL_CHANNEL_REFINED_SOURCE_DX025_500STEP)
    require(
        run.get("status") == "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-500STEP-MPI-CUDA",
        "Dataverse full-channel refined-source dx=0.025 500-step screen is not PASS",
    )
    summary = run.get("summary")
    require(isinstance(summary, dict), "Dataverse full-channel refined-source 500-step summary missing")
    require(summary.get("full_channel_refined_source_dx025_500step_ready") is True, "full-channel refined-source 500-step screen not ready")
    require(int(summary.get("mpi_rank_count", 0)) == 2, "full-channel refined-source 500-step MPI rank count mismatch")
    require(summary.get("cuda_initialized") is True, "full-channel refined-source 500-step CUDA not initialized")
    require(summary.get("run_log_has_no_abort_nan_or_cuda_error") is True, "full-channel refined-source 500-step runtime log regressed")
    require(summary.get("full_dataverse_domain") is True, "full-channel refined-source 500-step did not use full Dataverse domain")
    require(all(abs(float(v) - 0.025) <= 1.0e-12 for v in summary.get("dx_m", [])), "full-channel refined-source 500-step dx mismatch")
    require(abs(float(summary.get("leak_radius_m", 0.0)) - 0.0023) <= 1.0e-15, "full-channel refined-source 500-step leak radius mismatch")
    require(summary.get("active_volume_equals_single_cell") is True, "full-channel refined-source 500-step active volume is not one cell")
    require(float(summary.get("source_cfl", 1.0)) < 0.05, "full-channel refined-source 500-step source CFL too large")
    require(int(summary.get("max_step", 0)) == 500, "full-channel refined-source 500-step max_step mismatch")
    require(float(summary.get("validation_max_yh2", 0.0)) > 0.0, "full-channel refined-source 500-step plume missing")
    require(summary.get("clears_external_plume_reference_blocker") is False, "full-channel refined-source 500-step must not clear strict blocker")
    require(summary.get("strict_blocker_still_open") is True, "full-channel refined-source 500-step strict blocker state mismatch")
    return {
        "status": run.get("status"),
        "mpi_rank_count": summary.get("mpi_rank_count"),
        "cuda_initialized": summary.get("cuda_initialized"),
        "run_log_has_no_abort_nan_or_cuda_error": summary.get("run_log_has_no_abort_nan_or_cuda_error"),
        "full_dataverse_domain": summary.get("full_dataverse_domain"),
        "n_cell": summary.get("n_cell"),
        "dx_m": summary.get("dx_m"),
        "leak_radius_m": summary.get("leak_radius_m"),
        "active_volume_equals_single_cell": summary.get("active_volume_equals_single_cell"),
        "source_cfl": summary.get("source_cfl"),
        "max_step": summary.get("max_step"),
        "time_end_s": summary.get("time_end_s"),
        "validation_max_yh2": summary.get("validation_max_yh2"),
        "clears_external_plume_reference_blocker": summary.get("clears_external_plume_reference_blocker"),
        "strict_blocker_still_open": summary.get("strict_blocker_still_open"),
    }


def build_dataverse_full_channel_refined_source_dx025_1000step_dt5em6_summary() -> dict[str, Any]:
    run = load_json(DATAVERSE_FULL_CHANNEL_REFINED_SOURCE_DX025_1000STEP_DT5EM6)
    require(
        run.get("status") == "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-1000STEP-DT5EM6-MPI-CUDA",
        "Dataverse full-channel refined-source dx=0.025 1000-step dt=5e-6 screen is not PASS",
    )
    summary = run.get("summary")
    require(isinstance(summary, dict), "Dataverse full-channel refined-source 1000-step dt=5e-6 summary missing")
    require(summary.get("full_channel_refined_source_dx025_1000step_dt5em6_ready") is True, "full-channel refined-source 1000-step dt=5e-6 screen not ready")
    require(int(summary.get("mpi_rank_count", 0)) == 2, "full-channel refined-source 1000-step dt=5e-6 MPI rank count mismatch")
    require(summary.get("cuda_initialized") is True, "full-channel refined-source 1000-step dt=5e-6 CUDA not initialized")
    require(summary.get("run_log_has_no_abort_nan_or_cuda_error") is True, "full-channel refined-source 1000-step dt=5e-6 runtime log regressed")
    require(summary.get("full_dataverse_domain") is True, "full-channel refined-source 1000-step dt=5e-6 did not use full Dataverse domain")
    require(all(abs(float(v) - 0.025) <= 1.0e-12 for v in summary.get("dx_m", [])), "full-channel refined-source 1000-step dt=5e-6 dx mismatch")
    require(abs(float(summary.get("leak_radius_m", 0.0)) - 0.0023) <= 1.0e-15, "full-channel refined-source 1000-step dt=5e-6 leak radius mismatch")
    require(summary.get("active_volume_equals_single_cell") is True, "full-channel refined-source 1000-step dt=5e-6 active volume is not one cell")
    require(float(summary.get("source_cfl", 1.0)) < 0.15, "full-channel refined-source 1000-step dt=5e-6 source CFL too large")
    require(int(summary.get("max_step", 0)) == 1000, "full-channel refined-source 1000-step dt=5e-6 max_step mismatch")
    require(abs(float(summary.get("time_end_s", 0.0)) - 0.005) <= 1.0e-12, "full-channel refined-source 1000-step dt=5e-6 time_end mismatch")
    require(float(summary.get("validation_max_yh2", 0.0)) > 0.0, "full-channel refined-source 1000-step dt=5e-6 plume missing")
    require(summary.get("clears_external_plume_reference_blocker") is False, "full-channel refined-source 1000-step dt=5e-6 must not clear strict blocker")
    require(summary.get("strict_blocker_still_open") is True, "full-channel refined-source 1000-step dt=5e-6 strict blocker state mismatch")
    return {
        "status": run.get("status"),
        "mpi_rank_count": summary.get("mpi_rank_count"),
        "cuda_initialized": summary.get("cuda_initialized"),
        "run_log_has_no_abort_nan_or_cuda_error": summary.get("run_log_has_no_abort_nan_or_cuda_error"),
        "full_dataverse_domain": summary.get("full_dataverse_domain"),
        "n_cell": summary.get("n_cell"),
        "dx_m": summary.get("dx_m"),
        "leak_radius_m": summary.get("leak_radius_m"),
        "active_volume_equals_single_cell": summary.get("active_volume_equals_single_cell"),
        "source_cfl": summary.get("source_cfl"),
        "max_step": summary.get("max_step"),
        "time_end_s": summary.get("time_end_s"),
        "validation_max_yh2": summary.get("validation_max_yh2"),
        "clears_external_plume_reference_blocker": summary.get("clears_external_plume_reference_blocker"),
        "strict_blocker_still_open": summary.get("strict_blocker_still_open"),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    traceability_path = Path(args.traceability)
    traceability = load_json(traceability_path)
    blockers = traceability.get("remaining_blockers", [])
    blocker_names = [b.get("blocker") for b in blockers if isinstance(b, dict)]
    external_plume_blocker_present = (
        "reference_agreement_is_threshold_only_not_external_plume_shape_dataset" in blocker_names
    )
    dataverse = build_dataverse_summary()
    dataverse_full_audit = build_dataverse_full_audit_summary()
    dataverse_timeseries_index = build_dataverse_timeseries_index_summary()
    dataverse_geometry_mapping = build_dataverse_geometry_mapping_summary()
    dataverse_reference_package = build_dataverse_reference_package_summary()
    dataverse_agreement_contract = build_dataverse_agreement_contract_summary()
    dataverse_cfd_scout = build_dataverse_cfd_scout_summary()
    dataverse_cfd_agreement_attempt = build_dataverse_cfd_agreement_attempt_summary()
    dataverse_cfd_45s_agreement_attempt = build_dataverse_cfd_45s_agreement_attempt_summary()
    dataverse_cfd_120s_agreement_attempt = build_dataverse_cfd_120s_agreement_attempt_summary()
    dataverse_120s_calibration_diagnosis = build_dataverse_120s_calibration_diagnosis_summary()
    dataverse_45s_calibration_r005_z08 = build_dataverse_45s_calibration_r005_z08_summary()
    dataverse_45s_calibration_sweep = build_dataverse_45s_calibration_sweep_summary()
    dataverse_physics_alignment = build_dataverse_physics_alignment_summary()
    dataverse_orifice_velocity_scout = build_dataverse_orifice_velocity_scout_summary()
    dataverse_open_boundary_scout = build_dataverse_open_boundary_scout_summary()
    dataverse_open_boundary_orifice_extended_01s = (
        build_dataverse_open_boundary_orifice_extended_01s_summary()
    )
    dataverse_open_boundary_orifice_extended_1s = (
        build_dataverse_open_boundary_orifice_extended_1s_summary()
    )
    dataverse_open_boundary_orifice_extended_2s = (
        build_dataverse_open_boundary_orifice_extended_2s_summary()
    )
    dataverse_refined_source_projection_probe = (
        build_dataverse_refined_source_projection_probe_summary()
    )
    dataverse_full_channel_refined_source_dx025_probe = (
        build_dataverse_full_channel_refined_source_dx025_probe_summary()
    )
    dataverse_full_channel_refined_source_dx025_500step = (
        build_dataverse_full_channel_refined_source_dx025_500step_summary()
    )
    dataverse_full_channel_refined_source_dx025_1000step_dt5em6 = (
        build_dataverse_full_channel_refined_source_dx025_1000step_dt5em6_summary()
    )
    dataverse_amr_source_projection_contract = load_json(DATAVERSE_AMR_SOURCE_PROJECTION_CONTRACT)
    require(
        dataverse_amr_source_projection_contract.get("status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-CONTRACT",
        "Dataverse AMR source projection contract is not PASS",
    )
    dataverse_amr_source_projection_contract_summary = dataverse_amr_source_projection_contract.get("summary", {})
    require(
        isinstance(dataverse_amr_source_projection_contract_summary, dict),
        "Dataverse AMR source projection contract summary missing",
    )
    require(
        dataverse_amr_source_projection_contract_summary.get("amr_source_projection_contract_ready") is True,
        "Dataverse AMR source projection contract is not ready",
    )
    require(
        dataverse_amr_source_projection_contract_summary.get("strict_blocker_still_open") is True,
        "Dataverse AMR source projection contract must not clear strict blocker",
    )
    dataverse_amr_source_projection_implementation = load_json(
        DATAVERSE_AMR_SOURCE_PROJECTION_IMPLEMENTATION
    )
    require(
        dataverse_amr_source_projection_implementation.get("status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-IMPLEMENTATION",
        "Dataverse AMR source projection implementation is not PASS",
    )
    dataverse_amr_source_projection_implementation_summary = (
        dataverse_amr_source_projection_implementation.get("summary", {})
    )
    require(
        isinstance(dataverse_amr_source_projection_implementation_summary, dict),
        "Dataverse AMR source projection implementation summary missing",
    )
    require(
        dataverse_amr_source_projection_implementation_summary.get(
            "amr_source_projection_implementation_ready"
        )
        is True,
        "Dataverse AMR source projection implementation is not ready",
    )
    require(
        dataverse_amr_source_projection_implementation_summary.get("strict_blocker_still_open")
        is True,
        "Dataverse AMR source projection implementation must not clear strict blocker",
    )
    dataverse_long_window_reconciliation = load_json(DATAVERSE_LONG_WINDOW_RECONCILIATION)
    require(
        dataverse_long_window_reconciliation.get("status")
        == "TRIAGED-DATAVERSE-OPEN-CHANNEL-LONG-WINDOW-REFINED-SOURCE-GAP",
        "Dataverse long-window reconciliation status mismatch",
    )
    dataverse_long_window_reconciliation_summary = dataverse_long_window_reconciliation.get("summary", {})
    require(
        isinstance(dataverse_long_window_reconciliation_summary, dict),
        "Dataverse long-window reconciliation summary missing",
    )
    require(
        dataverse_long_window_reconciliation_summary.get(
            "existing_120s_window_reaches_experimental_peak_interval"
        )
        is True,
        "Dataverse long-window reconciliation does not record existing 120s peak-window coverage",
    )
    require(
        dataverse_long_window_reconciliation_summary.get("current_refined_source_ready") is True,
        "Dataverse long-window reconciliation does not record current refined-source readiness",
    )
    require(
        dataverse_long_window_reconciliation_summary.get("strict_blocker_still_open") is True,
        "Dataverse long-window reconciliation must not clear strict blocker",
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_TRIAGED,
        "summary": {
            "external_plume_blocker_present": external_plume_blocker_present,
            "public_sbepv5_d27_geometry_and_release_conditions_found": True,
            "public_machine_readable_sbepv5_d27_timeseries_found": False,
            "public_dataverse_open_channel_machine_readable_timeseries_found": True,
            "public_machine_readable_external_plume_timeseries_found": True,
            "dataverse_metadata_file_count": dataverse["file_count"],
            "dataverse_sample_h2_sensor_column_count": dataverse["sample_zip"]["h2_concentration_sensor_column_count"],
            "dataverse_sample_md5_verified": dataverse["sample_zip_md5_verified"],
            "dataverse_full_dataset_audit_status": dataverse_full_audit["status"],
            "dataverse_full_dataset_expected_file_count": dataverse_full_audit["expected_file_count"],
            "dataverse_full_dataset_ready_file_count": dataverse_full_audit["ready_file_count"],
            "dataverse_full_dataset_zip_csv_audited_file_count": dataverse_full_audit["zip_csv_audited_file_count"],
            "dataverse_full_dataset_sensor_column_counts_seen": dataverse_full_audit["sensor_column_counts_seen"],
            "dataverse_full_dataset_all_files_ready": dataverse_full_audit["all_expected_files_ready"],
            "dataverse_timeseries_index_status": dataverse_timeseries_index["status"],
            "dataverse_timeseries_zip_case_count": dataverse_timeseries_index["zip_case_count"],
            "dataverse_timeseries_strong_plume_candidate_count": dataverse_timeseries_index["strong_plume_candidate_count"],
            "dataverse_timeseries_ready_for_case_selection": dataverse_timeseries_index["ready_for_case_selection"],
            "dataverse_timeseries_top_candidate_filenames": dataverse_timeseries_index["top_candidate_filenames"],
            "dataverse_geometry_mapping_status": dataverse_geometry_mapping["status"],
            "dataverse_geometry_sensor_coordinate_count": dataverse_geometry_mapping["sensor_coordinate_count"],
            "dataverse_geometry_case_mapping_count": dataverse_geometry_mapping["case_mapping_count"],
            "dataverse_geometry_ready_for_sensor_sampling_map": dataverse_geometry_mapping["ready_for_sensor_sampling_map"],
            "dataverse_geometry_ready_for_full_mesh_parity": dataverse_geometry_mapping["ready_for_full_geometry_mesh_parity"],
            "dataverse_geometry_obstacle_exact_bounds_available": dataverse_geometry_mapping[
                "obstacle_geometry_exact_bounds_available"
            ],
            "dataverse_reference_package_status": dataverse_reference_package["status"],
            "dataverse_reference_selected_case_filename": dataverse_reference_package["selected_case_filename"],
            "dataverse_reference_article_test_id": dataverse_reference_package["article_test_id"],
            "dataverse_reference_raw_row_count": dataverse_reference_package["raw_row_count"],
            "dataverse_reference_sensor_time_sample_count": dataverse_reference_package[
                "sensor_time_sample_count"
            ],
            "dataverse_reference_sensor_record_count": dataverse_reference_package["sensor_record_count"],
            "dataverse_reference_duration_s": dataverse_reference_package["duration_s"],
            "dataverse_reference_peak_x_h2": dataverse_reference_package["h2_peak_x_h2"],
            "dataverse_reference_lfl_sensor_count": dataverse_reference_package["lfl_sensor_count"],
            "dataverse_reference_ready_for_signal_sampling": dataverse_reference_package[
                "ready_for_reference_signal_sampling"
            ],
            "dataverse_reference_ready_for_cfd_agreement_scoring": dataverse_reference_package[
                "ready_for_cfd_reference_agreement_scoring"
            ],
            "dataverse_agreement_contract_status": dataverse_agreement_contract["status"],
            "dataverse_agreement_contract_mode": dataverse_agreement_contract["mode"],
            "dataverse_agreement_sensor_count": dataverse_agreement_contract["agreement_sensor_count"],
            "dataverse_agreement_lfl_sensor_count": dataverse_agreement_contract["agreement_lfl_sensor_count"],
            "dataverse_agreement_peak_pass_count": dataverse_agreement_contract["peak_pass_count"],
            "dataverse_agreement_nrmse_pass_count": dataverse_agreement_contract["nrmse_pass_count"],
            "dataverse_agreement_ready_for_cfd_scoring": dataverse_agreement_contract[
                "ready_for_cfd_reference_agreement_scoring"
            ],
            "dataverse_agreement_production_completed": dataverse_agreement_contract[
                "production_agreement_completed"
            ],
            "dataverse_cfd_scout_status": dataverse_cfd_scout["status"],
            "dataverse_cfd_scout_mpi_rank_count": dataverse_cfd_scout["mpi_rank_count"],
            "dataverse_cfd_scout_cuda_initialized": dataverse_cfd_scout["cuda_initialized"],
            "dataverse_cfd_scout_plotfile_count": dataverse_cfd_scout["plotfile_count"],
            "dataverse_cfd_scout_sensor_count": dataverse_cfd_scout["sensor_count"],
            "dataverse_cfd_scout_sensor_timeseries_rows": dataverse_cfd_scout["sensor_timeseries_rows"],
            "dataverse_cfd_scout_time_end_s": dataverse_cfd_scout["time_end_s"],
            "dataverse_cfd_scout_mass_ratio_final": dataverse_cfd_scout["mass_ratio_final"],
            "dataverse_cfd_scout_agreement_attempt_status": dataverse_cfd_scout["agreement_attempt_status"],
            "dataverse_cfd_scout_ready_for_longer_campaign": dataverse_cfd_scout[
                "ready_for_longer_dataverse_cfd_campaign"
            ],
            "dataverse_cfd_agreement_attempt_status": dataverse_cfd_agreement_attempt["status"],
            "dataverse_cfd_agreement_attempt_sensor_count": dataverse_cfd_agreement_attempt["sensor_count"],
            "dataverse_cfd_agreement_attempt_common_sample_count_min": dataverse_cfd_agreement_attempt[
                "common_sample_count_min"
            ],
            "dataverse_cfd_agreement_attempt_common_sample_count_max": dataverse_cfd_agreement_attempt[
                "common_sample_count_max"
            ],
            "dataverse_cfd_agreement_attempt_failed_sensor_count": dataverse_cfd_agreement_attempt[
                "failed_sensor_count"
            ],
            "dataverse_cfd_agreement_attempt_peak_pass_count": dataverse_cfd_agreement_attempt["peak_pass_count"],
            "dataverse_cfd_agreement_attempt_nrmse_pass_count": dataverse_cfd_agreement_attempt["nrmse_pass_count"],
            "dataverse_cfd_agreement_attempt_arrival_pass_count": dataverse_cfd_agreement_attempt[
                "arrival_pass_count"
            ],
            "dataverse_cfd_agreement_attempt_simulation_time_end_s": dataverse_cfd_agreement_attempt[
                "simulation_time_end_s"
            ],
            "dataverse_cfd_agreement_attempt_mass_ratio_final": dataverse_cfd_agreement_attempt[
                "simulation_mass_ratio_final"
            ],
            "dataverse_cfd_agreement_attempt_production_completed": dataverse_cfd_agreement_attempt[
                "production_agreement_completed"
            ],
            "dataverse_cfd_agreement_attempt_clears_external_plume_blocker": dataverse_cfd_agreement_attempt[
                "clears_external_plume_reference_blocker"
            ],
            "dataverse_cfd_45s_agreement_attempt_status": dataverse_cfd_45s_agreement_attempt["status"],
            "dataverse_cfd_45s_agreement_attempt_sensor_count": dataverse_cfd_45s_agreement_attempt["sensor_count"],
            "dataverse_cfd_45s_agreement_attempt_common_sample_count_min": dataverse_cfd_45s_agreement_attempt[
                "common_sample_count_min"
            ],
            "dataverse_cfd_45s_agreement_attempt_common_sample_count_max": dataverse_cfd_45s_agreement_attempt[
                "common_sample_count_max"
            ],
            "dataverse_cfd_45s_agreement_attempt_failed_sensor_count": dataverse_cfd_45s_agreement_attempt[
                "failed_sensor_count"
            ],
            "dataverse_cfd_45s_agreement_attempt_peak_pass_count": dataverse_cfd_45s_agreement_attempt[
                "peak_pass_count"
            ],
            "dataverse_cfd_45s_agreement_attempt_nrmse_pass_count": dataverse_cfd_45s_agreement_attempt[
                "nrmse_pass_count"
            ],
            "dataverse_cfd_45s_agreement_attempt_arrival_pass_count": dataverse_cfd_45s_agreement_attempt[
                "arrival_pass_count"
            ],
            "dataverse_cfd_45s_agreement_attempt_simulation_time_end_s": dataverse_cfd_45s_agreement_attempt[
                "simulation_time_end_s"
            ],
            "dataverse_cfd_45s_agreement_attempt_mass_ratio_final": dataverse_cfd_45s_agreement_attempt[
                "simulation_mass_ratio_final"
            ],
            "dataverse_cfd_45s_agreement_attempt_production_completed": dataverse_cfd_45s_agreement_attempt[
                "production_agreement_completed"
            ],
            "dataverse_cfd_45s_agreement_attempt_clears_external_plume_blocker": dataverse_cfd_45s_agreement_attempt[
                "clears_external_plume_reference_blocker"
            ],
            "dataverse_cfd_120s_agreement_attempt_status": dataverse_cfd_120s_agreement_attempt["status"],
            "dataverse_cfd_120s_agreement_attempt_sensor_count": dataverse_cfd_120s_agreement_attempt["sensor_count"],
            "dataverse_cfd_120s_agreement_attempt_common_sample_count_min": dataverse_cfd_120s_agreement_attempt[
                "common_sample_count_min"
            ],
            "dataverse_cfd_120s_agreement_attempt_common_sample_count_max": dataverse_cfd_120s_agreement_attempt[
                "common_sample_count_max"
            ],
            "dataverse_cfd_120s_agreement_attempt_failed_sensor_count": dataverse_cfd_120s_agreement_attempt[
                "failed_sensor_count"
            ],
            "dataverse_cfd_120s_agreement_attempt_peak_pass_count": dataverse_cfd_120s_agreement_attempt[
                "peak_pass_count"
            ],
            "dataverse_cfd_120s_agreement_attempt_nrmse_pass_count": dataverse_cfd_120s_agreement_attempt[
                "nrmse_pass_count"
            ],
            "dataverse_cfd_120s_agreement_attempt_arrival_pass_count": dataverse_cfd_120s_agreement_attempt[
                "arrival_pass_count"
            ],
            "dataverse_cfd_120s_agreement_attempt_simulation_time_end_s": dataverse_cfd_120s_agreement_attempt[
                "simulation_time_end_s"
            ],
            "dataverse_cfd_120s_agreement_attempt_mass_ratio_final": dataverse_cfd_120s_agreement_attempt[
                "simulation_mass_ratio_final"
            ],
            "dataverse_cfd_120s_agreement_attempt_production_completed": dataverse_cfd_120s_agreement_attempt[
                "production_agreement_completed"
            ],
            "dataverse_cfd_120s_agreement_attempt_clears_external_plume_blocker": dataverse_cfd_120s_agreement_attempt[
                "clears_external_plume_reference_blocker"
            ],
            "dataverse_120s_calibration_diagnosis_status": dataverse_120s_calibration_diagnosis["status"],
            "dataverse_120s_source_radius_ratio": dataverse_120s_calibration_diagnosis["source_radius_ratio"],
            "dataverse_120s_source_area_ratio": dataverse_120s_calibration_diagnosis["source_area_ratio"],
            "dataverse_120s_source_center_z_offset_m": dataverse_120s_calibration_diagnosis[
                "source_center_z_offset_m"
            ],
            "dataverse_120s_minimum_active_radius_at_reference_source_on_current_grid_m": dataverse_120s_calibration_diagnosis[
                "minimum_active_radius_at_reference_source_on_current_grid_m"
            ],
            "dataverse_120s_severe_peak_error_count": dataverse_120s_calibration_diagnosis[
                "severe_peak_error_count"
            ],
            "dataverse_120s_infinite_arrival_error_count": dataverse_120s_calibration_diagnosis[
                "infinite_arrival_error_count"
            ],
            "dataverse_120s_ready_for_next_calibration_sweep": dataverse_120s_calibration_diagnosis[
                "ready_for_next_calibration_sweep"
            ],
            "dataverse_45s_calibration_r005_z08_status": dataverse_45s_calibration_r005_z08["status"],
            "dataverse_45s_calibration_r005_z08_candidate_peak_pass_count": dataverse_45s_calibration_r005_z08[
                "candidate_peak_pass_count"
            ],
            "dataverse_45s_calibration_r005_z08_candidate_nrmse_pass_count": dataverse_45s_calibration_r005_z08[
                "candidate_nrmse_pass_count"
            ],
            "dataverse_45s_calibration_r005_z08_candidate_arrival_pass_count": dataverse_45s_calibration_r005_z08[
                "candidate_arrival_pass_count"
            ],
            "dataverse_45s_calibration_r005_z08_promote_to_120s": dataverse_45s_calibration_r005_z08[
                "promote_to_120s_peak_window"
            ],
            "dataverse_45s_calibration_sweep_status": dataverse_45s_calibration_sweep["status"],
            "dataverse_45s_calibration_sweep_case_count": dataverse_45s_calibration_sweep["case_count"],
            "dataverse_45s_calibration_sweep_stable_case_count": dataverse_45s_calibration_sweep[
                "stable_case_count"
            ],
            "dataverse_45s_calibration_sweep_promoted_case_count": dataverse_45s_calibration_sweep[
                "promoted_case_count"
            ],
            "dataverse_45s_calibration_sweep_best_case_label": dataverse_45s_calibration_sweep[
                "best_case_label"
            ],
            "dataverse_45s_calibration_sweep_ready_for_next_screen": dataverse_45s_calibration_sweep[
                "ready_for_next_calibration_screen"
            ],
            "dataverse_physics_alignment_status": dataverse_physics_alignment["status"],
            "dataverse_physics_alignment_equivalent_orifice_velocity_m_s": dataverse_physics_alignment[
                "equivalent_orifice_velocity_m_s"
            ],
            "dataverse_physics_alignment_velocity_ratio": dataverse_physics_alignment[
                "equivalent_to_baseline_velocity_ratio"
            ],
            "dataverse_physics_alignment_active_cell_count_for_experimental_radius": dataverse_physics_alignment[
                "active_cell_count_for_experimental_radius"
            ],
            "dataverse_physics_alignment_ready_for_orifice_velocity_scout": dataverse_physics_alignment[
                "ready_for_orifice_velocity_scout"
            ],
            "dataverse_orifice_velocity_scout_status": dataverse_orifice_velocity_scout["status"],
            "dataverse_orifice_velocity_scout_mpi_rank_count": dataverse_orifice_velocity_scout["mpi_rank_count"],
            "dataverse_orifice_velocity_scout_cuda_initialized": dataverse_orifice_velocity_scout["cuda_initialized"],
            "dataverse_orifice_velocity_scout_time_end_s": dataverse_orifice_velocity_scout["time_end_s"],
            "dataverse_orifice_velocity_scout_mass_ratio_final": dataverse_orifice_velocity_scout[
                "mass_ratio_final"
            ],
            "dataverse_orifice_velocity_scout_max_yh2": dataverse_orifice_velocity_scout["max_yh2"],
            "dataverse_open_boundary_scout_status": dataverse_open_boundary_scout["status"],
            "dataverse_open_boundary_scout_mpi_rank_count": dataverse_open_boundary_scout["mpi_rank_count"],
            "dataverse_open_boundary_scout_cuda_initialized": dataverse_open_boundary_scout["cuda_initialized"],
            "dataverse_open_boundary_scout_time_end_s": dataverse_open_boundary_scout["time_end_s"],
            "dataverse_open_boundary_scout_mass_ratio_final": dataverse_open_boundary_scout["mass_ratio_final"],
            "dataverse_open_boundary_scout_max_yh2": dataverse_open_boundary_scout["max_yh2"],
            "dataverse_open_boundary_orifice_extended_01s_status": dataverse_open_boundary_orifice_extended_01s[
                "status"
            ],
            "dataverse_open_boundary_orifice_extended_01s_mpi_rank_count": dataverse_open_boundary_orifice_extended_01s[
                "mpi_rank_count"
            ],
            "dataverse_open_boundary_orifice_extended_01s_cuda_initialized": dataverse_open_boundary_orifice_extended_01s[
                "cuda_initialized"
            ],
            "dataverse_open_boundary_orifice_extended_01s_time_end_s": dataverse_open_boundary_orifice_extended_01s[
                "time_end_s"
            ],
            "dataverse_open_boundary_orifice_extended_01s_mass_ratio_final": dataverse_open_boundary_orifice_extended_01s[
                "mass_ratio_final"
            ],
            "dataverse_open_boundary_orifice_extended_01s_max_yh2": dataverse_open_boundary_orifice_extended_01s[
                "max_yh2"
            ],
            "dataverse_open_boundary_orifice_extended_01s_downstream_fraction": dataverse_open_boundary_orifice_extended_01s[
                "downstream_fraction"
            ],
            "dataverse_open_boundary_orifice_extended_1s_status": dataverse_open_boundary_orifice_extended_1s[
                "status"
            ],
            "dataverse_open_boundary_orifice_extended_1s_mpi_rank_count": dataverse_open_boundary_orifice_extended_1s[
                "mpi_rank_count"
            ],
            "dataverse_open_boundary_orifice_extended_1s_cuda_initialized": dataverse_open_boundary_orifice_extended_1s[
                "cuda_initialized"
            ],
            "dataverse_open_boundary_orifice_extended_1s_time_end_s": dataverse_open_boundary_orifice_extended_1s[
                "time_end_s"
            ],
            "dataverse_open_boundary_orifice_extended_1s_mass_ratio_final": dataverse_open_boundary_orifice_extended_1s[
                "mass_ratio_final"
            ],
            "dataverse_open_boundary_orifice_extended_1s_max_yh2": dataverse_open_boundary_orifice_extended_1s[
                "max_yh2"
            ],
            "dataverse_open_boundary_orifice_extended_1s_downstream_fraction": dataverse_open_boundary_orifice_extended_1s[
                "downstream_fraction"
            ],
            "dataverse_open_boundary_orifice_extended_2s_status": dataverse_open_boundary_orifice_extended_2s[
                "status"
            ],
            "dataverse_open_boundary_orifice_extended_2s_mpi_rank_count": dataverse_open_boundary_orifice_extended_2s[
                "mpi_rank_count"
            ],
            "dataverse_open_boundary_orifice_extended_2s_cuda_initialized": dataverse_open_boundary_orifice_extended_2s[
                "cuda_initialized"
            ],
            "dataverse_open_boundary_orifice_extended_2s_time_end_s": dataverse_open_boundary_orifice_extended_2s[
                "time_end_s"
            ],
            "dataverse_open_boundary_orifice_extended_2s_mass_ratio_final": dataverse_open_boundary_orifice_extended_2s[
                "mass_ratio_final"
            ],
            "dataverse_open_boundary_orifice_extended_2s_max_yh2": dataverse_open_boundary_orifice_extended_2s[
                "max_yh2"
            ],
            "dataverse_open_boundary_orifice_extended_2s_downstream_fraction": dataverse_open_boundary_orifice_extended_2s[
                "downstream_fraction"
            ],
            "dataverse_open_boundary_orifice_extended_2s_sensor_timeseries_rows": dataverse_open_boundary_orifice_extended_2s[
                "sensor_timeseries_rows"
            ],
            "dataverse_open_boundary_orifice_extended_2s_plotfile_count": dataverse_open_boundary_orifice_extended_2s[
                "plotfile_count"
            ],
            "dataverse_open_boundary_orifice_extended_2s_run_log_has_no_abort_nan_or_cuda_error": dataverse_open_boundary_orifice_extended_2s[
                "run_log_has_no_abort_nan_or_cuda_error"
            ],
            "dataverse_open_boundary_orifice_extended_2s_clears_external_plume_blocker": dataverse_open_boundary_orifice_extended_2s[
                "clears_external_plume_reference_blocker"
            ],
            "dataverse_open_boundary_orifice_extended_2s_strict_blocker_still_open": dataverse_open_boundary_orifice_extended_2s[
                "strict_blocker_still_open"
            ],
            "dataverse_open_boundary_orifice_extended_multi_second_screen_completed": True,
            "dataverse_refined_source_projection_probe_status": dataverse_refined_source_projection_probe[
                "status"
            ],
            "dataverse_refined_source_projection_probe_mpi_rank_count": dataverse_refined_source_projection_probe[
                "mpi_rank_count"
            ],
            "dataverse_refined_source_projection_probe_cuda_initialized": dataverse_refined_source_projection_probe[
                "cuda_initialized"
            ],
            "dataverse_refined_source_projection_probe_run_log_has_no_abort_nan_or_cuda_error": dataverse_refined_source_projection_probe[
                "run_log_has_no_abort_nan_or_cuda_error"
            ],
            "dataverse_refined_source_projection_probe_dx_m": dataverse_refined_source_projection_probe[
                "dx_m"
            ],
            "dataverse_refined_source_projection_probe_leak_radius_m": dataverse_refined_source_projection_probe[
                "leak_radius_m"
            ],
            "dataverse_refined_source_projection_probe_active_volume_equals_single_cell": dataverse_refined_source_projection_probe[
                "active_volume_equals_single_cell"
            ],
            "dataverse_refined_source_projection_probe_source_cfl": dataverse_refined_source_projection_probe[
                "source_cfl"
            ],
            "dataverse_refined_source_projection_probe_validation_max_yh2": dataverse_refined_source_projection_probe[
                "validation_max_yh2"
            ],
            "dataverse_refined_source_projection_probe_clears_external_plume_blocker": dataverse_refined_source_projection_probe[
                "clears_external_plume_reference_blocker"
            ],
            "dataverse_refined_source_projection_probe_strict_blocker_still_open": dataverse_refined_source_projection_probe[
                "strict_blocker_still_open"
            ],
            "dataverse_refined_source_projection_screen_completed": True,
            "dataverse_full_channel_refined_source_dx025_probe_status": dataverse_full_channel_refined_source_dx025_probe[
                "status"
            ],
            "dataverse_full_channel_refined_source_dx025_probe_mpi_rank_count": dataverse_full_channel_refined_source_dx025_probe[
                "mpi_rank_count"
            ],
            "dataverse_full_channel_refined_source_dx025_probe_cuda_initialized": dataverse_full_channel_refined_source_dx025_probe[
                "cuda_initialized"
            ],
            "dataverse_full_channel_refined_source_dx025_probe_run_log_has_no_abort_nan_or_cuda_error": dataverse_full_channel_refined_source_dx025_probe[
                "run_log_has_no_abort_nan_or_cuda_error"
            ],
            "dataverse_full_channel_refined_source_dx025_probe_full_dataverse_domain": dataverse_full_channel_refined_source_dx025_probe[
                "full_dataverse_domain"
            ],
            "dataverse_full_channel_refined_source_dx025_probe_n_cell": dataverse_full_channel_refined_source_dx025_probe[
                "n_cell"
            ],
            "dataverse_full_channel_refined_source_dx025_probe_dx_m": dataverse_full_channel_refined_source_dx025_probe[
                "dx_m"
            ],
            "dataverse_full_channel_refined_source_dx025_probe_leak_radius_m": dataverse_full_channel_refined_source_dx025_probe[
                "leak_radius_m"
            ],
            "dataverse_full_channel_refined_source_dx025_probe_active_volume_equals_single_cell": dataverse_full_channel_refined_source_dx025_probe[
                "active_volume_equals_single_cell"
            ],
            "dataverse_full_channel_refined_source_dx025_probe_source_cfl": dataverse_full_channel_refined_source_dx025_probe[
                "source_cfl"
            ],
            "dataverse_full_channel_refined_source_dx025_probe_validation_max_yh2": dataverse_full_channel_refined_source_dx025_probe[
                "validation_max_yh2"
            ],
            "dataverse_full_channel_refined_source_dx025_probe_clears_external_plume_blocker": dataverse_full_channel_refined_source_dx025_probe[
                "clears_external_plume_reference_blocker"
            ],
            "dataverse_full_channel_refined_source_dx025_probe_strict_blocker_still_open": dataverse_full_channel_refined_source_dx025_probe[
                "strict_blocker_still_open"
            ],
            "dataverse_full_channel_refined_source_dx025_screen_completed": True,
            "dataverse_full_channel_refined_source_dx025_500step_status": dataverse_full_channel_refined_source_dx025_500step[
                "status"
            ],
            "dataverse_full_channel_refined_source_dx025_500step_mpi_rank_count": dataverse_full_channel_refined_source_dx025_500step[
                "mpi_rank_count"
            ],
            "dataverse_full_channel_refined_source_dx025_500step_cuda_initialized": dataverse_full_channel_refined_source_dx025_500step[
                "cuda_initialized"
            ],
            "dataverse_full_channel_refined_source_dx025_500step_run_log_has_no_abort_nan_or_cuda_error": dataverse_full_channel_refined_source_dx025_500step[
                "run_log_has_no_abort_nan_or_cuda_error"
            ],
            "dataverse_full_channel_refined_source_dx025_500step_full_dataverse_domain": dataverse_full_channel_refined_source_dx025_500step[
                "full_dataverse_domain"
            ],
            "dataverse_full_channel_refined_source_dx025_500step_dx_m": dataverse_full_channel_refined_source_dx025_500step[
                "dx_m"
            ],
            "dataverse_full_channel_refined_source_dx025_500step_leak_radius_m": dataverse_full_channel_refined_source_dx025_500step[
                "leak_radius_m"
            ],
            "dataverse_full_channel_refined_source_dx025_500step_source_cfl": dataverse_full_channel_refined_source_dx025_500step[
                "source_cfl"
            ],
            "dataverse_full_channel_refined_source_dx025_500step_time_end_s": dataverse_full_channel_refined_source_dx025_500step[
                "time_end_s"
            ],
            "dataverse_full_channel_refined_source_dx025_500step_validation_max_yh2": dataverse_full_channel_refined_source_dx025_500step[
                "validation_max_yh2"
            ],
            "dataverse_full_channel_refined_source_dx025_500step_clears_external_plume_blocker": dataverse_full_channel_refined_source_dx025_500step[
                "clears_external_plume_reference_blocker"
            ],
            "dataverse_full_channel_refined_source_dx025_500step_strict_blocker_still_open": dataverse_full_channel_refined_source_dx025_500step[
                "strict_blocker_still_open"
            ],
            "dataverse_full_channel_refined_source_dx025_500step_completed": True,
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_status": dataverse_full_channel_refined_source_dx025_1000step_dt5em6[
                "status"
            ],
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_mpi_rank_count": dataverse_full_channel_refined_source_dx025_1000step_dt5em6[
                "mpi_rank_count"
            ],
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_cuda_initialized": dataverse_full_channel_refined_source_dx025_1000step_dt5em6[
                "cuda_initialized"
            ],
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_run_log_has_no_abort_nan_or_cuda_error": dataverse_full_channel_refined_source_dx025_1000step_dt5em6[
                "run_log_has_no_abort_nan_or_cuda_error"
            ],
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_full_dataverse_domain": dataverse_full_channel_refined_source_dx025_1000step_dt5em6[
                "full_dataverse_domain"
            ],
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_dx_m": dataverse_full_channel_refined_source_dx025_1000step_dt5em6[
                "dx_m"
            ],
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_leak_radius_m": dataverse_full_channel_refined_source_dx025_1000step_dt5em6[
                "leak_radius_m"
            ],
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_source_cfl": dataverse_full_channel_refined_source_dx025_1000step_dt5em6[
                "source_cfl"
            ],
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_time_end_s": dataverse_full_channel_refined_source_dx025_1000step_dt5em6[
                "time_end_s"
            ],
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_validation_max_yh2": dataverse_full_channel_refined_source_dx025_1000step_dt5em6[
                "validation_max_yh2"
            ],
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_clears_external_plume_blocker": dataverse_full_channel_refined_source_dx025_1000step_dt5em6[
                "clears_external_plume_reference_blocker"
            ],
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_strict_blocker_still_open": dataverse_full_channel_refined_source_dx025_1000step_dt5em6[
                "strict_blocker_still_open"
            ],
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_completed": True,
            "dataverse_amr_source_projection_contract_status": dataverse_amr_source_projection_contract[
                "status"
            ],
            "dataverse_amr_source_projection_contract_ready": dataverse_amr_source_projection_contract_summary[
                "amr_source_projection_contract_ready"
            ],
            "dataverse_amr_source_projection_contract_problem_hook_single_level": dataverse_amr_source_projection_contract_summary[
                "current_source_projection_is_single_level_cell_centered"
            ],
            "dataverse_amr_source_projection_contract_problem_hook_lacks_level_aware_mask": dataverse_amr_source_projection_contract_summary[
                "lacks_level_aware_mask"
            ],
            "dataverse_amr_source_projection_current_single_level": False,
            "dataverse_amr_source_projection_lacks_level_aware_mask": False,
            "dataverse_amr_source_projection_implementation_status": dataverse_amr_source_projection_implementation[
                "status"
            ],
            "dataverse_amr_source_projection_implementation_ready": dataverse_amr_source_projection_implementation_summary[
                "amr_source_projection_implementation_ready"
            ],
            "dataverse_amr_source_projection_framework_level_owner_mask_implemented": dataverse_amr_source_projection_implementation_summary[
                "framework_level_owner_mask_implemented"
            ],
            "dataverse_amr_source_projection_preserves_non_user_ext_sources": dataverse_amr_source_projection_implementation_summary[
                "non_user_ext_sources_preserved_on_fine_covered_coarse_cells"
            ],
            "dataverse_amr_source_projection_finest_available_level_only": dataverse_amr_source_projection_implementation_summary[
                "source_projected_only_on_finest_available_level"
            ],
            "dataverse_amr_source_projection_recommended_refinement_ratio": dataverse_amr_source_projection_contract_summary[
                "recommended_refinement_ratio_from_dx025"
            ],
            "dataverse_amr_source_projection_recommended_finest_dx_m": dataverse_amr_source_projection_contract_summary[
                "recommended_finest_dx_m"
            ],
            "dataverse_amr_source_projection_strict_blocker_still_open": dataverse_amr_source_projection_contract_summary[
                "strict_blocker_still_open"
            ],
            "dataverse_long_window_reconciliation_status": dataverse_long_window_reconciliation[
                "status"
            ],
            "dataverse_existing_120s_reaches_peak_interval": dataverse_long_window_reconciliation_summary[
                "existing_120s_window_reaches_experimental_peak_interval"
            ],
            "dataverse_existing_120s_all_sensors_passed": dataverse_long_window_reconciliation_summary[
                "existing_120s_all_sensors_passed"
            ],
            "dataverse_existing_120s_failed_sensor_count": dataverse_long_window_reconciliation_summary[
                "existing_120s_failed_sensor_count"
            ],
            "dataverse_current_refined_source_long_window_time_end_s": dataverse_long_window_reconciliation_summary[
                "current_refined_source_time_end_s"
            ],
            "dataverse_current_refined_source_steps_to_113s": dataverse_long_window_reconciliation_summary[
                "steps_to_113s_at_current_refined_dt"
            ],
            "strict_external_plume_blocker_cleared": False,
            "strict_external_plume_next_actions": [
                "Promote the completed full-channel dx=0.025 refined-source 1000-step dt=5e-6 MPI+CUDA screen into a longer sensor-history agreement window using the implemented AMR finest-owner source projection.",
                "Do not count the existing 120 s DataverseNO run as strict credit: it reaches the 113-117 s peak interval but uses the older inflated source radius and fails all-sensor agreement thresholds.",
                "Map exact DataverseNO obstacle/component bounds before claiming full geometry mesh parity.",
                "Retain SBEPV5/D27 as an optional secondary benchmark if original Excel can be obtained or if controlled digitization is performed.",
            ],
            "public_source_count": len(SOURCES),
        },
        "sources": SOURCES,
        "dataverse_open_channel_dataset": dataverse,
        "dataverse_open_channel_full_dataset_audit": dataverse_full_audit,
        "dataverse_open_channel_timeseries_index": dataverse_timeseries_index,
        "dataverse_open_channel_geometry_mapping": dataverse_geometry_mapping,
        "dataverse_open_channel_reference_package": dataverse_reference_package,
        "dataverse_open_channel_agreement_contract": dataverse_agreement_contract,
        "dataverse_open_channel_cfd_scout": dataverse_cfd_scout,
        "dataverse_open_channel_cfd_agreement_attempt": dataverse_cfd_agreement_attempt,
        "dataverse_open_channel_cfd_45s_agreement_attempt": dataverse_cfd_45s_agreement_attempt,
        "dataverse_open_channel_cfd_120s_agreement_attempt": dataverse_cfd_120s_agreement_attempt,
        "dataverse_open_channel_120s_calibration_diagnosis": dataverse_120s_calibration_diagnosis,
        "dataverse_open_channel_45s_calibration_r005_z08": dataverse_45s_calibration_r005_z08,
        "dataverse_open_channel_45s_calibration_sweep": dataverse_45s_calibration_sweep,
        "dataverse_open_channel_physics_alignment": dataverse_physics_alignment,
        "dataverse_open_channel_orifice_velocity_scout": dataverse_orifice_velocity_scout,
        "dataverse_open_channel_open_boundary_scout": dataverse_open_boundary_scout,
        "dataverse_open_channel_open_boundary_orifice_extended_01s": dataverse_open_boundary_orifice_extended_01s,
        "dataverse_open_channel_open_boundary_orifice_extended_1s": dataverse_open_boundary_orifice_extended_1s,
        "dataverse_open_channel_open_boundary_orifice_extended_2s": dataverse_open_boundary_orifice_extended_2s,
        "dataverse_refined_source_projection_probe": dataverse_refined_source_projection_probe,
        "dataverse_full_channel_refined_source_dx025_probe": dataverse_full_channel_refined_source_dx025_probe,
        "dataverse_full_channel_refined_source_dx025_500step": dataverse_full_channel_refined_source_dx025_500step,
        "dataverse_full_channel_refined_source_dx025_1000step_dt5em6": dataverse_full_channel_refined_source_dx025_1000step_dt5em6,
        "dataverse_open_channel_amr_source_projection_contract": dataverse_amr_source_projection_contract_summary,
        "available_public_fields": {
            "vessel_size_m": {"x_width": 1.20, "y_depth": 0.20, "z_height": 0.90},
            "baffle_count": 4,
            "baffle_size_m": {"y_depth": 0.20, "z_height": 0.30},
            "vent_size_m": {"y_width": 0.10, "z_height": 0.20},
            "release_period_s": 60,
            "nozzle_diameter_mm": 12,
            "exit_velocity_m_s": 10.17,
            "flow_rate_norm_l_s": 1.15,
            "jet_location_m": {"x": 0.03, "y": 0.1, "z": 0.145},
            "reliable_sensor_ids_reported": [1, 2, 5, 7, 8, 9, 10, 12],
            "problematic_sensor_ids_reported": [3, 4, 6, 11],
        },
        "missing_for_strict_credit": [
            "DataverseNO obstacle/component geometry exact bounds mapped into repository-ingestable geometry form",
            "longer DataverseNO refined-source/AMR CFD campaign reaching the 113-117 s experimental peak interval",
            "production agreement metrics passing accepted thresholds on real CFD sensor time histories",
            "longer boundary-condition parity and refined orifice/source projection screens using the new physics-alignment diagnosis",
            "controlled digitization uncertainty if plots are used instead of original Excel",
        ],
        "evidence_files": [
            evidence_entry("master_plan_traceability_report", traceability_path),
            evidence_entry("dataverse_dataset_metadata", DATAVERSE_METADATA),
            evidence_entry("dataverse_sample_zip", DATAVERSE_SAMPLE_ZIP),
            evidence_entry("dataverse_sample_zip_listing", DATAVERSE_SAMPLE_ZIP_LISTING),
            evidence_entry("dataverse_full_dataset_audit", DATAVERSE_FULL_AUDIT),
            evidence_entry("dataverse_timeseries_index", DATAVERSE_TIMESERIES_INDEX),
            evidence_entry("dataverse_geometry_mapping", DATAVERSE_GEOMETRY_MAPPING),
            evidence_entry("dataverse_reference_package", DATAVERSE_REFERENCE_PACKAGE),
            evidence_entry("dataverse_agreement_contract", DATAVERSE_AGREEMENT_CONTRACT),
            evidence_entry("dataverse_cfd_scout", DATAVERSE_CFD_SCOUT),
            evidence_entry("dataverse_cfd_agreement_attempt", DATAVERSE_CFD_AGREEMENT_ATTEMPT),
            evidence_entry("dataverse_cfd_45s_agreement_attempt", DATAVERSE_CFD_45S_AGREEMENT_ATTEMPT),
            evidence_entry("dataverse_cfd_120s_agreement_attempt", DATAVERSE_CFD_120S_AGREEMENT_ATTEMPT),
            evidence_entry("dataverse_120s_calibration_diagnosis", DATAVERSE_120S_CALIBRATION_DIAGNOSIS),
            evidence_entry("dataverse_45s_calibration_r005_z08", DATAVERSE_45S_CALIBRATION_R005_Z08),
            evidence_entry("dataverse_45s_calibration_sweep", DATAVERSE_45S_CALIBRATION_SWEEP),
            evidence_entry("dataverse_physics_alignment", DATAVERSE_PHYSICS_ALIGNMENT),
            evidence_entry("dataverse_orifice_velocity_scout", DATAVERSE_ORIFICE_VELOCITY_SCOUT),
            evidence_entry("dataverse_open_boundary_scout", DATAVERSE_OPEN_BOUNDARY_SCOUT),
            evidence_entry("dataverse_open_boundary_orifice_extended_01s", DATAVERSE_OPEN_BOUNDARY_ORIFICE_EXTENDED_01S),
            evidence_entry("dataverse_open_boundary_orifice_extended_1s", DATAVERSE_OPEN_BOUNDARY_ORIFICE_EXTENDED_1S),
            evidence_entry("dataverse_open_boundary_orifice_extended_2s", DATAVERSE_OPEN_BOUNDARY_ORIFICE_EXTENDED_2S),
            evidence_entry("dataverse_refined_source_projection_probe", DATAVERSE_REFINED_SOURCE_PROJECTION_PROBE),
            evidence_entry("dataverse_full_channel_refined_source_dx025_probe", DATAVERSE_FULL_CHANNEL_REFINED_SOURCE_DX025_PROBE),
            evidence_entry("dataverse_full_channel_refined_source_dx025_500step", DATAVERSE_FULL_CHANNEL_REFINED_SOURCE_DX025_500STEP),
            evidence_entry("dataverse_full_channel_refined_source_dx025_1000step_dt5em6", DATAVERSE_FULL_CHANNEL_REFINED_SOURCE_DX025_1000STEP_DT5EM6),
            evidence_entry("dataverse_amr_source_projection_contract", DATAVERSE_AMR_SOURCE_PROJECTION_CONTRACT),
            evidence_entry("dataverse_amr_source_projection_implementation", DATAVERSE_AMR_SOURCE_PROJECTION_IMPLEMENTATION),
            evidence_entry("dataverse_long_window_reconciliation", DATAVERSE_LONG_WINDOW_RECONCILIATION),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") == STATUS_TRIAGED, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("external_plume_blocker_present") is True, "external plume blocker not detected")
    require(
        summary.get("public_sbepv5_d27_geometry_and_release_conditions_found") is True,
        "public SBEPV5/D27 geometry/release source not recorded",
    )
    require(
        summary.get("public_machine_readable_sbepv5_d27_timeseries_found") is False,
        "report should not claim machine-readable time-series availability",
    )
    require(
        summary.get("public_dataverse_open_channel_machine_readable_timeseries_found") is True,
        "Dataverse open-channel machine-readable time-series source not recorded",
    )
    require(
        summary.get("public_machine_readable_external_plume_timeseries_found") is True,
        "public machine-readable external plume source not recorded",
    )
    require(int(summary.get("dataverse_metadata_file_count", 0)) >= 20, "Dataverse file count too small")
    require(int(summary.get("dataverse_sample_h2_sensor_column_count", 0)) == 29, "Dataverse sample sensor count mismatch")
    require(summary.get("dataverse_sample_md5_verified") is True, "Dataverse sample MD5 not verified")
    require(
        summary.get("dataverse_full_dataset_audit_status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-DATASET-AUDIT",
        "Dataverse full dataset audit is not PASS",
    )
    require(int(summary.get("dataverse_full_dataset_expected_file_count", 0)) >= 20, "Dataverse full dataset file count too small")
    require(
        summary.get("dataverse_full_dataset_ready_file_count")
        == summary.get("dataverse_full_dataset_expected_file_count"),
        "Dataverse full dataset does not have all expected files ready",
    )
    require(summary.get("dataverse_full_dataset_all_files_ready") is True, "Dataverse full dataset readiness is false")
    require(
        summary.get("dataverse_timeseries_index_status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-TIMESERIES-INDEX",
        "Dataverse time-series index is not PASS",
    )
    require(int(summary.get("dataverse_timeseries_zip_case_count", 0)) >= 20, "Dataverse time-series zip count too small")
    require(
        int(summary.get("dataverse_timeseries_strong_plume_candidate_count", 0)) >= 3,
        "too few Dataverse strong plume candidates",
    )
    require(summary.get("dataverse_timeseries_ready_for_case_selection") is True, "Dataverse case selection is not ready")
    require(
        summary.get("dataverse_geometry_mapping_status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-GEOMETRY-MAPPING",
        "Dataverse geometry mapping is not PASS",
    )
    require(int(summary.get("dataverse_geometry_sensor_coordinate_count", 0)) == 29, "Dataverse sensor map count mismatch")
    require(int(summary.get("dataverse_geometry_case_mapping_count", 0)) == 22, "Dataverse case map count mismatch")
    require(
        summary.get("dataverse_geometry_ready_for_sensor_sampling_map") is True,
        "Dataverse sensor sampling map is not ready",
    )
    require(
        summary.get("dataverse_geometry_ready_for_full_mesh_parity") is False,
        "Dataverse full mesh parity should not be claimed",
    )
    require(
        summary.get("dataverse_reference_package_status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-REFERENCE-PACKAGE",
        "Dataverse reference package is not PASS",
    )
    require(summary.get("dataverse_reference_selected_case_filename") == "23_FFI_P101_T00031.zip", "Dataverse reference case drifted")
    require(summary.get("dataverse_reference_article_test_id") == "test-08-1", "Dataverse reference article test mismatch")
    require(int(summary.get("dataverse_reference_raw_row_count", 0)) > 1000, "Dataverse reference raw row count too small")
    require(
        int(summary.get("dataverse_reference_sensor_time_sample_count", 0)) >= 500,
        "Dataverse reference sensor sample count too small",
    )
    require(int(summary.get("dataverse_reference_sensor_record_count", 0)) > 10000, "Dataverse reference package too small")
    require(float(summary.get("dataverse_reference_peak_x_h2", 0.0)) >= 0.10, "Dataverse reference peak too small")
    require(summary.get("dataverse_reference_ready_for_signal_sampling") is True, "Dataverse reference signal sampling is not ready")
    require(
        summary.get("dataverse_reference_ready_for_cfd_agreement_scoring") is False,
        "Dataverse reference package should not claim CFD agreement scoring readiness",
    )
    require(
        summary.get("dataverse_agreement_contract_status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-AGREEMENT-CONTRACT",
        "Dataverse agreement contract is not PASS",
    )
    require(summary.get("dataverse_agreement_contract_mode") == "selftest_reference_identity", "Dataverse agreement contract mode mismatch")
    require(int(summary.get("dataverse_agreement_sensor_count", 0)) == 29, "Dataverse agreement sensor count mismatch")
    require(int(summary.get("dataverse_agreement_lfl_sensor_count", 0)) >= 3, "Dataverse agreement LFL sensor count too small")
    require(int(summary.get("dataverse_agreement_peak_pass_count", 0)) == 29, "Dataverse agreement peak selftest failed")
    require(int(summary.get("dataverse_agreement_nrmse_pass_count", 0)) == 29, "Dataverse agreement NRMSE selftest failed")
    require(summary.get("dataverse_agreement_ready_for_cfd_scoring") is True, "Dataverse agreement contract is not ready")
    require(summary.get("dataverse_agreement_production_completed") is False, "Dataverse production agreement should remain incomplete")
    require(
        summary.get("dataverse_cfd_scout_status") == "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
        "Dataverse CFD scout is not PASS",
    )
    require(int(summary.get("dataverse_cfd_scout_mpi_rank_count", 0)) == 2, "Dataverse CFD scout MPI rank mismatch")
    require(summary.get("dataverse_cfd_scout_cuda_initialized") is True, "Dataverse CFD scout CUDA missing")
    require(int(summary.get("dataverse_cfd_scout_plotfile_count", 0)) >= 5, "Dataverse CFD scout plotfiles too few")
    require(int(summary.get("dataverse_cfd_scout_sensor_count", 0)) == 29, "Dataverse CFD scout sensors mismatch")
    require(summary.get("dataverse_cfd_scout_agreement_attempt_status") == "failed_expected_for_short_scout", "Dataverse CFD scout agreement status mismatch")
    require(summary.get("dataverse_cfd_scout_ready_for_longer_campaign") is True, "Dataverse CFD scout does not prepare longer campaign")
    require(
        summary.get("dataverse_cfd_agreement_attempt_status")
        == "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
        "Dataverse CFD agreement attempt status mismatch",
    )
    require(int(summary.get("dataverse_cfd_agreement_attempt_sensor_count", 0)) == 29, "Dataverse CFD agreement attempt sensors mismatch")
    require(
        int(summary.get("dataverse_cfd_agreement_attempt_common_sample_count_min", 0)) >= 2,
        "Dataverse CFD agreement attempt common samples too few",
    )
    require(
        float(summary.get("dataverse_cfd_agreement_attempt_simulation_time_end_s", 0.0)) >= 1.999,
        "Dataverse CFD agreement attempt did not reach 2 s",
    )
    require(
        summary.get("dataverse_cfd_agreement_attempt_production_completed") is False,
        "Dataverse CFD agreement attempt should not complete production agreement",
    )
    require(
        summary.get("dataverse_cfd_agreement_attempt_clears_external_plume_blocker") is False,
        "Dataverse CFD agreement attempt should not clear blocker",
    )
    require(
        summary.get("dataverse_cfd_45s_agreement_attempt_status")
        == "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
        "Dataverse 45s CFD agreement attempt status mismatch",
    )
    require(int(summary.get("dataverse_cfd_45s_agreement_attempt_sensor_count", 0)) == 29, "Dataverse 45s agreement attempt sensors mismatch")
    require(
        int(summary.get("dataverse_cfd_45s_agreement_attempt_common_sample_count_min", 0)) >= 60,
        "Dataverse 45s agreement attempt common samples too few",
    )
    require(
        float(summary.get("dataverse_cfd_45s_agreement_attempt_simulation_time_end_s", 0.0)) >= 44.9,
        "Dataverse 45s agreement attempt did not reach 45 s",
    )
    require(
        int(summary.get("dataverse_cfd_45s_agreement_attempt_nrmse_pass_count", 0)) >= 20,
        "Dataverse 45s agreement attempt NRMSE pass count too small",
    )
    require(
        summary.get("dataverse_cfd_45s_agreement_attempt_production_completed") is False,
        "Dataverse 45s agreement attempt should not complete production agreement",
    )
    require(
        summary.get("dataverse_cfd_45s_agreement_attempt_clears_external_plume_blocker") is False,
        "Dataverse 45s agreement attempt should not clear blocker",
    )
    require(
        summary.get("dataverse_cfd_120s_agreement_attempt_status")
        == "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
        "Dataverse 120s CFD agreement attempt status mismatch",
    )
    require(int(summary.get("dataverse_cfd_120s_agreement_attempt_sensor_count", 0)) == 29, "Dataverse 120s agreement attempt sensors mismatch")
    require(
        int(summary.get("dataverse_cfd_120s_agreement_attempt_common_sample_count_min", 0)) >= 180,
        "Dataverse 120s agreement attempt common samples too few",
    )
    require(
        float(summary.get("dataverse_cfd_120s_agreement_attempt_simulation_time_end_s", 0.0)) >= 119.9,
        "Dataverse 120s agreement attempt did not reach 120 s",
    )
    require(
        abs(float(summary.get("dataverse_cfd_120s_agreement_attempt_mass_ratio_final", 0.0)) - 1.0) <= 1.0e-12,
        "Dataverse 120s agreement attempt mass ratio regressed",
    )
    require(
        summary.get("dataverse_cfd_120s_agreement_attempt_production_completed") is False,
        "Dataverse 120s agreement attempt should not complete production agreement",
    )
    require(
        summary.get("dataverse_cfd_120s_agreement_attempt_clears_external_plume_blocker") is False,
        "Dataverse 120s agreement attempt should not clear blocker",
    )
    require(
        summary.get("dataverse_120s_calibration_diagnosis_status")
        == "DIAGNOSED-DATAVERSE-OPEN-CHANNEL-H2-120S-CALIBRATION-GAPS",
        "Dataverse 120s calibration diagnosis status mismatch",
    )
    require(
        float(summary.get("dataverse_120s_source_radius_ratio", 0.0)) > 10.0,
        "Dataverse 120s source-radius diagnosis missing",
    )
    require(
        abs(float(summary.get("dataverse_120s_source_center_z_offset_m", 0.0))) >= 0.05,
        "Dataverse 120s source-height diagnosis missing",
    )
    require(
        float(summary.get("dataverse_120s_minimum_active_radius_at_reference_source_on_current_grid_m", 0.0)) > 0.04,
        "Dataverse 120s grid-aware minimum source-radius diagnosis missing",
    )
    require(
        summary.get("dataverse_120s_ready_for_next_calibration_sweep") is True,
        "Dataverse 120s calibration sweep readiness missing",
    )
    require(
        summary.get("dataverse_45s_calibration_r005_z08_status")
        == "SCREENED-DATAVERSE-OPEN-CHANNEL-H2-45S-CALIBRATION-R005-Z08-NOT-PROMOTED",
        "Dataverse 45s calibration r005 z08 status mismatch",
    )
    require(
        summary.get("dataverse_45s_calibration_r005_z08_promote_to_120s") is False,
        "Dataverse 45s calibration r005 z08 should not promote to 120s",
    )
    require(
        summary.get("dataverse_45s_calibration_sweep_status")
        == "SCREENED-DATAVERSE-OPEN-CHANNEL-H2-45S-CALIBRATION-SWEEP-NO-PROMOTION",
        "Dataverse 45s calibration sweep status mismatch",
    )
    require(
        int(summary.get("dataverse_45s_calibration_sweep_promoted_case_count", -1)) == 0,
        "Dataverse 45s calibration sweep unexpectedly promoted a case",
    )
    require(
        summary.get("dataverse_physics_alignment_status")
        == "DIAGNOSED-DATAVERSE-OPEN-CHANNEL-H2-PHYSICS-ALIGNMENT-GAPS",
        "Dataverse physics alignment status mismatch",
    )
    require(
        float(summary.get("dataverse_physics_alignment_velocity_ratio", 0.0)) > 100.0,
        "Dataverse physics alignment velocity-ratio diagnosis missing",
    )
    require(
        int(summary.get("dataverse_physics_alignment_active_cell_count_for_experimental_radius", -1)) == 0,
        "Dataverse physics alignment experimental-radius active-cell diagnosis missing",
    )
    require(
        summary.get("dataverse_physics_alignment_ready_for_orifice_velocity_scout") is True,
        "Dataverse physics alignment does not ready the orifice-velocity scout",
    )
    require(
        summary.get("dataverse_orifice_velocity_scout_status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
        "Dataverse orifice-velocity scout status mismatch",
    )
    require(int(summary.get("dataverse_orifice_velocity_scout_mpi_rank_count", 0)) == 2, "Dataverse orifice-velocity scout MPI rank mismatch")
    require(summary.get("dataverse_orifice_velocity_scout_cuda_initialized") is True, "Dataverse orifice-velocity scout CUDA missing")
    require(abs(float(summary.get("dataverse_orifice_velocity_scout_mass_ratio_final", 0.0)) - 1.0) <= 1.0e-12, "Dataverse orifice-velocity scout mass ratio regressed")
    require(float(summary.get("dataverse_orifice_velocity_scout_max_yh2", 0.0)) > 0.0, "Dataverse orifice-velocity scout plume missing")
    require(
        summary.get("dataverse_open_boundary_scout_status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
        "Dataverse open-boundary scout status mismatch",
    )
    require(int(summary.get("dataverse_open_boundary_scout_mpi_rank_count", 0)) == 2, "Dataverse open-boundary scout MPI rank mismatch")
    require(summary.get("dataverse_open_boundary_scout_cuda_initialized") is True, "Dataverse open-boundary scout CUDA missing")
    require(abs(float(summary.get("dataverse_open_boundary_scout_mass_ratio_final", 0.0)) - 1.0) <= 1.0e-12, "Dataverse open-boundary scout mass ratio regressed")
    require(float(summary.get("dataverse_open_boundary_scout_max_yh2", 0.0)) > 0.0, "Dataverse open-boundary scout plume missing")
    require(
        summary.get("dataverse_open_boundary_orifice_extended_01s_status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
        "Dataverse open-boundary 0.1s status mismatch",
    )
    require(int(summary.get("dataverse_open_boundary_orifice_extended_01s_mpi_rank_count", 0)) == 2, "Dataverse open-boundary 0.1s MPI rank mismatch")
    require(summary.get("dataverse_open_boundary_orifice_extended_01s_cuda_initialized") is True, "Dataverse open-boundary 0.1s CUDA missing")
    require(abs(float(summary.get("dataverse_open_boundary_orifice_extended_01s_time_end_s", 0.0)) - 0.1) <= 1.0e-12, "Dataverse open-boundary 0.1s time mismatch")
    require(abs(float(summary.get("dataverse_open_boundary_orifice_extended_01s_mass_ratio_final", 0.0)) - 1.0) <= 1.0e-12, "Dataverse open-boundary 0.1s mass ratio regressed")
    require(float(summary.get("dataverse_open_boundary_orifice_extended_01s_downstream_fraction", 0.0)) > 0.95, "Dataverse open-boundary 0.1s downstream fraction too small")
    require(
        summary.get("dataverse_open_boundary_orifice_extended_1s_status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
        "Dataverse open-boundary 1.0s status mismatch",
    )
    require(int(summary.get("dataverse_open_boundary_orifice_extended_1s_mpi_rank_count", 0)) == 2, "Dataverse open-boundary 1.0s MPI rank mismatch")
    require(summary.get("dataverse_open_boundary_orifice_extended_1s_cuda_initialized") is True, "Dataverse open-boundary 1.0s CUDA missing")
    require(abs(float(summary.get("dataverse_open_boundary_orifice_extended_1s_time_end_s", 0.0)) - 1.0) <= 1.0e-12, "Dataverse open-boundary 1.0s time mismatch")
    require(abs(float(summary.get("dataverse_open_boundary_orifice_extended_1s_mass_ratio_final", 0.0)) - 1.0) <= 1.0e-12, "Dataverse open-boundary 1.0s mass ratio regressed")
    require(float(summary.get("dataverse_open_boundary_orifice_extended_1s_downstream_fraction", 0.0)) > 0.99, "Dataverse open-boundary 1.0s downstream fraction too small")
    require(
        summary.get("dataverse_open_boundary_orifice_extended_2s_status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-OPEN-BOUNDARY-ORIFICE-EXTENDED-2S-MPI-CUDA",
        "Dataverse open-boundary 2.0s status mismatch",
    )
    require(int(summary.get("dataverse_open_boundary_orifice_extended_2s_mpi_rank_count", 0)) == 2, "Dataverse open-boundary 2.0s MPI rank mismatch")
    require(summary.get("dataverse_open_boundary_orifice_extended_2s_cuda_initialized") is True, "Dataverse open-boundary 2.0s CUDA missing")
    require(abs(float(summary.get("dataverse_open_boundary_orifice_extended_2s_time_end_s", 0.0)) - 2.0) <= 1.0e-12, "Dataverse open-boundary 2.0s time mismatch")
    require(0.75 <= float(summary.get("dataverse_open_boundary_orifice_extended_2s_mass_ratio_final", 0.0)) <= 1.05, "Dataverse open-boundary 2.0s mass ratio outside open-boundary screen range")
    require(float(summary.get("dataverse_open_boundary_orifice_extended_2s_downstream_fraction", 0.0)) > 0.99, "Dataverse open-boundary 2.0s downstream fraction too small")
    require(summary.get("dataverse_open_boundary_orifice_extended_2s_clears_external_plume_blocker") is False, "Dataverse open-boundary 2.0s must not clear strict plume blocker")
    require(summary.get("dataverse_open_boundary_orifice_extended_2s_strict_blocker_still_open") is True, "Dataverse open-boundary 2.0s strict blocker state mismatch")
    require(summary.get("dataverse_open_boundary_orifice_extended_multi_second_screen_completed") is True, "Dataverse open-boundary multi-second screen not recorded")
    require(
        summary.get("dataverse_refined_source_projection_probe_status")
        == "PASS-DATAVERSE-REFINED-SOURCE-PROJECTION-PROBE-MPI-CUDA",
        "Dataverse refined source projection probe status mismatch",
    )
    require(int(summary.get("dataverse_refined_source_projection_probe_mpi_rank_count", 0)) == 2, "Dataverse refined source projection MPI rank mismatch")
    require(summary.get("dataverse_refined_source_projection_probe_cuda_initialized") is True, "Dataverse refined source projection CUDA missing")
    require(summary.get("dataverse_refined_source_projection_probe_run_log_has_no_abort_nan_or_cuda_error") is True, "Dataverse refined source projection runtime log regressed")
    require(all(abs(float(v) - 0.0125) <= 1.0e-12 for v in summary.get("dataverse_refined_source_projection_probe_dx_m", [])), "Dataverse refined source projection dx mismatch")
    require(abs(float(summary.get("dataverse_refined_source_projection_probe_leak_radius_m", 0.0)) - 0.0023) <= 1.0e-15, "Dataverse refined source projection radius mismatch")
    require(summary.get("dataverse_refined_source_projection_probe_active_volume_equals_single_cell") is True, "Dataverse refined source projection active volume mismatch")
    require(float(summary.get("dataverse_refined_source_projection_probe_source_cfl", 1.0)) < 0.01, "Dataverse refined source projection source CFL too large")
    require(float(summary.get("dataverse_refined_source_projection_probe_validation_max_yh2", 0.0)) > 0.0, "Dataverse refined source projection plume missing")
    require(summary.get("dataverse_refined_source_projection_probe_clears_external_plume_blocker") is False, "Dataverse refined source projection must not clear strict plume blocker")
    require(summary.get("dataverse_refined_source_projection_probe_strict_blocker_still_open") is True, "Dataverse refined source projection strict blocker state mismatch")
    require(summary.get("dataverse_refined_source_projection_screen_completed") is True, "Dataverse refined source projection screen not recorded")
    require(
        summary.get("dataverse_full_channel_refined_source_dx025_probe_status")
        == "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-PROBE-MPI-CUDA",
        "Dataverse full-channel refined-source dx=0.025 probe status mismatch",
    )
    require(int(summary.get("dataverse_full_channel_refined_source_dx025_probe_mpi_rank_count", 0)) == 2, "Dataverse full-channel refined-source MPI rank mismatch")
    require(summary.get("dataverse_full_channel_refined_source_dx025_probe_cuda_initialized") is True, "Dataverse full-channel refined-source CUDA missing")
    require(summary.get("dataverse_full_channel_refined_source_dx025_probe_run_log_has_no_abort_nan_or_cuda_error") is True, "Dataverse full-channel refined-source runtime log regressed")
    require(summary.get("dataverse_full_channel_refined_source_dx025_probe_full_dataverse_domain") is True, "Dataverse full-channel refined-source domain mismatch")
    require(all(abs(float(v) - 0.025) <= 1.0e-12 for v in summary.get("dataverse_full_channel_refined_source_dx025_probe_dx_m", [])), "Dataverse full-channel refined-source dx mismatch")
    require(abs(float(summary.get("dataverse_full_channel_refined_source_dx025_probe_leak_radius_m", 0.0)) - 0.0023) <= 1.0e-15, "Dataverse full-channel refined-source radius mismatch")
    require(summary.get("dataverse_full_channel_refined_source_dx025_probe_active_volume_equals_single_cell") is True, "Dataverse full-channel refined-source active volume mismatch")
    require(float(summary.get("dataverse_full_channel_refined_source_dx025_probe_source_cfl", 1.0)) < 0.05, "Dataverse full-channel refined-source source CFL too large")
    require(float(summary.get("dataverse_full_channel_refined_source_dx025_probe_validation_max_yh2", 0.0)) > 0.0, "Dataverse full-channel refined-source plume missing")
    require(summary.get("dataverse_full_channel_refined_source_dx025_probe_clears_external_plume_blocker") is False, "Dataverse full-channel refined-source must not clear strict plume blocker")
    require(summary.get("dataverse_full_channel_refined_source_dx025_probe_strict_blocker_still_open") is True, "Dataverse full-channel refined-source strict blocker state mismatch")
    require(summary.get("dataverse_full_channel_refined_source_dx025_screen_completed") is True, "Dataverse full-channel refined-source screen not recorded")
    require(
        summary.get("dataverse_full_channel_refined_source_dx025_500step_status")
        == "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-500STEP-MPI-CUDA",
        "Dataverse full-channel refined-source dx=0.025 500-step status mismatch",
    )
    require(int(summary.get("dataverse_full_channel_refined_source_dx025_500step_mpi_rank_count", 0)) == 2, "Dataverse full-channel refined-source 500-step MPI rank mismatch")
    require(summary.get("dataverse_full_channel_refined_source_dx025_500step_cuda_initialized") is True, "Dataverse full-channel refined-source 500-step CUDA missing")
    require(summary.get("dataverse_full_channel_refined_source_dx025_500step_run_log_has_no_abort_nan_or_cuda_error") is True, "Dataverse full-channel refined-source 500-step runtime log regressed")
    require(summary.get("dataverse_full_channel_refined_source_dx025_500step_full_dataverse_domain") is True, "Dataverse full-channel refined-source 500-step domain mismatch")
    require(all(abs(float(v) - 0.025) <= 1.0e-12 for v in summary.get("dataverse_full_channel_refined_source_dx025_500step_dx_m", [])), "Dataverse full-channel refined-source 500-step dx mismatch")
    require(abs(float(summary.get("dataverse_full_channel_refined_source_dx025_500step_leak_radius_m", 0.0)) - 0.0023) <= 1.0e-15, "Dataverse full-channel refined-source 500-step radius mismatch")
    require(float(summary.get("dataverse_full_channel_refined_source_dx025_500step_source_cfl", 1.0)) < 0.05, "Dataverse full-channel refined-source 500-step source CFL too large")
    require(abs(float(summary.get("dataverse_full_channel_refined_source_dx025_500step_time_end_s", 0.0)) - 5.0e-4) <= 1.0e-12, "Dataverse full-channel refined-source 500-step time mismatch")
    require(float(summary.get("dataverse_full_channel_refined_source_dx025_500step_validation_max_yh2", 0.0)) > 0.0, "Dataverse full-channel refined-source 500-step plume missing")
    require(summary.get("dataverse_full_channel_refined_source_dx025_500step_clears_external_plume_blocker") is False, "Dataverse full-channel refined-source 500-step must not clear strict plume blocker")
    require(summary.get("dataverse_full_channel_refined_source_dx025_500step_strict_blocker_still_open") is True, "Dataverse full-channel refined-source 500-step strict blocker state mismatch")
    require(summary.get("dataverse_full_channel_refined_source_dx025_500step_completed") is True, "Dataverse full-channel refined-source 500-step not recorded")
    require(
        summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_status")
        == "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-1000STEP-DT5EM6-MPI-CUDA",
        "Dataverse full-channel refined-source dx=0.025 1000-step dt=5e-6 status mismatch",
    )
    require(int(summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_mpi_rank_count", 0)) == 2, "Dataverse full-channel refined-source 1000-step dt=5e-6 MPI rank mismatch")
    require(summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_cuda_initialized") is True, "Dataverse full-channel refined-source 1000-step dt=5e-6 CUDA missing")
    require(summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_run_log_has_no_abort_nan_or_cuda_error") is True, "Dataverse full-channel refined-source 1000-step dt=5e-6 runtime log regressed")
    require(summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_full_dataverse_domain") is True, "Dataverse full-channel refined-source 1000-step dt=5e-6 domain mismatch")
    require(all(abs(float(v) - 0.025) <= 1.0e-12 for v in summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_dx_m", [])), "Dataverse full-channel refined-source 1000-step dt=5e-6 dx mismatch")
    require(abs(float(summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_leak_radius_m", 0.0)) - 0.0023) <= 1.0e-15, "Dataverse full-channel refined-source 1000-step dt=5e-6 radius mismatch")
    require(float(summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_source_cfl", 1.0)) < 0.15, "Dataverse full-channel refined-source 1000-step dt=5e-6 source CFL too large")
    require(abs(float(summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_time_end_s", 0.0)) - 0.005) <= 1.0e-12, "Dataverse full-channel refined-source 1000-step dt=5e-6 time mismatch")
    require(float(summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_validation_max_yh2", 0.0)) > 0.0, "Dataverse full-channel refined-source 1000-step dt=5e-6 plume missing")
    require(summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_clears_external_plume_blocker") is False, "Dataverse full-channel refined-source 1000-step dt=5e-6 must not clear strict plume blocker")
    require(summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_strict_blocker_still_open") is True, "Dataverse full-channel refined-source 1000-step dt=5e-6 strict blocker state mismatch")
    require(summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_completed") is True, "Dataverse full-channel refined-source 1000-step dt=5e-6 not recorded")
    require(
        summary.get("dataverse_amr_source_projection_contract_status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-CONTRACT",
        "Dataverse AMR source projection contract status mismatch",
    )
    require(summary.get("dataverse_amr_source_projection_contract_ready") is True, "Dataverse AMR source projection contract not ready")
    require(summary.get("dataverse_amr_source_projection_contract_problem_hook_single_level") is True, "Dataverse problem-hook projection characterization mismatch")
    require(summary.get("dataverse_amr_source_projection_contract_problem_hook_lacks_level_aware_mask") is True, "Dataverse problem-hook AMR contract characterization mismatch")
    require(summary.get("dataverse_amr_source_projection_current_single_level") is False, "Dataverse current source projection should no longer be single-level after implementation")
    require(summary.get("dataverse_amr_source_projection_lacks_level_aware_mask") is False, "Dataverse current AMR source projection still reports a missing level-aware mask")
    require(
        summary.get("dataverse_amr_source_projection_implementation_status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-IMPLEMENTATION",
        "Dataverse AMR source projection implementation status mismatch",
    )
    require(summary.get("dataverse_amr_source_projection_implementation_ready") is True, "Dataverse AMR source projection implementation not ready")
    require(summary.get("dataverse_amr_source_projection_framework_level_owner_mask_implemented") is True, "Dataverse AMR framework owner mask missing")
    require(summary.get("dataverse_amr_source_projection_preserves_non_user_ext_sources") is True, "Dataverse AMR source projection does not preserve non-user sources")
    require(summary.get("dataverse_amr_source_projection_finest_available_level_only") is True, "Dataverse AMR source projection does not enforce finest-level ownership")
    require(int(summary.get("dataverse_amr_source_projection_recommended_refinement_ratio", 0)) >= 8, "Dataverse AMR source projection refinement ratio too small")
    require(float(summary.get("dataverse_amr_source_projection_recommended_finest_dx_m", 1.0)) <= 0.003125, "Dataverse AMR source projection finest dx too coarse")
    require(summary.get("dataverse_amr_source_projection_strict_blocker_still_open") is True, "Dataverse AMR contract must not clear strict blocker")
    require(
        summary.get("dataverse_long_window_reconciliation_status")
        == "TRIAGED-DATAVERSE-OPEN-CHANNEL-LONG-WINDOW-REFINED-SOURCE-GAP",
        "Dataverse long-window reconciliation status mismatch",
    )
    require(summary.get("dataverse_existing_120s_reaches_peak_interval") is True, "existing 120s Dataverse run peak-window coverage missing")
    require(summary.get("dataverse_existing_120s_all_sensors_passed") is False, "existing 120s Dataverse run should not be counted as all-sensor PASS")
    require(int(summary.get("dataverse_existing_120s_failed_sensor_count", 0)) > 0, "existing 120s failed sensor count missing")
    require(float(summary.get("dataverse_current_refined_source_long_window_time_end_s", 1.0)) < 1.0, "current refined-source long-window status drifted")
    require(int(summary.get("dataverse_current_refined_source_steps_to_113s", 0)) > 20_000_000, "refined source step estimate to 113 s missing")
    require(summary.get("strict_external_plume_blocker_cleared") is False, "strict blocker must remain open")
    require(isinstance(data.get("missing_for_strict_credit"), list) and data["missing_for_strict_credit"], "missing strict-credit gap list")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Strict External Source Update",
        "",
        f"- Status: `{report['status']}`",
        f"- Public geometry/release fields found: `{s['public_sbepv5_d27_geometry_and_release_conditions_found']}`",
        f"- Public machine-readable time series found: `{s['public_machine_readable_sbepv5_d27_timeseries_found']}`",
        f"- DataverseNO machine-readable time series found: `{s['public_dataverse_open_channel_machine_readable_timeseries_found']}`",
        f"- DataverseNO sample H2 sensor columns: `{s['dataverse_sample_h2_sensor_column_count']}`",
        f"- DataverseNO sample MD5 verified: `{s['dataverse_sample_md5_verified']}`",
        f"- DataverseNO full dataset audit: `{s['dataverse_full_dataset_audit_status']}`",
        f"- DataverseNO full dataset ready files: `{s['dataverse_full_dataset_ready_file_count']}/{s['dataverse_full_dataset_expected_file_count']}`",
        f"- DataverseNO full dataset CSV sensor counts: `{s['dataverse_full_dataset_sensor_column_counts_seen']}`",
        f"- DataverseNO time-series index: `{s['dataverse_timeseries_index_status']}`",
        f"- DataverseNO strong plume candidates: `{s['dataverse_timeseries_strong_plume_candidate_count']}`",
        f"- DataverseNO top candidate files: `{s['dataverse_timeseries_top_candidate_filenames']}`",
        f"- DataverseNO geometry mapping: `{s['dataverse_geometry_mapping_status']}`",
        f"- DataverseNO sensor coordinates: `{s['dataverse_geometry_sensor_coordinate_count']}`",
        f"- DataverseNO ready for sensor sampling map: `{s['dataverse_geometry_ready_for_sensor_sampling_map']}`",
        f"- DataverseNO ready for full mesh parity: `{s['dataverse_geometry_ready_for_full_mesh_parity']}`",
        f"- DataverseNO reference package: `{s['dataverse_reference_package_status']}`",
        f"- DataverseNO reference case: `{s['dataverse_reference_selected_case_filename']}` / `{s['dataverse_reference_article_test_id']}`",
        f"- DataverseNO reference raw rows: `{s['dataverse_reference_raw_row_count']}`",
        f"- DataverseNO reference sensor time samples: `{s['dataverse_reference_sensor_time_sample_count']}`",
        f"- DataverseNO reference sensor records: `{s['dataverse_reference_sensor_record_count']}`",
        f"- DataverseNO reference ready for signal sampling: `{s['dataverse_reference_ready_for_signal_sampling']}`",
        f"- DataverseNO reference ready for CFD agreement scoring: `{s['dataverse_reference_ready_for_cfd_agreement_scoring']}`",
        f"- DataverseNO agreement contract: `{s['dataverse_agreement_contract_status']}`",
        f"- DataverseNO agreement mode: `{s['dataverse_agreement_contract_mode']}`",
        f"- DataverseNO agreement sensors: `{s['dataverse_agreement_sensor_count']}`",
        f"- DataverseNO agreement ready for CFD scoring: `{s['dataverse_agreement_ready_for_cfd_scoring']}`",
        f"- DataverseNO production agreement completed: `{s['dataverse_agreement_production_completed']}`",
        f"- DataverseNO CFD scout: `{s['dataverse_cfd_scout_status']}`",
        f"- DataverseNO CFD scout MPI ranks: `{s['dataverse_cfd_scout_mpi_rank_count']}`",
        f"- DataverseNO CFD scout CUDA initialized: `{s['dataverse_cfd_scout_cuda_initialized']}`",
        f"- DataverseNO CFD scout sensors: `{s['dataverse_cfd_scout_sensor_count']}`",
        f"- DataverseNO CFD scout agreement attempt: `{s['dataverse_cfd_scout_agreement_attempt_status']}`",
        f"- DataverseNO CFD agreement-window attempt: `{s['dataverse_cfd_agreement_attempt_status']}`",
        f"- DataverseNO CFD agreement-window common samples: `{s['dataverse_cfd_agreement_attempt_common_sample_count_min']}` to `{s['dataverse_cfd_agreement_attempt_common_sample_count_max']}`",
        f"- DataverseNO CFD agreement-window failed sensors: `{s['dataverse_cfd_agreement_attempt_failed_sensor_count']}`",
        f"- DataverseNO CFD 45s agreement attempt: `{s['dataverse_cfd_45s_agreement_attempt_status']}`",
        f"- DataverseNO CFD 45s common samples: `{s['dataverse_cfd_45s_agreement_attempt_common_sample_count_min']}` to `{s['dataverse_cfd_45s_agreement_attempt_common_sample_count_max']}`",
        f"- DataverseNO CFD 45s NRMSE pass count: `{s['dataverse_cfd_45s_agreement_attempt_nrmse_pass_count']}`",
        f"- DataverseNO CFD 120s peak-window attempt: `{s['dataverse_cfd_120s_agreement_attempt_status']}`",
        f"- DataverseNO CFD 120s common samples: `{s['dataverse_cfd_120s_agreement_attempt_common_sample_count_min']}` to `{s['dataverse_cfd_120s_agreement_attempt_common_sample_count_max']}`",
        f"- DataverseNO CFD 120s pass counts: peak `{s['dataverse_cfd_120s_agreement_attempt_peak_pass_count']}`, NRMSE `{s['dataverse_cfd_120s_agreement_attempt_nrmse_pass_count']}`, LFL arrival `{s['dataverse_cfd_120s_agreement_attempt_arrival_pass_count']}`",
        f"- DataverseNO 120s calibration diagnosis: `{s['dataverse_120s_calibration_diagnosis_status']}`",
        f"- DataverseNO 120s source radius/area ratios: `{s['dataverse_120s_source_radius_ratio']}` / `{s['dataverse_120s_source_area_ratio']}`",
        f"- DataverseNO 120s source center z offset: `{s['dataverse_120s_source_center_z_offset_m']}`",
        f"- DataverseNO 120s minimum active source radius on current grid: `{s['dataverse_120s_minimum_active_radius_at_reference_source_on_current_grid_m']}`",
        f"- DataverseNO 45s r005 z08 calibration screen: `{s['dataverse_45s_calibration_r005_z08_status']}`",
        f"- DataverseNO 45s r005 z08 promote to 120s: `{s['dataverse_45s_calibration_r005_z08_promote_to_120s']}`",
        f"- DataverseNO 45s calibration sweep: `{s['dataverse_45s_calibration_sweep_status']}`",
        f"- DataverseNO 45s calibration sweep promoted cases: `{s['dataverse_45s_calibration_sweep_promoted_case_count']}`",
        f"- DataverseNO physics alignment: `{s['dataverse_physics_alignment_status']}`",
        f"- DataverseNO equivalent/baseline source velocity ratio: `{s['dataverse_physics_alignment_velocity_ratio']}`",
        f"- DataverseNO orifice velocity MPI+CUDA scout: `{s['dataverse_orifice_velocity_scout_status']}`",
        f"- DataverseNO open/open boundary MPI+CUDA scout: `{s['dataverse_open_boundary_scout_status']}`",
        f"- DataverseNO open/open orifice 0.1s MPI+CUDA window: `{s['dataverse_open_boundary_orifice_extended_01s_status']}`",
        f"- DataverseNO open/open orifice 1.0s MPI+CUDA window: `{s['dataverse_open_boundary_orifice_extended_1s_status']}`",
        f"- DataverseNO open/open orifice 2.0s MPI+CUDA screen: `{s['dataverse_open_boundary_orifice_extended_2s_status']}`",
        f"- DataverseNO refined source projection MPI+CUDA probe: `{s['dataverse_refined_source_projection_probe_status']}`",
        f"- DataverseNO full-channel dx=0.025 refined-source MPI+CUDA probe: `{s['dataverse_full_channel_refined_source_dx025_probe_status']}`",
        f"- DataverseNO full-channel dx=0.025 refined-source 500-step MPI+CUDA screen: `{s['dataverse_full_channel_refined_source_dx025_500step_status']}`",
        f"- DataverseNO full-channel dx=0.025 refined-source 1000-step dt=5e-6 MPI+CUDA screen: `{s['dataverse_full_channel_refined_source_dx025_1000step_dt5em6_status']}`",
        f"- DataverseNO AMR source projection contract: `{s['dataverse_amr_source_projection_contract_status']}`",
        f"- DataverseNO AMR problem hook single-level: `{s['dataverse_amr_source_projection_contract_problem_hook_single_level']}`",
        f"- DataverseNO AMR current projection single-level: `{s['dataverse_amr_source_projection_current_single_level']}`",
        f"- DataverseNO AMR source projection implementation: `{s['dataverse_amr_source_projection_implementation_status']}`",
        f"- DataverseNO AMR finest-owner source projection active: `{s['dataverse_amr_source_projection_finest_available_level_only']}`",
        f"- DataverseNO AMR source projection recommended finest dx: `{s['dataverse_amr_source_projection_recommended_finest_dx_m']}`",
        f"- DataverseNO long-window reconciliation: `{s['dataverse_long_window_reconciliation_status']}`",
        f"- DataverseNO existing 120s reaches peak interval: `{s['dataverse_existing_120s_reaches_peak_interval']}`",
        f"- DataverseNO existing 120s failed sensors: `{s['dataverse_existing_120s_failed_sensor_count']}`",
        f"- DataverseNO current refined-source time end: `{s['dataverse_current_refined_source_long_window_time_end_s']}` s",
        f"- Strict external plume blocker cleared: `{s['strict_external_plume_blocker_cleared']}`",
        "",
        "## Sources",
        "",
    ]
    for source in report["sources"]:
        lines.append(f"- {source['label']}: {source['url']}")
    lines.extend(["", "## Missing For Strict Credit", ""])
    for item in report["missing_for_strict_credit"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Next Actions", ""])
    for item in s["strict_external_plume_next_actions"]:
        lines.append(f"- {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traceability", default=str(DEFAULT_TRACEABILITY))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"strict_external_source_update VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report(args)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_md)
    print(f"strict_external_source_update PASS json={out_json} md={out_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
