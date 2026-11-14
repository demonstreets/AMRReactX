#!/usr/bin/env python3
"""Write/verify the current-scope operator runbook readiness report."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-SCOPE-OPERATOR-RUNBOOK"
STATUS_NOT_READY = "NOT_READY-CURRENT-SCOPE-OPERATOR-RUNBOOK"

README = Path("README.md")
RUNBOOK = Path("docs/codex_audit/current_scope_operator_runbook.md")
DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_scope_operator_runbook_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_scope_operator_runbook_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_scope_operator_runbook_report.md"

FINAL_READINESS = Path(
    "docs/codex_audit/evidence/master_plan_final_readiness_20260731/"
    "master_plan_final_readiness_report.json"
)
MASTER_CURRENT_SCOPE = Path(
    "docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/"
    "master_plan_current_scope_verification_report.json"
)
PARALLEL_CAPABILITY = Path(
    "docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/"
    "current_parallel_capability_matrix_report.json"
)
STRICT_BLOCKER = Path(
    "docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/"
    "master_plan_strict_blocker_matrix_report.json"
)
MULTI_FUEL_CAPABILITY = Path(
    "docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/"
    "engineering_multi_fuel_capability_boundary_report.json"
)
MULTI_FUEL_OPERATOR_RUNBOOK = Path(
    "docs/codex_audit/evidence/engineering_multi_fuel_operator_runbook_20260806/"
    "engineering_multi_fuel_operator_runbook_report.json"
)
MULTI_FUEL_TEMPLATE_CATALOG = Path(
    "docs/codex_audit/evidence/engineering_multi_fuel_template_catalog_20260811/"
    "engineering_multi_fuel_template_catalog_report.json"
)
CURRENT_WORKTREE_REVIEW_QUEUE = Path(
    "docs/codex_audit/evidence/current_worktree_review_queue_20260820/"
    "current_worktree_review_queue_report.json"
)
LIQUEFIED_SOURCE_MODEL_CUDA_SMOKE = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_cuda_smoke_20260807/"
    "engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.json"
)
LIQUEFIED_SOURCE_BALANCE = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_source_balance_20260807/"
    "engineering_liquefied_release_source_balance_report.json"
)
LIQUEFIED_SOURCE_BALANCE_NEGATIVE = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_source_balance_negative_selftest_20260807/"
    "engineering_liquefied_release_source_balance_negative_selftest_report.json"
)
LIQUEFIED_PHASE_CHANGE_OVERCLAIM_GUARD = Path(
    "docs/codex_audit/evidence/engineering_liquefied_phase_change_overclaim_guard_20260811/"
    "engineering_liquefied_phase_change_overclaim_guard_report.json"
)
LIQUEFIED_THERMAL_PLAUSIBILITY = Path(
    "docs/codex_audit/evidence/engineering_liquefied_release_thermal_plausibility_20260811/"
    "engineering_liquefied_release_thermal_plausibility_report.json"
)
LIQUEFIED_BREACH_SOURCE_CONTRACT = Path(
    "docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/"
    "engineering_liquefied_breach_source_contract_report.json"
)
LIQUEFIED_BREACH_PRESET_TEMPLATES = Path(
    "docs/codex_audit/evidence/engineering_liquefied_breach_preset_templates_20260811/"
    "engineering_liquefied_breach_preset_templates_report.json"
)
MULTIFUEL_LIQUEFIED_USER_ANSWER = Path(
    "docs/codex_audit/evidence/engineering_multifuel_liquefied_user_answer_20260811/"
    "engineering_multifuel_liquefied_user_answer_report.json"
)
RELEASE_CANDIDATE_HANDOFF = Path(
    "docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812/"
    "current_scope_release_candidate_handoff_report.json"
)
STRICT_FIRE_CALIBRATION = Path(
    "docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731/"
    "master_plan_strict_fire_calibration_update_report.json"
)
STRICT_EXTERNAL_SOURCE = Path(
    "docs/codex_audit/evidence/master_plan_strict_external_source_update_20260731/"
    "master_plan_strict_external_source_update_report.json"
)
DATAVERSE_AMR_SOURCE_PROJECTION_IMPLEMENTATION = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_implementation_20260811/"
    "dataverse_open_channel_amr_source_projection_implementation_report.json"
)
DATAVERSE_LONG_WINDOW_RECONCILIATION = Path(
    "docs/codex_audit/evidence/dataverse_open_channel_long_window_reconciliation_20260811/"
    "dataverse_open_channel_long_window_reconciliation_report.json"
)
STRICT_REAL_CAD = Path(
    "docs/codex_audit/evidence/master_plan_strict_real_cad_update_20260731/"
    "master_plan_strict_real_cad_update_report.json"
)
REAL_CAD_NEGATIVE_SELFTEST = Path(
    "docs/codex_audit/evidence/engineering_h2_real_cad_guard_negative_selftest_20260807/"
    "real_cad_guard_negative_selftest_report.json"
)
EXP002_OVERPRESSURE_REDUCED = Path(
    "docs/codex_audit/evidence/h2_fire_overpressure_reduced_exp002_20260805/"
    "h2_fire_overpressure_reduced_exp002_report.json"
)
EXP002_PRESSURE_CFD_PROXY = Path(
    "docs/codex_audit/evidence/h2_fire_exp002_pressure_cfd_proxy_20260805/"
    "h2_fire_exp002_pressure_cfd_proxy_report.json"
)
PLOTFILE_SENSOR_SAMPLING = Path(
    "docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_contract_20260807/"
    "h2_fire_plotfile_sensor_sampling_contract_report.json"
)
PLOTFILE_SENSOR_SAMPLING_NEGATIVE = Path(
    "docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/"
    "h2_fire_plotfile_sensor_sampling_negative_selftest_report.json"
)
MDPI_RADIATION_INTEGRATED_PROXY = Path(
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_integrated_cfd_proxy_20260807/"
    "h2_fire_mdpi_radiation_integrated_cfd_proxy_report.json"
)
H2_FIRE_CALIBRATION_RESIDUAL_BUDGET = Path(
    "docs/codex_audit/evidence/h2_fire_calibration_residual_budget_20260811/"
    "h2_fire_calibration_residual_budget_report.json"
)
STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF = Path(
    "docs/codex_audit/evidence/strict_external_artifact_cn_handoff_20260818/"
    "strict_external_artifact_cn_handoff_report.json"
)

REQUIRED_COMMANDS = [
    "bash tools/codex_verify_current_scope.sh",
    "python3 tools/codex_print_current_status.py",
    "python3 tools/codex_print_current_status.py --json",
    "python3 tools/write_current_status_cli_report.py",
    "bash tools/verify_current_status_cli.sh",
    "python3 tools/check_machine_local_paths.py --strict",
    "python3 tools/write_current_parallel_capability_matrix_report.py",
    "bash tools/verify_current_parallel_capability_matrix.sh",
    "python3 tools/write_master_plan_final_readiness_report.py",
    "bash tools/verify_master_plan_final_readiness.sh",
    "bash tools/verify_master_plan_current_scope.sh",
    "python3 tools/write_master_plan_current_scope_verification_report.py",
    "bash tools/verify_master_plan_current_scope_verification.sh",
    "python3 tools/write_current_scope_state_snapshot_report.py",
    "bash tools/verify_current_scope_state_snapshot.sh",
    "python3 tools/write_strict_master_plan_unblock_runbook_report.py",
    "bash tools/verify_strict_master_plan_unblock_runbook.sh",
    "python3 tools/write_strict_unblock_command_inventory_report.py",
    "bash tools/verify_strict_unblock_command_inventory.sh",
    "python3 tools/write_strict_artifact_template_lint_report.py",
    "bash tools/verify_strict_artifact_template_lint.sh",
    "python3 tools/write_strict_artifact_drop_contract_preflight_report.py",
    "bash tools/verify_strict_artifact_drop_contract_preflight.sh",
    "python3 tools/write_strict_artifact_drop_contract_selftest_report.py",
    "bash tools/verify_strict_artifact_drop_contract_selftest.sh",
    "python3 tools/write_strict_external_artifact_cn_handoff_report.py",
    "bash tools/verify_strict_external_artifact_cn_handoff.sh",
    "python3 tools/write_master_plan_completion_audit_report.py",
    "bash tools/verify_master_plan_completion_audit.sh",
    "python3 tools/write_current_worktree_hygiene_report.py",
    "bash tools/verify_current_worktree_hygiene.sh",
    "python3 tools/write_current_worktree_source_ledger_report.py",
    "bash tools/verify_current_worktree_source_ledger.sh",
    "python3 tools/write_current_worktree_review_queue_report.py",
    "bash tools/verify_current_worktree_review_queue.sh",
    "python3 tools/write_current_case_output_cleanup_manifest_report.py",
    "bash tools/verify_current_case_output_cleanup_manifest.sh",
    "python3 tools/write_current_disk_usage_manifest_report.py",
    "bash tools/verify_current_disk_usage_manifest.sh",
    "python3 tools/write_current_disk_cleanup_plan_report.py",
    "bash tools/verify_current_disk_cleanup_plan.sh",
    "python3 tools/write_current_operator_command_inventory_report.py",
    "bash tools/verify_current_operator_command_inventory.sh",
    "python3 tools/write_current_scope_release_candidate_handoff_report.py",
    "bash tools/verify_current_scope_release_candidate_handoff.sh",
    "python3 tools/write_current_verification_chain_coverage_report.py",
    "bash tools/verify_current_verification_chain_coverage.sh",
    "python3 tools/write_engineering_multi_fuel_capability_boundary_report.py",
    "bash tools/verify_engineering_multi_fuel_capability_boundary.sh",
    "python3 tools/write_engineering_multi_fuel_operator_runbook_report.py",
    "bash tools/verify_engineering_multi_fuel_operator_runbook.sh",
    "python3 tools/write_engineering_multi_fuel_template_catalog_report.py",
    "bash tools/verify_engineering_multi_fuel_template_catalog.sh",
    "bash tools/run_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh",
    "python3 tools/write_engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.py",
    "bash tools/verify_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh",
    "python3 tools/write_engineering_liquefied_release_source_balance_report.py",
    "bash tools/verify_engineering_liquefied_release_source_balance.sh",
    "python3 tools/write_engineering_liquefied_release_source_balance_negative_selftest_report.py",
    "bash tools/verify_engineering_liquefied_release_source_balance_negative_selftest.sh",
    "python3 tools/write_engineering_liquefied_release_thermal_plausibility_report.py",
    "bash tools/verify_engineering_liquefied_release_thermal_plausibility.sh",
    "python3 tools/write_engineering_liquefied_breach_source_contract_report.py",
    "bash tools/verify_engineering_liquefied_breach_source_contract.sh",
    "python3 tools/write_engineering_liquefied_breach_preset_templates_report.py",
    "bash tools/verify_engineering_liquefied_breach_preset_templates.sh",
    "python3 tools/write_engineering_multifuel_liquefied_user_answer_report.py",
    "bash tools/verify_engineering_multifuel_liquefied_user_answer.sh",
    "python3 tools/write_engineering_liquefied_phase_change_overclaim_guard_report.py",
    "bash tools/verify_engineering_liquefied_phase_change_overclaim_guard.sh",
    "python3 tools/write_h2_fire_overpressure_reduced_exp002_report.py",
    "bash tools/verify_h2_fire_overpressure_reduced_exp002.sh",
    "python3 tools/write_h2_fire_exp002_pressure_cfd_proxy_report.py",
    "bash tools/verify_h2_fire_exp002_pressure_cfd_proxy.sh",
    "python3 tools/write_h2_fire_plotfile_sensor_sampling_contract_report.py",
    "bash tools/verify_h2_fire_plotfile_sensor_sampling_contract.sh",
    "python3 tools/write_h2_fire_plotfile_sensor_sampling_negative_selftest_report.py",
    "bash tools/verify_h2_fire_plotfile_sensor_sampling_negative_selftest.sh",
    "python3 tools/write_h2_fire_mdpi_radiation_integrated_cfd_proxy_report.py",
    "bash tools/verify_h2_fire_mdpi_radiation_integrated_cfd_proxy.sh",
    "python3 tools/write_h2_fire_calibration_residual_budget_report.py",
    "bash tools/verify_h2_fire_calibration_residual_budget.sh",
    "python3 tools/write_master_plan_strict_fire_calibration_update_report.py",
    "bash tools/verify_master_plan_strict_fire_calibration_update.sh",
    "bash tools/codex_build_h2_leak_mpi_cuda_repro.sh",
    "python3 tools/write_dataverse_open_channel_amr_source_projection_implementation_report.py",
    "bash tools/verify_dataverse_open_channel_amr_source_projection_implementation.sh",
    "python3 tools/write_dataverse_open_channel_long_window_reconciliation_report.py",
    "bash tools/verify_dataverse_open_channel_long_window_reconciliation.sh",
    "python3 tools/write_master_plan_strict_external_source_update_report.py",
    "bash tools/verify_master_plan_strict_external_source_update.sh",
    "python3 tools/write_master_plan_strict_real_cad_update_report.py",
    "bash tools/verify_master_plan_strict_real_cad_update.sh",
    "python3 tools/write_engineering_h2_real_cad_negative_selftest_report.py",
    "bash tools/verify_engineering_h2_real_cad_negative_selftest.sh",
    "CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh",
    "bash tools/verify_academic_evidence.sh",
    "bash tools/verify_academic_current_priority_scope.sh",
    "bash tools/codex_run_academic_gas_liquid_detonation_mpi_cuda_extended.sh",
    "bash tools/verify_academic_gas_liquid_detonation_mpi_cuda_extended.sh",
]

REQUIRED_TOOLS = [
    "tools/codex_verify_current_scope.sh",
    "tools/codex_print_current_status.py",
    "tools/write_current_status_cli_report.py",
    "tools/verify_current_status_cli.sh",
    "tools/check_machine_local_paths.py",
    "tools/write_current_parallel_capability_matrix_report.py",
    "tools/verify_current_parallel_capability_matrix.sh",
    "tools/write_master_plan_final_readiness_report.py",
    "tools/verify_master_plan_final_readiness.sh",
    "tools/verify_master_plan_current_scope.sh",
    "tools/write_master_plan_current_scope_verification_report.py",
    "tools/verify_master_plan_current_scope_verification.sh",
    "tools/write_current_scope_state_snapshot_report.py",
    "tools/verify_current_scope_state_snapshot.sh",
    "tools/write_strict_master_plan_unblock_runbook_report.py",
    "tools/verify_strict_master_plan_unblock_runbook.sh",
    "tools/write_strict_unblock_command_inventory_report.py",
    "tools/verify_strict_unblock_command_inventory.sh",
    "tools/write_strict_artifact_template_lint_report.py",
    "tools/verify_strict_artifact_template_lint.sh",
    "tools/write_strict_artifact_drop_contract_preflight_report.py",
    "tools/verify_strict_artifact_drop_contract_preflight.sh",
    "tools/write_strict_artifact_drop_contract_selftest_report.py",
    "tools/verify_strict_artifact_drop_contract_selftest.sh",
    "tools/write_strict_external_artifact_cn_handoff_report.py",
    "tools/verify_strict_external_artifact_cn_handoff.sh",
    "tools/write_master_plan_completion_audit_report.py",
    "tools/verify_master_plan_completion_audit.sh",
    "tools/write_current_worktree_hygiene_report.py",
    "tools/verify_current_worktree_hygiene.sh",
    "tools/write_current_worktree_source_ledger_report.py",
    "tools/verify_current_worktree_source_ledger.sh",
    "tools/write_current_worktree_review_queue_report.py",
    "tools/verify_current_worktree_review_queue.sh",
    "tools/write_current_case_output_cleanup_manifest_report.py",
    "tools/verify_current_case_output_cleanup_manifest.sh",
    "tools/write_current_disk_usage_manifest_report.py",
    "tools/verify_current_disk_usage_manifest.sh",
    "tools/write_current_disk_cleanup_plan_report.py",
    "tools/verify_current_disk_cleanup_plan.sh",
    "tools/write_current_operator_command_inventory_report.py",
    "tools/verify_current_operator_command_inventory.sh",
    "tools/write_current_scope_release_candidate_handoff_report.py",
    "tools/verify_current_scope_release_candidate_handoff.sh",
    "tools/write_current_verification_chain_coverage_report.py",
    "tools/verify_current_verification_chain_coverage.sh",
    "tools/write_engineering_multi_fuel_capability_boundary_report.py",
    "tools/verify_engineering_multi_fuel_capability_boundary.sh",
    "tools/write_engineering_multi_fuel_operator_runbook_report.py",
    "tools/verify_engineering_multi_fuel_operator_runbook.sh",
    "tools/write_engineering_multi_fuel_template_catalog_report.py",
    "tools/verify_engineering_multi_fuel_template_catalog.sh",
    "tools/run_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh",
    "tools/write_engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.py",
    "tools/verify_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh",
    "tools/write_engineering_liquefied_release_source_balance_report.py",
    "tools/verify_engineering_liquefied_release_source_balance.sh",
    "tools/write_engineering_liquefied_release_source_balance_negative_selftest_report.py",
    "tools/verify_engineering_liquefied_release_source_balance_negative_selftest.sh",
    "tools/write_engineering_liquefied_release_thermal_plausibility_report.py",
    "tools/verify_engineering_liquefied_release_thermal_plausibility.sh",
    "tools/write_engineering_liquefied_breach_source_contract_report.py",
    "tools/verify_engineering_liquefied_breach_source_contract.sh",
    "tools/write_engineering_liquefied_breach_preset_templates_report.py",
    "tools/verify_engineering_liquefied_breach_preset_templates.sh",
    "tools/write_engineering_multifuel_liquefied_user_answer_report.py",
    "tools/verify_engineering_multifuel_liquefied_user_answer.sh",
    "tools/write_engineering_liquefied_phase_change_overclaim_guard_report.py",
    "tools/verify_engineering_liquefied_phase_change_overclaim_guard.sh",
    "tools/write_h2_fire_overpressure_reduced_exp002_report.py",
    "tools/verify_h2_fire_overpressure_reduced_exp002.sh",
    "tools/write_h2_fire_exp002_pressure_cfd_proxy_report.py",
    "tools/verify_h2_fire_exp002_pressure_cfd_proxy.sh",
    "tools/write_h2_fire_plotfile_sensor_sampling_contract_report.py",
    "tools/verify_h2_fire_plotfile_sensor_sampling_contract.sh",
    "tools/write_h2_fire_plotfile_sensor_sampling_negative_selftest_report.py",
    "tools/verify_h2_fire_plotfile_sensor_sampling_negative_selftest.sh",
    "tools/write_h2_fire_mdpi_radiation_integrated_cfd_proxy_report.py",
    "tools/verify_h2_fire_mdpi_radiation_integrated_cfd_proxy.sh",
    "tools/write_h2_fire_calibration_residual_budget_report.py",
    "tools/verify_h2_fire_calibration_residual_budget.sh",
    "tools/write_master_plan_strict_fire_calibration_update_report.py",
    "tools/verify_master_plan_strict_fire_calibration_update.sh",
    "tools/codex_setup_cuda126_sundials_env.sh",
    "tools/codex_build_h2_leak_mpi_cuda_repro.sh",
    "tools/write_dataverse_open_channel_amr_source_projection_implementation_report.py",
    "tools/verify_dataverse_open_channel_amr_source_projection_implementation.sh",
    "tools/write_dataverse_open_channel_long_window_reconciliation_report.py",
    "tools/verify_dataverse_open_channel_long_window_reconciliation.sh",
    "tools/write_master_plan_strict_external_source_update_report.py",
    "tools/verify_master_plan_strict_external_source_update.sh",
    "tools/write_master_plan_strict_real_cad_update_report.py",
    "tools/verify_master_plan_strict_real_cad_update.sh",
    "tools/write_engineering_h2_real_cad_negative_selftest_report.py",
    "tools/verify_engineering_h2_real_cad_negative_selftest.sh",
    "tools/verify_engineering_h2_production_evidence.sh",
    "tools/codex_smoke_engineering_h2_leak_pipe_rack_obstacle.sh",
    "tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh",
    "tools/codex_smoke_engineering_h2_pipe_rack_reacting_mpi_cuda_restart.sh",
    "tools/codex_smoke_engineering_h2_reacting_mpi_cuda.sh",
    "tools/verify_academic_evidence.sh",
    "tools/verify_academic_current_priority_scope.sh",
    "tools/codex_run_academic_gpu_environment_preflight.sh",
    "tools/codex_run_academic_gas_2d_detonation_reference.sh",
    "tools/codex_run_academic_gas_3d_detonation_reference.sh",
    "tools/codex_run_academic_gas_detonation_front_amr_validation.sh",
    "tools/codex_run_academic_gas_liquid_detonation_mpi_cuda_extended.sh",
    "tools/verify_academic_gas_liquid_detonation_mpi_cuda_extended.sh",
]

REQUIRED_REPORTS = [
    FINAL_READINESS,
    MASTER_CURRENT_SCOPE,
    PARALLEL_CAPABILITY,
    STRICT_BLOCKER,
    MULTI_FUEL_CAPABILITY,
    MULTI_FUEL_OPERATOR_RUNBOOK,
    MULTI_FUEL_TEMPLATE_CATALOG,
    LIQUEFIED_SOURCE_MODEL_CUDA_SMOKE,
    LIQUEFIED_SOURCE_BALANCE,
    LIQUEFIED_SOURCE_BALANCE_NEGATIVE,
    LIQUEFIED_THERMAL_PLAUSIBILITY,
    LIQUEFIED_BREACH_SOURCE_CONTRACT,
    LIQUEFIED_BREACH_PRESET_TEMPLATES,
    MULTIFUEL_LIQUEFIED_USER_ANSWER,
    LIQUEFIED_PHASE_CHANGE_OVERCLAIM_GUARD,
    RELEASE_CANDIDATE_HANDOFF,
    STRICT_FIRE_CALIBRATION,
    STRICT_EXTERNAL_SOURCE,
    STRICT_REAL_CAD,
    REAL_CAD_NEGATIVE_SELFTEST,
    EXP002_OVERPRESSURE_REDUCED,
    EXP002_PRESSURE_CFD_PROXY,
    PLOTFILE_SENSOR_SAMPLING,
    PLOTFILE_SENSOR_SAMPLING_NEGATIVE,
    MDPI_RADIATION_INTEGRATED_PROXY,
    H2_FIRE_CALIBRATION_RESIDUAL_BUDGET,
    STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF,
    DATAVERSE_AMR_SOURCE_PROJECTION_IMPLEMENTATION,
    DATAVERSE_LONG_WINDOW_RECONCILIATION,
    Path(
        "docs/codex_audit/evidence/academic_gas_detonation_mpi_cuda_20260731/"
        "academic_gas_detonation_mpi_cuda_report.json"
    ),
    Path(
        "docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_extended_20260803/"
        "academic_gas_liquid_detonation_mpi_cuda_extended_report.json"
    ),
    CURRENT_WORKTREE_REVIEW_QUEUE,
]

REQUIRED_STRICT_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}

REQUIRED_README_SNIPPETS = [
    "my-pele Current Status",
    "docs/codex_audit/current_scope_operator_runbook.md",
    "docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/current_parallel_capability_matrix_report.json",
    "docs/codex_audit/evidence/master_plan_final_readiness_20260731/master_plan_final_readiness_report.json",
    "docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/master_plan_current_scope_verification_report.json",
    "docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/master_plan_strict_blocker_matrix_report.json",
    "docs/codex_audit/strict_master_plan_unblock_runbook.md",
    "docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_implementation_20260811/dataverse_open_channel_amr_source_projection_implementation_report.json",
    "docs/codex_audit/evidence/dataverse_open_channel_long_window_reconciliation_20260811/dataverse_open_channel_long_window_reconciliation_report.json",
    "docs/codex_audit/evidence/current_status_cli_20260803/current_status_cli_report.json",
    "docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/engineering_multi_fuel_capability_boundary_report.json",
    "docs/codex_audit/engineering_multi_fuel_operator_runbook.md",
    "docs/codex_audit/evidence/engineering_multi_fuel_operator_runbook_20260806/engineering_multi_fuel_operator_runbook_report.json",
    "docs/codex_audit/evidence/engineering_multi_fuel_template_catalog_20260811/engineering_multi_fuel_template_catalog_report.json",
    "docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_cuda_smoke_20260807/engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.json",
    "docs/codex_audit/evidence/engineering_liquefied_release_source_balance_20260807/engineering_liquefied_release_source_balance_report.json",
    "docs/codex_audit/evidence/engineering_liquefied_release_source_balance_negative_selftest_20260807/engineering_liquefied_release_source_balance_negative_selftest_report.json",
    "docs/codex_audit/evidence/engineering_liquefied_release_thermal_plausibility_20260811/engineering_liquefied_release_thermal_plausibility_report.json",
    "docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/engineering_liquefied_breach_source_contract_report.json",
    "docs/codex_audit/evidence/engineering_liquefied_breach_preset_templates_20260811/engineering_liquefied_breach_preset_templates_report.json",
    "docs/codex_audit/evidence/engineering_multifuel_liquefied_user_answer_20260811/engineering_multifuel_liquefied_user_answer_report.json",
    "docs/codex_audit/evidence/engineering_liquefied_phase_change_overclaim_guard_20260811/engineering_liquefied_phase_change_overclaim_guard_report.json",
    "docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812/current_scope_release_candidate_handoff_report.json",
    "Current-Scope Release Candidate Handoff",
    "release-candidate handoff ready: yes",
    "release-candidate usable for current priority scope: yes",
    "release-candidate is full strict master-plan completion: no",
    "Engineering Multifuel And Liquefied-Gas User Answer",
    "can_compute_liquefied_tank_breach_vaporization",
    "Dataverse long-window reconciliation: TRIAGED-DATAVERSE-OPEN-CHANNEL-LONG-WINDOW-REFINED-SOURCE-GAP",
    "Dataverse AMR MPI+CUDA reproducible build uses CUDA 12.6: yes",
    "docs/codex_audit/evidence/current_worktree_hygiene_20260803/current_worktree_hygiene_report.json",
    "docs/codex_audit/evidence/current_worktree_source_ledger_20260803/current_worktree_source_ledger_report.json",
    "docs/codex_audit/evidence/current_worktree_review_queue_20260820/current_worktree_review_queue_report.json",
    "docs/codex_audit/evidence/current_case_output_cleanup_manifest_20260803/current_case_output_cleanup_manifest_report.json",
    "docs/codex_audit/evidence/current_disk_usage_manifest_20260803/current_disk_usage_manifest_report.json",
    "docs/codex_audit/evidence/current_disk_cleanup_plan_20260803/current_disk_cleanup_plan_report.json",
    "docs/codex_audit/evidence/current_operator_command_inventory_20260803/current_operator_command_inventory_report.json",
    "docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812/current_scope_release_candidate_handoff_report.json",
    "docs/codex_audit/evidence/current_verification_chain_coverage_20260803/current_verification_chain_coverage_report.json",
    "docs/codex_audit/evidence/strict_unblock_command_inventory_20260803/strict_unblock_command_inventory_report.json",
    "docs/codex_audit/evidence/strict_artifact_template_lint_20260803/strict_artifact_template_lint_report.json",
    "docs/codex_audit/evidence/strict_artifact_drop_contract_preflight_20260803/strict_artifact_drop_contract_preflight_report.json",
    "docs/codex_audit/evidence/strict_artifact_drop_contract_selftest_20260803/strict_artifact_drop_contract_selftest_report.json",
    "docs/user_guides/真实资料投递清单_按文件路径.md",
    "docs/codex_audit/evidence/strict_external_artifact_cn_handoff_20260818/strict_external_artifact_cn_handoff_report.json",
    "PASS-STRICT-EXTERNAL-ARTIFACT-CN-HANDOFF",
    "真实资料投递清单_按文件路径",
    "strict external artifact Chinese handoff ready: yes",
    "bash tools/codex_verify_current_scope.sh",
    "python3 tools/codex_print_current_status.py",
    "python3 tools/codex_print_current_status.py --json",
    "python3 tools/write_current_status_cli_report.py",
    "bash tools/verify_current_status_cli.sh",
    "Fuel And Liquefied-Gas Boundary",
    "Engineering multi-fuel gas-source, gasified LNG/LPG surrogate, and screening",
    "CH4 gas/fire probes",
    "C3H8 gas/fire probes",
    "gasified LNG surrogate",
    "gasified LPG surrogate",
    "Liquefied-release source balance checks",
    "Liquefied-release source balance negative selftest guards",
    "Liquefied-release thermal plausibility checks",
    "Liquefied LNG/LPG breach-to-gas-source contract checks",
    "Operator-editable LNG/LPG breach preset JSONs",
    "Liquefied phase-change overclaim guard",
    "liquefied release source balance negative cases rejected: 5/5",
    "liquefied release source guard phase-change overclaim: yes",
    "liquefied release thermal plausibility ready: yes",
    "liquefied release vaporized fraction formula: yes",
    "liquefied release heat loads positive: yes",
    "liquefied breach source contract ready: yes",
    "liquefied breach source contract generates external gas source: yes",
    "liquefied phase-change overclaim guard ready: yes",
    "liquefied production phase-change claim allowed: no",
    "liquefied CFD solves liquid phase-change: no",
    "liquefied CFD solves flashing discharge: no",
    "internal liquid phase-change CFD: no",
    "multi-fuel production-ready claim: no",
    "overclaim guard: yes",
    "Fire Consequence Calibration Boundary",
    "docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731/master_plan_strict_fire_calibration_update_report.json",
    "docs/codex_audit/evidence/h2_fire_overpressure_reduced_exp002_20260805/h2_fire_overpressure_reduced_exp002_report.json",
    "docs/codex_audit/evidence/h2_fire_exp002_pressure_cfd_proxy_20260805/h2_fire_exp002_pressure_cfd_proxy_report.json",
    "docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_contract_20260807/h2_fire_plotfile_sensor_sampling_contract_report.json",
    "docs/codex_audit/evidence/h2_fire_mdpi_radiation_integrated_cfd_proxy_20260807/h2_fire_mdpi_radiation_integrated_cfd_proxy_report.json",
    "docs/codex_audit/evidence/h2_fire_calibration_residual_budget_20260811/h2_fire_calibration_residual_budget_report.json",
    "fire calibration residual budget ready: yes",
    "fire calibration residual budget clears blocker: no",
    "fire calibration blocker cleared: no",
    "EXP002 pressure CFD proxy CPU/GPU parity: yes",
    "MDPI CFD outputs sufficient for radiation agreement: no",
    "External Plume Reference Boundary",
    "docs/codex_audit/evidence/master_plan_strict_external_source_update_20260731/master_plan_strict_external_source_update_report.json",
    "external plume blocker cleared: no",
    "Dataverse agreement sensor count: 29",
    "Dataverse 120s agreement attempt status: QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
    "Dataverse geometry ready for full mesh parity: no",
    "Real CAD Boundary",
    "docs/codex_audit/evidence/master_plan_strict_real_cad_update_20260731/master_plan_strict_real_cad_update_report.json",
    "real CAD handoff contract ready: yes",
    "real CAD source CAD files: 0",
    "real CAD negative cases rejected: 8/8",
    "real CAD guard boundary missing required role: yes",
    "real CAD boundary contract ready for credit: no",
    "PASS-CURRENT-STATUS-CLI",
    "AUDITED-CURRENT-WORKTREE-HYGIENE",
    "AUDITED-CURRENT-WORKTREE-SOURCE-LEDGER",
    "AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST",
    "AUDITED-CURRENT-DISK-USAGE-MANIFEST",
    "AUDITED-CURRENT-DISK-CLEANUP-PLAN",
    "PASS-CURRENT-OPERATOR-COMMAND-INVENTORY",
    "PASS-CURRENT-VERIFICATION-CHAIN-COVERAGE",
    "PASS-STRICT-UNBLOCK-COMMAND-INVENTORY",
    "PASS-STRICT-ARTIFACT-TEMPLATE-LINT",
    "PASS-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT",
    "PASS-STRICT-ARTIFACT-DROP-CONTRACT-SELFTEST",
    "PASS-CURRENT-SCOPE-OPERATOR-RUNBOOK",
    "PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX",
    "PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS",
    "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION",
    "PASS-CURRENT-SCOPE-STATE-SNAPSHOT",
    "PASS-STRICT-MASTER-PLAN-UNBLOCK-RUNBOOK",
    "AUDITED-MASTER-PLAN-CURRENT-SCOPE-PASS-STRICT-INCOMPLETE",
    "Current-scope PASS does not claim strict completion",
]


class RunbookError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RunbookError(message)


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
        raise RunbookError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RunbookError(f"invalid JSON evidence {path}: {exc}") from exc
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


def build_report() -> dict[str, Any]:
    require(README.is_file(), f"missing README: {README}")
    require(RUNBOOK.is_file(), f"missing runbook: {RUNBOOK}")
    readme_text = README.read_text(encoding="utf-8")
    text = RUNBOOK.read_text(encoding="utf-8")

    missing_commands = [command for command in REQUIRED_COMMANDS if command not in text]
    missing_tools = [tool for tool in REQUIRED_TOOLS if not Path(tool).is_file()]
    missing_report_paths = [str(path) for path in REQUIRED_REPORTS if str(path) not in text]
    missing_reports = [str(path) for path in REQUIRED_REPORTS if not path.is_file()]
    missing_readme_snippets = [snippet for snippet in REQUIRED_README_SNIPPETS if snippet not in readme_text]

    final = load_json(FINAL_READINESS)
    master = load_json(MASTER_CURRENT_SCOPE)
    parallel = load_json(PARALLEL_CAPABILITY)
    strict = load_json(STRICT_BLOCKER)
    multi_fuel = load_json(MULTI_FUEL_CAPABILITY)
    multi_fuel_runbook = load_json(MULTI_FUEL_OPERATOR_RUNBOOK)
    multi_fuel_template_catalog = load_json(MULTI_FUEL_TEMPLATE_CATALOG)
    liquefied_cuda = load_json(LIQUEFIED_SOURCE_MODEL_CUDA_SMOKE)
    liquefied_balance = load_json(LIQUEFIED_SOURCE_BALANCE)
    liquefied_balance_negative = load_json(LIQUEFIED_SOURCE_BALANCE_NEGATIVE)
    liquefied_thermal = load_json(LIQUEFIED_THERMAL_PLAUSIBILITY)
    liquefied_breach = load_json(LIQUEFIED_BREACH_SOURCE_CONTRACT)
    liquefied_breach_presets = load_json(LIQUEFIED_BREACH_PRESET_TEMPLATES)
    multifuel_liquefied_answer = load_json(MULTIFUEL_LIQUEFIED_USER_ANSWER)
    liquefied_phase_change_guard = load_json(LIQUEFIED_PHASE_CHANGE_OVERCLAIM_GUARD)
    release_candidate = load_json(RELEASE_CANDIDATE_HANDOFF)
    strict_fire = load_json(STRICT_FIRE_CALIBRATION)
    fire_residual = load_json(H2_FIRE_CALIBRATION_RESIDUAL_BUDGET)
    cn_handoff = load_json(STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF)
    strict_external = load_json(STRICT_EXTERNAL_SOURCE)
    amr_source_projection = load_json(DATAVERSE_AMR_SOURCE_PROJECTION_IMPLEMENTATION)
    long_window = load_json(DATAVERSE_LONG_WINDOW_RECONCILIATION)
    strict_real_cad = load_json(STRICT_REAL_CAD)
    real_cad_negative = load_json(REAL_CAD_NEGATIVE_SELFTEST)

    strict_blockers = set(strict.get("summary", {}).get("open_strict_blockers", []))
    required_blockers_present = all(blocker in text for blocker in REQUIRED_STRICT_BLOCKERS)
    blocker_set_ok = strict_blockers == REQUIRED_STRICT_BLOCKERS

    ready = (
        not missing_commands
        and not missing_readme_snippets
        and not missing_tools
        and not missing_report_paths
        and not missing_reports
        and final.get("status") == "PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS"
        and final.get("summary", {}).get("current_parallel_capability_ready") is True
        and master.get("status") == "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION"
        and master.get("summary", {}).get("passed_gate_count") == master.get("summary", {}).get("gate_count")
        and parallel.get("status") == "PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX"
        and parallel.get("summary", {}).get("multi_gpu_mpi_cuda_ready_for_all_current_scenarios") is True
        and multi_fuel.get("status") == "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY"
        and multi_fuel.get("summary", {}).get("prevents_overclaim") is True
        and multi_fuel.get("summary", {}).get("liquefied_gas_phase_change_ready") is False
        and multi_fuel_runbook.get("status") == "PASS-ENGINEERING-MULTI-FUEL-OPERATOR-RUNBOOK"
        and multi_fuel_runbook.get("summary", {}).get("operator_runbook_ready") is True
        and multi_fuel_runbook.get("summary", {}).get("missing_runbook_snippet_count") == 0
        and multi_fuel_template_catalog.get("status") == "PASS-ENGINEERING-MULTI-FUEL-TEMPLATE-CATALOG"
        and multi_fuel_template_catalog.get("summary", {}).get("multi_fuel_template_catalog_ready") is True
        and multi_fuel_template_catalog.get("summary", {}).get("fuel_species_seen") == ["C3H8", "CH4", "H2"]
        and multi_fuel_template_catalog.get("summary", {}).get("cfd_internal_liquid_phase_change_claim_allowed")
        is False
        and liquefied_cuda.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE"
        and liquefied_cuda.get("summary", {}).get("liquefied_release_source_model_cuda_smoke_ready") is True
        and liquefied_balance.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE"
        and liquefied_balance.get("summary", {}).get("liquefied_release_source_balance_ready") is True
        and liquefied_balance.get("summary", {}).get("mapping_schedule_matches_csv") is True
        and liquefied_balance_negative.get("status")
        == "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE-NEGATIVE-SELFTEST"
        and liquefied_balance_negative.get("summary", {}).get("negative_rejected_count") == 5
        and liquefied_balance_negative.get("summary", {}).get("expected_fragment_seen_count") == 5
        and liquefied_thermal.get("status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-THERMAL-PLAUSIBILITY"
        and liquefied_thermal.get("summary", {}).get("liquefied_release_thermal_plausibility_ready") is True
        and liquefied_thermal.get("summary", {}).get("all_vaporized_fraction_matches_screening_formula") is True
        and liquefied_thermal.get("summary", {}).get("all_heat_loads_positive") is True
        and liquefied_thermal.get("summary", {}).get("production_phase_change_claim_allowed") is False
        and liquefied_breach.get("status") == "PASS-ENGINEERING-LIQUEFIED-BREACH-SOURCE-CONTRACT"
        and liquefied_breach.get("summary", {}).get("liquefied_breach_source_contract_ready") is True
        and liquefied_breach.get("summary", {}).get("contract_accepts_screening_breach_inputs") is True
        and liquefied_breach.get("summary", {}).get("generates_external_gas_source_schedule") is True
        and liquefied_breach.get("summary", {}).get("production_phase_change_claim_allowed") is False
        and liquefied_breach_presets.get("status") == "PASS-ENGINEERING-LIQUEFIED-BREACH-PRESET-TEMPLATES"
        and liquefied_breach_presets.get("summary", {}).get("liquefied_breach_preset_templates_ready") is True
        and liquefied_breach_presets.get("summary", {}).get("editable_json_presets") is True
        and liquefied_breach_presets.get("summary", {}).get("generates_cfd_source_csv") is True
        and liquefied_breach_presets.get("summary", {}).get("production_phase_change_claim_allowed") is False
        and multifuel_liquefied_answer.get("status") == "PASS-ENGINEERING-MULTIFUEL-LIQUEFIED-USER-ANSWER"
        and multifuel_liquefied_answer.get("summary", {}).get("operator_answer_ready") is True
        and multifuel_liquefied_answer.get("summary", {}).get("gas_phase_non_h2_ready") is True
        and multifuel_liquefied_answer.get("summary", {}).get("liquefied_breach_external_source_ready") is True
        and multifuel_liquefied_answer.get("summary", {}).get("internal_liquid_phase_change_cfd_ready") is False
        and liquefied_phase_change_guard.get("status")
        == "PASS-ENGINEERING-LIQUEFIED-PHASE-CHANGE-OVERCLAIM-GUARD"
        and liquefied_phase_change_guard.get("summary", {}).get("phase_change_overclaim_guard_ready") is True
        and liquefied_phase_change_guard.get("summary", {}).get("external_vaporization_bridge_ready") is True
        and liquefied_phase_change_guard.get("summary", {}).get("liquefied_release_screening_source_ready") is True
        and liquefied_phase_change_guard.get("summary", {}).get("liquefied_release_cuda_runtime_ready") is True
        and liquefied_phase_change_guard.get("summary", {}).get("production_phase_change_claim_allowed") is False
        and liquefied_phase_change_guard.get("summary", {}).get("cfd_solves_liquid_phase_change") is False
        and liquefied_phase_change_guard.get("summary", {}).get("cfd_solves_pool_spread_evaporation") is False
        and liquefied_phase_change_guard.get("summary", {}).get("cfd_solves_flashing_discharge") is False
        and strict_fire.get("status") == "TRIAGED-MASTER-PLAN-STRICT-FIRE-CALIBRATION-PARTIAL-DATA-BRIDGED"
        and strict_fire.get("summary", {}).get("strict_fire_calibration_blocker_cleared") is False
        and strict_fire.get("summary", {}).get("exp002_pressure_cfd_proxy_cpu_gpu_parity_passed") is True
        and strict_fire.get("summary", {}).get("plotfile_sensor_sampling_contract_ready") is True
        and strict_fire.get("summary", {}).get("mdpi_radiation_integrated_cfd_proxy_extracted") is True
        and fire_residual.get("status") == "TRIAGED-H2-FIRE-CALIBRATION-RESIDUAL-BUDGET"
        and fire_residual.get("summary", {}).get("fire_calibration_residual_budget_ready") is True
        and fire_residual.get("summary", {}).get("residual_budget_clears_strict_blocker") is False
        and fire_residual.get("summary", {}).get("production_fire_calibration_claim_allowed") is False
        and cn_handoff.get("status") == "PASS-STRICT-EXTERNAL-ARTIFACT-CN-HANDOFF"
        and cn_handoff.get("summary", {}).get("strict_external_artifact_cn_handoff_ready") is True
        and cn_handoff.get("summary", {}).get("required_file_count") == 14
        and isinstance(cn_handoff.get("summary", {}).get("missing_file_count"), int)
        and 0 <= cn_handoff.get("summary", {}).get("missing_file_count") <= 14
        and cn_handoff.get("summary", {}).get("open_strict_blocker_count") == 3
        and strict_external.get("status") == "TRIAGED-MASTER-PLAN-STRICT-EXTERNAL-SOURCES-PUBLIC-DATA-INCOMPLETE"
        and strict_external.get("summary", {}).get("strict_external_plume_blocker_cleared") is False
        and strict_external.get("summary", {}).get("dataverse_agreement_sensor_count") == 29
        and strict_external.get("summary", {}).get("dataverse_agreement_ready_for_cfd_scoring") is True
        and strict_external.get("summary", {}).get("dataverse_geometry_ready_for_full_mesh_parity") is False
        and strict_external.get("summary", {}).get("dataverse_amr_source_projection_current_single_level") is False
        and strict_external.get("summary", {}).get("dataverse_amr_source_projection_lacks_level_aware_mask") is False
        and strict_external.get("summary", {}).get("dataverse_amr_source_projection_finest_available_level_only")
        is True
        and amr_source_projection.get("status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-IMPLEMENTATION"
        and amr_source_projection.get("summary", {}).get("mpi_cuda_linked_executable") is True
        and amr_source_projection.get("summary", {}).get("mpi_cuda_reproducible_build_entrypoint_ready") is True
        and amr_source_projection.get("summary", {}).get("mpi_cuda_reproducible_build_uses_cuda_12_6") is True
        and amr_source_projection.get("summary", {}).get("mpi_cuda_reproducible_build_uses_local_sundials_cuda")
        is True
        and long_window.get("status") == "TRIAGED-DATAVERSE-OPEN-CHANNEL-LONG-WINDOW-REFINED-SOURCE-GAP"
        and long_window.get("summary", {}).get("existing_120s_window_reaches_experimental_peak_interval") is True
        and long_window.get("summary", {}).get("existing_120s_all_sensors_passed") is False
        and long_window.get("summary", {}).get("current_refined_source_time_end_s") == 0.005
        and long_window.get("summary", {}).get("steps_to_113s_at_current_refined_dt") >= 22000000
        and strict_real_cad.get("status") == "TRIAGED-MASTER-PLAN-STRICT-REAL-CAD-ARTIFACTS-MISSING"
        and strict_real_cad.get("summary", {}).get("strict_real_cad_blocker_cleared") is False
        and strict_real_cad.get("summary", {}).get("handoff_contract_ready") is True
        and strict_real_cad.get("summary", {}).get("source_cad_file_count") == 0
        and strict_real_cad.get("summary", {}).get("cleaned_geometry_file_count") == 0
        and real_cad_negative.get("status") == "PASS-H2-REAL-CAD-GUARD-NEGATIVE-SELFTEST"
        and real_cad_negative.get("summary", {}).get("negative_rejected_count") == 8
        and real_cad_negative.get("summary", {}).get("expected_fragment_seen_count") == 8
        and release_candidate.get("status") == "PASS-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF"
        and release_candidate.get("summary", {}).get("release_candidate_handoff_ready") is True
        and release_candidate.get("summary", {}).get("current_scope_ready") is True
        and release_candidate.get("summary", {}).get("release_candidate_can_be_used_for_current_priority_scope")
        is True
        and release_candidate.get("summary", {}).get("release_candidate_is_full_strict_master_plan_completion")
        is False
        and release_candidate.get("summary", {}).get("open_strict_blocker_count") == 3
        and blocker_set_ok
        and required_blockers_present
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "operator_runbook_ready": ready,
            "runbook_path": str(RUNBOOK),
            "readme_path": str(README),
            "required_command_count": len(REQUIRED_COMMANDS),
            "missing_command_count": len(missing_commands),
            "missing_readme_snippet_count": len(missing_readme_snippets),
            "missing_tool_count": len(missing_tools),
            "missing_report_path_count": len(missing_report_paths),
            "missing_report_count": len(missing_reports),
            "final_readiness_status": final.get("status"),
            "master_current_scope_status": master.get("status"),
            "parallel_capability_status": parallel.get("status"),
            "multi_fuel_capability_status": multi_fuel.get("status"),
            "multi_fuel_prevents_overclaim": multi_fuel.get("summary", {}).get("prevents_overclaim"),
            "multi_fuel_liquefied_gas_phase_change_ready": multi_fuel.get("summary", {}).get(
                "liquefied_gas_phase_change_ready"
            ),
            "multi_fuel_operator_runbook_status": multi_fuel_runbook.get("status"),
            "multi_fuel_operator_runbook_ready": multi_fuel_runbook.get("summary", {}).get(
                "operator_runbook_ready"
            ),
            "multi_fuel_operator_runbook_missing_snippet_count": multi_fuel_runbook.get("summary", {}).get(
                "missing_runbook_snippet_count"
            ),
            "multi_fuel_template_catalog_status": multi_fuel_template_catalog.get("status"),
            "multi_fuel_template_catalog_ready": multi_fuel_template_catalog.get("summary", {}).get(
                "multi_fuel_template_catalog_ready"
            ),
            "multi_fuel_template_catalog_template_count": multi_fuel_template_catalog.get("summary", {}).get(
                "template_count"
            ),
            "multi_fuel_template_catalog_fuel_species_seen": multi_fuel_template_catalog.get("summary", {}).get(
                "fuel_species_seen"
            ),
            "multi_fuel_template_catalog_cfd_internal_liquid_phase_change_claim_allowed": (
                multi_fuel_template_catalog.get("summary", {}).get("cfd_internal_liquid_phase_change_claim_allowed")
            ),
            "liquefied_source_model_cuda_smoke_status": liquefied_cuda.get("status"),
            "liquefied_source_model_cuda_smoke_ready": liquefied_cuda.get("summary", {}).get(
                "liquefied_release_source_model_cuda_smoke_ready"
            ),
            "liquefied_source_balance_status": liquefied_balance.get("status"),
            "liquefied_source_balance_ready": liquefied_balance.get("summary", {}).get(
                "liquefied_release_source_balance_ready"
            ),
            "liquefied_source_balance_mapping_schedule_matches_csv": liquefied_balance.get("summary", {}).get(
                "mapping_schedule_matches_csv"
            ),
            "liquefied_source_balance_negative_status": liquefied_balance_negative.get("status"),
            "liquefied_source_balance_negative_rejected_count": liquefied_balance_negative.get("summary", {}).get(
                "negative_rejected_count"
            ),
            "liquefied_source_balance_negative_expected_fragment_seen_count": liquefied_balance_negative.get(
                "summary", {}
            ).get("expected_fragment_seen_count"),
            "liquefied_source_balance_guards_phase_change_overclaim": liquefied_balance_negative.get(
                "summary", {}
            ).get("guards_phase_change_overclaim"),
            "liquefied_thermal_plausibility_status": liquefied_thermal.get("status"),
            "liquefied_thermal_plausibility_ready": liquefied_thermal.get("summary", {}).get(
                "liquefied_release_thermal_plausibility_ready"
            ),
            "liquefied_thermal_vaporized_fraction_formula_ok": liquefied_thermal.get("summary", {}).get(
                "all_vaporized_fraction_matches_screening_formula"
            ),
            "liquefied_thermal_heat_loads_positive": liquefied_thermal.get("summary", {}).get(
                "all_heat_loads_positive"
            ),
            "liquefied_thermal_production_phase_change_claim_allowed": liquefied_thermal.get("summary", {}).get(
                "production_phase_change_claim_allowed"
            ),
            "liquefied_thermal_cfd_solves_liquid_phase_change": liquefied_thermal.get("summary", {}).get(
                "cfd_solves_liquid_phase_change"
            ),
            "liquefied_breach_source_contract_status": liquefied_breach.get("status"),
            "liquefied_breach_source_contract_ready": liquefied_breach.get("summary", {}).get(
                "liquefied_breach_source_contract_ready"
            ),
            "liquefied_breach_source_contract_case_count": liquefied_breach.get("summary", {}).get("case_count"),
            "liquefied_breach_source_contract_fluids": liquefied_breach.get("summary", {}).get("fluids"),
            "liquefied_breach_source_contract_species": liquefied_breach.get("summary", {}).get("species"),
            "liquefied_breach_source_contract_accepts_screening_breach_inputs": liquefied_breach.get(
                "summary", {}
            ).get("contract_accepts_screening_breach_inputs"),
            "liquefied_breach_source_contract_generates_external_gas_source": liquefied_breach.get(
                "summary", {}
            ).get("generates_external_gas_source_schedule"),
            "liquefied_breach_source_contract_max_gas_mass_relative_error": liquefied_breach.get("summary", {}).get(
                "max_gas_mass_relative_error"
            ),
            "liquefied_breach_source_contract_production_phase_change_claim_allowed": liquefied_breach.get(
                "summary", {}
            ).get("production_phase_change_claim_allowed"),
            "liquefied_breach_preset_templates_status": liquefied_breach_presets.get("status"),
            "liquefied_breach_preset_templates_ready": liquefied_breach_presets.get("summary", {}).get(
                "liquefied_breach_preset_templates_ready"
            ),
            "liquefied_breach_preset_templates_editable_json_presets": liquefied_breach_presets.get(
                "summary", {}
            ).get("editable_json_presets"),
            "liquefied_breach_preset_templates_generates_cfd_source_csv": liquefied_breach_presets.get(
                "summary", {}
            ).get("generates_cfd_source_csv"),
            "liquefied_breach_preset_templates_production_phase_change_claim_allowed": liquefied_breach_presets.get(
                "summary", {}
            ).get("production_phase_change_claim_allowed"),
            "multifuel_liquefied_user_answer_status": multifuel_liquefied_answer.get("status"),
            "multifuel_liquefied_user_answer_ready": multifuel_liquefied_answer.get("summary", {}).get(
                "operator_answer_ready"
            ),
            "multifuel_liquefied_gas_phase_non_h2_ready": multifuel_liquefied_answer.get("summary", {}).get(
                "gas_phase_non_h2_ready"
            ),
            "multifuel_liquefied_breach_external_source_ready": multifuel_liquefied_answer.get("summary", {}).get(
                "liquefied_breach_external_source_ready"
            ),
            "multifuel_liquefied_internal_phase_change_cfd_ready": multifuel_liquefied_answer.get(
                "summary", {}
            ).get("internal_liquid_phase_change_cfd_ready"),
            "liquefied_phase_change_overclaim_guard_status": liquefied_phase_change_guard.get("status"),
            "liquefied_phase_change_overclaim_guard_ready": liquefied_phase_change_guard.get(
                "summary", {}
            ).get("phase_change_overclaim_guard_ready"),
            "liquefied_phase_change_external_vaporization_bridge_ready": liquefied_phase_change_guard.get(
                "summary", {}
            ).get("external_vaporization_bridge_ready"),
            "liquefied_phase_change_screening_source_ready": liquefied_phase_change_guard.get(
                "summary", {}
            ).get("liquefied_release_screening_source_ready"),
            "liquefied_phase_change_cuda_runtime_ready": liquefied_phase_change_guard.get("summary", {}).get(
                "liquefied_release_cuda_runtime_ready"
            ),
            "liquefied_phase_change_production_claim_allowed": liquefied_phase_change_guard.get(
                "summary", {}
            ).get("production_phase_change_claim_allowed"),
            "liquefied_phase_change_cfd_solves_liquid_phase_change": liquefied_phase_change_guard.get(
                "summary", {}
            ).get("cfd_solves_liquid_phase_change"),
            "liquefied_phase_change_cfd_solves_pool_spread_evaporation": liquefied_phase_change_guard.get(
                "summary", {}
            ).get("cfd_solves_pool_spread_evaporation"),
            "liquefied_phase_change_cfd_solves_flashing_discharge": liquefied_phase_change_guard.get(
                "summary", {}
            ).get("cfd_solves_flashing_discharge"),
            "strict_fire_calibration_status": strict_fire.get("status"),
            "strict_fire_calibration_blocker_cleared": strict_fire.get("summary", {}).get(
                "strict_fire_calibration_blocker_cleared"
            ),
            "strict_fire_exp002_pressure_cfd_proxy_cpu_gpu_parity_passed": strict_fire.get("summary", {}).get(
                "exp002_pressure_cfd_proxy_cpu_gpu_parity_passed"
            ),
            "strict_fire_plotfile_sensor_sampling_contract_ready": strict_fire.get("summary", {}).get(
                "plotfile_sensor_sampling_contract_ready"
            ),
            "strict_fire_mdpi_radiation_integrated_cfd_proxy_extracted": strict_fire.get("summary", {}).get(
                "mdpi_radiation_integrated_cfd_proxy_extracted"
            ),
            "h2_fire_calibration_residual_budget_status": fire_residual.get("status"),
            "h2_fire_calibration_residual_budget_ready": fire_residual.get("summary", {}).get(
                "fire_calibration_residual_budget_ready"
            ),
            "h2_fire_calibration_residual_budget_clears_blocker": fire_residual.get("summary", {}).get(
                "residual_budget_clears_strict_blocker"
            ),
            "h2_fire_calibration_residual_budget_production_claim_allowed": fire_residual.get(
                "summary", {}
            ).get("production_fire_calibration_claim_allowed"),
            "strict_external_artifact_cn_handoff_status": cn_handoff.get("status"),
            "strict_external_artifact_cn_handoff_ready": cn_handoff.get("summary", {}).get(
                "strict_external_artifact_cn_handoff_ready"
            ),
            "strict_external_artifact_cn_handoff_required_file_count": cn_handoff.get("summary", {}).get(
                "required_file_count"
            ),
            "strict_external_artifact_cn_handoff_missing_file_count": cn_handoff.get("summary", {}).get(
                "missing_file_count"
            ),
            "strict_external_source_status": strict_external.get("status"),
            "strict_external_plume_blocker_cleared": strict_external.get("summary", {}).get(
                "strict_external_plume_blocker_cleared"
            ),
            "strict_external_dataverse_agreement_sensor_count": strict_external.get("summary", {}).get(
                "dataverse_agreement_sensor_count"
            ),
            "strict_external_dataverse_agreement_ready_for_cfd_scoring": strict_external.get("summary", {}).get(
                "dataverse_agreement_ready_for_cfd_scoring"
            ),
            "strict_external_dataverse_geometry_ready_for_full_mesh_parity": strict_external.get("summary", {}).get(
                "dataverse_geometry_ready_for_full_mesh_parity"
            ),
            "strict_external_dataverse_amr_current_single_level": strict_external.get("summary", {}).get(
                "dataverse_amr_source_projection_current_single_level"
            ),
            "strict_external_dataverse_amr_lacks_level_aware_mask": strict_external.get("summary", {}).get(
                "dataverse_amr_source_projection_lacks_level_aware_mask"
            ),
            "strict_external_dataverse_amr_finest_available_level_only": strict_external.get("summary", {}).get(
                "dataverse_amr_source_projection_finest_available_level_only"
            ),
            "dataverse_amr_source_projection_implementation_status": amr_source_projection.get("status"),
            "dataverse_amr_source_projection_mpi_cuda_linked_executable": amr_source_projection.get(
                "summary", {}
            ).get("mpi_cuda_linked_executable"),
            "dataverse_amr_source_projection_mpi_cuda_reproducible_build_entrypoint_ready": (
                amr_source_projection.get("summary", {}).get("mpi_cuda_reproducible_build_entrypoint_ready")
            ),
            "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_cuda_12_6": (
                amr_source_projection.get("summary", {}).get("mpi_cuda_reproducible_build_uses_cuda_12_6")
            ),
            "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_local_sundials_cuda": (
                amr_source_projection.get("summary", {}).get(
                    "mpi_cuda_reproducible_build_uses_local_sundials_cuda"
                )
            ),
            "dataverse_long_window_reconciliation_status": long_window.get("status"),
            "dataverse_existing_120s_reaches_peak_interval": long_window.get("summary", {}).get(
                "existing_120s_window_reaches_experimental_peak_interval"
            ),
            "dataverse_existing_120s_all_sensors_passed": long_window.get("summary", {}).get(
                "existing_120s_all_sensors_passed"
            ),
            "dataverse_current_refined_source_time_end_s": long_window.get("summary", {}).get(
                "current_refined_source_time_end_s"
            ),
            "dataverse_current_refined_source_steps_to_113s": long_window.get("summary", {}).get(
                "steps_to_113s_at_current_refined_dt"
            ),
            "strict_real_cad_status": strict_real_cad.get("status"),
            "strict_real_cad_blocker_cleared": strict_real_cad.get("summary", {}).get(
                "strict_real_cad_blocker_cleared"
            ),
            "strict_real_cad_handoff_contract_ready": strict_real_cad.get("summary", {}).get(
                "handoff_contract_ready"
            ),
            "strict_real_cad_source_cad_file_count": strict_real_cad.get("summary", {}).get(
                "source_cad_file_count"
            ),
            "strict_real_cad_cleaned_geometry_file_count": strict_real_cad.get("summary", {}).get(
                "cleaned_geometry_file_count"
            ),
            "real_cad_negative_selftest_status": real_cad_negative.get("status"),
            "real_cad_negative_selftest_rejected_count": real_cad_negative.get("summary", {}).get(
                "negative_rejected_count"
            ),
            "real_cad_negative_selftest_expected_fragment_seen_count": real_cad_negative.get("summary", {}).get(
                "expected_fragment_seen_count"
            ),
            "release_candidate_handoff_status": release_candidate.get("status"),
            "release_candidate_handoff_ready": release_candidate.get("summary", {}).get(
                "release_candidate_handoff_ready"
            ),
            "release_candidate_current_scope_ready": release_candidate.get("summary", {}).get("current_scope_ready"),
            "release_candidate_can_be_used_for_current_priority_scope": release_candidate.get("summary", {}).get(
                "release_candidate_can_be_used_for_current_priority_scope"
            ),
            "release_candidate_is_full_strict_master_plan_completion": release_candidate.get("summary", {}).get(
                "release_candidate_is_full_strict_master_plan_completion"
            ),
            "release_candidate_open_strict_blocker_count": release_candidate.get("summary", {}).get(
                "open_strict_blocker_count"
            ),
            "strict_blocker_status": strict.get("status"),
            "strict_blocker_set_ok": blocker_set_ok,
            "strict_blockers_listed_in_runbook": required_blockers_present,
        },
        "findings": {
            "missing_commands": missing_commands,
            "missing_readme_snippets": missing_readme_snippets,
            "missing_tools": missing_tools,
            "missing_report_paths": missing_report_paths,
            "missing_reports": missing_reports,
        },
        "evidence_files": [
            evidence_entry("readme_current_status", README),
            evidence_entry("current_scope_operator_runbook", RUNBOOK),
            evidence_entry("current_parallel_capability_matrix_report", PARALLEL_CAPABILITY),
            evidence_entry("master_plan_strict_blocker_matrix_report", STRICT_BLOCKER),
            evidence_entry("engineering_multi_fuel_capability_boundary_report", MULTI_FUEL_CAPABILITY),
            evidence_entry("engineering_multi_fuel_operator_runbook_report", MULTI_FUEL_OPERATOR_RUNBOOK),
            evidence_entry("engineering_multi_fuel_template_catalog_report", MULTI_FUEL_TEMPLATE_CATALOG),
            evidence_entry(
                "engineering_liquefied_release_vaporization_source_model_cuda_smoke_report",
                LIQUEFIED_SOURCE_MODEL_CUDA_SMOKE,
            ),
            evidence_entry("engineering_liquefied_release_source_balance_report", LIQUEFIED_SOURCE_BALANCE),
            evidence_entry(
                "engineering_liquefied_release_source_balance_negative_selftest_report",
                LIQUEFIED_SOURCE_BALANCE_NEGATIVE,
            ),
            evidence_entry(
                "engineering_liquefied_release_thermal_plausibility_report",
                LIQUEFIED_THERMAL_PLAUSIBILITY,
            ),
            evidence_entry(
                "engineering_liquefied_phase_change_overclaim_guard_report",
                LIQUEFIED_PHASE_CHANGE_OVERCLAIM_GUARD,
            ),
            evidence_entry(
                "engineering_multifuel_liquefied_user_answer_report",
                MULTIFUEL_LIQUEFIED_USER_ANSWER,
            ),
            evidence_entry("current_scope_release_candidate_handoff_report", RELEASE_CANDIDATE_HANDOFF),
            evidence_entry("master_plan_strict_fire_calibration_update_report", STRICT_FIRE_CALIBRATION),
            evidence_entry("h2_fire_overpressure_reduced_exp002_report", EXP002_OVERPRESSURE_REDUCED),
            evidence_entry("h2_fire_exp002_pressure_cfd_proxy_report", EXP002_PRESSURE_CFD_PROXY),
            evidence_entry("h2_fire_plotfile_sensor_sampling_contract_report", PLOTFILE_SENSOR_SAMPLING),
            evidence_entry(
                "h2_fire_plotfile_sensor_sampling_negative_selftest_report",
                PLOTFILE_SENSOR_SAMPLING_NEGATIVE,
            ),
            evidence_entry("h2_fire_mdpi_radiation_integrated_cfd_proxy_report", MDPI_RADIATION_INTEGRATED_PROXY),
            evidence_entry("h2_fire_calibration_residual_budget_report", H2_FIRE_CALIBRATION_RESIDUAL_BUDGET),
            evidence_entry("strict_external_artifact_cn_handoff_report", STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF),
            evidence_entry("master_plan_strict_external_source_update_report", STRICT_EXTERNAL_SOURCE),
            evidence_entry(
                "dataverse_open_channel_amr_source_projection_implementation_report",
                DATAVERSE_AMR_SOURCE_PROJECTION_IMPLEMENTATION,
            ),
            evidence_entry(
                "dataverse_open_channel_long_window_reconciliation_report",
                DATAVERSE_LONG_WINDOW_RECONCILIATION,
            ),
            evidence_entry("master_plan_strict_real_cad_update_report", STRICT_REAL_CAD),
            evidence_entry("engineering_h2_real_cad_negative_selftest_report", REAL_CAD_NEGATIVE_SELFTEST),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("operator_runbook_ready") is True, "operator runbook is not ready")
    require(summary.get("missing_readme_snippet_count") == 0, "README is missing current-status snippets")
    require(summary.get("missing_command_count") == 0, "runbook is missing required commands")
    require(summary.get("missing_tool_count") == 0, "runbook references missing tools")
    require(summary.get("missing_report_path_count") == 0, "runbook is missing required report paths")
    require(summary.get("missing_report_count") == 0, "required reports are missing")
    require(summary.get("final_readiness_status") == "PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS", "final readiness is not passing")
    require(summary.get("master_current_scope_status") == "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION", "master current-scope is not passing")
    require(summary.get("parallel_capability_status") == "PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX", "parallel capability is not passing")
    require(
        summary.get("multi_fuel_capability_status") == "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY",
        "multi-fuel capability boundary is not passing",
    )
    require(summary.get("multi_fuel_prevents_overclaim") is True, "multi-fuel overclaim guard is not active")
    require(
        summary.get("multi_fuel_liquefied_gas_phase_change_ready") is False,
        "liquefied phase-change boundary changed unexpectedly",
    )
    require(
        summary.get("multi_fuel_operator_runbook_status") == "PASS-ENGINEERING-MULTI-FUEL-OPERATOR-RUNBOOK",
        "multi-fuel operator runbook is not passing",
    )
    require(summary.get("multi_fuel_operator_runbook_ready") is True, "multi-fuel operator runbook is not ready")
    require(
        summary.get("multi_fuel_operator_runbook_missing_snippet_count") == 0,
        "multi-fuel operator runbook is missing required snippets",
    )
    require(
        summary.get("multi_fuel_template_catalog_status") == "PASS-ENGINEERING-MULTI-FUEL-TEMPLATE-CATALOG",
        "multi-fuel template catalog is not passing",
    )
    require(summary.get("multi_fuel_template_catalog_ready") is True, "multi-fuel template catalog is not ready")
    require(summary.get("multi_fuel_template_catalog_template_count") == 5, "unexpected multi-fuel template count")
    require(
        summary.get("multi_fuel_template_catalog_fuel_species_seen") == ["C3H8", "CH4", "H2"],
        "multi-fuel template species set changed",
    )
    require(
        summary.get("multi_fuel_template_catalog_cfd_internal_liquid_phase_change_claim_allowed") is False,
        "multi-fuel template catalog overclaimed liquid phase-change CFD",
    )
    require(
        summary.get("liquefied_source_model_cuda_smoke_status")
        == "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE",
        "liquefied source-model CUDA smoke is not passing",
    )
    require(
        summary.get("liquefied_source_model_cuda_smoke_ready") is True,
        "liquefied source-model CUDA smoke is not ready",
    )
    require(
        summary.get("liquefied_source_balance_status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE",
        "liquefied source balance is not passing",
    )
    require(summary.get("liquefied_source_balance_ready") is True, "liquefied source balance is not ready")
    require(
        summary.get("liquefied_source_balance_mapping_schedule_matches_csv") is True,
        "liquefied source balance mapping does not match CSV",
    )
    require(
        summary.get("liquefied_source_balance_negative_status")
        == "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE-NEGATIVE-SELFTEST",
        "liquefied source balance negative selftest is not passing",
    )
    require(
        summary.get("liquefied_source_balance_negative_rejected_count") == 5,
        "liquefied source balance did not reject all negative cases",
    )
    require(
        summary.get("liquefied_source_balance_negative_expected_fragment_seen_count") == 5,
        "liquefied source balance negative selftest diagnostics changed",
    )
    require(
        summary.get("liquefied_source_balance_guards_phase_change_overclaim") is True,
        "liquefied source balance phase-change overclaim guard is not active",
    )
    require(
        summary.get("liquefied_thermal_plausibility_status")
        == "PASS-ENGINEERING-LIQUEFIED-RELEASE-THERMAL-PLAUSIBILITY",
        "liquefied thermal plausibility is not passing",
    )
    require(summary.get("liquefied_thermal_plausibility_ready") is True, "liquefied thermal plausibility is not ready")
    require(
        summary.get("liquefied_thermal_vaporized_fraction_formula_ok") is True,
        "liquefied vaporized fraction formula check is not passing",
    )
    require(summary.get("liquefied_thermal_heat_loads_positive") is True, "liquefied heat-load check is not passing")
    require(
        summary.get("liquefied_thermal_production_phase_change_claim_allowed") is False,
        "liquefied thermal report overclaimed production phase-change",
    )
    require(
        summary.get("liquefied_thermal_cfd_solves_liquid_phase_change") is False,
        "liquefied thermal report overclaimed liquid phase-change CFD",
    )
    require(
        summary.get("liquefied_breach_source_contract_status")
        == "PASS-ENGINEERING-LIQUEFIED-BREACH-SOURCE-CONTRACT",
        "liquefied breach source contract is not passing",
    )
    require(
        summary.get("liquefied_breach_source_contract_ready") is True,
        "liquefied breach source contract is not ready",
    )
    require(summary.get("liquefied_breach_source_contract_case_count") == 2, "unexpected breach source case count")
    require(
        summary.get("liquefied_breach_source_contract_fluids") == ["LNG_CH4", "LPG_C3H8"],
        "unexpected breach source fluids",
    )
    require(
        summary.get("liquefied_breach_source_contract_species") == ["C3H8", "CH4"],
        "unexpected breach source species",
    )
    require(
        summary.get("liquefied_breach_source_contract_accepts_screening_breach_inputs") is True,
        "breach source contract does not accept screening inputs",
    )
    require(
        summary.get("liquefied_breach_source_contract_generates_external_gas_source") is True,
        "breach source contract does not generate external gas source",
    )
    require(
        isinstance(summary.get("liquefied_breach_source_contract_max_gas_mass_relative_error"), (int, float))
        and summary.get("liquefied_breach_source_contract_max_gas_mass_relative_error") <= 0.20,
        "breach source contract mass error is too large",
    )
    require(
        summary.get("liquefied_breach_source_contract_production_phase_change_claim_allowed") is False,
        "breach source contract overclaimed production phase-change",
    )
    require(
        summary.get("liquefied_phase_change_overclaim_guard_status")
        == "PASS-ENGINEERING-LIQUEFIED-PHASE-CHANGE-OVERCLAIM-GUARD",
        "liquefied phase-change overclaim guard is not passing",
    )
    for key in (
        "liquefied_phase_change_overclaim_guard_ready",
        "liquefied_phase_change_external_vaporization_bridge_ready",
        "liquefied_phase_change_screening_source_ready",
        "liquefied_phase_change_cuda_runtime_ready",
    ):
        require(summary.get(key) is True, f"{key} is not ready")
    for key in (
        "liquefied_phase_change_production_claim_allowed",
        "liquefied_phase_change_cfd_solves_liquid_phase_change",
        "liquefied_phase_change_cfd_solves_pool_spread_evaporation",
        "liquefied_phase_change_cfd_solves_flashing_discharge",
    ):
        require(summary.get(key) is False, f"{key} boundary changed unexpectedly")
    require(
        summary.get("strict_fire_calibration_status")
        == "TRIAGED-MASTER-PLAN-STRICT-FIRE-CALIBRATION-PARTIAL-DATA-BRIDGED",
        "strict fire calibration update is not triaged",
    )
    require(
        summary.get("strict_fire_calibration_blocker_cleared") is False,
        "strict fire calibration blocker was overclaimed",
    )
    require(
        summary.get("strict_fire_exp002_pressure_cfd_proxy_cpu_gpu_parity_passed") is True,
        "strict fire EXP002 pressure CFD proxy CPU/GPU parity is not passing",
    )
    require(
        summary.get("strict_fire_plotfile_sensor_sampling_contract_ready") is True,
        "strict fire plotfile sensor sampling contract is not ready",
    )
    require(
        summary.get("strict_fire_mdpi_radiation_integrated_cfd_proxy_extracted") is True,
        "strict fire MDPI integrated radiation CFD proxy was not extracted",
    )
    require(
        summary.get("h2_fire_calibration_residual_budget_status")
        == "TRIAGED-H2-FIRE-CALIBRATION-RESIDUAL-BUDGET",
        "H2 fire residual budget is not triaged",
    )
    require(
        summary.get("h2_fire_calibration_residual_budget_ready") is True,
        "H2 fire residual budget is not ready",
    )
    require(
        summary.get("h2_fire_calibration_residual_budget_clears_blocker") is False,
        "H2 fire residual budget overclaimed strict blocker clearance",
    )
    require(
        summary.get("h2_fire_calibration_residual_budget_production_claim_allowed") is False,
        "H2 fire residual budget overclaimed production calibration",
    )
    require(
        summary.get("strict_external_artifact_cn_handoff_status")
        == "PASS-STRICT-EXTERNAL-ARTIFACT-CN-HANDOFF",
        "strict external artifact Chinese handoff is not passing",
    )
    require(
        summary.get("strict_external_artifact_cn_handoff_ready") is True,
        "strict external artifact Chinese handoff is not ready",
    )
    require(
        summary.get("strict_external_artifact_cn_handoff_required_file_count") == 14,
        "strict external artifact Chinese handoff required count changed",
    )
    cn_handoff_missing = summary.get("strict_external_artifact_cn_handoff_missing_file_count")
    require(
        isinstance(cn_handoff_missing, int) and 0 <= cn_handoff_missing <= 14,
        "strict external artifact Chinese handoff missing count is outside the contract range",
    )
    require(
        summary.get("strict_external_source_status")
        == "TRIAGED-MASTER-PLAN-STRICT-EXTERNAL-SOURCES-PUBLIC-DATA-INCOMPLETE",
        "strict external source update is not triaged",
    )
    require(
        summary.get("strict_external_plume_blocker_cleared") is False,
        "strict external plume blocker was overclaimed",
    )
    require(
        summary.get("strict_external_dataverse_agreement_sensor_count") == 29,
        "strict external Dataverse agreement sensor count changed",
    )
    require(
        summary.get("strict_external_dataverse_agreement_ready_for_cfd_scoring") is True,
        "strict external Dataverse agreement is not ready for CFD scoring",
    )
    require(
        summary.get("strict_external_dataverse_geometry_ready_for_full_mesh_parity") is False,
        "strict external Dataverse full mesh parity should not be claimed",
    )
    require(
        summary.get("strict_external_dataverse_amr_current_single_level") is False,
        "strict external Dataverse AMR source projection should no longer be single-level",
    )
    require(
        summary.get("strict_external_dataverse_amr_lacks_level_aware_mask") is False,
        "strict external Dataverse AMR source projection should have a level-aware mask",
    )
    require(
        summary.get("strict_external_dataverse_amr_finest_available_level_only") is True,
        "strict external Dataverse AMR finest-owner projection is not active",
    )
    require(
        summary.get("dataverse_amr_source_projection_implementation_status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-IMPLEMENTATION",
        "Dataverse AMR source projection implementation is not passing",
    )
    for key in (
        "dataverse_amr_source_projection_mpi_cuda_linked_executable",
        "dataverse_amr_source_projection_mpi_cuda_reproducible_build_entrypoint_ready",
        "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_cuda_12_6",
        "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_local_sundials_cuda",
    ):
        require(summary.get(key) is True, f"{key} is not active")
    require(
        summary.get("dataverse_long_window_reconciliation_status")
        == "TRIAGED-DATAVERSE-OPEN-CHANNEL-LONG-WINDOW-REFINED-SOURCE-GAP",
        "Dataverse long-window reconciliation is not triaged as expected",
    )
    require(
        summary.get("dataverse_existing_120s_reaches_peak_interval") is True,
        "Dataverse existing 120s run should be recorded as reaching the peak interval",
    )
    require(
        summary.get("dataverse_existing_120s_all_sensors_passed") is False,
        "Dataverse existing 120s run should not be credited as passing",
    )
    require(
        summary.get("dataverse_current_refined_source_time_end_s") == 0.005,
        "Dataverse current refined-source time window changed unexpectedly",
    )
    require(
        summary.get("dataverse_current_refined_source_steps_to_113s") >= 22000000,
        "Dataverse refined-source steps-to-113s estimate changed unexpectedly",
    )
    require(
        summary.get("strict_real_cad_status") == "TRIAGED-MASTER-PLAN-STRICT-REAL-CAD-ARTIFACTS-MISSING",
        "strict real CAD update is not triaged",
    )
    require(summary.get("strict_real_cad_blocker_cleared") is False, "strict real CAD blocker was overclaimed")
    require(
        summary.get("strict_real_cad_handoff_contract_ready") is True,
        "strict real CAD handoff contract is not ready",
    )
    require(summary.get("strict_real_cad_source_cad_file_count") == 0, "strict real CAD source file count changed")
    require(
        summary.get("strict_real_cad_cleaned_geometry_file_count") == 0,
        "strict real CAD cleaned geometry file count changed",
    )
    require(
        summary.get("real_cad_negative_selftest_status") == "PASS-H2-REAL-CAD-GUARD-NEGATIVE-SELFTEST",
        "real CAD negative selftest is not passing",
    )
    require(
        summary.get("real_cad_negative_selftest_rejected_count") == 8,
        "real CAD negative selftest did not reject all cases",
    )
    require(
        summary.get("real_cad_negative_selftest_expected_fragment_seen_count") == 8,
        "real CAD negative selftest diagnostics changed",
    )
    require(
        summary.get("multifuel_liquefied_user_answer_status")
        == "PASS-ENGINEERING-MULTIFUEL-LIQUEFIED-USER-ANSWER",
        "multifuel/liquefied user answer status is not passing",
    )
    for key in (
        "multifuel_liquefied_user_answer_ready",
        "multifuel_liquefied_gas_phase_non_h2_ready",
        "multifuel_liquefied_breach_external_source_ready",
    ):
        require(summary.get(key) is True, f"{key} is not active")
    require(
        summary.get("multifuel_liquefied_internal_phase_change_cfd_ready") is False,
        "multifuel/liquefied answer overclaimed internal phase-change CFD",
    )
    require(
        summary.get("release_candidate_handoff_status") == "PASS-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF",
        "release-candidate handoff status is not passing",
    )
    for key in (
        "release_candidate_handoff_ready",
        "release_candidate_current_scope_ready",
        "release_candidate_can_be_used_for_current_priority_scope",
    ):
        require(summary.get(key) is True, f"{key} is not active")
    require(
        summary.get("release_candidate_is_full_strict_master_plan_completion") is False,
        "release candidate overclaimed strict master-plan completion",
    )
    require(
        summary.get("release_candidate_open_strict_blocker_count") == 3,
        "unexpected release-candidate blocker count",
    )
    require(summary.get("strict_blocker_set_ok") is True, "strict blocker set changed")
    require(summary.get("strict_blockers_listed_in_runbook") is True, "strict blockers are not listed in runbook")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current-Scope Operator Runbook Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Runbook: `{summary['runbook_path']}`",
        f"- README: `{summary['readme_path']}`",
        f"- Missing README snippets: `{summary['missing_readme_snippet_count']}`",
        f"- Missing commands: `{summary['missing_command_count']}`",
        f"- Missing tools: `{summary['missing_tool_count']}`",
        f"- Missing report paths: `{summary['missing_report_path_count']}`",
        f"- Missing reports: `{summary['missing_report_count']}`",
        f"- Final readiness: `{summary['final_readiness_status']}`",
        f"- Master current-scope: `{summary['master_current_scope_status']}`",
        f"- Parallel capability: `{summary['parallel_capability_status']}`",
        f"- Multi-fuel capability: `{summary['multi_fuel_capability_status']}`",
        f"- Multi-fuel operator runbook: `{summary['multi_fuel_operator_runbook_status']}`",
        f"- Multi-fuel operator runbook ready: `{summary['multi_fuel_operator_runbook_ready']}`",
        f"- Multi-fuel template catalog: `{summary['multi_fuel_template_catalog_status']}`",
        f"- Multi-fuel template catalog ready: `{summary['multi_fuel_template_catalog_ready']}`",
        f"- Multi-fuel overclaim guard: `{summary['multi_fuel_prevents_overclaim']}`",
        f"- Liquefied phase-change ready: `{summary['multi_fuel_liquefied_gas_phase_change_ready']}`",
        f"- Liquefied source-model CUDA smoke: `{summary['liquefied_source_model_cuda_smoke_status']}`",
        f"- Liquefied source balance: `{summary['liquefied_source_balance_status']}`",
        f"- Liquefied source balance negative selftest: `{summary['liquefied_source_balance_negative_status']}`",
        f"- Liquefied source balance negative rejected: `{summary['liquefied_source_balance_negative_rejected_count']}`",
        f"- Liquefied breach source contract: `{summary['liquefied_breach_source_contract_status']}`",
        f"- Liquefied breach source contract ready: `{summary['liquefied_breach_source_contract_ready']}`",
        f"- Liquefied breach source cases: `{summary['liquefied_breach_source_contract_case_count']}`",
        f"- Multifuel/liquefied user answer: `{summary['multifuel_liquefied_user_answer_status']}`",
        f"- Multifuel/liquefied user answer ready: `{summary['multifuel_liquefied_user_answer_ready']}`",
        f"- Release-candidate handoff: `{summary['release_candidate_handoff_status']}`",
        f"- Release-candidate handoff ready: `{summary['release_candidate_handoff_ready']}`",
        f"- Release-candidate usable for current priority scope: `{summary['release_candidate_can_be_used_for_current_priority_scope']}`",
        f"- Release-candidate is full strict master-plan completion: `{summary['release_candidate_is_full_strict_master_plan_completion']}`",
        f"- Release-candidate open strict blockers: `{summary['release_candidate_open_strict_blocker_count']}`",
        f"- Dataverse AMR source projection implementation: `{summary['dataverse_amr_source_projection_implementation_status']}`",
        f"- Dataverse AMR MPI+CUDA linked executable: `{summary['dataverse_amr_source_projection_mpi_cuda_linked_executable']}`",
        f"- Dataverse AMR CUDA 12.6 reproducible build: `{summary['dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_cuda_12_6']}`",
        f"- Dataverse long-window reconciliation: `{summary['dataverse_long_window_reconciliation_status']}`",
        f"- Dataverse existing 120s reaches peak interval: `{summary['dataverse_existing_120s_reaches_peak_interval']}`",
        f"- Dataverse existing 120s all sensors passed: `{summary['dataverse_existing_120s_all_sensors_passed']}`",
        f"- Dataverse refined-source steps to 113s: `{summary['dataverse_current_refined_source_steps_to_113s']}`",
        f"- Strict blocker set ok: `{summary['strict_blocker_set_ok']}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"current_scope_operator_runbook VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_scope_operator_runbook PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
