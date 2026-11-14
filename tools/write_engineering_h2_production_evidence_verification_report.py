#!/usr/bin/env python3
"""Write and verify the engineering H2 production evidence verification report."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 62
EXPECTED_EXTERNAL_ARTIFACT_GATE_LEVEL = 'strict-v5-placeholder-free'
EXPECTED_CONTROLLED_COPY_SOURCE_GATE_LEVEL = 'strict-v1-regular-nonempty-files'
EXPECTED_OPERATOR_RECEIPT_GATE_LEVEL = 'strict-v1-operator-source-legal-attestation'

DEFAULT_LOG = Path(
    'docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/verification.log'
)
DEFAULT_OUTPUT_JSON = Path(
    'docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json'
)
DEFAULT_OUTPUT_MD = Path(
    'docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.md'
)
DEFAULT_SCORECARD = Path(
    'docs/codex_audit/evidence/engineering_production_scorecard_20260728_integrated_initial_acceptance/'
    'engineering_production_scorecard.json'
)
DEFAULT_HYBRID_CFD_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/hybrid_cfd_scout_report.json'
)
DEFAULT_HYBRID_PRODUCTION_MESH_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/hybrid_production_mesh_scout_report.json'
)
DEFAULT_HYBRID_PRODUCTION_MESH_8RANK_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/hybrid_production_mesh_8rank_scout_report.json'
)
DEFAULT_HYBRID_PRODUCTION_MESH_8RANK_600STEP_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_600step_stability_scout_20260721/hybrid_production_mesh_8rank_600step_stability_scout_report.json'
)
DEFAULT_HYBRID_PRODUCTION_MESH_600STEP_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/hybrid_production_mesh_600step_stability_scout_report.json'
)
DEFAULT_HYBRID_LARGEGRID_8RANK_120STEP_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/hybrid_largegrid_8rank_120step_scout_report.json'
)
DEFAULT_REFERENCE_AGREEMENT = Path(
    'docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/h2_reference_agreement_report.json'
)
DEFAULT_BFS_KEPSILON_REFERENCE = Path(
    'docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.json'
)
DEFAULT_MPI_LINK_SHIM = Path('tools/prepare_mpi_link_shims.sh')
DEFAULT_MPI_SCALING = Path(
    'docs/codex_audit/evidence/engineering_h2_mpi_scaling_20260720/mpi_scaling_report.json'
)
DEFAULT_HYBRID_AFFINITY = Path(
    'docs/codex_audit/evidence/engineering_runtime_affinity_hybrid_20260720/runtime_affinity_manifest.json'
)
DEFAULT_SCHEDULER = Path(
    'docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json'
)
DEFAULT_REAL_CAD_CLEANUP_PACKAGE = Path(
    'docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/'
    'real_cad_cleanup_package_report.json'
)
DEFAULT_REAL_CAD_INTAKE_PREFLIGHT = Path(
    'docs/codex_audit/evidence/engineering_h2_real_cad_intake_preflight_20260724/'
    'real_cad_intake_preflight_report.json'
)
DEFAULT_REAL_CAD_BOUNDARY_TAG_CONTRACT = Path(
    'docs/codex_audit/evidence/engineering_h2_real_cad_boundary_tag_contract_20260724/'
    'real_cad_boundary_tag_contract_report.json'
)
DEFAULT_FIRE_CALIBRATION_PACKAGE = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_package_20260723/'
    'fire_calibration_package_report.json'
)
DEFAULT_FIRE_CALIBRATION_PUBLIC_SOURCE_TRIAGE = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_public_source_triage_20260724/'
    'fire_calibration_public_source_triage_report.json'
)
DEFAULT_FIRE_CALIBRATION_DIGITIZATION_PREFLIGHT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/'
    'fire_calibration_digitization_preflight_report.json'
)
DEFAULT_FIRE_CALIBRATION_LITERATURE_METRIC_PREFLIGHT = Path(
    'docs/codex_audit/evidence/engineering_h2_fire_calibration_literature_metric_preflight_20260724/'
    'fire_calibration_literature_metric_preflight_report.json'
)
DEFAULT_EXTERNAL_PLUME_READINESS = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_benchmark_readiness_20260723/'
    'external_plume_benchmark_readiness_report.json'
)
DEFAULT_EXTERNAL_PLUME_PUBLIC_SOURCE_TRIAGE = Path(
    'docs/codex_audit/evidence/engineering_h2_external_plume_public_source_triage_20260724/'
    'external_plume_public_source_triage_report.json'
)
DEFAULT_BLOCKER_CLEARANCE_PREFLIGHT = Path(
    'docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723/'
    'h2_blocker_clearance_preflight_report.json'
)
DEFAULT_PRODUCTION_BLOCKER_DATA_ROOM = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_data_room_20260724/'
    'h2_production_blocker_data_room_report.json'
)
DEFAULT_PRODUCTION_BLOCKER_CLOSURE_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/'
    'h2_production_blocker_closure_manifest_report.json'
)
DEFAULT_EXTERNAL_EVIDENCE_INTAKE_KIT = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_intake_kit_20260724/'
    'h2_external_evidence_intake_kit_manifest.json'
)
DEFAULT_EXTERNAL_ARTIFACT_OPERATOR_RECEIPT = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_operator_receipt_20260724/'
    'h2_external_artifact_operator_receipt_report.json'
)
DEFAULT_EXTERNAL_ARTIFACT_OPERATOR_RECEIPT_GATE_SELFTEST = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_operator_receipt_gate_selftest_20260724/'
    'h2_external_artifact_operator_receipt_gate_selftest_report.json'
)
DEFAULT_EVIDENCE_CHAIN_REBUILD_MANIFEST = Path(
    'docs/codex_audit/evidence/engineering_h2_evidence_chain_rebuild_manifest_20260724/'
    'h2_evidence_chain_rebuild_manifest.json'
)
DEFAULT_EXTERNAL_ARTIFACT_DROP_VALIDATOR = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/'
    'h2_external_artifact_drop_validator_report.json'
)
DEFAULT_EXTERNAL_ARTIFACT_INGESTION_PLAN = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_ingestion_plan_20260724/'
    'h2_external_artifact_ingestion_plan.json'
)
DEFAULT_EXTERNAL_ARTIFACT_CONTROLLED_COPY = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_controlled_copy_20260724/'
    'h2_external_artifact_controlled_copy_report.json'
)
DEFAULT_EXTERNAL_EVIDENCE_OPERATIONS_DASHBOARD = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_operations_dashboard_20260724/'
    'h2_external_evidence_operations_dashboard.json'
)
DEFAULT_EXTERNAL_EVIDENCE_ACCEPTANCE_WORKSHEET = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_acceptance_worksheet_20260724/'
    'h2_external_evidence_acceptance_worksheet.json'
)
DEFAULT_EXTERNAL_ARTIFACT_MAPPING_ALIAS = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_mapping_alias_20260724/'
    'h2_external_artifact_mapping_alias_report.json'
)
DEFAULT_EXTERNAL_EVIDENCE_CASE_VALIDATION_PLAN = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_case_validation_plan_20260724/'
    'h2_external_evidence_case_validation_plan.json'
)
DEFAULT_CASE_VALIDATION_ACCEPTANCE_CONTRACT = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_acceptance_contract_20260724/'
    'h2_case_validation_acceptance_contract_report.json'
)
DEFAULT_CASE_VALIDATION_ACCEPTANCE_EVALUATION = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_acceptance_evaluation_20260724/'
    'h2_case_validation_acceptance_evaluation_report.json'
)
DEFAULT_CASE_VALIDATION_FAILURE_ATTRIBUTION = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_failure_attribution_20260724/'
    'h2_case_validation_failure_attribution_report.json'
)
DEFAULT_CASE_VALIDATION_CLOSURE_MATRIX = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_closure_matrix_20260724/'
    'h2_case_validation_closure_matrix_report.json'
)
DEFAULT_EXTERNAL_ARTIFACT_UNLOCK_FORECAST = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_unlock_forecast_20260724/'
    'h2_external_artifact_unlock_forecast_report.json'
)
DEFAULT_EXTERNAL_EVIDENCE_CASE_VALIDATION_PLAN_SELFTEST = Path(
    'docs/codex_audit/evidence/engineering_h2_external_evidence_case_validation_plan_selftest_20260724/'
    'h2_external_evidence_case_validation_plan_selftest_report.json'
)
DEFAULT_CASE_VALIDATION_RUNNER_LEDGER = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_runner_ledger_20260724/'
    'h2_case_validation_runner_ledger.json'
)
DEFAULT_CASE_VALIDATION_RUNNER_LEDGER_SELFTEST = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_runner_ledger_selftest_20260724/'
    'h2_case_validation_runner_ledger_selftest_report.json'
)
DEFAULT_CASE_VALIDATION_RUNNER_PREFLIGHT = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_runner_preflight_20260724/'
    'h2_case_validation_runner_preflight_report.json'
)
DEFAULT_CASE_VALIDATION_COMMAND_CONTRACT = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_command_contract_20260724/'
    'h2_case_validation_command_contract_report.json'
)
DEFAULT_CASE_VALIDATION_COMMAND_CONTRACT_SELFTEST = Path(
    'docs/codex_audit/evidence/engineering_h2_case_validation_command_contract_selftest_20260724/'
    'h2_case_validation_command_contract_selftest_report.json'
)
DEFAULT_QUALITY_REVIEW_COVERAGE = Path(
    'docs/codex_audit/evidence/engineering_h2_quality_review_coverage_20260724/'
    'h2_quality_review_coverage_report.json'
)
DEFAULT_EXTERNAL_ARTIFACT_GATE_SELFTEST = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/'
    'h2_external_artifact_gate_selftest_report.json'
)
DEFAULT_EXTERNAL_ARTIFACT_GATE_NEGATIVE_SELFTEST = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/'
    'h2_external_artifact_gate_negative_selftest_report.json'
)
DEFAULT_EXTERNAL_ARTIFACT_STRICT_QA_NEGATIVE_SELFTEST = Path(
    'docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/'
    'h2_external_artifact_strict_qa_negative_selftest_report.json'
)
DEFAULT_SYNTHETIC_SELFTEST_ISOLATION_GUARD = Path(
    'docs/codex_audit/evidence/engineering_h2_synthetic_selftest_isolation_guard_20260724/'
    'h2_synthetic_selftest_isolation_guard_report.json'
)
DEFAULT_SBEPV5_DATASET_INGESTION = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/'
    'sbepv5_d27_dataset_ingestion_report.json'
)
DEFAULT_SBEPV5_DATASET_INGESTION_SELFTEST = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_selftest_20260724/'
    'sbepv5_d27_dataset_ingestion_selftest_report.json'
)
DEFAULT_SBEPV5_DIGITIZATION_PREFLIGHT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_digitization_preflight_20260724/'
    'sbepv5_d27_digitization_preflight_report.json'
)
DEFAULT_SBEPV5_LITERATURE_METRIC_PREFLIGHT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_literature_metric_preflight_20260724/'
    'sbepv5_d27_literature_metric_preflight_report.json'
)
DEFAULT_SBEPV5_EXTERNAL_DATASET = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_external_dataset_20260723/'
    'sbepv5_d27_external_dataset_report.json'
)
DEFAULT_SBEPV5_CASE_PACKAGE = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/'
    'sbepv5_d27_case_package_report.json'
)
DEFAULT_SBEPV5_CASE_PACKAGE_PREFLIGHT = Path(
    'docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_preflight_20260723/'
    'sbepv5_d27_case_package_preflight_report.json'
)
DEFAULT_PRODUCTION_MESH_16RANK_SCOUT = Path(
    'docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/production_mesh_16rank_scout_report.json'
)
DEFAULT_ACADEMIC_GAS_DETONATION_READINESS = Path(
    'docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724/'
    'academic_gas_detonation_readiness_report.json'
)
DEFAULT_COMMAND = 'tools/verify_engineering_h2_production_evidence.sh'


class VerificationReportError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationReportError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise VerificationReportError(f'missing JSON evidence: {path}') from exc
    except json.JSONDecodeError as exc:
        raise VerificationReportError(f'invalid JSON in {path}: {exc}') from exc
    require(isinstance(data, dict), f'JSON evidence is not an object: {path}')
    return data


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def summary(data: dict[str, Any]) -> dict[str, Any]:
    out = data.get('summary', {})
    return out if isinstance(out, dict) else {}


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f'missing evidence file: {path}')
    return {
        'label': label,
        'path': str(path),
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def infer_ctest_count(log_text: str) -> int | None:
    if '100% tests passed, 0 tests failed out of 22' in log_text:
        return 22
    return None


def infer_returncode(log_text: str) -> int | None:
    if 'CODEX_VERIFY_RC:0' in log_text:
        return 0
    return None


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    log_path = Path(args.log)
    scorecard_path = Path(args.scorecard)
    hybrid_cfd_path = Path(args.hybrid_cfd_scout)
    hybrid_pm_path = Path(args.hybrid_production_mesh_scout)
    hybrid_pm8_path = Path(args.hybrid_production_mesh_8rank_scout)
    hybrid_pm8_600_path = Path(args.hybrid_production_mesh_8rank_600step_stability_scout)
    hybrid_pm600_path = Path(args.hybrid_production_mesh_600step_stability_scout)
    hybrid_largegrid_path = Path(args.hybrid_largegrid_8rank_120step_scout)
    reference_agreement_path = Path(args.reference_agreement)
    bfs_kepsilon_reference_path = Path(args.bfs_kepsilon_reference)
    mpi_link_shim_script_path = Path(args.mpi_link_shim_script)
    mpi_scaling_path = Path(args.mpi_scaling)
    hybrid_affinity_path = Path(args.hybrid_affinity)
    scheduler_path = Path(args.scheduler)
    real_cad_cleanup_package_path = Path(args.real_cad_cleanup_package_report)
    real_cad_intake_preflight_path = Path(args.real_cad_intake_preflight_report)
    real_cad_boundary_tag_contract_path = Path(args.real_cad_boundary_tag_contract_report)
    fire_calibration_package_path = Path(args.fire_calibration_package_report)
    fire_calibration_public_source_triage_path = Path(args.fire_calibration_public_source_triage_report)
    fire_calibration_digitization_preflight_path = Path(args.fire_calibration_digitization_preflight_report)
    fire_calibration_literature_metric_preflight_path = Path(
        args.fire_calibration_literature_metric_preflight_report
    )
    external_plume_readiness_path = Path(args.external_plume_readiness_report)
    external_plume_public_source_triage_path = Path(args.external_plume_public_source_triage_report)
    blocker_clearance_preflight_path = Path(args.blocker_clearance_preflight_report)
    production_blocker_data_room_path = Path(args.production_blocker_data_room_report)
    production_blocker_closure_manifest_path = Path(args.production_blocker_closure_manifest_report)
    external_evidence_intake_kit_path = Path(args.external_evidence_intake_kit_report)
    external_artifact_operator_receipt_path = Path(args.external_artifact_operator_receipt_report)
    external_artifact_operator_receipt_gate_selftest_path = Path(
        args.external_artifact_operator_receipt_gate_selftest_report
    )
    evidence_chain_rebuild_manifest_path = Path(args.evidence_chain_rebuild_manifest_report)
    external_artifact_drop_validator_path = Path(args.external_artifact_drop_validator_report)
    external_artifact_ingestion_plan_path = Path(args.external_artifact_ingestion_plan_report)
    external_artifact_controlled_copy_path = Path(args.external_artifact_controlled_copy_report)
    external_evidence_operations_dashboard_path = Path(args.external_evidence_operations_dashboard_report)
    external_evidence_acceptance_worksheet_path = Path(args.external_evidence_acceptance_worksheet_report)
    external_artifact_mapping_alias_path = Path(args.external_artifact_mapping_alias_report)
    external_evidence_case_validation_plan_path = Path(args.external_evidence_case_validation_plan_report)
    case_validation_acceptance_contract_path = Path(args.case_validation_acceptance_contract_report)
    case_validation_acceptance_evaluation_path = Path(args.case_validation_acceptance_evaluation_report)
    case_validation_failure_attribution_path = Path(args.case_validation_failure_attribution_report)
    case_validation_closure_matrix_path = Path(args.case_validation_closure_matrix_report)
    external_artifact_unlock_forecast_path = Path(args.external_artifact_unlock_forecast_report)
    external_evidence_case_validation_plan_selftest_path = Path(
        args.external_evidence_case_validation_plan_selftest_report
    )
    case_validation_runner_ledger_path = Path(args.case_validation_runner_ledger)
    case_validation_runner_ledger_selftest_path = Path(args.case_validation_runner_ledger_selftest_report)
    case_validation_runner_preflight_path = Path(args.case_validation_runner_preflight_report)
    case_validation_command_contract_path = Path(args.case_validation_command_contract_report)
    case_validation_command_contract_selftest_path = Path(args.case_validation_command_contract_selftest_report)
    quality_review_coverage_path = Path(args.quality_review_coverage_report)
    external_artifact_gate_selftest_path = Path(args.external_artifact_gate_selftest_report)
    external_artifact_gate_negative_selftest_path = Path(args.external_artifact_gate_negative_selftest_report)
    external_artifact_strict_qa_negative_selftest_path = Path(args.external_artifact_strict_qa_negative_selftest_report)
    synthetic_selftest_isolation_guard_path = Path(args.synthetic_selftest_isolation_guard_report)
    sbepv5_dataset_ingestion_path = Path(args.sbepv5_dataset_ingestion_report)
    sbepv5_dataset_ingestion_selftest_path = Path(args.sbepv5_dataset_ingestion_selftest_report)
    sbepv5_digitization_preflight_path = Path(args.sbepv5_digitization_preflight_report)
    sbepv5_literature_metric_preflight_path = Path(args.sbepv5_literature_metric_preflight_report)
    sbepv5_external_dataset_path = Path(args.sbepv5_external_dataset_report)
    sbepv5_case_package_path = Path(args.sbepv5_case_package_report)
    sbepv5_case_package_preflight_path = Path(args.sbepv5_case_package_preflight_report)
    prod16_path = Path(args.production_mesh_16rank_scout)
    academic_gas_path = Path(args.academic_gas_detonation_readiness_report)

    require(log_path.is_file(), f'missing verification log: {log_path}')
    log_text = log_path.read_text(encoding='utf-8', errors='replace')
    score = load_json(scorecard_path)
    hybrid = load_json(hybrid_cfd_path)
    hybrid_pm = load_json(hybrid_pm_path)
    hybrid_pm8 = load_json(hybrid_pm8_path)
    hybrid_pm8_600 = load_json(hybrid_pm8_600_path)
    hybrid_pm600 = load_json(hybrid_pm600_path)
    hybrid_largegrid = load_json(hybrid_largegrid_path)
    reference_agreement = load_json(reference_agreement_path)
    bfs_kepsilon_reference = load_json(bfs_kepsilon_reference_path)
    mpi_scaling = load_json(mpi_scaling_path)
    hybrid_aff = load_json(hybrid_affinity_path)
    scheduler = load_json(scheduler_path)
    real_cad_cleanup_package = load_json(real_cad_cleanup_package_path)
    real_cad_intake_preflight = load_json(real_cad_intake_preflight_path)
    real_cad_boundary_tag_contract = load_json(real_cad_boundary_tag_contract_path)
    fire_calibration_package = load_json(fire_calibration_package_path)
    fire_calibration_public_source_triage = load_json(fire_calibration_public_source_triage_path)
    fire_calibration_digitization_preflight = load_json(fire_calibration_digitization_preflight_path)
    fire_calibration_literature_metric_preflight = load_json(fire_calibration_literature_metric_preflight_path)
    external_plume_readiness = load_json(external_plume_readiness_path)
    external_plume_public_source_triage = load_json(external_plume_public_source_triage_path)
    blocker_clearance_preflight = load_json(blocker_clearance_preflight_path)
    production_blocker_data_room = load_json(production_blocker_data_room_path)
    production_blocker_closure_manifest = load_json(production_blocker_closure_manifest_path)
    external_evidence_intake_kit = load_json(external_evidence_intake_kit_path)
    external_artifact_operator_receipt = load_json(external_artifact_operator_receipt_path)
    external_artifact_operator_receipt_gate_selftest = load_json(external_artifact_operator_receipt_gate_selftest_path)
    evidence_chain_rebuild_manifest = load_json(evidence_chain_rebuild_manifest_path)
    external_artifact_drop_validator = load_json(external_artifact_drop_validator_path)
    external_artifact_ingestion_plan = load_json(external_artifact_ingestion_plan_path)
    external_artifact_controlled_copy = load_json(external_artifact_controlled_copy_path)
    external_evidence_operations_dashboard = load_json(external_evidence_operations_dashboard_path)
    external_evidence_acceptance_worksheet = load_json(external_evidence_acceptance_worksheet_path)
    external_artifact_mapping_alias = load_json(external_artifact_mapping_alias_path)
    external_evidence_case_validation_plan = load_json(external_evidence_case_validation_plan_path)
    case_validation_acceptance_contract = load_json(case_validation_acceptance_contract_path)
    case_validation_acceptance_evaluation = load_json(case_validation_acceptance_evaluation_path)
    case_validation_failure_attribution = load_json(case_validation_failure_attribution_path)
    case_validation_closure_matrix = load_json(case_validation_closure_matrix_path)
    external_artifact_unlock_forecast = load_json(external_artifact_unlock_forecast_path)
    external_evidence_case_validation_plan_selftest = load_json(external_evidence_case_validation_plan_selftest_path)
    case_validation_runner_ledger = load_json(case_validation_runner_ledger_path)
    case_validation_runner_ledger_selftest = load_json(case_validation_runner_ledger_selftest_path)
    case_validation_runner_preflight = load_json(case_validation_runner_preflight_path)
    case_validation_command_contract = load_json(case_validation_command_contract_path)
    case_validation_command_contract_selftest = load_json(case_validation_command_contract_selftest_path)
    quality_review_coverage = load_json(quality_review_coverage_path)
    external_artifact_gate_selftest = load_json(external_artifact_gate_selftest_path)
    external_artifact_gate_negative_selftest = load_json(external_artifact_gate_negative_selftest_path)
    external_artifact_strict_qa_negative_selftest = load_json(external_artifact_strict_qa_negative_selftest_path)
    synthetic_selftest_isolation_guard = load_json(synthetic_selftest_isolation_guard_path)
    sbepv5_dataset_ingestion = load_json(sbepv5_dataset_ingestion_path)
    sbepv5_dataset_ingestion_selftest = load_json(sbepv5_dataset_ingestion_selftest_path)
    sbepv5_digitization_preflight = load_json(sbepv5_digitization_preflight_path)
    sbepv5_literature_metric_preflight = load_json(sbepv5_literature_metric_preflight_path)
    sbepv5_external_dataset = load_json(sbepv5_external_dataset_path)
    sbepv5_case_package = load_json(sbepv5_case_package_path)
    sbepv5_case_package_preflight = load_json(sbepv5_case_package_preflight_path)
    prod16 = load_json(prod16_path)
    academic_gas = load_json(academic_gas_path)

    hs = summary(hybrid)
    hp = summary(hybrid_pm)
    hp8 = summary(hybrid_pm8)
    hp8_600 = summary(hybrid_pm8_600)
    hp600 = summary(hybrid_pm600)
    hlg = summary(hybrid_largegrid)
    href = summary(reference_agreement)
    hbfs = summary(bfs_kepsilon_reference)
    ha_req = hybrid_aff.get('requested', {}) if isinstance(hybrid_aff.get('requested'), dict) else {}
    rc_inputs = (
        real_cad_cleanup_package.get('current_inputs', {})
        if isinstance(real_cad_cleanup_package.get('current_inputs'), dict)
        else {}
    )
    rc_intake_summary = (
        real_cad_intake_preflight.get('summary', {})
        if isinstance(real_cad_intake_preflight.get('summary'), dict)
        else {}
    )
    rc_boundary_summary = (
        real_cad_boundary_tag_contract.get('summary', {})
        if isinstance(real_cad_boundary_tag_contract.get('summary'), dict)
        else {}
    )
    fire_cal_inputs = (
        fire_calibration_package.get('current_inputs', {})
        if isinstance(fire_calibration_package.get('current_inputs'), dict)
        else {}
    )
    fire_source_triage_summary = (
        fire_calibration_public_source_triage.get('summary', {})
        if isinstance(fire_calibration_public_source_triage.get('summary'), dict)
        else {}
    )
    fire_digitization_summary = (
        fire_calibration_digitization_preflight.get('summary', {})
        if isinstance(fire_calibration_digitization_preflight.get('summary'), dict)
        else {}
    )
    fire_literature_summary = (
        fire_calibration_literature_metric_preflight.get('summary', {})
        if isinstance(fire_calibration_literature_metric_preflight.get('summary'), dict)
        else {}
    )
    plume_ready_inputs = (
        external_plume_readiness.get('current_outputs', {})
        if isinstance(external_plume_readiness.get('current_outputs'), dict)
        else (
            external_plume_readiness.get('current_inputs', {})
            if isinstance(external_plume_readiness.get('current_inputs'), dict)
            else {}
        )
    )
    plume_source_triage_summary = (
        external_plume_public_source_triage.get('summary', {})
        if isinstance(external_plume_public_source_triage.get('summary'), dict)
        else {}
    )
    sbepv5_ingestion_inputs = (
        sbepv5_dataset_ingestion.get('current_inputs', {})
        if isinstance(sbepv5_dataset_ingestion.get('current_inputs'), dict)
        else {}
    )
    sbepv5_ingestion_selftest_summary = (
        sbepv5_dataset_ingestion_selftest.get('summary', {})
        if isinstance(sbepv5_dataset_ingestion_selftest.get('summary'), dict)
        else {}
    )
    sbepv5_external_inputs = (
        sbepv5_external_dataset.get('current_inputs', {})
        if isinstance(sbepv5_external_dataset.get('current_inputs'), dict)
        else {}
    )
    sbepv5_digitization_summary = (
        sbepv5_digitization_preflight.get('summary', {})
        if isinstance(sbepv5_digitization_preflight.get('summary'), dict)
        else {}
    )
    sbepv5_literature_summary = (
        sbepv5_literature_metric_preflight.get('summary', {})
        if isinstance(sbepv5_literature_metric_preflight.get('summary'), dict)
        else {}
    )
    academic_gas_summary = (
        academic_gas.get('summary', {})
        if isinstance(academic_gas.get('summary'), dict)
        else {}
    )
    scores = score.get('scores', {}) if isinstance(score.get('scores'), dict) else {}

    ctest_count = infer_ctest_count(log_text)
    ctest_passed = ctest_count is not None
    path_audit_pass = 'machine_local_paths PASS' in log_text
    mpi_link_shim_pass = 'MPI link shim PASS' in log_text
    verifier_passed = 'PASS engineering H2 production evidence verification' in log_text
    if args.require_ctest and not ctest_passed:
        status = 'FAIL'
    else:
        status = 'PASS' if verifier_passed and path_audit_pass else 'FAIL'

    report = {
        'schema_version': SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'command': args.command,
        'returncode': args.returncode if args.returncode is not None else infer_returncode(log_text),
        'log': str(log_path),
        'log_sha256': sha256_file(log_path),
        'summary': {
            'scorecard_functional_percent': scores.get('engineering_functional_coverage_percent'),
            'scorecard_production_credibility_percent': scores.get('engineering_production_credibility_percent'),
            'scheduler_status': scheduler.get('status'),
            'hybrid_runtime_affinity_status': hybrid_aff.get('status'),
            'hybrid_runtime_affinity_ranks': ha_req.get('ranks'),
            'hybrid_runtime_affinity_threads_per_rank': ha_req.get('threads_per_rank'),
            'hybrid_runtime_affinity_warnings': hybrid_aff.get('warnings'),
            'hybrid_cfd_scout_status': hybrid.get('status'),
            'hybrid_cfd_scout_ranks': hs.get('ranks'),
            'hybrid_cfd_scout_threads_per_rank': hs.get('threads_per_rank'),
            'hybrid_cfd_cloud_rel_diff': hs.get('cloud_rel_diff'),
            'hybrid_cfd_peak_rel_diff': hs.get('peak_rel_diff'),
            'hybrid_production_mesh_scout_status': hybrid_pm.get('status'),
            'hybrid_production_mesh_scout_ranks': hp.get('ranks'),
            'hybrid_production_mesh_scout_threads_per_rank': hp.get('threads_per_rank'),
            'hybrid_production_mesh_max_step': hp.get('max_step'),
            'hybrid_production_mesh_base_cell_count': hp.get('base_cell_count'),
            'hybrid_production_mesh_amr_equivalent_fine_cell_count': hp.get('amr_equivalent_fine_cell_count'),
            'hybrid_production_mesh_cloud_rel_diff': hp.get('cloud_rel_diff'),
            'hybrid_production_mesh_peak_rel_diff': hp.get('peak_rel_diff'),
            'hybrid_production_mesh_advance_seconds_ratio': hp.get('advance_seconds_ratio'),
            'hybrid_production_mesh_8rank_status': hybrid_pm8.get('status'),
            'hybrid_production_mesh_8rank_ranks': hp8.get('ranks'),
            'hybrid_production_mesh_8rank_threads_per_rank': hp8.get('threads_per_rank'),
            'hybrid_production_mesh_8rank_max_step': hp8.get('max_step'),
            'hybrid_production_mesh_8rank_base_cell_count': hp8.get('base_cell_count'),
            'hybrid_production_mesh_8rank_amr_equivalent_fine_cell_count': hp8.get('amr_equivalent_fine_cell_count'),
            'hybrid_production_mesh_8rank_cloud_rel_diff': hp8.get('cloud_rel_diff'),
            'hybrid_production_mesh_8rank_peak_rel_diff': hp8.get('peak_rel_diff'),
            'hybrid_production_mesh_8rank_advance_seconds_ratio': hp8.get('advance_seconds_ratio'),
            'hybrid_production_mesh_8rank_regrid_count': hp8.get('regrid_count'),
            'hybrid_production_mesh_8rank_600step_status': hybrid_pm8_600.get('status'),
            'hybrid_production_mesh_8rank_600step_ranks': hp8_600.get('ranks'),
            'hybrid_production_mesh_8rank_600step_threads_per_rank': hp8_600.get('threads_per_rank'),
            'hybrid_production_mesh_8rank_600step_max_step': hp8_600.get('max_step'),
            'hybrid_production_mesh_8rank_600step_base_cell_count': hp8_600.get('base_cell_count'),
            'hybrid_production_mesh_8rank_600step_amr_equivalent_fine_cell_count': hp8_600.get('amr_equivalent_fine_cell_count'),
            'hybrid_production_mesh_8rank_600step_cloud_rel_diff': hp8_600.get('cloud_rel_diff'),
            'hybrid_production_mesh_8rank_600step_peak_rel_diff': hp8_600.get('peak_rel_diff'),
            'hybrid_production_mesh_8rank_600step_advance_seconds_ratio': hp8_600.get('advance_seconds_ratio'),
            'hybrid_production_mesh_8rank_600step_regrid_count': hp8_600.get('regrid_count'),
            'hybrid_production_mesh_600step_status': hybrid_pm600.get('status'),
            'hybrid_production_mesh_600step_ranks': hp600.get('ranks'),
            'hybrid_production_mesh_600step_threads_per_rank': hp600.get('threads_per_rank'),
            'hybrid_production_mesh_600step_max_step': hp600.get('max_step'),
            'hybrid_production_mesh_600step_base_cell_count': hp600.get('base_cell_count'),
            'hybrid_production_mesh_600step_amr_equivalent_fine_cell_count': hp600.get('amr_equivalent_fine_cell_count'),
            'hybrid_production_mesh_600step_cloud_rel_diff': hp600.get('cloud_rel_diff'),
            'hybrid_production_mesh_600step_peak_rel_diff': hp600.get('peak_rel_diff'),
            'hybrid_production_mesh_600step_advance_seconds_ratio': hp600.get('advance_seconds_ratio'),
            'hybrid_production_mesh_600step_regrid_count': hp600.get('regrid_count'),
            'hybrid_largegrid_8rank_120step_status': hybrid_largegrid.get('status'),
            'hybrid_largegrid_8rank_120step_ranks': hlg.get('ranks'),
            'hybrid_largegrid_8rank_120step_threads_per_rank': hlg.get('threads_per_rank'),
            'hybrid_largegrid_8rank_120step_max_step': hlg.get('max_step'),
            'hybrid_largegrid_8rank_120step_base_cell_count': hlg.get('base_cell_count'),
            'hybrid_largegrid_8rank_120step_amr_equivalent_fine_cell_count': hlg.get('amr_equivalent_fine_cell_count'),
            'hybrid_largegrid_8rank_120step_baseline_plotfiles': hlg.get('baseline_plotfiles'),
            'hybrid_largegrid_8rank_120step_amr_plotfiles': hlg.get('amr_plotfiles'),
            'hybrid_largegrid_8rank_120step_amr_finest_level': hlg.get('amr_finest_level'),
            'hybrid_largegrid_8rank_120step_cloud_rel_diff': hlg.get('cloud_rel_diff'),
            'hybrid_largegrid_8rank_120step_peak_rel_diff': hlg.get('peak_rel_diff'),
            'hybrid_largegrid_8rank_120step_advance_seconds_ratio': hlg.get('advance_seconds_ratio'),
            'hybrid_largegrid_8rank_120step_regrid_count': hlg.get('regrid_count'),
            'reference_agreement_status': reference_agreement.get('status'),
            'reference_agreement_all_threshold_checks_passed': href.get('all_threshold_checks_passed'),
            'reference_agreement_amr_peak_x': href.get('amr_peak_x'),
            'reference_agreement_amr_lel_cloud_volume': href.get('amr_lel_cloud_volume'),
            'reference_agreement_cloud_rel_diff': href.get('cloud_rel_diff'),
            'reference_agreement_peak_rel_diff': href.get('peak_rel_diff'),
            'bfs_kepsilon_reference_status': bfs_kepsilon_reference.get('status'),
            'bfs_kepsilon_reference_bfs_verdict': hbfs.get('bfs_validator_verdict'),
            'bfs_kepsilon_reference_bfs_returncode': hbfs.get('bfs_validator_returncode'),
            'bfs_kepsilon_reference_loglaw_returncode': hbfs.get('loglaw_validator_returncode'),
            'bfs_kepsilon_reference_loglaw_linf': hbfs.get('loglaw_linf'),
            'bfs_kepsilon_reference_blocks_production_readiness': hbfs.get('blocks_production_readiness'),
            'real_cad_cleanup_package_status': real_cad_cleanup_package.get('status'),
            'real_cad_cleanup_package_clears_blocker': real_cad_cleanup_package.get(
                'clears_real_cad_cleanup_blocker'
            ),
            'real_cad_cleanup_package_manifest_present': real_cad_cleanup_package.get('manifest_present'),
            'real_cad_cleanup_package_geometry_count': rc_inputs.get('geometry_count'),
            'real_cad_cleanup_package_large_layout': rc_inputs.get('large_layout_campaign'),
            'real_cad_intake_preflight_status': real_cad_intake_preflight.get('status'),
            'real_cad_intake_package_scaffold_available': rc_intake_summary.get('package_scaffold_available'),
            'real_cad_intake_templates_available': rc_intake_summary.get('data_room_templates_available'),
            'real_cad_intake_data_room_index_present': rc_intake_summary.get('data_room_index_present'),
            'real_cad_intake_data_room_index_validates': rc_intake_summary.get('data_room_index_validates'),
            'real_cad_intake_data_room_index_row_count': rc_intake_summary.get('data_room_index_row_count'),
            'real_cad_intake_data_room_index_paired_label_count': rc_intake_summary.get(
                'data_room_index_paired_label_count'
            ),
            'real_cad_intake_cleanup_quality_record_present': rc_intake_summary.get(
                'cleanup_quality_record_present'
            ),
            'real_cad_intake_cleanup_quality_record_validates': rc_intake_summary.get(
                'cleanup_quality_record_validates'
            ),
            'real_cad_intake_cleanup_quality_record_row_count': rc_intake_summary.get(
                'cleanup_quality_record_row_count'
            ),
            'real_cad_intake_source_cad_file_count': rc_intake_summary.get('source_cad_file_count'),
            'real_cad_intake_cleaned_geometry_file_count': rc_intake_summary.get('cleaned_geometry_file_count'),
            'real_cad_intake_missing_artifact_count': rc_intake_summary.get('missing_artifact_count'),
            'real_cad_intake_manifest_validates': rc_intake_summary.get('manifest_validates'),
            'real_cad_intake_large_layout_valid': rc_intake_summary.get('large_layout_valid'),
            'real_cad_boundary_tag_contract_status': real_cad_boundary_tag_contract.get('status'),
            'real_cad_boundary_tag_contract_does_not_clear_blockers': real_cad_boundary_tag_contract.get(
                'does_not_clear_production_blockers'
            ),
            'real_cad_boundary_tag_template_available': rc_boundary_summary.get('template_available'),
            'real_cad_boundary_tags_present': rc_boundary_summary.get('boundary_tags_present'),
            'real_cad_boundary_tags_valid': rc_boundary_summary.get('boundary_tags_valid'),
            'real_cad_boundary_tag_row_count': rc_boundary_summary.get('boundary_tag_row_count'),
            'real_cad_boundary_tag_label_count': rc_boundary_summary.get('boundary_tag_label_count'),
            'real_cad_boundary_tag_patch_count': rc_boundary_summary.get('boundary_tag_patch_count'),
            'real_cad_boundary_tag_required_role_count': rc_boundary_summary.get('required_role_count'),
            'real_cad_boundary_tag_observed_required_role_count': rc_boundary_summary.get(
                'observed_required_role_count'
            ),
            'real_cad_boundary_tag_cleanup_package_clears_blocker': rc_boundary_summary.get(
                'cleanup_package_clears_blocker'
            ),
            'real_cad_boundary_tag_intake_large_layout_valid': rc_boundary_summary.get(
                'intake_preflight_large_layout_valid'
            ),
            'real_cad_boundary_tag_ready_for_credit': rc_boundary_summary.get(
                'ready_for_real_cad_bc_tagging_credit'
            ),
            'fire_calibration_package_status': fire_calibration_package.get('status'),
            'fire_calibration_public_source_triage_status': fire_calibration_public_source_triage.get('status'),
            'fire_calibration_public_source_registry_available': fire_source_triage_summary.get(
                'public_source_registry_available'
            ),
            'fire_calibration_public_source_missing_artifact_count': fire_source_triage_summary.get(
                'missing_artifact_count'
            ),
            'fire_calibration_digitization_preflight_status': fire_calibration_digitization_preflight.get('status'),
            'fire_calibration_digitization_templates_available': fire_digitization_summary.get(
                'templates_available'
            ),
            'fire_calibration_digitization_missing_artifact_count': fire_digitization_summary.get(
                'missing_artifact_count'
            ),
            'fire_calibration_literature_metric_preflight_status': fire_calibration_literature_metric_preflight.get(
                'status'
            ),
            'fire_calibration_literature_metric_anchor_count': fire_calibration_literature_metric_preflight.get(
                'metric_anchor_count'
            ),
            'fire_calibration_literature_radiation_anchor_available': fire_literature_summary.get(
                'radiation_metric_anchor_available'
            ),
            'fire_calibration_literature_overpressure_anchor_available': fire_literature_summary.get(
                'overpressure_metric_anchor_available'
            ),
            'fire_calibration_literature_missing_artifact_count': fire_literature_summary.get(
                'missing_artifact_count'
            ),
            'fire_calibration_package_builder_ready': fire_calibration_package.get(
                'package_ready_for_dataset_builder'
            ),
            'fire_calibration_ingestion_schema_version': fire_cal_inputs.get('ingestion_schema_version'),
            'fire_calibration_ingestion_content_quality_gate_level': fire_cal_inputs.get(
                'ingestion_content_quality_gate_level'
            ),
            'fire_calibration_ingestion_selftest_status': fire_cal_inputs.get('ingestion_selftest_status'),
            'fire_calibration_ingestion_selftest_positive_passed_count': fire_cal_inputs.get(
                'ingestion_selftest_positive_passed_count'
            ),
            'fire_calibration_ingestion_selftest_negative_refused_count': fire_cal_inputs.get(
                'ingestion_selftest_negative_refused_count'
            ),
            'fire_calibration_ingestion_selftest_placeholder_negative_refused': fire_cal_inputs.get(
                'ingestion_selftest_placeholder_negative_refused'
            ),
            'fire_calibration_ingestion_selftest_duplicate_metric_negative_refused': fire_cal_inputs.get(
                'ingestion_selftest_duplicate_metric_negative_refused'
            ),
            'fire_calibration_package_metadata_available': fire_cal_inputs.get('metadata_available'),
            'fire_calibration_package_radiation_metrics_available': fire_cal_inputs.get(
                'radiation_metrics_available'
            ),
            'fire_calibration_package_overpressure_metrics_available': fire_cal_inputs.get(
                'overpressure_metrics_available'
            ),
            'external_plume_readiness_status': external_plume_readiness.get('status'),
            'external_plume_readiness_blocking_gaps': external_plume_readiness.get('blocking_gaps'),
            'external_plume_public_source_triage_status': external_plume_public_source_triage.get('status'),
            'external_plume_public_source_registry_available': plume_source_triage_summary.get(
                'public_source_registry_available'
            ),
            'external_plume_public_source_missing_artifact_count': plume_source_triage_summary.get(
                'missing_artifact_count'
            ),
            'external_plume_public_source_artifact_resolution_matrix_row_count': plume_source_triage_summary.get(
                'artifact_resolution_matrix_row_count'
            ),
            'external_plume_public_source_artifact_resolution_clearable_count': plume_source_triage_summary.get(
                'artifact_resolution_clearable_count'
            ),
            'external_plume_public_source_case_input_map_row_count': plume_source_triage_summary.get(
                'public_fact_to_case_input_map_row_count'
            ),
            'external_plume_public_source_case_input_public_fact_available_count': plume_source_triage_summary.get(
                'case_input_public_fact_available_count'
            ),
            'external_plume_public_source_case_input_needs_digitization_count': plume_source_triage_summary.get(
                'case_input_needs_digitization_count'
            ),
            'external_plume_dataset_json_written': plume_ready_inputs.get('external_plume_dataset_json_written'),
            'external_plume_shape_dataset_agreement': plume_ready_inputs.get(
                'external_plume_shape_dataset_agreement'
            ),
            'blocker_clearance_preflight_status': blocker_clearance_preflight.get('status'),
            'blocker_clearance_preflight_ready': blocker_clearance_preflight.get(
                'ready_for_production_scorecard_clearance'
            ),
            'blocker_clearance_preflight_remaining_count': blocker_clearance_preflight.get(
                'remaining_blocker_count'
            ),
            'blocker_clearance_preflight_cleared_count': blocker_clearance_preflight.get(
                'cleared_blocker_count'
            ),
            'production_blocker_data_room_status': production_blocker_data_room.get('status'),
            'production_blocker_data_room_ready': production_blocker_data_room.get(
                'ready_for_production_scorecard_clearance'
            ),
            'production_blocker_data_room_missing_artifact_count': production_blocker_data_room.get(
                'total_missing_artifact_count'
            ),
            'production_blocker_data_room_remaining_blocker_count': production_blocker_data_room.get(
                'remaining_blocker_count'
            ),
            'production_blocker_closure_manifest_status': production_blocker_closure_manifest.get('status'),
            'production_blocker_closure_manifest_missing_artifact_count': production_blocker_closure_manifest.get(
                'total_missing_artifact_count'
            ),
            'production_blocker_closure_manifest_remaining_blocker_count': production_blocker_closure_manifest.get(
                'remaining_blocker_count'
            ),
            'production_blocker_closure_manifest_domain_count': len(
                production_blocker_closure_manifest.get('domain_closure_records', [])
                if isinstance(production_blocker_closure_manifest.get('domain_closure_records'), list)
                else []
            ),
            'external_evidence_intake_kit_status': external_evidence_intake_kit.get('status'),
            'external_evidence_intake_kit_total_template_count': external_evidence_intake_kit.get(
                'total_template_count'
            ),
            'external_evidence_intake_kit_all_templates_present': external_evidence_intake_kit.get(
                'all_required_templates_present'
            ),
            'external_evidence_intake_kit_operator_receipt_template_present': external_evidence_intake_kit.get(
                'operator_receipt_template_present'
            ),
            'external_evidence_intake_kit_missing_artifact_count': external_evidence_intake_kit.get(
                'total_missing_artifact_count'
            ),
            'external_evidence_intake_kit_ready_for_external_data_handoff': external_evidence_intake_kit.get(
                'ready_for_external_data_handoff'
            ),
            'external_artifact_operator_receipt_status': external_artifact_operator_receipt.get('status'),
            'external_artifact_operator_receipt_gate_level': external_artifact_operator_receipt.get(
                'receipt_gate_level'
            ),
            'external_artifact_operator_receipt_present': external_artifact_operator_receipt.get('receipt_present'),
            'external_artifact_operator_receipt_valid': external_artifact_operator_receipt.get('receipt_valid'),
            'external_artifact_operator_receipt_gap_count': external_artifact_operator_receipt.get(
                'receipt_validation_gap_count'
            ),
            'external_artifact_operator_receipt_ready_for_acceptance': external_artifact_operator_receipt.get(
                'ready_for_external_artifact_acceptance'
            ),
            'external_artifact_operator_receipt_does_not_clear_blockers': external_artifact_operator_receipt.get(
                'does_not_clear_production_blockers'
            ),
            'external_artifact_operator_receipt_gate_selftest_status': external_artifact_operator_receipt_gate_selftest.get(
                'status'
            ),
            'external_artifact_operator_receipt_gate_selftest_only': external_artifact_operator_receipt_gate_selftest.get(
                'selftest_only'
            ),
            'external_artifact_operator_receipt_gate_selftest_does_not_clear_blockers': external_artifact_operator_receipt_gate_selftest.get(
                'does_not_clear_production_blockers'
            ),
            'external_artifact_operator_receipt_gate_selftest_positive_status': external_artifact_operator_receipt_gate_selftest.get(
                'summary', {}
            ).get('positive_status')
            if isinstance(external_artifact_operator_receipt_gate_selftest.get('summary'), dict)
            else None,
            'external_artifact_operator_receipt_gate_selftest_positive_gap_count': external_artifact_operator_receipt_gate_selftest.get(
                'summary', {}
            ).get('positive_gap_count')
            if isinstance(external_artifact_operator_receipt_gate_selftest.get('summary'), dict)
            else None,
            'external_artifact_operator_receipt_gate_selftest_negative_status': external_artifact_operator_receipt_gate_selftest.get(
                'summary', {}
            ).get('negative_status')
            if isinstance(external_artifact_operator_receipt_gate_selftest.get('summary'), dict)
            else None,
            'external_artifact_operator_receipt_gate_selftest_negative_gap_count': external_artifact_operator_receipt_gate_selftest.get(
                'summary', {}
            ).get('negative_gap_count')
            if isinstance(external_artifact_operator_receipt_gate_selftest.get('summary'), dict)
            else None,
            'external_artifact_operator_receipt_gate_selftest_negative_placeholder_gap_detected': external_artifact_operator_receipt_gate_selftest.get(
                'summary', {}
            ).get('negative_placeholder_gap_detected')
            if isinstance(external_artifact_operator_receipt_gate_selftest.get('summary'), dict)
            else None,
            'evidence_chain_rebuild_manifest_status': evidence_chain_rebuild_manifest.get('status'),
            'evidence_chain_rebuild_manifest_expected_command_count': evidence_chain_rebuild_manifest.get(
                'expected_rebuild_command_count'
            ),
            'evidence_chain_rebuild_manifest_commands_present': evidence_chain_rebuild_manifest.get(
                'all_expected_rebuild_commands_present'
            ),
            'evidence_chain_rebuild_manifest_bootstrap_passed': evidence_chain_rebuild_manifest.get(
                'bootstrap_verifier_passed'
            ),
            'evidence_chain_rebuild_manifest_bootstrap_ctest_tests': evidence_chain_rebuild_manifest.get(
                'bootstrap_ctest_tests'
            ),
            'evidence_chain_rebuild_manifest_bootstrap_ctest_skipped': evidence_chain_rebuild_manifest.get(
                'bootstrap_ctest_skipped'
            ),
            'evidence_chain_rebuild_manifest_bootstrap_ctest_evidence_status': evidence_chain_rebuild_manifest.get(
                'bootstrap_ctest_evidence_status'
            ),
            'evidence_chain_rebuild_manifest_does_not_clear_blockers': evidence_chain_rebuild_manifest.get(
                'does_not_clear_production_blockers'
            ),
            'external_artifact_drop_validator_status': external_artifact_drop_validator.get('status'),
            'external_artifact_drop_validator_content_quality_gate_level': external_artifact_drop_validator.get(
                'content_quality_gate_level'
            ),
            'external_artifact_drop_validator_domain_quality_gap_count': external_artifact_drop_validator.get(
                'domain_quality_gap_count'
            ),
            'external_artifact_drop_validator_test_fixture_data_allowed': external_artifact_drop_validator.get(
                'test_fixture_data_allowed'
            ),
            'external_artifact_drop_validator_total_expected_artifact_count': external_artifact_drop_validator.get(
                'total_expected_artifact_count'
            ),
            'external_artifact_drop_validator_valid_artifact_count': external_artifact_drop_validator.get(
                'valid_artifact_count'
            ),
            'external_artifact_drop_validator_missing_or_invalid_artifact_count': external_artifact_drop_validator.get(
                'missing_or_invalid_artifact_count'
            ),
            'external_artifact_drop_validator_ready_for_controlled_ingestion': external_artifact_drop_validator.get(
                'ready_for_controlled_ingestion'
            ),
            'external_artifact_drop_validator_does_not_clear_blockers': external_artifact_drop_validator.get(
                'does_not_clear_production_blockers'
            ),
            'external_artifact_ingestion_plan_status': external_artifact_ingestion_plan.get('status'),
            'external_artifact_ingestion_plan_total_copy_action_count': external_artifact_ingestion_plan.get(
                'total_copy_action_count'
            ),
            'external_artifact_ingestion_plan_ready_copy_action_count': external_artifact_ingestion_plan.get(
                'ready_copy_action_count'
            ),
            'external_artifact_ingestion_plan_missing_or_invalid_copy_action_count': external_artifact_ingestion_plan.get(
                'missing_or_invalid_copy_action_count'
            ),
            'external_artifact_ingestion_plan_ready_for_controlled_copy': external_artifact_ingestion_plan.get(
                'ready_for_controlled_copy'
            ),
            'external_artifact_ingestion_plan_does_not_apply_copy_actions': external_artifact_ingestion_plan.get(
                'does_not_apply_copy_actions'
            ),
            'external_artifact_ingestion_plan_does_not_clear_blockers': external_artifact_ingestion_plan.get(
                'does_not_clear_production_blockers'
            ),
            'external_artifact_controlled_copy_status': external_artifact_controlled_copy.get('status'),
            'external_artifact_controlled_copy_source_filesystem_gate_level': external_artifact_controlled_copy.get(
                'source_filesystem_gate_level'
            ),
            'external_artifact_controlled_copy_source_integrity_gap_count': external_artifact_controlled_copy.get(
                'source_integrity_gap_count'
            ),
            'external_artifact_controlled_copy_total_copy_action_count': external_artifact_controlled_copy.get(
                'total_copy_action_count'
            ),
            'external_artifact_controlled_copy_ready_copy_action_count': external_artifact_controlled_copy.get(
                'ready_copy_action_count'
            ),
            'external_artifact_controlled_copy_missing_or_invalid_copy_action_count': external_artifact_controlled_copy.get(
                'missing_or_invalid_copy_action_count'
            ),
            'external_artifact_controlled_copy_apply_requested': external_artifact_controlled_copy.get(
                'apply_requested'
            ),
            'external_artifact_controlled_copy_applied_copy_actions': external_artifact_controlled_copy.get(
                'applied_copy_actions'
            ),
            'external_artifact_controlled_copy_copied_file_count': external_artifact_controlled_copy.get(
                'copied_file_count'
            ),
            'external_artifact_controlled_copy_ready_for_controlled_copy': external_artifact_controlled_copy.get(
                'ready_for_controlled_copy'
            ),
            'external_artifact_controlled_copy_does_not_clear_blockers': external_artifact_controlled_copy.get(
                'does_not_clear_production_blockers'
            ),
            'external_evidence_operations_dashboard_status': external_evidence_operations_dashboard.get('status'),
            'external_evidence_operations_dashboard_remaining_blocker_count': external_evidence_operations_dashboard.get(
                'current_status', {}
            ).get('remaining_blocker_count')
            if isinstance(external_evidence_operations_dashboard.get('current_status'), dict)
            else None,
            'external_evidence_operations_dashboard_missing_artifact_count': external_evidence_operations_dashboard.get(
                'current_status', {}
            ).get('missing_external_artifact_count')
            if isinstance(external_evidence_operations_dashboard.get('current_status'), dict)
            else None,
            'external_evidence_operations_dashboard_drop_valid_artifact_count': external_evidence_operations_dashboard.get(
                'current_status', {}
            ).get('drop_valid_artifact_count')
            if isinstance(external_evidence_operations_dashboard.get('current_status'), dict)
            else None,
            'external_evidence_operations_dashboard_total_expected_artifact_count': external_evidence_operations_dashboard.get(
                'current_status', {}
            ).get('total_expected_external_artifact_count')
            if isinstance(external_evidence_operations_dashboard.get('current_status'), dict)
            else None,
            'external_evidence_operations_dashboard_controlled_copy_copied_file_count': external_evidence_operations_dashboard.get(
                'current_status', {}
            ).get('controlled_copy_copied_file_count')
            if isinstance(external_evidence_operations_dashboard.get('current_status'), dict)
            else None,
            'external_evidence_operations_dashboard_ready_for_production_blocker_clearance': external_evidence_operations_dashboard.get(
                'current_status', {}
            ).get('ready_for_production_blocker_clearance')
            if isinstance(external_evidence_operations_dashboard.get('current_status'), dict)
            else None,
            'external_evidence_operations_dashboard_domain_count': len(
                external_evidence_operations_dashboard.get('domain_artifact_status', [])
                if isinstance(external_evidence_operations_dashboard.get('domain_artifact_status'), list)
                else []
            ),
            'external_evidence_operations_dashboard_next_operator_command_count': len(
                external_evidence_operations_dashboard.get('next_operator_commands', [])
                if isinstance(external_evidence_operations_dashboard.get('next_operator_commands'), list)
                else []
            ),
            'external_evidence_operations_dashboard_does_not_clear_blockers': external_evidence_operations_dashboard.get(
                'does_not_clear_production_blockers'
            ),
            'external_evidence_acceptance_worksheet_status': external_evidence_acceptance_worksheet.get('status'),
            'external_evidence_acceptance_worksheet_domain_count': external_evidence_acceptance_worksheet.get(
                'summary', {}
            ).get('domain_count')
            if isinstance(external_evidence_acceptance_worksheet.get('summary'), dict)
            else None,
            'external_evidence_acceptance_worksheet_row_count': external_evidence_acceptance_worksheet.get(
                'summary', {}
            ).get('worksheet_row_count')
            if isinstance(external_evidence_acceptance_worksheet.get('summary'), dict)
            else None,
            'external_evidence_acceptance_worksheet_valid_artifact_row_count': external_evidence_acceptance_worksheet.get(
                'summary', {}
            ).get('valid_artifact_row_count')
            if isinstance(external_evidence_acceptance_worksheet.get('summary'), dict)
            else None,
            'external_evidence_acceptance_worksheet_missing_or_invalid_artifact_row_count': external_evidence_acceptance_worksheet.get(
                'summary', {}
            ).get('missing_or_invalid_artifact_row_count')
            if isinstance(external_evidence_acceptance_worksheet.get('summary'), dict)
            else None,
            'external_evidence_acceptance_worksheet_ready_for_external_evidence_acceptance': external_evidence_acceptance_worksheet.get(
                'summary', {}
            ).get('ready_for_external_evidence_acceptance')
            if isinstance(external_evidence_acceptance_worksheet.get('summary'), dict)
            else None,
            'external_evidence_acceptance_worksheet_operator_receipt_status': external_evidence_acceptance_worksheet.get(
                'summary', {}
            ).get('operator_receipt_status')
            if isinstance(external_evidence_acceptance_worksheet.get('summary'), dict)
            else None,
            'external_evidence_acceptance_worksheet_does_not_clear_blockers': external_evidence_acceptance_worksheet.get(
                'does_not_clear_production_blockers'
            ),
            'external_artifact_mapping_alias_status': external_artifact_mapping_alias.get('status'),
            'external_artifact_mapping_alias_does_not_clear_blockers': external_artifact_mapping_alias.get(
                'does_not_clear_production_blockers'
            ),
            'external_artifact_mapping_alias_domain_count': external_artifact_mapping_alias.get(
                'summary', {}
            ).get('domain_count')
            if isinstance(external_artifact_mapping_alias.get('summary'), dict)
            else None,
            'external_artifact_mapping_alias_artifact_row_count': external_artifact_mapping_alias.get(
                'summary', {}
            ).get('artifact_row_count')
            if isinstance(external_artifact_mapping_alias.get('summary'), dict)
            else None,
            'external_artifact_mapping_alias_alias_group_count': external_artifact_mapping_alias.get(
                'summary', {}
            ).get('alias_group_count')
            if isinstance(external_artifact_mapping_alias.get('summary'), dict)
            else None,
            'external_artifact_mapping_alias_observed_allowed_alias_group_count': external_artifact_mapping_alias.get(
                'summary', {}
            ).get('observed_allowed_alias_group_count')
            if isinstance(external_artifact_mapping_alias.get('summary'), dict)
            else None,
            'external_artifact_mapping_alias_duplicate_target_group_count': external_artifact_mapping_alias.get(
                'summary', {}
            ).get('duplicate_target_group_count')
            if isinstance(external_artifact_mapping_alias.get('summary'), dict)
            else None,
            'external_artifact_mapping_alias_duplicate_drop_group_count': external_artifact_mapping_alias.get(
                'summary', {}
            ).get('duplicate_drop_group_count')
            if isinstance(external_artifact_mapping_alias.get('summary'), dict)
            else None,
            'external_artifact_mapping_alias_unexpected_duplicate_target_group_count': external_artifact_mapping_alias.get(
                'summary', {}
            ).get('unexpected_duplicate_target_group_count')
            if isinstance(external_artifact_mapping_alias.get('summary'), dict)
            else None,
            'external_artifact_mapping_alias_unexpected_duplicate_drop_group_count': external_artifact_mapping_alias.get(
                'summary', {}
            ).get('unexpected_duplicate_drop_group_count')
            if isinstance(external_artifact_mapping_alias.get('summary'), dict)
            else None,
            'external_evidence_case_validation_plan_status': external_evidence_case_validation_plan.get('status'),
            'external_evidence_case_validation_plan_domain_count': external_evidence_case_validation_plan.get(
                'summary', {}
            ).get('domain_count')
            if isinstance(external_evidence_case_validation_plan.get('summary'), dict)
            else None,
            'external_evidence_case_validation_plan_worksheet_row_count': external_evidence_case_validation_plan.get(
                'summary', {}
            ).get('worksheet_row_count')
            if isinstance(external_evidence_case_validation_plan.get('summary'), dict)
            else None,
            'external_evidence_case_validation_plan_campaign_count': external_evidence_case_validation_plan.get(
                'summary', {}
            ).get('case_validation_campaign_count')
            if isinstance(external_evidence_case_validation_plan.get('summary'), dict)
            else None,
            'external_evidence_case_validation_plan_ready_campaign_count': external_evidence_case_validation_plan.get(
                'summary', {}
            ).get('ready_case_validation_campaign_count')
            if isinstance(external_evidence_case_validation_plan.get('summary'), dict)
            else None,
            'external_evidence_case_validation_plan_integrated_replay_ready': external_evidence_case_validation_plan.get(
                'summary', {}
            ).get('integrated_replay_ready')
            if isinstance(external_evidence_case_validation_plan.get('summary'), dict)
            else None,
            'external_evidence_case_validation_plan_acceptance_contract_metric_count': external_evidence_case_validation_plan.get(
                'summary', {}
            ).get('acceptance_contract_metric_count')
            if isinstance(external_evidence_case_validation_plan.get('summary'), dict)
            else None,
            'external_evidence_case_validation_plan_does_not_clear_blockers': external_evidence_case_validation_plan.get(
                'does_not_clear_production_blockers'
            ),
            'case_validation_acceptance_contract_status': case_validation_acceptance_contract.get('status'),
            'case_validation_acceptance_contract_does_not_clear_blockers': case_validation_acceptance_contract.get(
                'does_not_clear_production_blockers'
            ),
            'case_validation_acceptance_contract_campaign_count': case_validation_acceptance_contract.get(
                'summary', {}
            ).get('campaign_count')
            if isinstance(case_validation_acceptance_contract.get('summary'), dict)
            else None,
            'case_validation_acceptance_contract_metric_count': case_validation_acceptance_contract.get(
                'summary', {}
            ).get('acceptance_contract_metric_count')
            if isinstance(case_validation_acceptance_contract.get('summary'), dict)
            else None,
            'case_validation_acceptance_contract_quantitative_metric_count': case_validation_acceptance_contract.get(
                'summary', {}
            ).get('quantitative_metric_count')
            if isinstance(case_validation_acceptance_contract.get('summary'), dict)
            else None,
            'case_validation_acceptance_contract_failed_campaign_count': case_validation_acceptance_contract.get(
                'summary', {}
            ).get('failed_contract_campaign_count')
            if isinstance(case_validation_acceptance_contract.get('summary'), dict)
            else None,
            'case_validation_acceptance_contract_negative_missing_threshold_refused': case_validation_acceptance_contract.get(
                'summary', {}
            ).get('negative_missing_threshold_refused')
            if isinstance(case_validation_acceptance_contract.get('summary'), dict)
            else None,
            'case_validation_acceptance_evaluation_status': case_validation_acceptance_evaluation.get('status'),
            'case_validation_acceptance_evaluation_does_not_clear_blockers': case_validation_acceptance_evaluation.get(
                'does_not_clear_production_blockers'
            ),
            'case_validation_acceptance_evaluation_campaign_count': case_validation_acceptance_evaluation.get(
                'summary', {}
            ).get('campaign_count')
            if isinstance(case_validation_acceptance_evaluation.get('summary'), dict)
            else None,
            'case_validation_acceptance_evaluation_ready_campaign_count': case_validation_acceptance_evaluation.get(
                'summary', {}
            ).get('ready_campaign_count')
            if isinstance(case_validation_acceptance_evaluation.get('summary'), dict)
            else None,
            'case_validation_acceptance_evaluation_metric_count': case_validation_acceptance_evaluation.get(
                'summary', {}
            ).get('acceptance_metric_count')
            if isinstance(case_validation_acceptance_evaluation.get('summary'), dict)
            else None,
            'case_validation_acceptance_evaluation_passed_metric_count': case_validation_acceptance_evaluation.get(
                'summary', {}
            ).get('passed_metric_count')
            if isinstance(case_validation_acceptance_evaluation.get('summary'), dict)
            else None,
            'case_validation_acceptance_evaluation_failed_metric_count': case_validation_acceptance_evaluation.get(
                'summary', {}
            ).get('failed_metric_count')
            if isinstance(case_validation_acceptance_evaluation.get('summary'), dict)
            else None,
            'case_validation_acceptance_evaluation_deferred_metric_count': case_validation_acceptance_evaluation.get(
                'summary', {}
            ).get('deferred_metric_count')
            if isinstance(case_validation_acceptance_evaluation.get('summary'), dict)
            else None,
            'case_validation_acceptance_evaluation_ready_for_production_credit': case_validation_acceptance_evaluation.get(
                'summary', {}
            ).get('ready_for_production_credit')
            if isinstance(case_validation_acceptance_evaluation.get('summary'), dict)
            else None,
            'case_validation_acceptance_evaluation_comparator_selftest_passed': case_validation_acceptance_evaluation.get(
                'summary', {}
            ).get('comparator_selftest_passed')
            if isinstance(case_validation_acceptance_evaluation.get('summary'), dict)
            else None,
            'case_validation_failure_attribution_status': case_validation_failure_attribution.get('status'),
            'case_validation_failure_attribution_does_not_clear_blockers': case_validation_failure_attribution.get(
                'does_not_clear_production_blockers'
            ),
            'case_validation_failure_attribution_failed_metric_count': case_validation_failure_attribution.get(
                'summary', {}
            ).get('failed_metric_count')
            if isinstance(case_validation_failure_attribution.get('summary'), dict)
            else None,
            'case_validation_failure_attribution_deferred_metric_count': case_validation_failure_attribution.get(
                'summary', {}
            ).get('deferred_metric_count')
            if isinstance(case_validation_failure_attribution.get('summary'), dict)
            else None,
            'case_validation_failure_attribution_attributed_problem_metric_count': case_validation_failure_attribution.get(
                'summary', {}
            ).get('attributed_problem_metric_count')
            if isinstance(case_validation_failure_attribution.get('summary'), dict)
            else None,
            'case_validation_failure_attribution_unattributed_problem_metric_count': case_validation_failure_attribution.get(
                'summary', {}
            ).get('unattributed_problem_metric_count')
            if isinstance(case_validation_failure_attribution.get('summary'), dict)
            else None,
            'case_validation_failure_attribution_action_group_count': case_validation_failure_attribution.get(
                'summary', {}
            ).get('action_group_count')
            if isinstance(case_validation_failure_attribution.get('summary'), dict)
            else None,
            'case_validation_failure_attribution_missing_or_invalid_artifact_row_count': case_validation_failure_attribution.get(
                'summary', {}
            ).get('missing_or_invalid_artifact_row_count')
            if isinstance(case_validation_failure_attribution.get('summary'), dict)
            else None,
            'case_validation_closure_matrix_status': case_validation_closure_matrix.get('status'),
            'case_validation_closure_matrix_does_not_clear_blockers': case_validation_closure_matrix.get(
                'does_not_clear_production_blockers'
            ),
            'case_validation_closure_matrix_artifact_row_count': case_validation_closure_matrix.get('summary', {}).get(
                'artifact_row_count'
            )
            if isinstance(case_validation_closure_matrix.get('summary'), dict)
            else None,
            'case_validation_closure_matrix_missing_or_invalid_artifact_row_count': case_validation_closure_matrix.get(
                'summary', {}
            ).get('missing_or_invalid_artifact_row_count')
            if isinstance(case_validation_closure_matrix.get('summary'), dict)
            else None,
            'case_validation_closure_matrix_problem_metric_count': case_validation_closure_matrix.get('summary', {}).get(
                'problem_metric_count'
            )
            if isinstance(case_validation_closure_matrix.get('summary'), dict)
            else None,
            'case_validation_closure_matrix_mapped_problem_metric_count': case_validation_closure_matrix.get(
                'summary', {}
            ).get('mapped_problem_metric_count')
            if isinstance(case_validation_closure_matrix.get('summary'), dict)
            else None,
            'case_validation_closure_matrix_unmapped_problem_metric_count': case_validation_closure_matrix.get(
                'summary', {}
            ).get('unmapped_problem_metric_count')
            if isinstance(case_validation_closure_matrix.get('summary'), dict)
            else None,
            'case_validation_closure_matrix_artifact_rows_without_metric_context_count': case_validation_closure_matrix.get(
                'summary', {}
            ).get('artifact_rows_without_metric_context_count')
            if isinstance(case_validation_closure_matrix.get('summary'), dict)
            else None,
            'external_artifact_unlock_forecast_status': external_artifact_unlock_forecast.get('status'),
            'external_artifact_unlock_forecast_does_not_clear_blockers': external_artifact_unlock_forecast.get(
                'does_not_clear_production_blockers'
            ),
            'external_artifact_unlock_forecast_unresolved_blocker_count': external_artifact_unlock_forecast.get(
                'summary', {}
            ).get('unresolved_blocker_count')
            if isinstance(external_artifact_unlock_forecast.get('summary'), dict)
            else None,
            'external_artifact_unlock_forecast_unmapped_blocker_count': external_artifact_unlock_forecast.get(
                'summary', {}
            ).get('unmapped_blocker_count')
            if isinstance(external_artifact_unlock_forecast.get('summary'), dict)
            else None,
            'external_artifact_unlock_forecast_domain_unlock_count': external_artifact_unlock_forecast.get(
                'summary', {}
            ).get('domain_unlock_count')
            if isinstance(external_artifact_unlock_forecast.get('summary'), dict)
            else None,
            'external_artifact_unlock_forecast_artifact_unlock_requirement_count': external_artifact_unlock_forecast.get(
                'summary', {}
            ).get('artifact_unlock_requirement_count')
            if isinstance(external_artifact_unlock_forecast.get('summary'), dict)
            else None,
            'external_artifact_unlock_forecast_missing_or_invalid_artifact_count': external_artifact_unlock_forecast.get(
                'summary', {}
            ).get('missing_or_invalid_artifact_count')
            if isinstance(external_artifact_unlock_forecast.get('summary'), dict)
            else None,
            'external_artifact_unlock_forecast_problem_metric_count': external_artifact_unlock_forecast.get(
                'summary', {}
            ).get('case_validation_problem_metric_count')
            if isinstance(external_artifact_unlock_forecast.get('summary'), dict)
            else None,
            'external_artifact_unlock_forecast_mapped_problem_metric_count': external_artifact_unlock_forecast.get(
                'summary', {}
            ).get('case_validation_mapped_problem_metric_count')
            if isinstance(external_artifact_unlock_forecast.get('summary'), dict)
            else None,
            'external_artifact_unlock_forecast_ready_for_production_blocker_clearance': external_artifact_unlock_forecast.get(
                'summary', {}
            ).get('ready_for_production_blocker_clearance')
            if isinstance(external_artifact_unlock_forecast.get('summary'), dict)
            else None,
            'external_evidence_case_validation_plan_selftest_status': external_evidence_case_validation_plan_selftest.get(
                'status'
            ),
            'external_evidence_case_validation_plan_selftest_only': external_evidence_case_validation_plan_selftest.get(
                'selftest_only'
            ),
            'external_evidence_case_validation_plan_selftest_does_not_clear_blockers': external_evidence_case_validation_plan_selftest.get(
                'does_not_clear_production_blockers'
            ),
            'external_evidence_case_validation_plan_selftest_negative_ready_campaign_count': external_evidence_case_validation_plan_selftest.get(
                'summary', {}
            ).get('negative_ready_campaign_count')
            if isinstance(external_evidence_case_validation_plan_selftest.get('summary'), dict)
            else None,
            'external_evidence_case_validation_plan_selftest_negative_integrated_replay_ready': external_evidence_case_validation_plan_selftest.get(
                'summary', {}
            ).get('negative_integrated_replay_ready')
            if isinstance(external_evidence_case_validation_plan_selftest.get('summary'), dict)
            else None,
            'external_evidence_case_validation_plan_selftest_positive_ready_campaign_count': external_evidence_case_validation_plan_selftest.get(
                'summary', {}
            ).get('positive_ready_campaign_count')
            if isinstance(external_evidence_case_validation_plan_selftest.get('summary'), dict)
            else None,
            'external_evidence_case_validation_plan_selftest_positive_integrated_replay_ready': external_evidence_case_validation_plan_selftest.get(
                'summary', {}
            ).get('positive_integrated_replay_ready')
            if isinstance(external_evidence_case_validation_plan_selftest.get('summary'), dict)
            else None,
            'case_validation_runner_ledger_status': case_validation_runner_ledger.get('status'),
            'case_validation_runner_ledger_does_not_clear_blockers': case_validation_runner_ledger.get(
                'does_not_clear_production_blockers'
            ),
            'case_validation_runner_ledger_execute_requested': case_validation_runner_ledger.get('execute_requested'),
            'case_validation_runner_ledger_selected_campaign_count': case_validation_runner_ledger.get(
                'summary', {}
            ).get('selected_campaign_count')
            if isinstance(case_validation_runner_ledger.get('summary'), dict)
            else None,
            'case_validation_runner_ledger_selected_blocked_campaign_count': case_validation_runner_ledger.get(
                'summary', {}
            ).get('selected_blocked_campaign_count')
            if isinstance(case_validation_runner_ledger.get('summary'), dict)
            else None,
            'case_validation_runner_ledger_unresolved_command_count': case_validation_runner_ledger.get(
                'summary', {}
            ).get('unresolved_command_count')
            if isinstance(case_validation_runner_ledger.get('summary'), dict)
            else None,
            'case_validation_runner_ledger_command_result_count': len(case_validation_runner_ledger.get('command_results', []))
            if isinstance(case_validation_runner_ledger.get('command_results'), list)
            else None,
            'case_validation_runner_ledger_selftest_status': case_validation_runner_ledger_selftest.get('status'),
            'case_validation_runner_ledger_selftest_only': case_validation_runner_ledger_selftest.get('selftest_only'),
            'case_validation_runner_ledger_selftest_does_not_clear_blockers': case_validation_runner_ledger_selftest.get(
                'does_not_clear_production_blockers'
            ),
            'case_validation_runner_ledger_selftest_positive_verify_returncode': case_validation_runner_ledger_selftest.get(
                'summary', {}
            ).get('positive_verify_returncode')
            if isinstance(case_validation_runner_ledger_selftest.get('summary'), dict)
            else None,
            'case_validation_runner_ledger_selftest_negative_case_count': case_validation_runner_ledger_selftest.get(
                'summary', {}
            ).get('negative_case_count')
            if isinstance(case_validation_runner_ledger_selftest.get('summary'), dict)
            else None,
            'case_validation_runner_ledger_selftest_negative_refused_count': case_validation_runner_ledger_selftest.get(
                'summary', {}
            ).get('negative_refused_count')
            if isinstance(case_validation_runner_ledger_selftest.get('summary'), dict)
            else None,
            'case_validation_runner_preflight_status': case_validation_runner_preflight.get('status'),
            'case_validation_runner_preflight_does_not_clear_blockers': case_validation_runner_preflight.get(
                'does_not_clear_production_blockers'
            ),
            'case_validation_runner_preflight_dryrun_returncode': case_validation_runner_preflight.get(
                'summary', {}
            ).get('runner_dryrun_returncode')
            if isinstance(case_validation_runner_preflight.get('summary'), dict)
            else None,
            'case_validation_runner_preflight_execute_refused': case_validation_runner_preflight.get(
                'summary', {}
            ).get('execute_refused')
            if isinstance(case_validation_runner_preflight.get('summary'), dict)
            else None,
            'case_validation_runner_preflight_refusal_ledger_status': case_validation_runner_preflight.get(
                'summary', {}
            ).get('refusal_ledger_status')
            if isinstance(case_validation_runner_preflight.get('summary'), dict)
            else None,
            'case_validation_runner_preflight_refusal_ledger_written': case_validation_runner_preflight.get(
                'summary', {}
            ).get('refusal_ledger_written')
            if isinstance(case_validation_runner_preflight.get('summary'), dict)
            else None,
            'case_validation_runner_preflight_refusal_ledger_command_result_count': case_validation_runner_preflight.get(
                'summary', {}
            ).get('refusal_ledger_command_result_count')
            if isinstance(case_validation_runner_preflight.get('summary'), dict)
            else None,
            'case_validation_runner_preflight_selected_campaign_count': case_validation_runner_preflight.get(
                'summary', {}
            ).get('selected_campaign_count')
            if isinstance(case_validation_runner_preflight.get('summary'), dict)
            else None,
            'case_validation_runner_preflight_selected_ready_campaign_count': case_validation_runner_preflight.get(
                'summary', {}
            ).get('selected_ready_campaign_count')
            if isinstance(case_validation_runner_preflight.get('summary'), dict)
            else None,
            'case_validation_runner_preflight_selected_blocked_campaign_count': case_validation_runner_preflight.get(
                'summary', {}
            ).get('selected_blocked_campaign_count')
            if isinstance(case_validation_runner_preflight.get('summary'), dict)
            else None,
            'case_validation_runner_preflight_unresolved_command_count': case_validation_runner_preflight.get(
                'summary', {}
            ).get('unresolved_command_count')
            if isinstance(case_validation_runner_preflight.get('summary'), dict)
            else None,
            'case_validation_runner_preflight_positive_placeholder_all_resolved': case_validation_runner_preflight.get(
                'summary', {}
            ).get('positive_placeholder_selftest_all_resolved')
            if isinstance(case_validation_runner_preflight.get('summary'), dict)
            else None,
            'case_validation_runner_preflight_positive_placeholder_resolved_count': case_validation_runner_preflight.get(
                'summary', {}
            ).get('positive_placeholder_selftest_resolved_placeholder_count')
            if isinstance(case_validation_runner_preflight.get('summary'), dict)
            else None,
            'case_validation_runner_preflight_positive_placeholder_unresolved_command_count': case_validation_runner_preflight.get(
                'summary', {}
            ).get('positive_placeholder_selftest_unresolved_command_count')
            if isinstance(case_validation_runner_preflight.get('summary'), dict)
            else None,
            'case_validation_command_contract_status': case_validation_command_contract.get('status'),
            'case_validation_command_contract_does_not_clear_blockers': case_validation_command_contract.get(
                'does_not_clear_production_blockers'
            ),
            'case_validation_command_contract_command_count': case_validation_command_contract.get(
                'summary', {}
            ).get('command_count')
            if isinstance(case_validation_command_contract.get('summary'), dict)
            else None,
            'case_validation_command_contract_python_command_count': case_validation_command_contract.get(
                'summary', {}
            ).get('python_command_count')
            if isinstance(case_validation_command_contract.get('summary'), dict)
            else None,
            'case_validation_command_contract_bash_command_count': case_validation_command_contract.get(
                'summary', {}
            ).get('bash_command_count')
            if isinstance(case_validation_command_contract.get('summary'), dict)
            else None,
            'case_validation_command_contract_option_check_count': case_validation_command_contract.get(
                'summary', {}
            ).get('option_check_count')
            if isinstance(case_validation_command_contract.get('summary'), dict)
            else None,
            'case_validation_command_contract_placeholder_command_count': case_validation_command_contract.get(
                'summary', {}
            ).get('placeholder_command_count')
            if isinstance(case_validation_command_contract.get('summary'), dict)
            else None,
            'case_validation_command_contract_failed_command_count': case_validation_command_contract.get(
                'summary', {}
            ).get('failed_command_count')
            if isinstance(case_validation_command_contract.get('summary'), dict)
            else None,
            'case_validation_command_contract_missing_or_unsupported_contract_count': case_validation_command_contract.get(
                'summary', {}
            ).get('missing_or_unsupported_contract_count')
            if isinstance(case_validation_command_contract.get('summary'), dict)
            else None,
            'case_validation_command_contract_selftest_status': case_validation_command_contract_selftest.get('status'),
            'case_validation_command_contract_selftest_only': case_validation_command_contract_selftest.get(
                'selftest_only'
            ),
            'case_validation_command_contract_selftest_does_not_clear_blockers': case_validation_command_contract_selftest.get(
                'does_not_clear_production_blockers'
            ),
            'case_validation_command_contract_selftest_positive_verify_returncode': case_validation_command_contract_selftest.get(
                'summary', {}
            ).get('positive_verify_returncode')
            if isinstance(case_validation_command_contract_selftest.get('summary'), dict)
            else None,
            'case_validation_command_contract_selftest_negative_case_count': case_validation_command_contract_selftest.get(
                'summary', {}
            ).get('negative_case_count')
            if isinstance(case_validation_command_contract_selftest.get('summary'), dict)
            else None,
            'case_validation_command_contract_selftest_negative_refused_count': case_validation_command_contract_selftest.get(
                'summary', {}
            ).get('negative_refused_count')
            if isinstance(case_validation_command_contract_selftest.get('summary'), dict)
            else None,
            'case_validation_command_contract_selftest_missing_script_refused': case_validation_command_contract_selftest.get(
                'summary', {}
            ).get('missing_script_refused')
            if isinstance(case_validation_command_contract_selftest.get('summary'), dict)
            else None,
            'case_validation_command_contract_selftest_unsupported_option_refused': case_validation_command_contract_selftest.get(
                'summary', {}
            ).get('unsupported_option_refused')
            if isinstance(case_validation_command_contract_selftest.get('summary'), dict)
            else None,
            'quality_review_coverage_status': quality_review_coverage.get('status'),
            'quality_review_coverage_does_not_clear_blockers': quality_review_coverage.get(
                'does_not_clear_production_blockers'
            ),
            'quality_review_coverage_type_a_expected_module_count': quality_review_coverage.get(
                'summary', {}
            ).get('type_a_expected_module_count')
            if isinstance(quality_review_coverage.get('summary'), dict)
            else None,
            'quality_review_coverage_type_a_audit_record_covered_count': quality_review_coverage.get(
                'summary', {}
            ).get('type_a_audit_record_covered_count')
            if isinstance(quality_review_coverage.get('summary'), dict)
            else None,
            'quality_review_coverage_type_b_expected_phase_count': quality_review_coverage.get(
                'summary', {}
            ).get('type_b_expected_phase_count')
            if isinstance(quality_review_coverage.get('summary'), dict)
            else None,
            'quality_review_coverage_type_b_audit_record_covered_count': quality_review_coverage.get(
                'summary', {}
            ).get('type_b_audit_record_covered_count')
            if isinstance(quality_review_coverage.get('summary'), dict)
            else None,
            'quality_review_coverage_formal_independent_review_missing_count': quality_review_coverage.get(
                'summary', {}
            ).get('formal_independent_review_missing_count')
            if isinstance(quality_review_coverage.get('summary'), dict)
            else None,
            'quality_review_coverage_missing_audit_record_count': quality_review_coverage.get(
                'summary', {}
            ).get('missing_audit_record_count')
            if isinstance(quality_review_coverage.get('summary'), dict)
            else None,
            'quality_review_coverage_ready_for_qlt01_credit': quality_review_coverage.get(
                'summary', {}
            ).get('ready_for_qlt01_credit')
            if isinstance(quality_review_coverage.get('summary'), dict)
            else None,
            'quality_review_coverage_ready_for_qlt02_credit': quality_review_coverage.get(
                'summary', {}
            ).get('ready_for_qlt02_credit')
            if isinstance(quality_review_coverage.get('summary'), dict)
            else None,
            'external_artifact_gate_selftest_status': external_artifact_gate_selftest.get('status'),
            'external_artifact_gate_selftest_synthetic_only': external_artifact_gate_selftest.get(
                'synthetic_selftest_only'
            ),
            'external_artifact_gate_selftest_does_not_clear_blockers': external_artifact_gate_selftest.get(
                'does_not_clear_production_blockers'
            ),
            'external_artifact_gate_selftest_drop_valid_artifact_count': external_artifact_gate_selftest.get(
                'summary', {}
            ).get('drop_valid_artifact_count')
            if isinstance(external_artifact_gate_selftest.get('summary'), dict)
            else None,
            'external_artifact_gate_selftest_drop_total_expected_artifact_count': external_artifact_gate_selftest.get(
                'summary', {}
            ).get('drop_total_expected_artifact_count')
            if isinstance(external_artifact_gate_selftest.get('summary'), dict)
            else None,
            'external_artifact_gate_selftest_ingestion_ready_copy_action_count': external_artifact_gate_selftest.get(
                'summary', {}
            ).get('ingestion_ready_copy_action_count')
            if isinstance(external_artifact_gate_selftest.get('summary'), dict)
            else None,
            'external_artifact_gate_selftest_dryrun_copied_file_count': external_artifact_gate_selftest.get(
                'summary', {}
            ).get('dryrun_copied_file_count')
            if isinstance(external_artifact_gate_selftest.get('summary'), dict)
            else None,
            'external_artifact_gate_selftest_apply_copied_file_count': external_artifact_gate_selftest.get(
                'summary', {}
            ).get('apply_copied_file_count')
            if isinstance(external_artifact_gate_selftest.get('summary'), dict)
            else None,
            'external_artifact_gate_selftest_targets_isolated': external_artifact_gate_selftest.get(
                'summary', {}
            ).get('all_apply_targets_under_synthetic_root')
            if isinstance(external_artifact_gate_selftest.get('summary'), dict)
            else None,
            'external_artifact_gate_negative_selftest_status': external_artifact_gate_negative_selftest.get(
                'status'
            ),
            'external_artifact_gate_negative_selftest_only': external_artifact_gate_negative_selftest.get(
                'negative_selftest_only'
            ),
            'external_artifact_gate_negative_selftest_does_not_clear_blockers': external_artifact_gate_negative_selftest.get(
                'does_not_clear_production_blockers'
            ),
            'external_artifact_gate_negative_selftest_drop_status': external_artifact_gate_negative_selftest.get(
                'summary', {}
            ).get('drop_status')
            if isinstance(external_artifact_gate_negative_selftest.get('summary'), dict)
            else None,
            'external_artifact_gate_negative_selftest_drop_valid_artifact_count': external_artifact_gate_negative_selftest.get(
                'summary', {}
            ).get('drop_valid_artifact_count')
            if isinstance(external_artifact_gate_negative_selftest.get('summary'), dict)
            else None,
            'external_artifact_gate_negative_selftest_ingestion_status': external_artifact_gate_negative_selftest.get(
                'summary', {}
            ).get('ingestion_status')
            if isinstance(external_artifact_gate_negative_selftest.get('summary'), dict)
            else None,
            'external_artifact_gate_negative_selftest_controlled_copy_status': external_artifact_gate_negative_selftest.get(
                'summary', {}
            ).get('controlled_copy_status')
            if isinstance(external_artifact_gate_negative_selftest.get('summary'), dict)
            else None,
            'external_artifact_gate_negative_selftest_controlled_copy_copied_file_count': external_artifact_gate_negative_selftest.get(
                'summary', {}
            ).get('controlled_copy_copied_file_count')
            if isinstance(external_artifact_gate_negative_selftest.get('summary'), dict)
            else None,
            'external_artifact_gate_negative_selftest_apply_refused_returncode': external_artifact_gate_negative_selftest.get(
                'summary', {}
            ).get('apply_refused_returncode')
            if isinstance(external_artifact_gate_negative_selftest.get('summary'), dict)
            else None,
            'external_artifact_strict_qa_negative_selftest_status': external_artifact_strict_qa_negative_selftest.get(
                'status'
            ),
            'external_artifact_strict_qa_negative_selftest_only': external_artifact_strict_qa_negative_selftest.get(
                'negative_selftest_only'
            ),
            'external_artifact_strict_qa_negative_selftest_all_present': external_artifact_strict_qa_negative_selftest.get(
                'all_expected_artifacts_present_fixture'
            ),
            'external_artifact_strict_qa_negative_selftest_does_not_clear_blockers': external_artifact_strict_qa_negative_selftest.get(
                'does_not_clear_production_blockers'
            ),
            'external_artifact_strict_qa_negative_selftest_drop_status': external_artifact_strict_qa_negative_selftest.get(
                'summary', {}
            ).get('drop_status')
            if isinstance(external_artifact_strict_qa_negative_selftest.get('summary'), dict)
            else None,
            'external_artifact_strict_qa_negative_selftest_drop_content_quality_gate_level': external_artifact_strict_qa_negative_selftest.get(
                'summary', {}
            ).get('drop_content_quality_gate_level')
            if isinstance(external_artifact_strict_qa_negative_selftest.get('summary'), dict)
            else None,
            'external_artifact_strict_qa_negative_selftest_drop_placeholder_gap_detected': external_artifact_strict_qa_negative_selftest.get(
                'summary', {}
            ).get('drop_placeholder_gap_detected')
            if isinstance(external_artifact_strict_qa_negative_selftest.get('summary'), dict)
            else None,
            'external_artifact_strict_qa_negative_selftest_drop_domain_quality_gap_count': external_artifact_strict_qa_negative_selftest.get(
                'summary', {}
            ).get('drop_domain_quality_gap_count')
            if isinstance(external_artifact_strict_qa_negative_selftest.get('summary'), dict)
            else None,
            'external_artifact_strict_qa_negative_selftest_drop_present_artifact_count': external_artifact_strict_qa_negative_selftest.get(
                'summary', {}
            ).get('drop_present_artifact_count')
            if isinstance(external_artifact_strict_qa_negative_selftest.get('summary'), dict)
            else None,
            'external_artifact_strict_qa_negative_selftest_drop_valid_artifact_count': external_artifact_strict_qa_negative_selftest.get(
                'summary', {}
            ).get('drop_valid_artifact_count')
            if isinstance(external_artifact_strict_qa_negative_selftest.get('summary'), dict)
            else None,
            'external_artifact_strict_qa_negative_selftest_controlled_copy_copied_file_count': external_artifact_strict_qa_negative_selftest.get(
                'summary', {}
            ).get('controlled_copy_copied_file_count')
            if isinstance(external_artifact_strict_qa_negative_selftest.get('summary'), dict)
            else None,
            'external_artifact_strict_qa_negative_selftest_apply_refused_returncode': external_artifact_strict_qa_negative_selftest.get(
                'summary', {}
            ).get('apply_refused_returncode')
            if isinstance(external_artifact_strict_qa_negative_selftest.get('summary'), dict)
            else None,
            'synthetic_selftest_isolation_guard_status': synthetic_selftest_isolation_guard.get('status'),
            'synthetic_selftest_isolation_guard_synthetic_only': synthetic_selftest_isolation_guard.get(
                'synthetic_selftest_only'
            ),
            'synthetic_selftest_isolation_guard_does_not_clear_blockers': synthetic_selftest_isolation_guard.get(
                'does_not_clear_production_blockers'
            ),
            'synthetic_selftest_isolation_guard_scanned_report_count': synthetic_selftest_isolation_guard.get(
                'scanned_report_count'
            ),
            'synthetic_selftest_isolation_guard_forbidden_hit_count': synthetic_selftest_isolation_guard.get(
                'forbidden_hit_count'
            ),
            'synthetic_selftest_isolation_guard_remaining_blocker_count': synthetic_selftest_isolation_guard.get(
                'current_status', {}
            ).get('remaining_blocker_count')
            if isinstance(synthetic_selftest_isolation_guard.get('current_status'), dict)
            else None,
            'synthetic_selftest_isolation_guard_real_controlled_copy_copied_file_count': synthetic_selftest_isolation_guard.get(
                'current_status', {}
            ).get('real_controlled_copy_copied_file_count')
            if isinstance(synthetic_selftest_isolation_guard.get('current_status'), dict)
            else None,
            'sbepv5_dataset_ingestion_status': sbepv5_dataset_ingestion.get('status'),
            'sbepv5_dataset_ingestion_schema_version': sbepv5_dataset_ingestion.get('schema_version'),
            'sbepv5_dataset_ingestion_content_quality_gate_level': sbepv5_dataset_ingestion.get(
                'schema_requirements', {}
            ).get('content_quality_gate_level')
            if isinstance(sbepv5_dataset_ingestion.get('schema_requirements'), dict)
            else None,
            'sbepv5_dataset_ingestion_selftest_status': sbepv5_dataset_ingestion_selftest.get('status'),
            'sbepv5_dataset_ingestion_selftest_positive_case_count': sbepv5_ingestion_selftest_summary.get(
                'positive_case_count'
            ),
            'sbepv5_dataset_ingestion_selftest_positive_passed_count': sbepv5_ingestion_selftest_summary.get(
                'positive_passed_count'
            ),
            'sbepv5_dataset_ingestion_selftest_negative_case_count': sbepv5_ingestion_selftest_summary.get(
                'negative_case_count'
            ),
            'sbepv5_dataset_ingestion_selftest_negative_refused_count': sbepv5_ingestion_selftest_summary.get(
                'negative_refused_count'
            ),
            'sbepv5_dataset_ingestion_selftest_numeric_sensor_id_fixture_passed': sbepv5_ingestion_selftest_summary.get(
                'numeric_sensor_id_fixture_passed'
            ),
            'sbepv5_dataset_ingestion_selftest_gas_sensor_id_fixture_passed': sbepv5_ingestion_selftest_summary.get(
                'gas_sensor_id_fixture_passed'
            ),
            'sbepv5_digitization_preflight_status': sbepv5_digitization_preflight.get('status'),
            'sbepv5_digitization_templates_available': sbepv5_digitization_summary.get('templates_available'),
            'sbepv5_digitization_missing_artifact_count': sbepv5_digitization_summary.get(
                'missing_artifact_count'
            ),
            'sbepv5_literature_metric_preflight_status': sbepv5_literature_metric_preflight.get('status'),
            'sbepv5_literature_metric_anchor_available': sbepv5_literature_summary.get(
                'literature_metric_anchor_available'
            ),
            'sbepv5_literature_metric_anchor_count': sbepv5_literature_metric_preflight.get(
                'metric_anchor_count'
            ),
            'sbepv5_literature_metric_missing_artifact_count': sbepv5_literature_summary.get(
                'missing_artifact_count'
            ),
            'sbepv5_literature_gas09_arrival_interval_s': sbepv5_literature_summary.get(
                'gas09_arrival_interval_s'
            ),
            'sbepv5_literature_gas10_arrival_interval_s': sbepv5_literature_summary.get(
                'gas10_arrival_interval_s'
            ),
            'sbepv5_literature_ready_for_reference_agreement_consumption': sbepv5_literature_summary.get(
                'ready_for_reference_agreement_consumption'
            ),
            'sbepv5_dataset_metadata_available': sbepv5_ingestion_inputs.get('dataset_metadata_available'),
            'sbepv5_exact_sensor_coordinates_available': sbepv5_ingestion_inputs.get(
                'exact_sensor_coordinates_available'
            ),
            'sbepv5_exact_baffle_geometry_available': sbepv5_ingestion_inputs.get(
                'exact_baffle_geometry_available'
            ),
            'sbepv5_experimental_timeseries_available': sbepv5_ingestion_inputs.get(
                'experimental_timeseries_available'
            ),
            'sbepv5_external_dataset_status': sbepv5_external_dataset.get('status'),
            'sbepv5_external_dataset_written': sbepv5_external_dataset.get('external_dataset_written'),
            'sbepv5_external_dataset_plume_observation_passed': sbepv5_external_inputs.get(
                'plume_observation_passed'
            ),
            'sbepv5_case_package_status': sbepv5_case_package.get('status'),
            'sbepv5_case_package_runnable': sbepv5_case_package.get('case_runnable'),
            'sbepv5_case_package_preflight_status': sbepv5_case_package_preflight.get('status'),
            'academic_gas_detonation_readiness_status': academic_gas.get('status'),
            'academic_gas_foundation_ready': academic_gas_summary.get('foundation_ready'),
            'academic_gas_short_2d_detonation_wave_validation_passed': academic_gas_summary.get(
                'short_2d_detonation_wave_validation_passed'
            ),
            'academic_gas_clears_acd_02': academic_gas_summary.get('clears_acd_02'),
            'academic_gas_clears_acd_03': academic_gas_summary.get('clears_acd_03'),
            'academic_gas_missing_or_partial_quality_gate_count': academic_gas_summary.get(
                'missing_or_partial_quality_gate_count'
            ),
            'mpi_scaling': mpi_scaling.get('status'),
            'production_mesh_16rank_scout': prod16.get('status'),
            'mpi_link_shim_pass': mpi_link_shim_pass,
            'path_audit_pass': path_audit_pass,
            'ctest_passed': ctest_passed,
            'ctest_tests': ctest_count,
        },
        'evidence_files': [
            evidence_entry('verification_log', log_path),
            evidence_entry('engineering_production_scorecard', scorecard_path),
            evidence_entry('engineering_h2_hybrid_cfd_scout_report', hybrid_cfd_path),
            evidence_entry('engineering_h2_hybrid_production_mesh_scout_report', hybrid_pm_path),
            evidence_entry('engineering_h2_hybrid_production_mesh_8rank_scout_report', hybrid_pm8_path),
            evidence_entry(
                'engineering_h2_hybrid_production_mesh_8rank_600step_stability_scout_report',
                hybrid_pm8_600_path,
            ),
            evidence_entry('engineering_h2_hybrid_production_mesh_600step_stability_scout_report', hybrid_pm600_path),
            evidence_entry('engineering_h2_hybrid_largegrid_8rank_120step_scout_report', hybrid_largegrid_path),
            evidence_entry('engineering_h2_reference_agreement_report', reference_agreement_path),
            evidence_entry('engineering_bfs_kepsilon_reference_report', bfs_kepsilon_reference_path),
            evidence_entry('mpi_link_shim_script', mpi_link_shim_script_path),
            evidence_entry('engineering_h2_mpi_scaling_report', mpi_scaling_path),
            evidence_entry('hybrid_runtime_affinity_manifest', hybrid_affinity_path),
            evidence_entry('scheduler_run_report', scheduler_path),
            evidence_entry('engineering_h2_real_cad_cleanup_package_report', real_cad_cleanup_package_path),
            evidence_entry('engineering_h2_real_cad_intake_preflight_report', real_cad_intake_preflight_path),
            evidence_entry('engineering_h2_real_cad_boundary_tag_contract_report', real_cad_boundary_tag_contract_path),
            evidence_entry('engineering_h2_fire_calibration_package_report', fire_calibration_package_path),
            evidence_entry('engineering_h2_fire_calibration_public_source_triage_report', fire_calibration_public_source_triage_path),
            evidence_entry('engineering_h2_fire_calibration_digitization_preflight_report', fire_calibration_digitization_preflight_path),
            evidence_entry(
                'engineering_h2_fire_calibration_literature_metric_preflight_report',
                fire_calibration_literature_metric_preflight_path,
            ),
            evidence_entry('engineering_h2_external_plume_readiness_report', external_plume_readiness_path),
            evidence_entry('engineering_h2_external_plume_public_source_triage_report', external_plume_public_source_triage_path),
            evidence_entry('engineering_h2_blocker_clearance_preflight_report', blocker_clearance_preflight_path),
            evidence_entry('engineering_h2_production_blocker_data_room_report', production_blocker_data_room_path),
            evidence_entry('engineering_h2_production_blocker_closure_manifest_report', production_blocker_closure_manifest_path),
            evidence_entry('engineering_h2_external_evidence_intake_kit_manifest', external_evidence_intake_kit_path),
            evidence_entry('engineering_h2_external_artifact_operator_receipt_report', external_artifact_operator_receipt_path),
            evidence_entry(
                'engineering_h2_external_artifact_operator_receipt_gate_selftest_report',
                external_artifact_operator_receipt_gate_selftest_path,
            ),
            evidence_entry('engineering_h2_evidence_chain_rebuild_manifest', evidence_chain_rebuild_manifest_path),
            evidence_entry('engineering_h2_external_artifact_drop_validator_report', external_artifact_drop_validator_path),
            evidence_entry('engineering_h2_external_artifact_ingestion_plan_report', external_artifact_ingestion_plan_path),
            evidence_entry('engineering_h2_external_artifact_controlled_copy_report', external_artifact_controlled_copy_path),
            evidence_entry('engineering_h2_external_evidence_operations_dashboard_report', external_evidence_operations_dashboard_path),
            evidence_entry('engineering_h2_external_evidence_acceptance_worksheet_report', external_evidence_acceptance_worksheet_path),
            evidence_entry('engineering_h2_external_artifact_mapping_alias_report', external_artifact_mapping_alias_path),
            evidence_entry('engineering_h2_external_evidence_case_validation_plan_report', external_evidence_case_validation_plan_path),
            evidence_entry(
                'engineering_h2_case_validation_acceptance_contract_report',
                case_validation_acceptance_contract_path,
            ),
            evidence_entry(
                'engineering_h2_case_validation_acceptance_evaluation_report',
                case_validation_acceptance_evaluation_path,
            ),
            evidence_entry(
                'engineering_h2_case_validation_failure_attribution_report',
                case_validation_failure_attribution_path,
            ),
            evidence_entry(
                'engineering_h2_case_validation_closure_matrix_report',
                case_validation_closure_matrix_path,
            ),
            evidence_entry(
                'engineering_h2_external_artifact_unlock_forecast_report',
                external_artifact_unlock_forecast_path,
            ),
            evidence_entry(
                'engineering_h2_external_evidence_case_validation_plan_selftest_report',
                external_evidence_case_validation_plan_selftest_path,
            ),
            evidence_entry('engineering_h2_case_validation_runner_ledger', case_validation_runner_ledger_path),
            evidence_entry(
                'engineering_h2_case_validation_runner_ledger_selftest_report',
                case_validation_runner_ledger_selftest_path,
            ),
            evidence_entry(
                'engineering_h2_case_validation_runner_preflight_report',
                case_validation_runner_preflight_path,
            ),
            evidence_entry(
                'engineering_h2_case_validation_command_contract_report',
                case_validation_command_contract_path,
            ),
            evidence_entry(
                'engineering_h2_case_validation_command_contract_selftest_report',
                case_validation_command_contract_selftest_path,
            ),
            evidence_entry('engineering_h2_external_artifact_gate_selftest_report', external_artifact_gate_selftest_path),
            evidence_entry('engineering_h2_external_artifact_gate_negative_selftest_report', external_artifact_gate_negative_selftest_path),
            evidence_entry(
                'engineering_h2_external_artifact_strict_qa_negative_selftest_report',
                external_artifact_strict_qa_negative_selftest_path,
            ),
            evidence_entry('engineering_h2_synthetic_selftest_isolation_guard_report', synthetic_selftest_isolation_guard_path),
            evidence_entry('engineering_h2_sbepv5_dataset_ingestion_report', sbepv5_dataset_ingestion_path),
            evidence_entry(
                'engineering_h2_sbepv5_dataset_ingestion_selftest_report',
                sbepv5_dataset_ingestion_selftest_path,
            ),
            evidence_entry('engineering_h2_sbepv5_digitization_preflight_report', sbepv5_digitization_preflight_path),
            evidence_entry('engineering_h2_sbepv5_literature_metric_preflight_report', sbepv5_literature_metric_preflight_path),
            evidence_entry('engineering_h2_sbepv5_external_dataset_report', sbepv5_external_dataset_path),
            evidence_entry('engineering_h2_sbepv5_case_package_report', sbepv5_case_package_path),
            evidence_entry('engineering_h2_sbepv5_case_package_preflight_report', sbepv5_case_package_preflight_path),
            evidence_entry('production_mesh_16rank_scout_report', prod16_path),
            evidence_entry('academic_gas_detonation_readiness_report', academic_gas_path),
        ],
        'criteria': {
            'require_verifier_pass_line': True,
            'require_path_audit_pass': True,
            'require_mpi_link_shim_pass': True,
            'require_ctest': bool(args.require_ctest),
            'expected_ctest_tests': 22 if args.require_ctest else None,
            'expected_scorecard_status': 'NOT_PRODUCTION_READY',
            'expected_scheduler_status': 'PASS',
        },
        'limitations': [
            'This report packages verification evidence for the maintained engineering H2 evidence ledger.',
            'It does not launch new CFD cases and does not clear reference-data, real-CAD, or calibrated fire metric blockers.',
            'BFS/k-epsilon reference validation is tracked as a separate production blocker until reattachment, recirculation, and log-law checks pass.',
        ],
    }
    validate_report_object(report, check_hashes=False)
    return report


def validate_report_object(data: dict[str, Any], check_hashes: bool = True) -> None:
    require(data.get('schema_version') == SCHEMA_VERSION, 'schema_version mismatch')
    require(data.get('status') in {'PASS', 'FAIL'}, f'invalid status {data.get("status")}')
    require(data.get('command') == DEFAULT_COMMAND, f'unexpected command {data.get("command")}')
    log = Path(str(data.get('log', '')))
    require(log.is_file(), f'missing referenced verification log: {log}')
    if check_hashes:
        require(sha256_file(log) == data.get('log_sha256'), f'log sha256 mismatch: {log}')
    summ = summary(data)
    criteria = data.get('criteria', {}) if isinstance(data.get('criteria'), dict) else {}
    require(finite(summ.get('scorecard_functional_percent')), 'missing functional score')
    require(finite(summ.get('scorecard_production_credibility_percent')), 'missing production score')
    require(float(summ['scorecard_functional_percent']) < 100.0, 'functional score must remain below 100 while blockers exist')
    require(float(summ['scorecard_production_credibility_percent']) < 90.0, 'production credibility must stay below production-ready threshold')
    require(summ.get('scheduler_status') == 'PASS', 'scheduler status did not PASS')
    require(summ.get('hybrid_runtime_affinity_status') == 'PASS', 'hybrid runtime affinity did not PASS')
    require(summ.get('hybrid_cfd_scout_status') == 'PASS-HYBRID-CFD-SCOUT', 'hybrid CFD scout did not PASS')
    require(summ.get('hybrid_production_mesh_scout_status') == 'PASS-HYBRID-CFD-SCOUT', 'hybrid production-mesh scout did not PASS')
    require(summ.get('hybrid_production_mesh_8rank_status') == 'PASS-HYBRID-CFD-SCOUT', 'hybrid production-mesh 8-rank scout did not PASS')
    require(int(summ.get('hybrid_production_mesh_8rank_max_step', 0)) >= 120, 'hybrid 8-rank max_step too small')
    require(int(summ.get('hybrid_production_mesh_8rank_ranks', 0)) >= 8, 'hybrid 8-rank ranks too small')
    require(int(summ.get('hybrid_production_mesh_8rank_threads_per_rank', 0)) >= 2, 'hybrid 8-rank threads too small')
    require(finite(summ.get('hybrid_production_mesh_8rank_cloud_rel_diff')), 'missing hybrid 8-rank cloud_rel_diff')
    require(float(summ['hybrid_production_mesh_8rank_cloud_rel_diff']) <= 0.20, 'hybrid 8-rank cloud_rel_diff too high')
    require(finite(summ.get('hybrid_production_mesh_8rank_peak_rel_diff')), 'missing hybrid 8-rank peak_rel_diff')
    require(float(summ['hybrid_production_mesh_8rank_peak_rel_diff']) <= 0.20, 'hybrid 8-rank peak_rel_diff too high')
    require(finite(summ.get('hybrid_production_mesh_8rank_advance_seconds_ratio')), 'missing hybrid 8-rank advance ratio')
    require(float(summ['hybrid_production_mesh_8rank_advance_seconds_ratio']) <= 4.0, 'hybrid 8-rank advance ratio too high')
    require(summ.get('hybrid_production_mesh_8rank_600step_status') == 'PASS-HYBRID-CFD-SCOUT', 'hybrid production-mesh 8-rank/600-step scout did not PASS')
    require(int(summ.get('hybrid_production_mesh_8rank_600step_max_step', 0)) >= 600, 'hybrid 8-rank/600-step max_step too small')
    require(int(summ.get('hybrid_production_mesh_8rank_600step_ranks', 0)) >= 8, 'hybrid 8-rank/600-step ranks too small')
    require(int(summ.get('hybrid_production_mesh_8rank_600step_threads_per_rank', 0)) >= 2, 'hybrid 8-rank/600-step threads too small')
    require(finite(summ.get('hybrid_production_mesh_8rank_600step_cloud_rel_diff')), 'missing hybrid 8-rank/600-step cloud_rel_diff')
    require(float(summ['hybrid_production_mesh_8rank_600step_cloud_rel_diff']) <= 0.20, 'hybrid 8-rank/600-step cloud_rel_diff too high')
    require(finite(summ.get('hybrid_production_mesh_8rank_600step_peak_rel_diff')), 'missing hybrid 8-rank/600-step peak_rel_diff')
    require(float(summ['hybrid_production_mesh_8rank_600step_peak_rel_diff']) <= 0.20, 'hybrid 8-rank/600-step peak_rel_diff too high')
    require(finite(summ.get('hybrid_production_mesh_8rank_600step_advance_seconds_ratio')), 'missing hybrid 8-rank/600-step advance ratio')
    require(float(summ['hybrid_production_mesh_8rank_600step_advance_seconds_ratio']) <= 4.0, 'hybrid 8-rank/600-step advance ratio too high')
    require(summ.get('hybrid_production_mesh_600step_status') == 'PASS-HYBRID-CFD-SCOUT', 'hybrid production-mesh 600-step scout did not PASS')
    require(int(summ.get('hybrid_production_mesh_600step_max_step', 0)) >= 600, 'hybrid 600-step max_step too small')
    require(int(summ.get('hybrid_production_mesh_600step_ranks', 0)) >= 4, 'hybrid 600-step ranks too small')
    require(int(summ.get('hybrid_production_mesh_600step_threads_per_rank', 0)) >= 2, 'hybrid 600-step threads too small')
    require(finite(summ.get('hybrid_production_mesh_600step_cloud_rel_diff')), 'missing hybrid 600-step cloud_rel_diff')
    require(float(summ['hybrid_production_mesh_600step_cloud_rel_diff']) <= 0.20, 'hybrid 600-step cloud_rel_diff too high')
    require(finite(summ.get('hybrid_production_mesh_600step_peak_rel_diff')), 'missing hybrid 600-step peak_rel_diff')
    require(float(summ['hybrid_production_mesh_600step_peak_rel_diff']) <= 0.20, 'hybrid 600-step peak_rel_diff too high')
    require(finite(summ.get('hybrid_production_mesh_600step_advance_seconds_ratio')), 'missing hybrid 600-step advance ratio')
    require(float(summ['hybrid_production_mesh_600step_advance_seconds_ratio']) <= 4.0, 'hybrid 600-step advance ratio too high')
    require(summ.get('hybrid_largegrid_8rank_120step_status') == 'PASS-HYBRID-CFD-SCOUT', 'hybrid large-grid 8-rank/120-step scout did not PASS')
    require(int(summ.get('hybrid_largegrid_8rank_120step_ranks', 0)) >= 8, 'hybrid large-grid ranks too small')
    require(int(summ.get('hybrid_largegrid_8rank_120step_threads_per_rank', 0)) >= 2, 'hybrid large-grid threads too small')
    require(int(summ.get('hybrid_largegrid_8rank_120step_max_step', 0)) >= 120, 'hybrid large-grid max_step too small')
    require(int(summ.get('hybrid_largegrid_8rank_120step_base_cell_count', 0)) >= 200000, 'hybrid large-grid base cell count too small')
    require(int(summ.get('hybrid_largegrid_8rank_120step_amr_equivalent_fine_cell_count', 0)) >= 1500000, 'hybrid large-grid equivalent fine cell count too small')
    require(int(summ.get('hybrid_largegrid_8rank_120step_baseline_plotfiles', 0)) >= 5, 'hybrid large-grid baseline plotfiles too few')
    require(int(summ.get('hybrid_largegrid_8rank_120step_amr_plotfiles', 0)) >= 5, 'hybrid large-grid AMR plotfiles too few')
    require(int(summ.get('hybrid_largegrid_8rank_120step_amr_finest_level', 0)) >= 1, 'hybrid large-grid AMR finest level too small')
    require(finite(summ.get('hybrid_largegrid_8rank_120step_cloud_rel_diff')), 'missing hybrid large-grid cloud_rel_diff')
    require(float(summ['hybrid_largegrid_8rank_120step_cloud_rel_diff']) <= 0.20, 'hybrid large-grid cloud_rel_diff too high')
    require(finite(summ.get('hybrid_largegrid_8rank_120step_peak_rel_diff')), 'missing hybrid large-grid peak_rel_diff')
    require(float(summ['hybrid_largegrid_8rank_120step_peak_rel_diff']) <= 0.20, 'hybrid large-grid peak_rel_diff too high')
    require(finite(summ.get('hybrid_largegrid_8rank_120step_advance_seconds_ratio')), 'missing hybrid large-grid advance ratio')
    require(float(summ['hybrid_largegrid_8rank_120step_advance_seconds_ratio']) <= 4.0, 'hybrid large-grid advance ratio too high')
    require(summ.get('reference_agreement_status') == 'PASS-REFERENCE-THRESHOLD-AGREEMENT', 'reference threshold agreement did not PASS')
    require(summ.get('reference_agreement_all_threshold_checks_passed') is True, 'reference threshold checks did not all PASS')
    require(finite(summ.get('reference_agreement_amr_peak_x')), 'missing reference agreement AMR peak')
    require(0.04 <= float(summ['reference_agreement_amr_peak_x']) < 0.75, 'reference agreement AMR peak outside LEL/UEL range')
    require(finite(summ.get('reference_agreement_amr_lel_cloud_volume')), 'missing reference agreement AMR LEL cloud volume')
    require(float(summ['reference_agreement_amr_lel_cloud_volume']) > 0.0, 'reference agreement AMR LEL cloud volume not positive')
    require(finite(summ.get('reference_agreement_cloud_rel_diff')), 'missing reference agreement cloud_rel_diff')
    require(float(summ['reference_agreement_cloud_rel_diff']) <= 0.05, 'reference agreement cloud_rel_diff too high')
    require(finite(summ.get('reference_agreement_peak_rel_diff')), 'missing reference agreement peak_rel_diff')
    require(float(summ['reference_agreement_peak_rel_diff']) <= 0.05, 'reference agreement peak_rel_diff too high')
    require(
        summ.get('bfs_kepsilon_reference_status') in {
            'PASS-BFS-KEPSILON-REFERENCE',
            'NOT_READY-BFS-KEPSILON-REFERENCE',
        },
        'invalid BFS/k-epsilon reference status',
    )
    if summ.get('bfs_kepsilon_reference_status') == 'PASS-BFS-KEPSILON-REFERENCE':
        require(summ.get('bfs_kepsilon_reference_bfs_returncode') == 0, 'BFS reference PASS has nonzero BFS rc')
        require(
            summ.get('bfs_kepsilon_reference_blocks_production_readiness') is False,
            'BFS reference PASS still blocks production',
        )
    else:
        require(
            summ.get('bfs_kepsilon_reference_blocks_production_readiness') is True,
            'BFS reference NOT_READY must block production',
        )
    require(
        summ.get('real_cad_cleanup_package_status')
        in {'PASS-H2-REAL-CAD-CLEANUP-PACKAGE', 'NOT_READY-H2-REAL-CAD-CLEANUP-PACKAGE'},
        'invalid real-CAD cleanup package status',
    )
    if summ.get('real_cad_cleanup_package_status') == 'PASS-H2-REAL-CAD-CLEANUP-PACKAGE':
        require(summ.get('real_cad_cleanup_package_clears_blocker') is True, 'real-CAD PASS does not clear blocker')
        require(summ.get('real_cad_cleanup_package_manifest_present') is True, 'real-CAD PASS has no manifest')
        require(int(summ.get('real_cad_cleanup_package_geometry_count', 0)) >= 3, 'real-CAD PASS geometry count too small')
        require(summ.get('real_cad_cleanup_package_large_layout') is True, 'real-CAD PASS is not large-layout')
    else:
        require(summ.get('real_cad_cleanup_package_clears_blocker') is False, 'real-CAD NOT_READY cannot clear blocker')
    require(
        summ.get('real_cad_intake_preflight_status') == 'PASS-H2-REAL-CAD-INTAKE-PREFLIGHT',
        'real-CAD intake preflight did not PASS',
    )
    require(
        summ.get('real_cad_intake_package_scaffold_available') is True,
        'real-CAD intake package scaffold missing',
    )
    require(
        summ.get('real_cad_intake_templates_available') is True,
        'real-CAD intake templates missing',
    )
    require(
        isinstance(summ.get('real_cad_intake_data_room_index_present'), bool),
        'real-CAD intake data-room index presence missing',
    )
    require(
        isinstance(summ.get('real_cad_intake_data_room_index_validates'), bool),
        'real-CAD intake data-room index validity missing',
    )
    require(
        isinstance(summ.get('real_cad_intake_cleanup_quality_record_present'), bool),
        'real-CAD intake cleanup quality record presence missing',
    )
    require(
        isinstance(summ.get('real_cad_intake_cleanup_quality_record_validates'), bool),
        'real-CAD intake cleanup quality record validity missing',
    )
    if summ.get('real_cad_cleanup_package_status') == 'PASS-H2-REAL-CAD-CLEANUP-PACKAGE':
        require(summ.get('real_cad_intake_manifest_validates') is True, 'real-CAD PASS lacks valid intake manifest')
        require(summ.get('real_cad_intake_large_layout_valid') is True, 'real-CAD PASS lacks large-layout intake validity')
        require(
            summ.get('real_cad_intake_data_room_index_validates') is True,
            'real-CAD PASS lacks valid data-room index',
        )
        require(
            summ.get('real_cad_intake_cleanup_quality_record_validates') is True,
            'real-CAD PASS lacks valid cleanup quality record',
        )
    else:
        require(
            int(summ.get('real_cad_intake_missing_artifact_count', 0)) >= 1,
            'real-CAD NOT_READY must retain missing intake artifacts',
        )
    require(
        summ.get('real_cad_boundary_tag_contract_status')
        in {'PASS-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT', 'NOT_READY-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT'},
        'invalid real-CAD boundary tag contract status',
    )
    require(
        summ.get('real_cad_boundary_tag_contract_does_not_clear_blockers') is True,
        'real-CAD boundary tag contract must not clear blockers',
    )
    require(
        summ.get('real_cad_boundary_tag_template_available') is True,
        'real-CAD boundary tag template missing',
    )
    require(isinstance(summ.get('real_cad_boundary_tags_present'), bool), 'real-CAD boundary tag presence missing')
    require(isinstance(summ.get('real_cad_boundary_tags_valid'), bool), 'real-CAD boundary tag validity missing')
    require(
        int(summ.get('real_cad_boundary_tag_required_role_count', 0)) == 3,
        'real-CAD boundary tag required role count mismatch',
    )
    if summ.get('real_cad_boundary_tag_contract_status') == 'PASS-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT':
        require(summ.get('real_cad_boundary_tags_valid') is True, 'PASS boundary tag contract has invalid tags')
        require(
            int(summ.get('real_cad_boundary_tag_label_count', 0)) >= 3,
            'PASS boundary tag contract has too few labels',
        )
        require(
            int(summ.get('real_cad_boundary_tag_observed_required_role_count', 0)) == 3,
            'PASS boundary tag contract missing required roles',
        )
        require(
            summ.get('real_cad_boundary_tag_cleanup_package_clears_blocker') is True,
            'PASS boundary tag contract lacks cleanup blocker clearance',
        )
        require(
            summ.get('real_cad_boundary_tag_intake_large_layout_valid') is True,
            'PASS boundary tag contract lacks real-CAD intake validity',
        )
        require(summ.get('real_cad_boundary_tag_ready_for_credit') is True, 'PASS boundary tag contract not credit-ready')
    else:
        require(
            summ.get('real_cad_boundary_tag_ready_for_credit') is False,
            'NOT_READY boundary tag contract marked credit-ready',
        )
    require(
        summ.get('fire_calibration_package_status')
        in {'PASS-H2-FIRE-CALIBRATION-PACKAGE', 'NOT_READY-H2-FIRE-CALIBRATION-PACKAGE'},
        'invalid fire calibration package status',
    )
    require(
        summ.get('fire_calibration_public_source_triage_status') == 'PASS-H2-FIRE-CALIBRATION-PUBLIC-SOURCE-TRIAGE',
        'fire calibration public-source triage did not PASS',
    )
    require(
        summ.get('fire_calibration_public_source_registry_available') is True,
        'fire calibration public-source registry missing',
    )
    require(
        int(summ.get('fire_calibration_public_source_missing_artifact_count', 0)) >= 3,
        'fire calibration public-source triage must retain missing calibration artifacts',
    )
    require(
        summ.get('fire_calibration_digitization_preflight_status')
        == 'PASS-H2-FIRE-CALIBRATION-DIGITIZATION-PREFLIGHT',
        'fire calibration digitization preflight did not PASS',
    )
    require(
        summ.get('fire_calibration_digitization_templates_available') is True,
        'fire calibration digitization templates missing',
    )
    require(
        summ.get('fire_calibration_literature_metric_preflight_status')
        == 'PASS-H2-FIRE-CALIBRATION-LITERATURE-METRIC-PREFLIGHT',
        'fire calibration literature metric preflight did not PASS',
    )
    require(
        int(summ.get('fire_calibration_literature_metric_anchor_count', 0)) >= 4,
        'fire calibration literature metric anchor count too small',
    )
    require(
        summ.get('fire_calibration_literature_radiation_anchor_available') is True,
        'fire calibration radiation literature anchors missing',
    )
    require(
        summ.get('fire_calibration_literature_overpressure_anchor_available') is True,
        'fire calibration overpressure literature anchors missing',
    )
    require(
        int(summ.get('fire_calibration_literature_missing_artifact_count', 0)) >= 1,
        'fire calibration literature preflight must retain missing artifacts',
    )
    if summ.get('fire_calibration_package_status') == 'PASS-H2-FIRE-CALIBRATION-PACKAGE':
        require(summ.get('fire_calibration_package_builder_ready') is True, 'fire calibration PASS is not builder-ready')
        require(summ.get('fire_calibration_package_metadata_available') is True, 'fire calibration PASS missing metadata')
        require(
            summ.get('fire_calibration_package_radiation_metrics_available') is True,
            'fire calibration PASS missing radiation metrics',
        )
        require(
            summ.get('fire_calibration_package_overpressure_metrics_available') is True,
            'fire calibration PASS missing overpressure metrics',
        )
    else:
        require(
            summ.get('fire_calibration_package_builder_ready') is False,
            'fire calibration NOT_READY cannot be builder-ready',
        )
        require(
            int(summ.get('fire_calibration_digitization_missing_artifact_count', 0)) >= 1,
            'fire calibration NOT_READY must retain missing digitization artifacts',
        )
    require(int(summ.get('fire_calibration_ingestion_schema_version', 0)) >= 2, 'fire calibration ingestion schema too old')
    require(
        summ.get('fire_calibration_ingestion_content_quality_gate_level')
        == 'strict-v1-placeholder-free-and-non-synthetic',
        'fire calibration ingestion content quality gate mismatch',
    )
    require(
        summ.get('fire_calibration_ingestion_selftest_status')
        == 'PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION-SELFTEST',
        'fire calibration ingestion selftest did not PASS',
    )
    require(
        int(summ.get('fire_calibration_ingestion_selftest_positive_passed_count', 0)) == 2,
        'fire calibration ingestion selftest positive fixtures did not pass',
    )
    require(
        int(summ.get('fire_calibration_ingestion_selftest_negative_refused_count', 0)) == 1,
        'fire calibration ingestion selftest negative fixture was not refused',
    )
    require(
        summ.get('fire_calibration_ingestion_selftest_placeholder_negative_refused') is True,
        'fire calibration ingestion selftest did not refuse placeholder marker',
    )
    require(
        summ.get('fire_calibration_ingestion_selftest_duplicate_metric_negative_refused') is True,
        'fire calibration ingestion selftest did not refuse duplicate metric',
    )
    require(
        summ.get('external_plume_readiness_status')
        in {'PASS-EXTERNAL-PLUME-BENCHMARK', 'NOT_READY-EXTERNAL-PLUME-BENCHMARK'},
        'invalid external plume readiness status',
    )
    require(
        summ.get('external_plume_public_source_triage_status') == 'PASS-H2-EXTERNAL-PLUME-PUBLIC-SOURCE-TRIAGE',
        'external plume public-source triage did not PASS',
    )
    require(
        summ.get('external_plume_public_source_registry_available') is True,
        'external plume public-source registry missing',
    )
    require(
        int(summ.get('external_plume_public_source_missing_artifact_count', 0)) >= 3,
        'external plume public-source triage must retain missing exact-data artifacts',
    )
    require(
        int(summ.get('external_plume_public_source_artifact_resolution_matrix_row_count', 0)) >= 4,
        'external plume public-source artifact resolution matrix incomplete',
    )
    require(
        int(summ.get('external_plume_public_source_artifact_resolution_clearable_count', -1)) == 0,
        'external plume public-source triage cannot mark artifacts clearable',
    )
    require(
        int(summ.get('external_plume_public_source_case_input_map_row_count', 0)) >= 6,
        'external plume public fact-to-case input map incomplete',
    )
    require(
        int(summ.get('external_plume_public_source_case_input_public_fact_available_count', 0)) >= 3,
        'external plume public case fact count too small',
    )
    require(
        int(summ.get('external_plume_public_source_case_input_needs_digitization_count', 0)) >= 3,
        'external plume triage must retain digitization-needed case inputs',
    )
    if summ.get('external_plume_readiness_status') == 'PASS-EXTERNAL-PLUME-BENCHMARK':
        require(
            summ.get('external_plume_dataset_json_written') is True,
            'external plume PASS has no dataset JSON',
        )
        require(
            summ.get('external_plume_shape_dataset_agreement') is True,
            'external plume PASS lacks shape agreement',
        )
    else:
        gaps = summ.get('external_plume_readiness_blocking_gaps')
        require(isinstance(gaps, list) and gaps, 'external plume NOT_READY must list blocking gaps')
        require(
            summ.get('external_plume_shape_dataset_agreement') is not True,
            'external plume NOT_READY cannot claim shape agreement',
        )
    require(
        summ.get('blocker_clearance_preflight_status')
        in {'PASS-H2-BLOCKER-CLEARANCE-PREFLIGHT', 'NOT_READY-H2-BLOCKER-CLEARANCE-PREFLIGHT'},
        'invalid blocker clearance preflight status',
    )
    require(
        summ.get('production_blocker_data_room_status') == 'PASS-H2-PRODUCTION-BLOCKER-DATA-ROOM',
        'production blocker data-room report did not PASS',
    )
    require(
        summ.get('production_blocker_closure_manifest_status')
        == 'PASS-H2-PRODUCTION-BLOCKER-CLOSURE-MANIFEST',
        'production blocker closure manifest did not PASS',
    )
    require(
        int(summ.get('production_blocker_closure_manifest_domain_count', 0)) == 3,
        'production blocker closure manifest domain count mismatch',
    )
    if summ.get('blocker_clearance_preflight_status') == 'PASS-H2-BLOCKER-CLEARANCE-PREFLIGHT':
        require(
            summ.get('blocker_clearance_preflight_ready') is True,
            'blocker clearance PASS is not marked ready',
        )
        require(
            int(summ.get('blocker_clearance_preflight_remaining_count', -1)) == 0,
            'blocker clearance PASS still has remaining blockers',
        )
    else:
        require(
            summ.get('blocker_clearance_preflight_ready') is False,
            'blocker clearance NOT_READY cannot be ready',
        )
        require(
            int(summ.get('blocker_clearance_preflight_remaining_count', 0)) >= 1,
            'blocker clearance NOT_READY must retain remaining blockers',
        )
        require(
            summ.get('production_blocker_data_room_ready') is False,
            'data-room report cannot be ready while blocker preflight is NOT_READY',
        )
        require(
            int(summ.get('production_blocker_data_room_missing_artifact_count', 0)) >= 1,
            'data-room NOT_READY path must retain missing artifacts',
        )
        require(
            int(summ.get('production_blocker_data_room_remaining_blocker_count', 0))
            == int(summ.get('blocker_clearance_preflight_remaining_count', 0)),
            'data-room remaining blocker count differs from blocker preflight',
        )
        require(
            int(summ.get('production_blocker_closure_manifest_missing_artifact_count', 0))
            == int(summ.get('production_blocker_data_room_missing_artifact_count', 0)),
            'closure manifest missing artifact count differs from data-room',
        )
        require(
            int(summ.get('production_blocker_closure_manifest_remaining_blocker_count', 0))
            == int(summ.get('blocker_clearance_preflight_remaining_count', 0)),
            'closure manifest remaining blocker count differs from blocker preflight',
        )
        require(
            summ.get('external_evidence_intake_kit_status')
            == 'PASS-H2-EXTERNAL-EVIDENCE-INTAKE-KIT-MANIFEST',
            'external evidence intake kit manifest did not PASS',
        )
        require(
            int(summ.get('external_evidence_intake_kit_total_template_count', 0)) >= 23,
            'external evidence intake kit template count too small',
        )
        require(
            summ.get('external_evidence_intake_kit_all_templates_present') is True,
            'external evidence intake kit has missing templates',
        )
        require(
            summ.get('external_evidence_intake_kit_operator_receipt_template_present') is True,
            'external evidence intake kit missing operator receipt template',
        )
        require(
            summ.get('external_evidence_intake_kit_ready_for_external_data_handoff') is True,
            'external evidence intake kit is not ready for external data handoff',
        )
        require(
            int(summ.get('external_evidence_intake_kit_missing_artifact_count', 0))
            == int(summ.get('production_blocker_data_room_missing_artifact_count', 0)),
            'external evidence intake kit missing artifact count differs from data-room',
        )
        require(
            summ.get('external_artifact_operator_receipt_status')
            in {
                'PASS-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT',
                'NOT_READY-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT',
            },
            'invalid external artifact operator receipt status',
        )
        require(
            summ.get('external_artifact_operator_receipt_gate_level') == EXPECTED_OPERATOR_RECEIPT_GATE_LEVEL,
            'external artifact operator receipt gate mismatch',
        )
        require(
            summ.get('external_artifact_operator_receipt_does_not_clear_blockers') is True,
            'external artifact operator receipt must not clear blockers',
        )
        if summ.get('external_artifact_operator_receipt_status') == 'PASS-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT':
            require(
                summ.get('external_artifact_operator_receipt_present') is True,
                'PASS operator receipt report is missing receipt',
            )
            require(
                summ.get('external_artifact_operator_receipt_valid') is True,
                'PASS operator receipt report is invalid',
            )
            require(
                int(summ.get('external_artifact_operator_receipt_gap_count', -1)) == 0,
                'PASS operator receipt report has gaps',
            )
            require(
                summ.get('external_artifact_operator_receipt_ready_for_acceptance') is True,
                'PASS operator receipt is not ready for external artifact acceptance',
            )
        else:
            require(
                summ.get('external_artifact_operator_receipt_valid') is False,
                'NOT_READY operator receipt report marked valid',
            )
            require(
                int(summ.get('external_artifact_operator_receipt_gap_count', 0)) >= 1,
                'NOT_READY operator receipt report must retain receipt gaps',
            )
            require(
                summ.get('external_artifact_operator_receipt_ready_for_acceptance') is False,
                'NOT_READY operator receipt marked ready',
            )
        require(
            summ.get('external_artifact_operator_receipt_gate_selftest_status')
            == 'PASS-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT-GATE-SELFTEST',
            'operator receipt gate selftest did not PASS',
        )
        require(
            summ.get('external_artifact_operator_receipt_gate_selftest_only') is True,
            'operator receipt gate selftest must be marked selftest-only',
        )
        require(
            summ.get('external_artifact_operator_receipt_gate_selftest_does_not_clear_blockers') is True,
            'operator receipt gate selftest must not clear blockers',
        )
        require(
            summ.get('external_artifact_operator_receipt_gate_selftest_positive_status')
            == 'PASS-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT',
            'operator receipt gate positive fixture did not PASS',
        )
        require(
            int(summ.get('external_artifact_operator_receipt_gate_selftest_positive_gap_count', -1)) == 0,
            'operator receipt gate positive fixture has gaps',
        )
        require(
            summ.get('external_artifact_operator_receipt_gate_selftest_negative_status')
            == 'NOT_READY-H2-EXTERNAL-ARTIFACT-OPERATOR-RECEIPT',
            'operator receipt gate template fixture was not rejected',
        )
        require(
            int(summ.get('external_artifact_operator_receipt_gate_selftest_negative_gap_count', 0)) >= 1,
            'operator receipt gate negative fixture did not retain gaps',
        )
        require(
            summ.get('external_artifact_operator_receipt_gate_selftest_negative_placeholder_gap_detected') is True,
            'operator receipt gate negative fixture did not detect placeholder/template markers',
        )
        require(
            summ.get('evidence_chain_rebuild_manifest_status') == 'PASS-H2-EVIDENCE-CHAIN-REBUILD-MANIFEST',
            'evidence-chain rebuild manifest did not PASS',
        )
        require(
            int(summ.get('evidence_chain_rebuild_manifest_expected_command_count', 0)) >= 25,
            'evidence-chain rebuild command count too small',
        )
        require(
            summ.get('evidence_chain_rebuild_manifest_commands_present') is True,
            'evidence-chain rebuild manifest missing commands',
        )
        require(
            summ.get('evidence_chain_rebuild_manifest_bootstrap_passed') is True,
            'evidence-chain rebuild bootstrap verifier did not PASS',
        )
        manifest_ctest_status = summ.get('evidence_chain_rebuild_manifest_bootstrap_ctest_evidence_status')
        if criteria.get('require_ctest', True):
            require(manifest_ctest_status == 'PASS', 'evidence-chain rebuild bootstrap CTest did not PASS')
            require(
                int(summ.get('evidence_chain_rebuild_manifest_bootstrap_ctest_tests', 0)) == 22,
                'evidence-chain rebuild bootstrap CTest count mismatch',
            )
            require(
                summ.get('evidence_chain_rebuild_manifest_bootstrap_ctest_skipped') is False,
                'required evidence-chain rebuild bootstrap CTest was marked skipped',
            )
        else:
            require(
                manifest_ctest_status in {'PASS', 'SKIPPED'},
                'evidence-chain rebuild bootstrap CTest evidence status invalid',
            )
            if manifest_ctest_status == 'SKIPPED':
                require(
                    summ.get('evidence_chain_rebuild_manifest_bootstrap_ctest_skipped') is True,
                    'skipped evidence-chain rebuild bootstrap CTest lacks skip marker',
                )
        require(
            summ.get('evidence_chain_rebuild_manifest_does_not_clear_blockers') is True,
            'evidence-chain rebuild manifest must not clear blockers',
        )
        require(
            summ.get('external_artifact_drop_validator_status')
            in {'PASS-H2-EXTERNAL-ARTIFACT-DROP', 'NOT_READY-H2-EXTERNAL-ARTIFACT-DROP'},
            'invalid external artifact drop validator status',
        )
        require(
            summ.get('external_artifact_drop_validator_content_quality_gate_level') == EXPECTED_EXTERNAL_ARTIFACT_GATE_LEVEL,
            'external artifact drop validator is not using strict content QA',
        )
        require(
            summ.get('external_artifact_drop_validator_test_fixture_data_allowed') is False,
            'production external artifact drop validator must reject test fixture markers',
        )
        require(
            int(summ.get('external_artifact_drop_validator_total_expected_artifact_count', 0))
            == int(summ.get('production_blocker_data_room_missing_artifact_count', 0)),
            'external artifact drop expected count differs from data-room',
        )
        require(
            summ.get('external_artifact_drop_validator_does_not_clear_blockers') is True,
            'external artifact drop validator must not clear blockers',
        )
        if summ.get('external_artifact_drop_validator_status') == 'PASS-H2-EXTERNAL-ARTIFACT-DROP':
            require(
                summ.get('external_artifact_drop_validator_ready_for_controlled_ingestion') is True,
                'PASS external artifact drop is not ready for ingestion',
            )
            require(
                int(summ.get('external_artifact_drop_validator_missing_or_invalid_artifact_count', -1)) == 0,
                'PASS external artifact drop still has missing artifacts',
            )
        else:
            require(
                summ.get('external_artifact_drop_validator_ready_for_controlled_ingestion') is False,
                'NOT_READY external artifact drop marked ready',
            )
            require(
                int(summ.get('external_artifact_drop_validator_missing_or_invalid_artifact_count', 0)) >= 1,
                'NOT_READY external artifact drop must retain missing artifacts',
            )
        require(
            summ.get('external_artifact_ingestion_plan_status')
            in {'PASS-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN', 'NOT_READY-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN'},
            'invalid external artifact ingestion plan status',
        )
        require(
            int(summ.get('external_artifact_ingestion_plan_total_copy_action_count', 0))
            == int(summ.get('external_artifact_drop_validator_total_expected_artifact_count', 0)),
            'external artifact ingestion plan count differs from drop validator',
        )
        require(
            summ.get('external_artifact_ingestion_plan_does_not_apply_copy_actions') is True,
            'external artifact ingestion plan must not apply copy actions',
        )
        require(
            summ.get('external_artifact_ingestion_plan_does_not_clear_blockers') is True,
            'external artifact ingestion plan must not clear blockers',
        )
        if summ.get('external_artifact_ingestion_plan_status') == 'PASS-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN':
            require(
                summ.get('external_artifact_ingestion_plan_ready_for_controlled_copy') is True,
                'PASS external artifact ingestion plan is not ready for controlled copy',
            )
            require(
                int(summ.get('external_artifact_ingestion_plan_missing_or_invalid_copy_action_count', -1)) == 0,
                'PASS external artifact ingestion plan still has invalid copy actions',
            )
        else:
            require(
                summ.get('external_artifact_ingestion_plan_ready_for_controlled_copy') is False,
                'NOT_READY external artifact ingestion plan marked ready',
            )
            require(
                int(summ.get('external_artifact_ingestion_plan_missing_or_invalid_copy_action_count', 0)) >= 1,
                'NOT_READY external artifact ingestion plan must retain invalid copy actions',
            )
        require(
            summ.get('external_artifact_controlled_copy_status')
            in {
                'NOT_READY-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY',
                'DRYRUN-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY',
                'PASS-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY',
            },
            'invalid external artifact controlled-copy status',
        )
        require(
            summ.get('external_artifact_controlled_copy_source_filesystem_gate_level')
            == EXPECTED_CONTROLLED_COPY_SOURCE_GATE_LEVEL,
            'external artifact controlled-copy source filesystem gate mismatch',
        )
        require(
            int(summ.get('external_artifact_controlled_copy_source_integrity_gap_count', 0)) >= 0,
            'external artifact controlled-copy source integrity gap count invalid',
        )
        require(
            int(summ.get('external_artifact_controlled_copy_total_copy_action_count', 0))
            == int(summ.get('external_artifact_ingestion_plan_total_copy_action_count', 0)),
            'external artifact controlled-copy count differs from ingestion plan',
        )
        require(
            summ.get('external_artifact_controlled_copy_does_not_clear_blockers') is True,
            'external artifact controlled-copy report must not clear blockers',
        )
        if summ.get('external_artifact_controlled_copy_status') == 'PASS-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY':
            require(
                summ.get('external_artifact_controlled_copy_apply_requested') is True,
                'PASS external artifact controlled-copy report did not request apply',
            )
            require(
                summ.get('external_artifact_controlled_copy_applied_copy_actions') is True,
                'PASS external artifact controlled-copy report did not apply copy actions',
            )
            require(
                summ.get('external_artifact_controlled_copy_ready_for_controlled_copy') is True,
                'PASS external artifact controlled-copy report is not ready',
            )
            require(
                int(summ.get('external_artifact_controlled_copy_source_integrity_gap_count', -1)) == 0,
                'PASS external artifact controlled-copy has source filesystem gaps',
            )
        else:
            require(
                summ.get('external_artifact_controlled_copy_apply_requested') is False,
                'non-PASS external artifact controlled-copy report requested apply',
            )
            require(
                summ.get('external_artifact_controlled_copy_applied_copy_actions') is False,
                'non-PASS external artifact controlled-copy report copied files',
            )
            require(
                int(summ.get('external_artifact_controlled_copy_copied_file_count', -1)) == 0,
                'non-PASS external artifact controlled-copy report copied files',
            )
        if summ.get('external_artifact_controlled_copy_status') == 'NOT_READY-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY':
            require(
                int(summ.get('external_artifact_controlled_copy_missing_or_invalid_copy_action_count', 0)) >= 1,
                'NOT_READY external artifact controlled-copy report must retain invalid actions',
            )
        if summ.get('external_artifact_controlled_copy_status') == 'DRYRUN-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY':
            require(
                summ.get('external_artifact_controlled_copy_ready_for_controlled_copy') is True,
                'DRYRUN external artifact controlled-copy report is not ready',
            )
            require(
                int(summ.get('external_artifact_controlled_copy_source_integrity_gap_count', -1)) == 0,
                'DRYRUN external artifact controlled-copy has source filesystem gaps',
            )
            require(
                int(summ.get('external_artifact_controlled_copy_missing_or_invalid_copy_action_count', -1)) == 0,
                'DRYRUN external artifact controlled-copy report has invalid actions',
            )
        require(
            summ.get('external_evidence_operations_dashboard_status')
            in {
                'PASS-H2-EXTERNAL-EVIDENCE-OPERATIONS-DASHBOARD',
                'NOT_READY-H2-EXTERNAL-EVIDENCE-OPERATIONS-DASHBOARD',
            },
            'invalid external evidence operations dashboard status',
        )
        require(
            int(summ.get('external_evidence_operations_dashboard_total_expected_artifact_count', 0))
            == int(summ.get('external_artifact_drop_validator_total_expected_artifact_count', 0)),
            'external evidence dashboard expected artifact count differs from drop validator',
        )
        require(
            int(summ.get('external_evidence_operations_dashboard_drop_valid_artifact_count', 0))
            == int(summ.get('external_artifact_drop_validator_valid_artifact_count', 0)),
            'external evidence dashboard valid artifact count differs from drop validator',
        )
        require(
            int(summ.get('external_evidence_operations_dashboard_missing_artifact_count', 0))
            == int(summ.get('production_blocker_data_room_missing_artifact_count', 0)),
            'external evidence dashboard missing artifact count differs from data-room',
        )
        require(
            int(summ.get('external_evidence_operations_dashboard_remaining_blocker_count', 0))
            == int(summ.get('blocker_clearance_preflight_remaining_count', 0)),
            'external evidence dashboard remaining blocker count differs from preflight',
        )
        require(
            int(summ.get('external_evidence_operations_dashboard_controlled_copy_copied_file_count', 0))
            == int(summ.get('external_artifact_controlled_copy_copied_file_count', 0)),
            'external evidence dashboard copied-file count differs from controlled-copy report',
        )
        require(
            summ.get('external_evidence_operations_dashboard_domain_count') == 3,
            'external evidence dashboard domain count mismatch',
        )
        require(
            int(summ.get('external_evidence_operations_dashboard_next_operator_command_count', 0)) >= 6,
            'external evidence dashboard command list incomplete',
        )
        require(
            summ.get('external_evidence_operations_dashboard_does_not_clear_blockers') is True,
            'external evidence dashboard must not clear blockers',
        )
        if summ.get('external_evidence_operations_dashboard_status') == 'PASS-H2-EXTERNAL-EVIDENCE-OPERATIONS-DASHBOARD':
            require(
                summ.get('external_evidence_operations_dashboard_ready_for_production_blocker_clearance') is True,
                'PASS external evidence dashboard is not ready for blocker clearance',
            )
            require(
                int(summ.get('external_evidence_operations_dashboard_remaining_blocker_count', -1)) == 0,
                'PASS external evidence dashboard still has blockers',
            )
        else:
            require(
                summ.get('external_evidence_operations_dashboard_ready_for_production_blocker_clearance') is False,
                'NOT_READY external evidence dashboard marked ready',
            )
            require(
                int(summ.get('external_evidence_operations_dashboard_remaining_blocker_count', 0)) >= 1,
                'NOT_READY external evidence dashboard must retain blockers',
            )
        require(
            summ.get('external_evidence_acceptance_worksheet_status')
            == 'PASS-H2-EXTERNAL-EVIDENCE-ACCEPTANCE-WORKSHEET',
            'external evidence acceptance worksheet did not PASS',
        )
        require(
            summ.get('external_evidence_acceptance_worksheet_does_not_clear_blockers') is True,
            'external evidence acceptance worksheet must not clear blockers',
        )
        require(
            summ.get('external_evidence_acceptance_worksheet_domain_count') == 3,
            'external evidence acceptance worksheet domain count mismatch',
        )
        require(
            int(summ.get('external_evidence_acceptance_worksheet_row_count', 0)) == 14,
            'external evidence acceptance worksheet row count mismatch',
        )
        require(
            int(summ.get('external_evidence_acceptance_worksheet_valid_artifact_row_count', -1))
            == int(summ.get('external_artifact_drop_validator_valid_artifact_count', -2)),
            'external evidence acceptance worksheet valid rows differ from drop validator',
        )
        require(
            int(summ.get('external_evidence_acceptance_worksheet_missing_or_invalid_artifact_row_count', -1))
            == int(summ.get('external_artifact_drop_validator_missing_or_invalid_artifact_count', -2)),
            'external evidence acceptance worksheet missing rows differ from drop validator',
        )
        require(
            summ.get('external_evidence_acceptance_worksheet_operator_receipt_status')
            == summ.get('external_artifact_operator_receipt_status'),
            'external evidence acceptance worksheet receipt status differs from operator receipt report',
        )
        if int(summ.get('external_artifact_drop_validator_missing_or_invalid_artifact_count', 0)) >= 1:
            require(
                summ.get('external_evidence_acceptance_worksheet_ready_for_external_evidence_acceptance') is False,
                'external evidence acceptance worksheet marked ready while artifacts are missing',
            )
        require(
            summ.get('external_artifact_mapping_alias_status')
            == 'PASS-H2-EXTERNAL-ARTIFACT-MAPPING-ALIAS',
            'external artifact mapping alias report did not PASS',
        )
        require(
            summ.get('external_artifact_mapping_alias_does_not_clear_blockers') is True,
            'external artifact mapping alias report must not clear blockers',
        )
        require(
            int(summ.get('external_artifact_mapping_alias_domain_count', 0)) == 3,
            'external artifact mapping alias domain count mismatch',
        )
        require(
            int(summ.get('external_artifact_mapping_alias_artifact_row_count', 0)) == 14,
            'external artifact mapping alias row count mismatch',
        )
        require(
            int(summ.get('external_artifact_mapping_alias_alias_group_count', 0)) == 1,
            'external artifact mapping alias allowed group count mismatch',
        )
        require(
            int(summ.get('external_artifact_mapping_alias_observed_allowed_alias_group_count', 0)) == 1,
            'external artifact mapping alias allowed group was not observed',
        )
        require(
            int(summ.get('external_artifact_mapping_alias_duplicate_target_group_count', 0)) == 1,
            'external artifact mapping alias duplicate target group count mismatch',
        )
        require(
            int(summ.get('external_artifact_mapping_alias_duplicate_drop_group_count', 0)) == 1,
            'external artifact mapping alias duplicate drop group count mismatch',
        )
        require(
            int(summ.get('external_artifact_mapping_alias_unexpected_duplicate_target_group_count', -1)) == 0,
            'external artifact mapping alias found unexpected target duplicates',
        )
        require(
            int(summ.get('external_artifact_mapping_alias_unexpected_duplicate_drop_group_count', -1)) == 0,
            'external artifact mapping alias found unexpected drop duplicates',
        )
        require(
            summ.get('external_evidence_case_validation_plan_status')
            == 'PASS-H2-EXTERNAL-EVIDENCE-CASE-VALIDATION-PLAN',
            'external evidence case validation plan did not PASS',
        )
        require(
            summ.get('external_evidence_case_validation_plan_does_not_clear_blockers') is True,
            'external evidence case validation plan must not clear blockers',
        )
        require(
            summ.get('external_evidence_case_validation_plan_domain_count') == 3,
            'external evidence case validation plan domain count mismatch',
        )
        require(
            int(summ.get('external_evidence_case_validation_plan_worksheet_row_count', 0))
            == int(summ.get('external_evidence_acceptance_worksheet_row_count', 0)),
            'external evidence case validation plan worksheet row count differs from worksheet',
        )
        require(
            int(summ.get('external_evidence_case_validation_plan_campaign_count', 0)) == 4,
            'external evidence case validation plan campaign count mismatch',
        )
        require(
            int(summ.get('external_evidence_case_validation_plan_acceptance_contract_metric_count', 0)) >= 35,
            'external evidence case validation plan acceptance contract metric count too small',
        )
        if int(summ.get('external_evidence_acceptance_worksheet_missing_or_invalid_artifact_row_count', 0)) >= 1:
            require(
                int(summ.get('external_evidence_case_validation_plan_ready_campaign_count', -1)) == 0,
                'external evidence case validation plan marked campaigns ready while artifacts are missing',
            )
            require(
                summ.get('external_evidence_case_validation_plan_integrated_replay_ready') is False,
                'external evidence case validation plan marked integrated replay ready while artifacts are missing',
            )
        require(
            summ.get('case_validation_acceptance_contract_status')
            == 'PASS-H2-CASE-VALIDATION-ACCEPTANCE-CONTRACT',
            'case validation acceptance contract did not PASS',
        )
        require(
            summ.get('case_validation_acceptance_contract_does_not_clear_blockers') is True,
            'case validation acceptance contract must not clear blockers',
        )
        require(
            int(summ.get('case_validation_acceptance_contract_campaign_count', 0)) == 4,
            'case validation acceptance contract campaign count mismatch',
        )
        require(
            int(summ.get('case_validation_acceptance_contract_metric_count', 0)) >= 35,
            'case validation acceptance contract metric count too small',
        )
        require(
            int(summ.get('case_validation_acceptance_contract_quantitative_metric_count', 0)) >= 12,
            'case validation acceptance contract quantitative metric count too small',
        )
        require(
            int(summ.get('case_validation_acceptance_contract_failed_campaign_count', -1)) == 0,
            'case validation acceptance contract has failed campaign contracts',
        )
        require(
            summ.get('case_validation_acceptance_contract_negative_missing_threshold_refused') is True,
            'case validation acceptance contract negative threshold selftest was not refused',
        )
        require(
            summ.get('case_validation_acceptance_evaluation_status')
            == 'NOT_READY-H2-CASE-VALIDATION-ACCEPTANCE-EVALUATION',
            'case validation acceptance evaluation should remain NOT_READY until real metrics pass',
        )
        require(
            summ.get('case_validation_acceptance_evaluation_does_not_clear_blockers') is True,
            'case validation acceptance evaluation must not clear blockers',
        )
        require(
            int(summ.get('case_validation_acceptance_evaluation_campaign_count', 0)) == 4,
            'case validation acceptance evaluation campaign count mismatch',
        )
        require(
            int(summ.get('case_validation_acceptance_evaluation_metric_count', 0)) >= 35,
            'case validation acceptance evaluation metric count too small',
        )
        require(
            int(summ.get('case_validation_acceptance_evaluation_ready_campaign_count', -1)) == 0,
            'case validation acceptance evaluation opened campaigns before real data passed',
        )
        require(
            int(summ.get('case_validation_acceptance_evaluation_failed_metric_count', 0)) >= 1,
            'case validation acceptance evaluation must retain failed metrics in current NOT_READY state',
        )
        require(
            int(summ.get('case_validation_acceptance_evaluation_deferred_metric_count', 0)) >= 1,
            'case validation acceptance evaluation must defer final verifier metrics to avoid a hash cycle',
        )
        require(
            summ.get('case_validation_acceptance_evaluation_ready_for_production_credit') is False,
            'case validation acceptance evaluation marked production credit ready too early',
        )
        require(
            summ.get('case_validation_acceptance_evaluation_comparator_selftest_passed') is True,
            'case validation acceptance evaluation comparator selftest did not pass',
        )
        require(
            summ.get('case_validation_failure_attribution_status')
            == 'PASS-H2-CASE-VALIDATION-FAILURE-ATTRIBUTION',
            'case validation failure attribution did not PASS',
        )
        require(
            summ.get('case_validation_failure_attribution_does_not_clear_blockers') is True,
            'case validation failure attribution must not clear blockers',
        )
        require(
            int(summ.get('case_validation_failure_attribution_failed_metric_count', -1))
            == int(summ.get('case_validation_acceptance_evaluation_failed_metric_count', -2)),
            'failure attribution failed metric count differs from evaluation',
        )
        require(
            int(summ.get('case_validation_failure_attribution_deferred_metric_count', -1))
            == int(summ.get('case_validation_acceptance_evaluation_deferred_metric_count', -2)),
            'failure attribution deferred metric count differs from evaluation',
        )
        require(
            int(summ.get('case_validation_failure_attribution_unattributed_problem_metric_count', -1)) == 0,
            'failure attribution left unattributed problem metrics',
        )
        require(
            int(summ.get('case_validation_failure_attribution_action_group_count', 0)) >= 1,
            'failure attribution action groups missing',
        )
        require(
            int(summ.get('case_validation_failure_attribution_missing_or_invalid_artifact_row_count', 0)) >= 1,
            'failure attribution must retain missing artifact rows in current NOT_READY state',
        )
        require(
            summ.get('case_validation_closure_matrix_status') == 'PASS-H2-CASE-VALIDATION-CLOSURE-MATRIX',
            'case validation closure matrix did not PASS',
        )
        require(
            summ.get('case_validation_closure_matrix_does_not_clear_blockers') is True,
            'case validation closure matrix must not clear blockers',
        )
        require(
            int(summ.get('case_validation_closure_matrix_artifact_row_count', -1)) == 14,
            'case validation closure matrix artifact row count mismatch',
        )
        require(
            int(summ.get('case_validation_closure_matrix_problem_metric_count', -1))
            == int(summ.get('case_validation_failure_attribution_attributed_problem_metric_count', -2)),
            'case validation closure matrix problem metric count differs from attribution',
        )
        require(
            int(summ.get('case_validation_closure_matrix_mapped_problem_metric_count', -1))
            == int(summ.get('case_validation_closure_matrix_problem_metric_count', -2)),
            'case validation closure matrix did not map all problem metrics',
        )
        require(
            int(summ.get('case_validation_closure_matrix_unmapped_problem_metric_count', -1)) == 0,
            'case validation closure matrix left unmapped problem metrics',
        )
        require(
            int(summ.get('case_validation_closure_matrix_artifact_rows_without_metric_context_count', -1)) == 0,
            'case validation closure matrix left artifacts without metric context',
        )
        require(
            int(summ.get('case_validation_closure_matrix_missing_or_invalid_artifact_row_count', 0)) >= 1,
            'closure matrix must retain missing artifact rows in current NOT_READY state',
        )
        require(
            summ.get('external_artifact_unlock_forecast_status')
            == 'PASS-H2-EXTERNAL-ARTIFACT-UNLOCK-FORECAST',
            'external artifact unlock forecast did not PASS',
        )
        require(
            summ.get('external_artifact_unlock_forecast_does_not_clear_blockers') is True,
            'external artifact unlock forecast must not clear blockers',
        )
        require(
            int(summ.get('external_artifact_unlock_forecast_unresolved_blocker_count', -1)) == 3,
            'external artifact unlock forecast blocker count mismatch',
        )
        require(
            int(summ.get('external_artifact_unlock_forecast_unmapped_blocker_count', -1)) == 0,
            'external artifact unlock forecast left unmapped blockers',
        )
        require(
            int(summ.get('external_artifact_unlock_forecast_domain_unlock_count', -1)) == 3,
            'external artifact unlock forecast domain count mismatch',
        )
        require(
            int(summ.get('external_artifact_unlock_forecast_artifact_unlock_requirement_count', -1)) == 14,
            'external artifact unlock forecast artifact count mismatch',
        )
        require(
            int(summ.get('external_artifact_unlock_forecast_missing_or_invalid_artifact_count', 0)) >= 1,
            'external artifact unlock forecast must retain missing artifacts in current NOT_READY state',
        )
        require(
            int(summ.get('external_artifact_unlock_forecast_problem_metric_count', -1))
            == int(summ.get('case_validation_closure_matrix_problem_metric_count', -2)),
            'external artifact unlock forecast problem metric count differs from closure matrix',
        )
        require(
            int(summ.get('external_artifact_unlock_forecast_mapped_problem_metric_count', -1))
            == int(summ.get('external_artifact_unlock_forecast_problem_metric_count', -2)),
            'external artifact unlock forecast did not map all problem metrics',
        )
        require(
            summ.get('external_artifact_unlock_forecast_ready_for_production_blocker_clearance') is False,
            'external artifact unlock forecast marked blocker clearance ready too early',
        )
        require(
            summ.get('external_evidence_case_validation_plan_selftest_status')
            == 'PASS-H2-EXTERNAL-EVIDENCE-CASE-VALIDATION-PLAN-SELFTEST',
            'external evidence case validation plan selftest did not PASS',
        )
        require(
            summ.get('external_evidence_case_validation_plan_selftest_only') is True,
            'external evidence case validation plan selftest must be selftest-only',
        )
        require(
            summ.get('external_evidence_case_validation_plan_selftest_does_not_clear_blockers') is True,
            'external evidence case validation plan selftest must not clear blockers',
        )
        require(
            int(summ.get('external_evidence_case_validation_plan_selftest_negative_ready_campaign_count', -1)) == 0,
            'case validation plan negative selftest opened campaigns',
        )
        require(
            summ.get('external_evidence_case_validation_plan_selftest_negative_integrated_replay_ready') is False,
            'case validation plan negative selftest opened integrated replay',
        )
        require(
            int(summ.get('external_evidence_case_validation_plan_selftest_positive_ready_campaign_count', -1)) == 4,
            'case validation plan positive selftest did not open all campaigns',
        )
        require(
            summ.get('external_evidence_case_validation_plan_selftest_positive_integrated_replay_ready') is True,
            'case validation plan positive selftest did not open integrated replay',
        )
        require(
            summ.get('case_validation_runner_ledger_status')
            in {
                'DRYRUN-H2-CASE-VALIDATION-RUNNER-LEDGER',
                'REFUSED-H2-CASE-VALIDATION-RUNNER-LEDGER',
                'PASS-H2-CASE-VALIDATION-RUNNER-LEDGER',
                'FAIL-H2-CASE-VALIDATION-RUNNER-LEDGER',
            },
            'case validation runner ledger status mismatch',
        )
        require(
            summ.get('case_validation_runner_ledger_does_not_clear_blockers') is True,
            'case validation runner ledger must not clear blockers',
        )
        if summ.get('case_validation_runner_ledger_status') == 'DRYRUN-H2-CASE-VALIDATION-RUNNER-LEDGER':
            require(
                summ.get('case_validation_runner_ledger_execute_requested') is False,
                'DRYRUN runner ledger requested execution',
            )
            require(
                int(summ.get('case_validation_runner_ledger_selected_campaign_count', 0)) == 4,
                'DRYRUN runner ledger campaign count mismatch',
            )
            require(
                int(summ.get('case_validation_runner_ledger_selected_blocked_campaign_count', 0)) == 4,
                'DRYRUN runner ledger blocked campaign count mismatch',
            )
            require(
                int(summ.get('case_validation_runner_ledger_command_result_count', -1)) == 0,
                'DRYRUN runner ledger recorded command results',
            )
        elif summ.get('case_validation_runner_ledger_status') == 'PASS-H2-CASE-VALIDATION-RUNNER-LEDGER':
            require(
                summ.get('case_validation_runner_ledger_execute_requested') is True,
                'PASS runner ledger did not request execution',
            )
            require(
                int(summ.get('case_validation_runner_ledger_selected_blocked_campaign_count', -1)) == 0,
                'PASS runner ledger has blocked campaigns',
            )
            require(
                int(summ.get('case_validation_runner_ledger_unresolved_command_count', -1)) == 0,
                'PASS runner ledger has unresolved commands',
            )
            require(
                int(summ.get('case_validation_runner_ledger_command_result_count', 0)) >= 1,
                'PASS runner ledger has no command results',
            )
        require(
            summ.get('case_validation_runner_ledger_selftest_status')
            == 'PASS-H2-CASE-VALIDATION-RUNNER-LEDGER-SELFTEST',
            'case validation runner ledger selftest did not PASS',
        )
        require(
            summ.get('case_validation_runner_ledger_selftest_only') is True,
            'case validation runner ledger selftest must be selftest-only',
        )
        require(
            summ.get('case_validation_runner_ledger_selftest_does_not_clear_blockers') is True,
            'case validation runner ledger selftest must not clear blockers',
        )
        require(
            int(summ.get('case_validation_runner_ledger_selftest_positive_verify_returncode', -1)) == 0,
            'case validation runner ledger positive selftest failed',
        )
        require(
            int(summ.get('case_validation_runner_ledger_selftest_negative_case_count', 0)) == 4,
            'case validation runner ledger negative case count mismatch',
        )
        require(
            int(summ.get('case_validation_runner_ledger_selftest_negative_refused_count', 0)) == 4,
            'case validation runner ledger negative fixtures were not all refused',
        )
        require(
            summ.get('case_validation_runner_preflight_status') == 'PASS-H2-CASE-VALIDATION-RUNNER-PREFLIGHT',
            'case validation runner preflight did not PASS',
        )
        require(
            summ.get('case_validation_runner_preflight_does_not_clear_blockers') is True,
            'case validation runner preflight must not clear blockers',
        )
        require(
            int(summ.get('case_validation_runner_preflight_dryrun_returncode', -1)) == 0,
            'case validation runner dry-run failed',
        )
        require(
            int(summ.get('case_validation_runner_preflight_selected_campaign_count', 0)) == 4,
            'case validation runner campaign count mismatch',
        )
        require(
            int(summ.get('case_validation_runner_preflight_selected_ready_campaign_count', -1)) == 0,
            'case validation runner marked campaigns ready while artifacts are missing',
        )
        require(
            int(summ.get('case_validation_runner_preflight_selected_blocked_campaign_count', 0)) == 4,
            'case validation runner blocked campaign count mismatch',
        )
        require(
            summ.get('case_validation_runner_preflight_execute_refused') is True,
            'case validation runner execute was not refused while campaigns are blocked',
        )
        require(
            summ.get('case_validation_runner_preflight_refusal_ledger_status')
            == 'REFUSED-H2-CASE-VALIDATION-RUNNER-LEDGER',
            'case validation runner refusal ledger status mismatch',
        )
        require(
            summ.get('case_validation_runner_preflight_refusal_ledger_written') is True,
            'case validation runner refusal ledger was not written',
        )
        require(
            int(summ.get('case_validation_runner_preflight_refusal_ledger_command_result_count', -1)) == 0,
            'case validation runner refusal ledger recorded executed commands',
        )
        require(
            int(summ.get('case_validation_runner_preflight_unresolved_command_count', 0)) >= 1,
            'case validation runner did not preserve unresolved placeholder guard',
        )
        require(
            summ.get('case_validation_runner_preflight_positive_placeholder_all_resolved') is True,
            'case validation runner positive placeholder selftest did not resolve all placeholders',
        )
        require(
            int(summ.get('case_validation_runner_preflight_positive_placeholder_resolved_count', 0)) == 2,
            'case validation runner positive placeholder resolved count mismatch',
        )
        require(
            int(summ.get('case_validation_runner_preflight_positive_placeholder_unresolved_command_count', -1)) == 0,
            'case validation runner positive placeholder selftest left unresolved commands',
        )
        require(
            summ.get('case_validation_command_contract_status') == 'PASS-H2-CASE-VALIDATION-COMMAND-CONTRACT',
            'case validation command contract did not PASS',
        )
        require(
            summ.get('case_validation_command_contract_does_not_clear_blockers') is True,
            'case validation command contract must not clear blockers',
        )
        require(
            int(summ.get('case_validation_command_contract_command_count', 0)) == 17,
            'case validation command contract command count mismatch',
        )
        require(
            int(summ.get('case_validation_command_contract_python_command_count', 0)) == 12,
            'case validation command contract python command count mismatch',
        )
        require(
            int(summ.get('case_validation_command_contract_bash_command_count', 0)) == 5,
            'case validation command contract bash command count mismatch',
        )
        require(
            int(summ.get('case_validation_command_contract_placeholder_command_count', 0)) == 2,
            'case validation command contract placeholder command count mismatch',
        )
        require(
            int(summ.get('case_validation_command_contract_option_check_count', 0)) >= 4,
            'case validation command contract option checks too few',
        )
        require(
            int(summ.get('case_validation_command_contract_failed_command_count', -1)) == 0,
            'case validation command contract has failed commands',
        )
        require(
            int(summ.get('case_validation_command_contract_missing_or_unsupported_contract_count', -1)) == 0,
            'case validation command contract has missing or unsupported contracts',
        )
        require(
            summ.get('case_validation_command_contract_selftest_status')
            == 'PASS-H2-CASE-VALIDATION-COMMAND-CONTRACT-SELFTEST',
            'case validation command contract selftest did not PASS',
        )
        require(
            summ.get('case_validation_command_contract_selftest_only') is True,
            'case validation command contract selftest must be selftest-only',
        )
        require(
            summ.get('case_validation_command_contract_selftest_does_not_clear_blockers') is True,
            'case validation command contract selftest must not clear blockers',
        )
        require(
            int(summ.get('case_validation_command_contract_selftest_positive_verify_returncode', -1)) == 0,
            'case validation command contract selftest positive verify failed',
        )
        require(
            int(summ.get('case_validation_command_contract_selftest_negative_case_count', 0)) == 2,
            'case validation command contract selftest negative case count mismatch',
        )
        require(
            int(summ.get('case_validation_command_contract_selftest_negative_refused_count', 0)) == 2,
            'case validation command contract selftest did not refuse all negative cases',
        )
        require(
            summ.get('case_validation_command_contract_selftest_missing_script_refused') is True,
            'case validation command contract selftest did not refuse missing script',
        )
        require(
            summ.get('case_validation_command_contract_selftest_unsupported_option_refused') is True,
            'case validation command contract selftest did not refuse unsupported option',
        )
        require(
            summ.get('quality_review_coverage_status') == 'PASS-H2-QUALITY-REVIEW-COVERAGE',
            'quality review coverage did not PASS',
        )
        require(
            summ.get('quality_review_coverage_does_not_clear_blockers') is True,
            'quality review coverage must not clear blockers',
        )
        require(
            int(summ.get('quality_review_coverage_type_a_expected_module_count', 0)) >= 8,
            'quality review coverage Type A module count too small',
        )
        require(
            int(summ.get('quality_review_coverage_type_b_expected_phase_count', 0)) >= 4,
            'quality review coverage Type B phase count too small',
        )
        require(
            int(summ.get('quality_review_coverage_missing_audit_record_count', -1)) >= 0,
            'quality review coverage missing audit count invalid',
        )
        require(
            int(summ.get('quality_review_coverage_formal_independent_review_missing_count', 0)) >= 1,
            'quality review coverage did not retain formal review gap',
        )
        require(
            summ.get('quality_review_coverage_ready_for_qlt01_credit') is False,
            'quality review coverage incorrectly marked QLT-01 ready',
        )
        require(
            summ.get('quality_review_coverage_ready_for_qlt02_credit') is False,
            'quality review coverage incorrectly marked QLT-02 ready',
        )
        require(
            summ.get('external_artifact_gate_selftest_status')
            == 'PASS-H2-EXTERNAL-ARTIFACT-GATE-SELFTEST',
            'external artifact gate selftest did not PASS',
        )
        require(
            summ.get('external_artifact_gate_selftest_synthetic_only') is True,
            'external artifact gate selftest must be marked synthetic-only',
        )
        require(
            summ.get('external_artifact_gate_selftest_does_not_clear_blockers') is True,
            'external artifact gate selftest must not clear blockers',
        )
        require(
            int(summ.get('external_artifact_gate_selftest_drop_valid_artifact_count', 0)) == 14,
            'external artifact gate selftest drop count mismatch',
        )
        require(
            int(summ.get('external_artifact_gate_selftest_drop_total_expected_artifact_count', 0)) == 14,
            'external artifact gate selftest expected count mismatch',
        )
        require(
            int(summ.get('external_artifact_gate_selftest_ingestion_ready_copy_action_count', 0)) == 14,
            'external artifact gate selftest ingestion count mismatch',
        )
        require(
            int(summ.get('external_artifact_gate_selftest_dryrun_copied_file_count', -1)) == 0,
            'external artifact gate selftest dryrun copied files',
        )
        require(
            int(summ.get('external_artifact_gate_selftest_apply_copied_file_count', 0)) >= 14,
            'external artifact gate selftest apply copied too few files',
        )
        require(
            summ.get('external_artifact_gate_selftest_targets_isolated') is True,
            'external artifact gate selftest targets are not isolated',
        )
        require(
            summ.get('external_artifact_gate_negative_selftest_status')
            == 'PASS-H2-EXTERNAL-ARTIFACT-GATE-NEGATIVE-SELFTEST',
            'external artifact gate negative selftest did not PASS',
        )
        require(
            summ.get('external_artifact_gate_negative_selftest_only') is True,
            'external artifact gate negative selftest must be marked selftest-only',
        )
        require(
            summ.get('external_artifact_gate_negative_selftest_does_not_clear_blockers') is True,
            'external artifact gate negative selftest must not clear blockers',
        )
        require(
            summ.get('external_artifact_gate_negative_selftest_drop_status')
            == 'NOT_READY-H2-EXTERNAL-ARTIFACT-DROP',
            'negative selftest drop unexpectedly ready',
        )
        require(
            int(summ.get('external_artifact_gate_negative_selftest_drop_valid_artifact_count', 14)) < 14,
            'negative selftest drop validated all artifacts',
        )
        require(
            summ.get('external_artifact_gate_negative_selftest_ingestion_status')
            == 'NOT_READY-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN',
            'negative selftest ingestion unexpectedly ready',
        )
        require(
            summ.get('external_artifact_gate_negative_selftest_controlled_copy_status')
            == 'NOT_READY-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY',
            'negative selftest controlled-copy unexpectedly ready',
        )
        require(
            int(summ.get('external_artifact_gate_negative_selftest_controlled_copy_copied_file_count', -1)) == 0,
            'negative selftest controlled-copy copied files',
        )
        require(
            int(summ.get('external_artifact_gate_negative_selftest_apply_refused_returncode', 0)) != 0,
            'negative selftest apply was not refused',
        )
        require(
            summ.get('external_artifact_strict_qa_negative_selftest_status')
            == 'PASS-H2-EXTERNAL-ARTIFACT-STRICT-QA-NEGATIVE-SELFTEST',
            'external artifact strict-QA negative selftest did not PASS',
        )
        require(
            summ.get('external_artifact_strict_qa_negative_selftest_only') is True,
            'strict-QA negative selftest must be marked selftest-only',
        )
        require(
            summ.get('external_artifact_strict_qa_negative_selftest_all_present') is True,
            'strict-QA negative selftest must use an all-present fixture',
        )
        require(
            summ.get('external_artifact_strict_qa_negative_selftest_does_not_clear_blockers') is True,
            'strict-QA negative selftest must not clear blockers',
        )
        require(
            summ.get('external_artifact_strict_qa_negative_selftest_drop_status')
            == 'NOT_READY-H2-EXTERNAL-ARTIFACT-DROP',
            'strict-QA bad complete drop unexpectedly ready',
        )
        require(
            summ.get('external_artifact_strict_qa_negative_selftest_drop_content_quality_gate_level')
            == EXPECTED_EXTERNAL_ARTIFACT_GATE_LEVEL,
            'strict-QA negative selftest did not exercise strict-v5-placeholder-free',
        )
        require(
            summ.get('external_artifact_strict_qa_negative_selftest_drop_placeholder_gap_detected') is True,
            'strict-QA negative selftest did not detect placeholder/template markers',
        )
        require(
            int(summ.get('external_artifact_strict_qa_negative_selftest_drop_domain_quality_gap_count', 0)) >= 1,
            'strict-QA negative selftest did not detect domain quality gaps',
        )
        require(
            int(summ.get('external_artifact_strict_qa_negative_selftest_drop_present_artifact_count', -1)) == 14,
            'strict-QA negative selftest did not present all artifacts',
        )
        require(
            int(summ.get('external_artifact_strict_qa_negative_selftest_drop_valid_artifact_count', 14)) < 14,
            'strict-QA negative selftest validated all artifacts',
        )
        require(
            int(summ.get('external_artifact_strict_qa_negative_selftest_controlled_copy_copied_file_count', -1)) == 0,
            'strict-QA negative selftest controlled-copy copied files',
        )
        require(
            int(summ.get('external_artifact_strict_qa_negative_selftest_apply_refused_returncode', 0)) != 0,
            'strict-QA negative selftest apply was not refused',
        )
        require(
            summ.get('synthetic_selftest_isolation_guard_status')
            == 'PASS-H2-SYNTHETIC-SELFTEST-ISOLATION-GUARD',
            'synthetic selftest isolation guard did not PASS',
        )
        require(
            summ.get('synthetic_selftest_isolation_guard_synthetic_only') is True,
            'synthetic selftest isolation guard must mark selftest as synthetic',
        )
        require(
            summ.get('synthetic_selftest_isolation_guard_does_not_clear_blockers') is True,
            'synthetic selftest isolation guard must not clear blockers',
        )
        require(
            int(summ.get('synthetic_selftest_isolation_guard_scanned_report_count', 0)) >= 8,
            'synthetic selftest isolation guard scanned too few reports',
        )
        require(
            int(summ.get('synthetic_selftest_isolation_guard_forbidden_hit_count', -1)) == 0,
            'synthetic selftest isolation guard found forbidden production references',
        )
        if int(summ.get('synthetic_selftest_isolation_guard_remaining_blocker_count', 0)) >= 1:
            require(
                int(summ.get('synthetic_selftest_isolation_guard_real_controlled_copy_copied_file_count', -1)) == 0,
                'synthetic selftest isolation guard found real controlled-copy files copied while blockers remain',
            )
    require(
        summ.get('sbepv5_dataset_ingestion_status')
        in {'PASS-SBEPV5-D27-DATASET-INGESTION', 'NOT_READY-SBEPV5-D27-DATASET-INGESTION'},
        'invalid SBEPV5 dataset ingestion status',
    )
    require(int(summ.get('sbepv5_dataset_ingestion_schema_version', 0)) >= 2, 'SBEPV5 ingestion schema too old')
    require(
        summ.get('sbepv5_dataset_ingestion_content_quality_gate_level')
        == 'strict-v1-placeholder-free-and-non-synthetic',
        'SBEPV5 ingestion content quality gate mismatch',
    )
    require(
        summ.get('sbepv5_dataset_ingestion_selftest_status')
        == 'PASS-SBEPV5-D27-DATASET-INGESTION-SELFTEST',
        'SBEPV5 ingestion selftest did not PASS',
    )
    require(
        int(summ.get('sbepv5_dataset_ingestion_selftest_positive_case_count', 0)) == 2,
        'SBEPV5 ingestion selftest positive case count mismatch',
    )
    require(
        int(summ.get('sbepv5_dataset_ingestion_selftest_positive_passed_count', 0)) == 2,
        'SBEPV5 ingestion selftest positive fixtures did not pass',
    )
    require(
        int(summ.get('sbepv5_dataset_ingestion_selftest_negative_case_count', 0)) == 1,
        'SBEPV5 ingestion selftest negative case count mismatch',
    )
    require(
        int(summ.get('sbepv5_dataset_ingestion_selftest_negative_refused_count', 0)) == 1,
        'SBEPV5 ingestion selftest negative fixture was not refused',
    )
    require(
        summ.get('sbepv5_dataset_ingestion_selftest_numeric_sensor_id_fixture_passed') is True,
        'SBEPV5 ingestion selftest did not accept numeric sensor IDs',
    )
    require(
        summ.get('sbepv5_dataset_ingestion_selftest_gas_sensor_id_fixture_passed') is True,
        'SBEPV5 ingestion selftest did not accept Gas-label sensor IDs',
    )
    require(
        summ.get('sbepv5_digitization_preflight_status') == 'PASS-SBEPV5-D27-DIGITIZATION-PREFLIGHT',
        'SBEPV5 digitization preflight did not PASS',
    )
    require(
        summ.get('sbepv5_digitization_templates_available') is True,
        'SBEPV5 digitization templates missing',
    )
    require(
        summ.get('sbepv5_literature_metric_preflight_status')
        == 'PASS-SBEPV5-D27-LITERATURE-METRIC-PREFLIGHT',
        'SBEPV5 literature metric preflight did not PASS',
    )
    require(
        summ.get('sbepv5_literature_metric_anchor_available') is True,
        'SBEPV5 literature metric anchors missing',
    )
    require(
        int(summ.get('sbepv5_literature_metric_anchor_count', 0)) >= 4,
        'SBEPV5 literature metric anchor count too small',
    )
    require(
        summ.get('sbepv5_literature_ready_for_reference_agreement_consumption') is False,
        'SBEPV5 literature metric preflight cannot be reference-agreement ready before data ingestion',
    )
    require(
        int(summ.get('sbepv5_literature_metric_missing_artifact_count', 0)) >= 1,
        'SBEPV5 literature metric preflight must retain missing artifacts',
    )
    if summ.get('sbepv5_dataset_ingestion_status') == 'PASS-SBEPV5-D27-DATASET-INGESTION':
        for key in (
            'sbepv5_dataset_metadata_available',
            'sbepv5_exact_sensor_coordinates_available',
            'sbepv5_exact_baffle_geometry_available',
            'sbepv5_experimental_timeseries_available',
        ):
            require(summ.get(key) is True, f'SBEPV5 PASS missing {key}')
    else:
        require(summ.get('sbepv5_dataset_metadata_available') is False, 'SBEPV5 NOT_READY has metadata marked available')
        require(
            int(summ.get('sbepv5_digitization_missing_artifact_count', 0)) >= 1,
            'SBEPV5 NOT_READY must retain missing digitization artifacts',
        )
    require(
        summ.get('sbepv5_external_dataset_status')
        in {'PASS-SBEPV5-D27-EXTERNAL-PLUME-DATASET', 'NOT_READY-SBEPV5-D27-EXTERNAL-PLUME-DATASET'},
        'invalid SBEPV5 external dataset status',
    )
    if summ.get('sbepv5_external_dataset_status') == 'PASS-SBEPV5-D27-EXTERNAL-PLUME-DATASET':
        require(summ.get('sbepv5_external_dataset_written') is True, 'SBEPV5 external dataset PASS wrote no JSON')
    else:
        require(summ.get('sbepv5_external_dataset_written') is False, 'SBEPV5 external dataset NOT_READY wrote JSON')
    require(
        summ.get('sbepv5_case_package_status') == 'PASS-SBEPV5-D27-CASE-PACKAGE-SCAFFOLD',
        'SBEPV5 case package scaffold did not PASS',
    )
    require(summ.get('sbepv5_case_package_runnable') is False, 'SBEPV5 case package cannot be runnable before data ingestion')
    require(
        summ.get('sbepv5_case_package_preflight_status') == 'PASS-SBEPV5-D27-CASE-PACKAGE-PREFLIGHT',
        'SBEPV5 case package preflight did not PASS',
    )
    require(
        summ.get('academic_gas_detonation_readiness_status')
        in {
            'PASS-ACADEMIC-GAS-DETONATION-READINESS',
            'PARTIAL-ACADEMIC-GAS-DETONATION-READINESS',
            'NOT_READY-ACADEMIC-GAS-DETONATION-READINESS',
        },
        'invalid academic gas detonation readiness status',
    )
    if summ.get('academic_gas_detonation_readiness_status') == 'PASS-ACADEMIC-GAS-DETONATION-READINESS':
        require(summ.get('academic_gas_foundation_ready') is True, 'academic gas PASS requires foundation readiness')
        require(summ.get('academic_gas_clears_acd_02') is True, 'academic gas PASS must clear ACD-02')
        require(summ.get('academic_gas_clears_acd_03') is True, 'academic gas PASS must clear ACD-03')
        require(
            int(summ.get('academic_gas_missing_or_partial_quality_gate_count', -1)) == 0,
            'academic gas PASS must have no missing/partial gates',
        )
    elif summ.get('academic_gas_detonation_readiness_status') == 'PARTIAL-ACADEMIC-GAS-DETONATION-READINESS':
        require(summ.get('academic_gas_clears_acd_02') is False, 'academic gas PARTIAL cannot clear ACD-02')
        require(summ.get('academic_gas_clears_acd_03') is False, 'academic gas PARTIAL cannot clear ACD-03')
        require(summ.get('academic_gas_foundation_ready') is True, 'academic gas PARTIAL requires foundation readiness')
        require(
            int(summ.get('academic_gas_missing_or_partial_quality_gate_count', 0)) >= 1,
            'academic gas PARTIAL must retain missing/partial gates',
        )
    else:
        require(summ.get('academic_gas_clears_acd_02') is False, 'academic gas NOT_READY cannot clear ACD-02')
        require(summ.get('academic_gas_clears_acd_03') is False, 'academic gas NOT_READY cannot clear ACD-03')
        require(summ.get('academic_gas_foundation_ready') is False, 'academic gas NOT_READY should not be foundation ready')
        require(
            int(summ.get('academic_gas_missing_or_partial_quality_gate_count', 0)) >= 1,
            'academic gas NOT_READY must retain missing/partial gates',
        )
    require(summ.get('mpi_scaling') == 'PASS-SCALING-SCOUT', 'MPI scaling did not PASS')
    require(summ.get('mpi_link_shim_pass') is True, 'MPI link shim did not PASS')
    require(summ.get('path_audit_pass') is True, 'path audit did not PASS')
    if criteria.get('require_ctest', True):
        require(summ.get('ctest_passed') is True, 'CTest did not PASS')
        require(int(summ.get('ctest_tests', 0)) == int(criteria.get('expected_ctest_tests', 22)), 'CTest count mismatch')
    if data.get('status') == 'PASS':
        require(data.get('returncode') in {0, None}, f'unexpected returncode for PASS: {data.get("returncode")}')
    entries = data.get('evidence_files')
    require(isinstance(entries, list) and entries, 'evidence_files missing')
    if check_hashes:
        for item in entries:
            require(isinstance(item, dict), 'evidence entry is not an object')
            p = Path(str(item.get('path', '')))
            require(p.is_file(), f'missing evidence file: {p}')
            require(sha256_file(p) == item.get('sha256'), f'evidence sha256 mismatch: {p}')


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        '# Engineering H2 Production Evidence Verification',
        '',
        f"Status: `{report['status']}`",
        f"Command: `{report['command']}`",
        f"Log: `{report['log']}` sha256 `{report['log_sha256'][:16]}`",
        '',
        '## Summary',
        '',
    ]
    for key, value in report['summary'].items():
        lines.append(f'- `{key}`: `{value}`')
    lines += [
        '',
        '## Evidence Files',
        '',
    ]
    for item in report['evidence_files']:
        lines.append(f"- `{item['label']}`: `{item['path']}` sha256 `{item['sha256'][:16]}`")
    lines += [
        '',
        '## Limitations',
        '',
    ]
    for item in report['limitations']:
        lines.append(f'- {item}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def verify_report(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_report_object(data, check_hashes=True)
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--log', default=str(DEFAULT_LOG))
    ap.add_argument('--scorecard', default=str(DEFAULT_SCORECARD))
    ap.add_argument('--hybrid-cfd-scout', default=str(DEFAULT_HYBRID_CFD_SCOUT))
    ap.add_argument('--hybrid-production-mesh-scout', default=str(DEFAULT_HYBRID_PRODUCTION_MESH_SCOUT))
    ap.add_argument(
        '--hybrid-production-mesh-8rank-scout',
        default=str(DEFAULT_HYBRID_PRODUCTION_MESH_8RANK_SCOUT),
    )
    ap.add_argument(
        '--hybrid-production-mesh-8rank-600step-stability-scout',
        default=str(DEFAULT_HYBRID_PRODUCTION_MESH_8RANK_600STEP_SCOUT),
    )
    ap.add_argument(
        '--hybrid-production-mesh-600step-stability-scout',
        default=str(DEFAULT_HYBRID_PRODUCTION_MESH_600STEP_SCOUT),
    )
    ap.add_argument(
        '--hybrid-largegrid-8rank-120step-scout',
        default=str(DEFAULT_HYBRID_LARGEGRID_8RANK_120STEP_SCOUT),
    )
    ap.add_argument('--reference-agreement', default=str(DEFAULT_REFERENCE_AGREEMENT))
    ap.add_argument('--bfs-kepsilon-reference', default=str(DEFAULT_BFS_KEPSILON_REFERENCE))
    ap.add_argument('--mpi-link-shim-script', default=str(DEFAULT_MPI_LINK_SHIM))
    ap.add_argument('--mpi-scaling', default=str(DEFAULT_MPI_SCALING))
    ap.add_argument('--hybrid-affinity', default=str(DEFAULT_HYBRID_AFFINITY))
    ap.add_argument('--scheduler', default=str(DEFAULT_SCHEDULER))
    ap.add_argument('--real-cad-cleanup-package-report', default=str(DEFAULT_REAL_CAD_CLEANUP_PACKAGE))
    ap.add_argument('--real-cad-intake-preflight-report', default=str(DEFAULT_REAL_CAD_INTAKE_PREFLIGHT))
    ap.add_argument('--real-cad-boundary-tag-contract-report', default=str(DEFAULT_REAL_CAD_BOUNDARY_TAG_CONTRACT))
    ap.add_argument('--fire-calibration-package-report', default=str(DEFAULT_FIRE_CALIBRATION_PACKAGE))
    ap.add_argument(
        '--fire-calibration-public-source-triage-report',
        default=str(DEFAULT_FIRE_CALIBRATION_PUBLIC_SOURCE_TRIAGE),
    )
    ap.add_argument(
        '--fire-calibration-digitization-preflight-report',
        default=str(DEFAULT_FIRE_CALIBRATION_DIGITIZATION_PREFLIGHT),
    )
    ap.add_argument(
        '--fire-calibration-literature-metric-preflight-report',
        default=str(DEFAULT_FIRE_CALIBRATION_LITERATURE_METRIC_PREFLIGHT),
    )
    ap.add_argument('--external-plume-readiness-report', default=str(DEFAULT_EXTERNAL_PLUME_READINESS))
    ap.add_argument(
        '--external-plume-public-source-triage-report',
        default=str(DEFAULT_EXTERNAL_PLUME_PUBLIC_SOURCE_TRIAGE),
    )
    ap.add_argument('--blocker-clearance-preflight-report', default=str(DEFAULT_BLOCKER_CLEARANCE_PREFLIGHT))
    ap.add_argument('--production-blocker-data-room-report', default=str(DEFAULT_PRODUCTION_BLOCKER_DATA_ROOM))
    ap.add_argument('--production-blocker-closure-manifest-report', default=str(DEFAULT_PRODUCTION_BLOCKER_CLOSURE_MANIFEST))
    ap.add_argument('--external-evidence-intake-kit-report', default=str(DEFAULT_EXTERNAL_EVIDENCE_INTAKE_KIT))
    ap.add_argument('--external-artifact-operator-receipt-report', default=str(DEFAULT_EXTERNAL_ARTIFACT_OPERATOR_RECEIPT))
    ap.add_argument(
        '--external-artifact-operator-receipt-gate-selftest-report',
        default=str(DEFAULT_EXTERNAL_ARTIFACT_OPERATOR_RECEIPT_GATE_SELFTEST),
    )
    ap.add_argument('--evidence-chain-rebuild-manifest-report', default=str(DEFAULT_EVIDENCE_CHAIN_REBUILD_MANIFEST))
    ap.add_argument('--external-artifact-drop-validator-report', default=str(DEFAULT_EXTERNAL_ARTIFACT_DROP_VALIDATOR))
    ap.add_argument('--external-artifact-ingestion-plan-report', default=str(DEFAULT_EXTERNAL_ARTIFACT_INGESTION_PLAN))
    ap.add_argument('--external-artifact-controlled-copy-report', default=str(DEFAULT_EXTERNAL_ARTIFACT_CONTROLLED_COPY))
    ap.add_argument('--external-evidence-operations-dashboard-report', default=str(DEFAULT_EXTERNAL_EVIDENCE_OPERATIONS_DASHBOARD))
    ap.add_argument('--external-evidence-acceptance-worksheet-report', default=str(DEFAULT_EXTERNAL_EVIDENCE_ACCEPTANCE_WORKSHEET))
    ap.add_argument('--external-artifact-mapping-alias-report', default=str(DEFAULT_EXTERNAL_ARTIFACT_MAPPING_ALIAS))
    ap.add_argument('--external-evidence-case-validation-plan-report', default=str(DEFAULT_EXTERNAL_EVIDENCE_CASE_VALIDATION_PLAN))
    ap.add_argument('--case-validation-acceptance-contract-report', default=str(DEFAULT_CASE_VALIDATION_ACCEPTANCE_CONTRACT))
    ap.add_argument('--case-validation-acceptance-evaluation-report', default=str(DEFAULT_CASE_VALIDATION_ACCEPTANCE_EVALUATION))
    ap.add_argument('--case-validation-failure-attribution-report', default=str(DEFAULT_CASE_VALIDATION_FAILURE_ATTRIBUTION))
    ap.add_argument('--case-validation-closure-matrix-report', default=str(DEFAULT_CASE_VALIDATION_CLOSURE_MATRIX))
    ap.add_argument('--external-artifact-unlock-forecast-report', default=str(DEFAULT_EXTERNAL_ARTIFACT_UNLOCK_FORECAST))
    ap.add_argument(
        '--external-evidence-case-validation-plan-selftest-report',
        default=str(DEFAULT_EXTERNAL_EVIDENCE_CASE_VALIDATION_PLAN_SELFTEST),
    )
    ap.add_argument('--case-validation-runner-ledger', default=str(DEFAULT_CASE_VALIDATION_RUNNER_LEDGER))
    ap.add_argument(
        '--case-validation-runner-ledger-selftest-report',
        default=str(DEFAULT_CASE_VALIDATION_RUNNER_LEDGER_SELFTEST),
    )
    ap.add_argument('--case-validation-runner-preflight-report', default=str(DEFAULT_CASE_VALIDATION_RUNNER_PREFLIGHT))
    ap.add_argument('--case-validation-command-contract-report', default=str(DEFAULT_CASE_VALIDATION_COMMAND_CONTRACT))
    ap.add_argument(
        '--case-validation-command-contract-selftest-report',
        default=str(DEFAULT_CASE_VALIDATION_COMMAND_CONTRACT_SELFTEST),
    )
    ap.add_argument('--quality-review-coverage-report', default=str(DEFAULT_QUALITY_REVIEW_COVERAGE))
    ap.add_argument('--external-artifact-gate-selftest-report', default=str(DEFAULT_EXTERNAL_ARTIFACT_GATE_SELFTEST))
    ap.add_argument('--external-artifact-gate-negative-selftest-report', default=str(DEFAULT_EXTERNAL_ARTIFACT_GATE_NEGATIVE_SELFTEST))
    ap.add_argument(
        '--external-artifact-strict-qa-negative-selftest-report',
        default=str(DEFAULT_EXTERNAL_ARTIFACT_STRICT_QA_NEGATIVE_SELFTEST),
    )
    ap.add_argument('--synthetic-selftest-isolation-guard-report', default=str(DEFAULT_SYNTHETIC_SELFTEST_ISOLATION_GUARD))
    ap.add_argument('--sbepv5-dataset-ingestion-report', default=str(DEFAULT_SBEPV5_DATASET_INGESTION))
    ap.add_argument(
        '--sbepv5-dataset-ingestion-selftest-report',
        default=str(DEFAULT_SBEPV5_DATASET_INGESTION_SELFTEST),
    )
    ap.add_argument('--sbepv5-digitization-preflight-report', default=str(DEFAULT_SBEPV5_DIGITIZATION_PREFLIGHT))
    ap.add_argument('--sbepv5-literature-metric-preflight-report', default=str(DEFAULT_SBEPV5_LITERATURE_METRIC_PREFLIGHT))
    ap.add_argument('--sbepv5-external-dataset-report', default=str(DEFAULT_SBEPV5_EXTERNAL_DATASET))
    ap.add_argument('--sbepv5-case-package-report', default=str(DEFAULT_SBEPV5_CASE_PACKAGE))
    ap.add_argument('--sbepv5-case-package-preflight-report', default=str(DEFAULT_SBEPV5_CASE_PACKAGE_PREFLIGHT))
    ap.add_argument('--production-mesh-16rank-scout', default=str(DEFAULT_PRODUCTION_MESH_16RANK_SCOUT))
    ap.add_argument(
        '--academic-gas-detonation-readiness-report',
        default=str(DEFAULT_ACADEMIC_GAS_DETONATION_READINESS),
    )
    ap.add_argument('--command', default=DEFAULT_COMMAND)
    ap.add_argument('--returncode', type=int)
    ap.add_argument('--output-json', default=str(DEFAULT_OUTPUT_JSON))
    ap.add_argument('--output-md', default=str(DEFAULT_OUTPUT_MD))
    ap.add_argument('--no-require-ctest', action='store_true')
    ap.add_argument('--verify-json')
    args = ap.parse_args(argv)
    args.require_ctest = not args.no_require_ctest

    try:
        if args.verify_json:
            data = verify_report(Path(args.verify_json))
            summ = data.get('summary', {})
            print(
                'engineering_h2_production_evidence_verification_report VERIFY-PASS '
                f"json={args.verify_json} status={data['status']} "
                f"score={float(summ['scorecard_functional_percent']):.1f}/"
                f"{float(summ['scorecard_production_credibility_percent']):.1f} "
                f"ctest={summ.get('ctest_tests')}"
            )
            return 0
        report = build_report(args)
        out_json = Path(args.output_json)
        out_md = Path(args.output_md)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        write_markdown(report, out_md)
        print(
            'engineering_h2_production_evidence_verification_report PASS '
            f"json={out_json} md={out_md} status={report['status']} "
            f"score={float(report['summary']['scorecard_functional_percent']):.1f}/"
            f"{float(report['summary']['scorecard_production_credibility_percent']):.1f}"
        )
        return 0
    except VerificationReportError as exc:
        print(f'engineering_h2_production_evidence_verification_report FAIL {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
