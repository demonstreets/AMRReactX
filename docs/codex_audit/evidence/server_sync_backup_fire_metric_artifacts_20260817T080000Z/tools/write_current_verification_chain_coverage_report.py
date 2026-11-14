#!/usr/bin/env python3
"""Audit that current key reports are covered by the one-command verification chain."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-VERIFICATION-CHAIN-COVERAGE"
STATUS_NOT_READY = "NOT_READY-CURRENT-VERIFICATION-CHAIN-COVERAGE"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_verification_chain_coverage_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_verification_chain_coverage_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_verification_chain_coverage_report.md"

CHAIN = Path("tools/codex_verify_current_scope.sh")
SNAPSHOT_WRITER = Path("tools/write_current_scope_state_snapshot_report.py")

COVERAGE_RULES: dict[str, dict[str, Any]] = {
    "parallel_capability": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_parallel_capability_matrix_report.py",
            "bash tools/verify_current_parallel_capability_matrix.sh",
        ],
    },
    "scenario_readiness_matrix": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_scenario_readiness_matrix_report.py",
            "bash tools/verify_current_scenario_readiness_matrix.sh",
        ],
    },
    "engineering_multi_fuel_capability_boundary": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_multi_fuel_capability_boundary_report.py",
            "bash tools/verify_engineering_multi_fuel_capability_boundary.sh",
        ],
    },
    "engineering_liquefied_external_vaporization_contract": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_liquefied_external_vaporization_contract_report.py",
            "bash tools/verify_engineering_liquefied_external_vaporization_contract.sh",
        ],
    },
    "engineering_liquefied_release_vaporization_source_model": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_liquefied_release_vaporization_source_model_report.py",
            "bash tools/verify_engineering_liquefied_release_vaporization_source_model.sh",
        ],
    },
    "engineering_liquefied_release_vaporization_source_model_negative_selftest": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_liquefied_release_vaporization_source_model_negative_selftest_report.py",
            "bash tools/verify_engineering_liquefied_release_vaporization_source_model_negative_selftest.sh",
        ],
    },
    "engineering_liquefied_release_vaporization_source_model_cuda_smoke": {
        "mode": "direct",
        "commands": [
            "bash tools/run_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh",
            "python3 tools/write_engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.py",
            "bash tools/verify_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh",
        ],
    },
    "engineering_liquefied_release_source_balance": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_liquefied_release_source_balance_report.py",
            "bash tools/verify_engineering_liquefied_release_source_balance.sh",
        ],
    },
    "engineering_liquefied_release_source_balance_negative_selftest": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_liquefied_release_source_balance_negative_selftest_report.py",
            "bash tools/verify_engineering_liquefied_release_source_balance_negative_selftest.sh",
        ],
    },
    "engineering_liquefied_release_thermal_plausibility": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_liquefied_release_thermal_plausibility_report.py",
            "bash tools/verify_engineering_liquefied_release_thermal_plausibility.sh",
        ],
    },
    "engineering_liquefied_breach_source_contract": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_liquefied_breach_source_contract_report.py",
            "bash tools/verify_engineering_liquefied_breach_source_contract.sh",
        ],
    },
    "engineering_liquefied_breach_preset_templates": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_liquefied_breach_preset_templates_report.py",
            "bash tools/verify_engineering_liquefied_breach_preset_templates.sh",
        ],
    },
    "engineering_multifuel_liquefied_user_answer": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_multifuel_liquefied_user_answer_report.py",
            "bash tools/verify_engineering_multifuel_liquefied_user_answer.sh",
        ],
    },
    "engineering_liquefied_external_vaporization_negative_selftest": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_liquefied_external_vaporization_negative_selftest_report.py",
            "bash tools/verify_engineering_liquefied_external_vaporization_negative_selftest.sh",
        ],
    },
    "engineering_liquefied_phase_change_overclaim_guard": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_liquefied_phase_change_overclaim_guard_report.py",
            "bash tools/verify_engineering_liquefied_phase_change_overclaim_guard.sh",
        ],
    },
    "engineering_fixed_mass_flow_valve_schedule": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_fixed_mass_flow_valve_schedule_report.py",
            "bash tools/verify_engineering_fixed_mass_flow_valve_schedule.sh",
        ],
    },
    "engineering_external_vaporization_timeseries": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_external_vaporization_timeseries_report.py",
            "bash tools/verify_engineering_external_vaporization_timeseries.sh",
        ],
    },
    "engineering_external_vaporization_timeseries_cuda": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_external_vaporization_timeseries_cuda_report.py",
            "bash tools/verify_engineering_external_vaporization_timeseries_cuda.sh",
        ],
    },
    "engineering_external_vaporization_multifuel_source_matrix": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_external_vaporization_multifuel_source_matrix_report.py",
            "bash tools/verify_engineering_external_vaporization_multifuel_source_matrix.sh",
        ],
    },
    "engineering_external_vaporization_ch4_timeseries_cuda": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_external_vaporization_ch4_timeseries_cuda_report.py",
            "bash tools/verify_engineering_external_vaporization_ch4_timeseries_cuda.sh",
        ],
    },
    "engineering_external_vaporization_c3h8_timeseries_cuda": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_external_vaporization_c3h8_timeseries_cuda_report.py",
            "bash tools/verify_engineering_external_vaporization_c3h8_timeseries_cuda.sh",
        ],
    },
    "engineering_multi_fuel_operator_runbook": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_multi_fuel_operator_runbook_report.py",
            "bash tools/verify_engineering_multi_fuel_operator_runbook.sh",
        ],
    },
    "engineering_multi_fuel_template_catalog": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_multi_fuel_template_catalog_report.py",
            "bash tools/verify_engineering_multi_fuel_template_catalog.sh",
        ],
    },
    "engineering_fuel_species_guard": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_fuel_species_guard_report.py",
            "bash tools/verify_engineering_fuel_species_guard.sh",
        ],
    },
    "engineering_log_marker_compatibility": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_log_marker_compatibility_report.py",
            "bash tools/verify_engineering_log_marker_compatibility.sh",
        ],
    },
    "engineering_ch4_cold_plume_cpu_probe": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_ch4_cold_plume_cpu_probe_report.py",
            "bash tools/verify_engineering_ch4_cold_plume_cpu_probe.sh",
        ],
    },
    "engineering_ch4_pipe_rack_delayed_ignition_cuda": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_ch4_pipe_rack_delayed_ignition_cuda_report.py",
            "bash tools/verify_engineering_ch4_pipe_rack_delayed_ignition_cuda.sh",
        ],
    },
    "engineering_ch4_pipe_rack_delayed_ignition_mpi": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_ch4_pipe_rack_delayed_ignition_mpi_report.py",
            "bash tools/verify_engineering_ch4_pipe_rack_delayed_ignition_mpi.sh",
        ],
    },
    "engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_report.py",
            "bash tools/verify_engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda.sh",
        ],
    },
    "engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.py",
            "bash tools/verify_engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step.sh",
        ],
    },
    "academic_gas_detonation_single_cuda": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_academic_gas_detonation_single_cuda_report.py",
            "bash tools/verify_academic_gas_detonation_single_cuda.sh",
        ],
    },
    "operator_runbook": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_scope_operator_runbook_report.py",
            "bash tools/verify_current_scope_operator_runbook.sh",
        ],
    },
    "final_readiness": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_master_plan_final_readiness_report.py",
            "bash tools/verify_master_plan_final_readiness.sh",
        ],
    },
    "master_current_scope": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_master_plan_current_scope_verification_report.py",
            "bash tools/verify_master_plan_current_scope_verification.sh",
        ],
    },
    "strict_blocker_matrix": {
        "mode": "master_current_scope_gate",
        "commands": ["bash tools/verify_master_plan_current_scope.sh"],
    },
    "engineering_h2_real_cad_handoff_contract": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_h2_real_cad_handoff_contract_report.py",
            "bash tools/verify_engineering_h2_real_cad_handoff_contract.sh",
        ],
    },
    "h2_fire_overpressure_dataverse_metadata": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_overpressure_dataverse_metadata_report.py",
            "bash tools/verify_h2_fire_overpressure_dataverse_metadata.sh",
        ],
    },
    "h2_fire_overpressure_reduced_exp002": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_overpressure_reduced_exp002_report.py",
            "bash tools/verify_h2_fire_overpressure_reduced_exp002.sh",
        ],
    },
    "h2_fire_exp002_overpressure_calibration_table": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_exp002_overpressure_calibration_table_report.py",
            "bash tools/verify_h2_fire_exp002_overpressure_calibration_table.sh",
        ],
    },
    "h2_fire_exp002_pressure_comparison_contract": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_exp002_pressure_comparison_contract_report.py",
            "bash tools/verify_h2_fire_exp002_pressure_comparison_contract.sh",
        ],
    },
    "h2_fire_calibration_candidate_sources_20260805": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_calibration_candidate_sources_20260805_report.py",
            "bash tools/verify_h2_fire_calibration_candidate_sources_20260805.sh",
        ],
    },
    "h2_fire_mdpi_radiation_calibration_table": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_mdpi_radiation_calibration_table_report.py",
            "bash tools/verify_h2_fire_mdpi_radiation_calibration_table.sh",
        ],
    },
    "h2_fire_mdpi_radiation_comparison_contract": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_mdpi_radiation_comparison_contract_report.py",
            "bash tools/verify_h2_fire_mdpi_radiation_comparison_contract.sh",
        ],
    },
    "h2_fire_mdpi_radiation_screening_comparison": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_mdpi_radiation_screening_comparison_report.py",
            "bash tools/verify_h2_fire_mdpi_radiation_screening_comparison.sh",
        ],
    },
    "engineering_h2_pipe_rack_delayed_ignition_cuda": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_h2_pipe_rack_delayed_ignition_cuda_report.py",
            "bash tools/verify_engineering_h2_pipe_rack_delayed_ignition_cuda.sh",
        ],
    },
    "engineering_h2_pipe_rack_delayed_ignition_mpi": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_h2_pipe_rack_delayed_ignition_mpi_report.py",
            "bash tools/verify_engineering_h2_pipe_rack_delayed_ignition_mpi.sh",
        ],
    },
    "engineering_h2_pipe_rack_delayed_ignition_cross_platform": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_h2_pipe_rack_delayed_ignition_cross_platform_report.py",
            "bash tools/verify_engineering_h2_pipe_rack_delayed_ignition_cross_platform.sh",
        ],
    },
    "h2_fire_exp002_pressure_cfd_proxy": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_exp002_pressure_cfd_proxy_report.py",
            "bash tools/verify_h2_fire_exp002_pressure_cfd_proxy.sh",
        ],
    },
    "h2_fire_plotfile_sensor_sampling_contract": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_plotfile_sensor_sampling_contract_report.py",
            "bash tools/verify_h2_fire_plotfile_sensor_sampling_contract.sh",
        ],
    },
    "h2_fire_plotfile_sensor_sampling_negative_selftest": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_plotfile_sensor_sampling_negative_selftest_report.py",
            "bash tools/verify_h2_fire_plotfile_sensor_sampling_negative_selftest.sh",
        ],
    },
    "h2_fire_mdpi_radiation_cfd_proxy": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_mdpi_radiation_cfd_proxy_report.py",
            "bash tools/verify_h2_fire_mdpi_radiation_cfd_proxy.sh",
        ],
    },
    "h2_fire_mdpi_radiation_integrated_cfd_proxy": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_mdpi_radiation_integrated_cfd_proxy_report.py",
            "bash tools/verify_h2_fire_mdpi_radiation_integrated_cfd_proxy.sh",
        ],
    },
    "h2_fire_calibration_residual_budget": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_h2_fire_calibration_residual_budget_report.py",
            "bash tools/verify_h2_fire_calibration_residual_budget.sh",
        ],
    },
    "engineering_h2_fire_exp002_delayed_ignition_bridge": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_engineering_h2_fire_exp002_delayed_ignition_bridge_report.py",
            "bash tools/verify_engineering_h2_fire_exp002_delayed_ignition_bridge.sh",
        ],
    },
    "strict_unblock_runbook": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_master_plan_unblock_runbook_report.py",
            "bash tools/verify_strict_master_plan_unblock_runbook.sh",
        ],
    },
    "strict_unblock_command_inventory": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_unblock_command_inventory_report.py",
            "bash tools/verify_strict_unblock_command_inventory.sh",
        ],
    },
    "strict_artifact_template_lint": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_artifact_template_lint_report.py",
            "bash tools/verify_strict_artifact_template_lint.sh",
        ],
    },
    "strict_artifact_drop_contract_preflight": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_artifact_drop_contract_preflight_report.py",
            "bash tools/verify_strict_artifact_drop_contract_preflight.sh",
        ],
    },
    "strict_artifact_drop_contract_selftest": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_artifact_drop_contract_selftest_report.py",
            "bash tools/verify_strict_artifact_drop_contract_selftest.sh",
        ],
    },
    "master_plan_completion_audit": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_master_plan_completion_audit_report.py",
            "bash tools/verify_master_plan_completion_audit.sh",
        ],
    },
    "current_status_cli": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_status_cli_report.py",
            "bash tools/verify_current_status_cli.sh",
        ],
    },
    "current_worktree_hygiene": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_worktree_hygiene_report.py",
            "bash tools/verify_current_worktree_hygiene.sh",
        ],
    },
    "current_worktree_source_ledger": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_worktree_source_ledger_report.py",
            "bash tools/verify_current_worktree_source_ledger.sh",
        ],
    },
    "current_case_output_cleanup_manifest": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_case_output_cleanup_manifest_report.py",
            "bash tools/verify_current_case_output_cleanup_manifest.sh",
        ],
    },
    "current_disk_usage_manifest": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_disk_usage_manifest_report.py",
            "bash tools/verify_current_disk_usage_manifest.sh",
        ],
    },
    "current_disk_cleanup_plan": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_disk_cleanup_plan_report.py",
            "bash tools/verify_current_disk_cleanup_plan.sh",
        ],
    },
    "current_operator_command_inventory": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_operator_command_inventory_report.py",
            "bash tools/verify_current_operator_command_inventory.sh",
        ],
    },
    "current_scope_release_candidate_handoff": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_scope_release_candidate_handoff_report.py",
            "bash tools/verify_current_scope_release_candidate_handoff.sh",
        ],
    },
    "project_closeout_forecast": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_project_closeout_forecast_report.py",
            "bash tools/verify_project_closeout_forecast.sh",
        ],
    },
    "strict_master_plan_completion_gate": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_master_plan_completion_gate_report.py",
            "bash tools/verify_strict_master_plan_completion_gate.sh",
        ],
    },
    "strict_external_artifact_drop_index": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_external_artifact_drop_index_report.py",
            "bash tools/verify_strict_external_artifact_drop_index.sh",
        ],
    },
    "strict_external_artifact_drop_index_cli": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_external_artifact_drop_index_cli_report.py",
            "bash tools/verify_strict_external_artifact_drop_index_cli.sh",
        ],
    },
    "strict_external_artifact_drop_checklist": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_external_artifact_drop_checklist_report.py",
            "bash tools/verify_strict_external_artifact_drop_checklist.sh",
        ],
    },
    "strict_fire_calibration_source_registry_artifact": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_fire_calibration_source_registry_artifact_report.py",
            "bash tools/verify_strict_fire_calibration_source_registry_artifact.sh",
        ],
    },
    "strict_external_evidence_receiving_pack": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_external_evidence_receiving_pack_report.py",
            "bash tools/verify_strict_external_evidence_receiving_pack.sh",
        ],
    },
    "strict_external_artifact_template_clone_selftest": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_external_artifact_template_clone_selftest_report.py",
            "bash tools/verify_strict_external_artifact_template_clone_selftest.sh",
        ],
    },
    "strict_external_artifact_cross_benchmark_alias_selftest": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_external_artifact_cross_benchmark_alias_selftest_report.py",
            "bash tools/verify_strict_external_artifact_cross_benchmark_alias_selftest.sh",
        ],
    },
    "strict_external_plume_source_separation_audit": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_external_plume_source_separation_audit_report.py",
            "bash tools/verify_strict_external_plume_source_separation_audit.sh",
        ],
    },
    "strict_external_artifact_progress_selftest": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_external_artifact_progress_selftest_report.py",
            "bash tools/verify_strict_external_artifact_progress_selftest.sh",
        ],
    },
    "strict_master_plan_closeout_action_pack": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_strict_master_plan_closeout_action_pack_report.py",
            "bash tools/verify_strict_master_plan_closeout_action_pack.sh",
        ],
    },
    "project_closeout_acceptance_gate": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_project_closeout_acceptance_gate_report.py",
            "bash tools/verify_project_closeout_acceptance_gate.sh",
        ],
    },
    "current_scope_delivery_package": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_scope_delivery_package_report.py",
            "bash tools/verify_current_scope_delivery_package.sh",
        ],
    },
    "current_scope_final_handoff_note": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_scope_final_handoff_note_report.py",
            "bash tools/verify_current_scope_final_handoff_note.sh",
        ],
    },
    "current_operator_quickstart_smoke": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_operator_quickstart_smoke_report.py",
            "bash tools/verify_current_operator_quickstart_smoke.sh",
        ],
    },
    "current_phase_closure_certificate": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_phase_closure_certificate_report.py",
            "bash tools/verify_current_phase_closure_certificate.sh",
        ],
    },
    "current_phase_release_manifest": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_phase_release_manifest_report.py",
            "bash tools/verify_current_phase_release_manifest.sh",
        ],
    },
    "current_scope_release_refresh_entrypoint": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_scope_release_refresh_entrypoint_report.py",
            "bash tools/verify_current_scope_release_refresh_entrypoint.sh",
        ],
    },
    "current_verification_chain_coverage": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_current_verification_chain_coverage_report.py",
            "bash tools/verify_current_verification_chain_coverage.sh",
        ],
    },
    "dataverse_open_channel_reference_package": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_dataverse_open_channel_reference_package_report.py",
            "bash tools/verify_dataverse_open_channel_reference_package.sh",
        ],
    },
    "dataverse_open_channel_agreement_contract": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_dataverse_open_channel_agreement_contract_report.py",
            "bash tools/verify_dataverse_open_channel_agreement_contract.sh",
        ],
    },
    "dataverse_open_channel_cfd_scout": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_dataverse_open_channel_cfd_scout_report.py",
            "bash tools/verify_dataverse_open_channel_cfd_scout.sh",
        ],
    },
    "dataverse_open_channel_cfd_agreement_attempt": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_dataverse_open_channel_cfd_agreement_attempt_report.py",
            "bash tools/verify_dataverse_open_channel_cfd_agreement_attempt.sh",
        ],
    },
    "dataverse_open_channel_cfd_45s_agreement_attempt": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_cfd_45s_agreement_attempt.sh",
        ],
    },
    "dataverse_open_channel_cfd_120s_agreement_attempt": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_cfd_120s_agreement_attempt.sh",
        ],
    },
    "dataverse_open_channel_120s_calibration_diagnosis": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_120s_calibration_diagnosis.sh",
        ],
    },
    "dataverse_open_channel_45s_calibration_r005_z08": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_45s_calibration_r005_z08.sh",
        ],
    },
    "dataverse_open_channel_45s_calibration_sweep": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_45s_calibration_sweep.sh",
        ],
    },
    "dataverse_open_channel_physics_alignment": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_physics_alignment.sh",
        ],
    },
    "dataverse_open_channel_orifice_velocity_scout": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_orifice_velocity_scout.sh",
        ],
    },
    "dataverse_open_channel_open_boundary_scout": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_open_boundary_scout.sh",
        ],
    },
    "dataverse_open_channel_open_boundary_orifice_extended_01s": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_open_boundary_orifice_extended_01s.sh",
        ],
    },
    "dataverse_open_channel_open_boundary_orifice_extended_1s": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_open_boundary_orifice_extended_1s.sh",
        ],
    },
    "dataverse_open_channel_open_boundary_orifice_extended_2s": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_open_boundary_orifice_extended_2s.sh",
        ],
    },
    "dataverse_refined_source_projection_probe": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_refined_source_projection_probe.sh",
        ],
    },
    "dataverse_full_channel_refined_source_dx025_probe": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_full_channel_refined_source_dx025_probe.sh",
        ],
    },
    "dataverse_full_channel_refined_source_dx025_500step": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_full_channel_refined_source_dx025_500step.sh",
        ],
    },
    "dataverse_full_channel_refined_source_dx025_1000step_dt5em6": {
        "mode": "direct",
        "commands": [
            "bash tools/verify_dataverse_open_channel_full_channel_refined_source_dx025_1000step_dt5em6.sh",
        ],
    },
    "dataverse_open_channel_amr_source_projection_contract": {
        "mode": "direct",
        "commands": [
            "python3 tools/write_dataverse_open_channel_amr_source_projection_contract_report.py",
            "bash tools/verify_dataverse_open_channel_amr_source_projection_contract.sh",
        ],
    },
    "dataverse_open_channel_amr_source_projection_implementation": {
        "mode": "direct",
        "commands": [
            "bash tools/codex_build_h2_leak_mpi_cuda_repro.sh",
            "python3 tools/write_dataverse_open_channel_amr_source_projection_implementation_report.py",
            "bash tools/verify_dataverse_open_channel_amr_source_projection_implementation.sh",
        ],
    },
}


class CoverageError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CoverageError(message)


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
        raise CoverageError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CoverageError(f"invalid JSON evidence {path}: {exc}") from exc
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


def load_snapshot_module() -> Any:
    require(SNAPSHOT_WRITER.is_file(), f"missing snapshot writer: {SNAPSHOT_WRITER}")
    spec = importlib.util.spec_from_file_location("current_scope_state_snapshot", SNAPSHOT_WRITER)
    require(spec is not None and spec.loader is not None, "unable to load snapshot writer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def command_positions(chain_text: str, command: str) -> list[int]:
    pattern = re.escape(command)
    return [match.start() for match in re.finditer(pattern, chain_text)]


def build_report() -> dict[str, Any]:
    require(CHAIN.is_file(), f"missing verification chain: {CHAIN}")
    chain_text = CHAIN.read_text(encoding="utf-8")
    snapshot = load_snapshot_module()
    key_reports: dict[str, tuple[Path, str]] = snapshot.KEY_REPORTS
    key_report_labels = set(key_reports)
    rules = set(COVERAGE_RULES)
    missing_rules = sorted(key_report_labels - rules)
    stale_rules = sorted(rules - key_report_labels)

    snapshot_command = "python3 tools/write_current_scope_state_snapshot_report.py"
    snapshot_positions = command_positions(chain_text, snapshot_command)
    snapshot_position = snapshot_positions[-1] if snapshot_positions else None

    entries: list[dict[str, Any]] = []
    for label in sorted(key_report_labels):
        rule = COVERAGE_RULES.get(label, {"mode": "missing_rule", "commands": []})
        command_entries = []
        for command in rule["commands"]:
            positions = command_positions(chain_text, command)
            command_entries.append(
                {
                    "command": command,
                    "present": bool(positions),
                    "positions": positions,
                    "before_snapshot": bool(positions and snapshot_position is not None and min(positions) < snapshot_position),
                }
            )
        covered = bool(command_entries) and all(item["present"] and item["before_snapshot"] for item in command_entries)
        entries.append(
            {
                "label": label,
                "expected_status": key_reports[label][1],
                "report_path": str(key_reports[label][0]),
                "mode": rule["mode"],
                "covered_before_snapshot": covered,
                "commands": command_entries,
            }
        )

    uncovered = [entry for entry in entries if not entry["covered_before_snapshot"]]
    ready = not missing_rules and not stale_rules and not uncovered and snapshot_position is not None
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "current_verification_chain_coverage_ready": ready,
            "key_report_count": len(key_reports),
            "coverage_rule_count": len(COVERAGE_RULES),
            "missing_rule_count": len(missing_rules),
            "stale_rule_count": len(stale_rules),
            "uncovered_key_report_count": len(uncovered),
            "snapshot_command_present": snapshot_position is not None,
            "snapshot_command_count": len(snapshot_positions),
        },
        "key_report_coverage": entries,
        "missing_rules": missing_rules,
        "stale_rules": stale_rules,
        "uncovered_key_reports": uncovered,
        "evidence_files": [
            evidence_entry("codex_verify_current_scope", CHAIN),
            evidence_entry("state_snapshot_writer", SNAPSHOT_WRITER),
        ],
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_verification_chain_coverage_ready") is True, "verification chain coverage is not ready")
    require(summary.get("key_report_count", 0) >= 18, "unexpectedly low key report count")
    require(summary.get("missing_rule_count") == 0, "missing coverage rules")
    require(summary.get("stale_rule_count") == 0, "stale coverage rules")
    require(summary.get("uncovered_key_report_count") == 0, "one or more key reports are not covered before snapshot")
    require(summary.get("snapshot_command_present") is True, "snapshot command missing")
    for entry in data.get("key_report_coverage", []):
        require(isinstance(entry, dict), "invalid coverage entry")
        require(entry.get("covered_before_snapshot") is True, f"key report not covered: {entry.get('label')}")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(entry.get("sha256") == sha256_file(path), f"hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current Verification Chain Coverage",
        "",
        f"- Status: `{report['status']}`",
        f"- Key reports: `{summary['key_report_count']}`",
        f"- Missing rules: `{summary['missing_rule_count']}`",
        f"- Stale rules: `{summary['stale_rule_count']}`",
        f"- Uncovered key reports: `{summary['uncovered_key_report_count']}`",
        "",
        "## Coverage",
        "",
    ]
    for entry in report["key_report_coverage"]:
        lines.append(f"- `{entry['label']}` mode=`{entry['mode']}` covered=`{entry['covered_before_snapshot']}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--verify-json")
    args = parser.parse_args()

    if args.verify_json:
        data = load_json(Path(args.verify_json))
        validate_report(data, verify_hashes=True)
        print(f"current_verification_chain_coverage VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_verification_chain_coverage PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
