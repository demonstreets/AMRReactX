#!/usr/bin/env python3
"""Write/verify the current-scope state snapshot report."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-SCOPE-STATE-SNAPSHOT"
STATUS_NOT_READY = "NOT_READY-CURRENT-SCOPE-STATE-SNAPSHOT"
VOLATILE_HASH_LABELS = {
    "current_scope_delivery_package",
    "current_phase_release_manifest",
    "current_status_cli",
    "current_verification_chain_coverage",
}

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_scope_state_snapshot_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_scope_state_snapshot_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_scope_state_snapshot_report.md"

KEY_REPORTS: dict[str, tuple[Path, str]] = {
    "parallel_capability": (
        Path("docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/current_parallel_capability_matrix_report.json"),
        "PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX",
    ),
    "scenario_readiness_matrix": (
        Path("docs/codex_audit/evidence/current_scenario_readiness_matrix_20260805/current_scenario_readiness_matrix_report.json"),
        "PASS-CURRENT-SCENARIO-READINESS-MATRIX",
    ),
    "engineering_multi_fuel_capability_boundary": (
        Path("docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/engineering_multi_fuel_capability_boundary_report.json"),
        "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY",
    ),
    "engineering_liquefied_external_vaporization_contract": (
        Path("docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/engineering_liquefied_external_vaporization_contract_report.json"),
        "PASS-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-CONTRACT",
    ),
    "engineering_liquefied_release_vaporization_source_model": (
        Path("docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/engineering_liquefied_release_vaporization_source_model_report.json"),
        "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL",
    ),
    "engineering_liquefied_release_vaporization_source_model_negative_selftest": (
        Path("docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_negative_selftest_20260807/engineering_liquefied_release_vaporization_source_model_negative_selftest_report.json"),
        "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-NEGATIVE-SELFTEST",
    ),
    "engineering_liquefied_release_vaporization_source_model_cuda_smoke": (
        Path("docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_cuda_smoke_20260807/engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.json"),
        "PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE",
    ),
    "engineering_liquefied_release_source_balance": (
        Path("docs/codex_audit/evidence/engineering_liquefied_release_source_balance_20260807/engineering_liquefied_release_source_balance_report.json"),
        "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE",
    ),
    "engineering_liquefied_release_source_balance_negative_selftest": (
        Path("docs/codex_audit/evidence/engineering_liquefied_release_source_balance_negative_selftest_20260807/engineering_liquefied_release_source_balance_negative_selftest_report.json"),
        "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE-NEGATIVE-SELFTEST",
    ),
    "engineering_liquefied_release_thermal_plausibility": (
        Path("docs/codex_audit/evidence/engineering_liquefied_release_thermal_plausibility_20260811/engineering_liquefied_release_thermal_plausibility_report.json"),
        "PASS-ENGINEERING-LIQUEFIED-RELEASE-THERMAL-PLAUSIBILITY",
    ),
    "engineering_liquefied_breach_source_contract": (
        Path("docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/engineering_liquefied_breach_source_contract_report.json"),
        "PASS-ENGINEERING-LIQUEFIED-BREACH-SOURCE-CONTRACT",
    ),
    "engineering_liquefied_breach_preset_templates": (
        Path("docs/codex_audit/evidence/engineering_liquefied_breach_preset_templates_20260811/engineering_liquefied_breach_preset_templates_report.json"),
        "PASS-ENGINEERING-LIQUEFIED-BREACH-PRESET-TEMPLATES",
    ),
    "engineering_multifuel_liquefied_user_answer": (
        Path("docs/codex_audit/evidence/engineering_multifuel_liquefied_user_answer_20260811/engineering_multifuel_liquefied_user_answer_report.json"),
        "PASS-ENGINEERING-MULTIFUEL-LIQUEFIED-USER-ANSWER",
    ),
    "current_scope_release_candidate_handoff": (
        Path("docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812/current_scope_release_candidate_handoff_report.json"),
        "PASS-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF",
    ),
    "project_closeout_forecast": (
        Path("docs/codex_audit/evidence/project_closeout_forecast_20260812/project_closeout_forecast_report.json"),
        "PASS-PROJECT-CLOSEOUT-FORECAST",
    ),
    "project_closeout_acceptance_gate": (
        Path("docs/codex_audit/evidence/project_closeout_acceptance_gate_20260812/project_closeout_acceptance_gate_report.json"),
        "PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE",
    ),
    "strict_master_plan_completion_gate": (
        Path("docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812/strict_master_plan_completion_gate_report.json"),
        "AWAITING-STRICT-MASTER-PLAN-COMPLETION-GATE-EXTERNAL-ARTIFACTS",
    ),
    "strict_external_artifact_drop_index": (
        Path("docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/strict_external_artifact_drop_index_report.json"),
        "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX",
    ),
    "strict_external_artifact_drop_index_cli": (
        Path("docs/codex_audit/evidence/strict_external_artifact_drop_index_cli_20260812/strict_external_artifact_drop_index_cli_report.json"),
        "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX-CLI",
    ),
    "strict_external_artifact_drop_checklist": (
        Path("docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812/strict_external_artifact_drop_checklist_report.json"),
        "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-CHECKLIST",
    ),
    "strict_fire_calibration_source_registry_artifact": (
        Path("docs/codex_audit/evidence/strict_fire_calibration_source_registry_artifact_20260817/strict_fire_calibration_source_registry_artifact_report.json"),
        "PASS-STRICT-FIRE-CALIBRATION-SOURCE-REGISTRY-ARTIFACT",
    ),
    "strict_fire_calibration_metric_artifacts": (
        Path("docs/codex_audit/evidence/strict_fire_calibration_metric_artifacts_20260817/strict_fire_calibration_metric_artifacts_report.json"),
        "PASS-STRICT-FIRE-CALIBRATION-METRIC-ARTIFACTS",
    ),
    "strict_fire_calibration_metadata_artifacts": (
        Path("docs/codex_audit/evidence/strict_fire_calibration_metadata_artifacts_20260817/strict_fire_calibration_metadata_artifacts_report.json"),
        "PASS-STRICT-FIRE-CALIBRATION-METADATA-ARTIFACTS",
    ),
    "strict_external_evidence_receiving_pack": (
        Path("docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812/strict_external_evidence_receiving_pack_report.json"),
        "PASS-STRICT-EXTERNAL-EVIDENCE-RECEIVING-PACK",
    ),
    "strict_external_artifact_template_clone_selftest": (
        Path("docs/codex_audit/evidence/strict_external_artifact_template_clone_selftest_20260817/strict_external_artifact_template_clone_selftest_report.json"),
        "PASS-STRICT-EXTERNAL-ARTIFACT-TEMPLATE-CLONE-SELFTEST",
    ),
    "strict_external_artifact_cross_benchmark_alias_selftest": (
        Path("docs/codex_audit/evidence/strict_external_artifact_cross_benchmark_alias_selftest_20260817/strict_external_artifact_cross_benchmark_alias_selftest_report.json"),
        "PASS-STRICT-EXTERNAL-ARTIFACT-CROSS-BENCHMARK-ALIAS-SELFTEST",
    ),
    "strict_external_plume_source_separation_audit": (
        Path("docs/codex_audit/evidence/strict_external_plume_source_separation_audit_20260817/strict_external_plume_source_separation_audit_report.json"),
        "PASS-STRICT-EXTERNAL-PLUME-SOURCE-SEPARATION-AUDIT",
    ),
    "strict_external_artifact_progress_selftest": (
        Path("docs/codex_audit/evidence/strict_external_artifact_progress_selftest_20260812/strict_external_artifact_progress_selftest_report.json"),
        "PASS-STRICT-EXTERNAL-ARTIFACT-PROGRESS-SELFTEST",
    ),
    "strict_master_plan_closeout_action_pack": (
        Path("docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812/strict_master_plan_closeout_action_pack_report.json"),
        "PASS-STRICT-MASTER-PLAN-CLOSEOUT-ACTION-PACK",
    ),
    "current_scope_delivery_package": (
        Path("docs/codex_audit/evidence/current_scope_delivery_package_20260812/current_scope_delivery_package_report.json"),
        "PASS-CURRENT-SCOPE-DELIVERY-PACKAGE",
    ),
    "complete_walkthrough_guide": (
        Path("docs/codex_audit/evidence/complete_walkthrough_guide_20260818/complete_walkthrough_guide_report.json"),
        "PASS-COMPLETE-WALKTHROUGH-GUIDE",
    ),
    "current_scope_final_handoff_note": (
        Path("docs/codex_audit/evidence/current_scope_final_handoff_note_20260812/current_scope_final_handoff_note_report.json"),
        "PASS-CURRENT-SCOPE-FINAL-HANDOFF-NOTE",
    ),
    "current_operator_quickstart_smoke": (
        Path("docs/codex_audit/evidence/current_operator_quickstart_smoke_20260812/current_operator_quickstart_smoke_report.json"),
        "PASS-CURRENT-OPERATOR-QUICKSTART-SMOKE",
    ),
    "current_phase_closure_certificate": (
        Path("docs/codex_audit/evidence/current_phase_closure_certificate_20260812/current_phase_closure_certificate_report.json"),
        "PASS-CURRENT-PHASE-CLOSURE-CERTIFICATE",
    ),
    "current_phase_release_manifest": (
        Path("docs/codex_audit/evidence/current_phase_release_manifest_20260812/current_phase_release_manifest_report.json"),
        "PASS-CURRENT-PHASE-RELEASE-MANIFEST",
    ),
    "current_scope_release_refresh_entrypoint": (
        Path("docs/codex_audit/evidence/current_scope_release_refresh_entrypoint_20260812/current_scope_release_refresh_entrypoint_report.json"),
        "PASS-CURRENT-SCOPE-RELEASE-REFRESH-ENTRYPOINT",
    ),
    "engineering_liquefied_external_vaporization_negative_selftest": (
        Path("docs/codex_audit/evidence/engineering_liquefied_external_vaporization_negative_selftest_20260806/engineering_liquefied_external_vaporization_negative_selftest_report.json"),
        "PASS-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-NEGATIVE-SELFTEST",
    ),
    "engineering_liquefied_phase_change_overclaim_guard": (
        Path("docs/codex_audit/evidence/engineering_liquefied_phase_change_overclaim_guard_20260811/engineering_liquefied_phase_change_overclaim_guard_report.json"),
        "PASS-ENGINEERING-LIQUEFIED-PHASE-CHANGE-OVERCLAIM-GUARD",
    ),
    "dataverse_open_channel_amr_source_projection_contract": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_contract_20260811/dataverse_open_channel_amr_source_projection_contract_report.json"),
        "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-CONTRACT",
    ),
    "dataverse_open_channel_amr_source_projection_implementation": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_implementation_20260811/dataverse_open_channel_amr_source_projection_implementation_report.json"),
        "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-IMPLEMENTATION",
    ),
    "engineering_fixed_mass_flow_valve_schedule": (
        Path("docs/codex_audit/evidence/engineering_fixed_mass_flow_valve_schedule_20260806/engineering_fixed_mass_flow_valve_schedule_report.json"),
        "PASS-ENGINEERING-FIXED-MASS-FLOW-VALVE-SCHEDULE",
    ),
    "engineering_external_vaporization_timeseries": (
        Path("docs/codex_audit/evidence/engineering_external_vaporization_timeseries_20260806/engineering_external_vaporization_timeseries_report.json"),
        "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES",
    ),
    "engineering_external_vaporization_timeseries_cuda": (
        Path("docs/codex_audit/evidence/engineering_external_vaporization_timeseries_cuda_20260807/engineering_external_vaporization_timeseries_cuda_report.json"),
        "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES-CUDA",
    ),
    "engineering_external_vaporization_multifuel_source_matrix": (
        Path("docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/engineering_external_vaporization_multifuel_source_matrix_report.json"),
        "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-MULTIFUEL-SOURCE-MATRIX",
    ),
    "engineering_external_vaporization_ch4_timeseries_cuda": (
        Path("docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/ch4_timeseries_cuda/engineering_external_vaporization_ch4_timeseries_cuda_report.json"),
        "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-CH4-TIMESERIES-CUDA",
    ),
    "engineering_external_vaporization_c3h8_timeseries_cuda": (
        Path("docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/c3h8_timeseries_cuda/engineering_external_vaporization_c3h8_timeseries_cuda_report.json"),
        "PASS-ENGINEERING-EXTERNAL-VAPORIZATION-C3H8-TIMESERIES-CUDA",
    ),
    "engineering_multi_fuel_operator_runbook": (
        Path("docs/codex_audit/evidence/engineering_multi_fuel_operator_runbook_20260806/engineering_multi_fuel_operator_runbook_report.json"),
        "PASS-ENGINEERING-MULTI-FUEL-OPERATOR-RUNBOOK",
    ),
    "engineering_multi_fuel_template_catalog": (
        Path("docs/codex_audit/evidence/engineering_multi_fuel_template_catalog_20260811/engineering_multi_fuel_template_catalog_report.json"),
        "PASS-ENGINEERING-MULTI-FUEL-TEMPLATE-CATALOG",
    ),
    "engineering_fuel_species_guard": (
        Path("docs/codex_audit/evidence/engineering_fuel_species_guard_20260806/engineering_fuel_species_guard_report.json"),
        "PASS-ENGINEERING-FUEL-SPECIES-GUARD",
    ),
    "engineering_log_marker_compatibility": (
        Path("docs/codex_audit/evidence/engineering_log_marker_compatibility_20260806/engineering_log_marker_compatibility_report.json"),
        "PASS-ENGINEERING-LOG-MARKER-COMPATIBILITY",
    ),
    "engineering_ch4_cold_plume_cpu_probe": (
        Path("docs/codex_audit/evidence/engineering_ch4_cold_plume_cpu_probe_20260806/engineering_ch4_cold_plume_cpu_probe_report.json"),
        "PASS-ENGINEERING-CH4-COLD-PLUME-CPU-MPI-CUDA-PROBE",
    ),
    "engineering_ch4_pipe_rack_delayed_ignition_cuda": (
        Path("docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_cuda_20260806/engineering_ch4_pipe_rack_delayed_ignition_cuda_report.json"),
        "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-SINGLE-CUDA",
    ),
    "engineering_ch4_pipe_rack_delayed_ignition_mpi": (
        Path("docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_20260806/engineering_ch4_pipe_rack_delayed_ignition_mpi_report.json"),
        "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-CPU-MPI",
    ),
    "engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda": (
        Path("docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_20260806/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_report.json"),
        "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA",
    ),
    "engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step": (
        Path("docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_20260806/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.json"),
        "PASS-CH4-PIPE-RACK-DELAYED-IGNITION-MPI-CUDA-500STEP",
    ),
    "operator_runbook": (
        Path("docs/codex_audit/evidence/current_scope_operator_runbook_20260803/current_scope_operator_runbook_report.json"),
        "PASS-CURRENT-SCOPE-OPERATOR-RUNBOOK",
    ),
    "final_readiness": (
        Path("docs/codex_audit/evidence/master_plan_final_readiness_20260731/master_plan_final_readiness_report.json"),
        "PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS",
    ),
    "master_current_scope": (
        Path("docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/master_plan_current_scope_verification_report.json"),
        "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION",
    ),
    "strict_blocker_matrix": (
        Path("docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/master_plan_strict_blocker_matrix_report.json"),
        "TRIAGED-MASTER-PLAN-STRICT-BLOCKER-MATRIX",
    ),
    "engineering_h2_real_cad_handoff_contract": (
        Path("docs/codex_audit/evidence/engineering_h2_real_cad_handoff_contract_20260805/real_cad_handoff_contract_report.json"),
        "PASS-H2-REAL-CAD-HANDOFF-CONTRACT",
    ),
    "h2_fire_overpressure_dataverse_metadata": (
        Path("docs/codex_audit/evidence/h2_fire_overpressure_dataverse_metadata_20260805/h2_fire_overpressure_dataverse_metadata_report.json"),
        "PASS-H2-FIRE-OVERPRESSURE-DATAVERSE-METADATA",
    ),
    "h2_fire_overpressure_reduced_exp002": (
        Path("docs/codex_audit/evidence/h2_fire_overpressure_reduced_exp002_20260805/h2_fire_overpressure_reduced_exp002_report.json"),
        "PASS-H2-FIRE-OVERPRESSURE-REDUCED-EXP002",
    ),
    "h2_fire_exp002_overpressure_calibration_table": (
        Path("docs/codex_audit/evidence/h2_fire_exp002_overpressure_calibration_table_20260805/h2_fire_exp002_overpressure_calibration_table_report.json"),
        "PASS-H2-FIRE-EXP002-OVERPRESSURE-CALIBRATION-TABLE",
    ),
    "h2_fire_exp002_pressure_comparison_contract": (
        Path("docs/codex_audit/evidence/h2_fire_exp002_pressure_comparison_contract_20260805/h2_fire_exp002_pressure_comparison_contract_report.json"),
        "PASS-H2-FIRE-EXP002-PRESSURE-COMPARISON-CONTRACT",
    ),
    "h2_fire_calibration_candidate_sources_20260805": (
        Path("docs/codex_audit/evidence/h2_fire_calibration_candidate_sources_20260805/h2_fire_calibration_candidate_sources_report.json"),
        "PASS-H2-FIRE-CALIBRATION-CANDIDATE-SOURCES-20260805",
    ),
    "h2_fire_mdpi_radiation_calibration_table": (
        Path("docs/codex_audit/evidence/h2_fire_mdpi_radiation_calibration_table_20260805/h2_fire_mdpi_radiation_calibration_table_report.json"),
        "PASS-H2-FIRE-MDPI-RADIATION-CALIBRATION-TABLE",
    ),
    "h2_fire_mdpi_radiation_comparison_contract": (
        Path("docs/codex_audit/evidence/h2_fire_mdpi_radiation_comparison_contract_20260805/h2_fire_mdpi_radiation_comparison_contract_report.json"),
        "PASS-H2-FIRE-MDPI-RADIATION-COMPARISON-CONTRACT",
    ),
    "h2_fire_mdpi_radiation_screening_comparison": (
        Path("docs/codex_audit/evidence/h2_fire_mdpi_radiation_screening_comparison_20260805/h2_fire_mdpi_radiation_screening_comparison_report.json"),
        "QUANTIFIED-H2-FIRE-MDPI-RADIATION-SCREENING-NOT-PASSING",
    ),
    "engineering_h2_pipe_rack_delayed_ignition_cuda": (
        Path("docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cuda_20260805/engineering_h2_pipe_rack_delayed_ignition_cuda_report.json"),
        "PASS-H2-PIPE-RACK-DELAYED-IGNITION-SINGLE-CUDA",
    ),
    "engineering_h2_pipe_rack_delayed_ignition_mpi": (
        Path("docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_mpi_20260805/engineering_h2_pipe_rack_delayed_ignition_mpi_report.json"),
        "PASS-H2-PIPE-RACK-DELAYED-IGNITION-CPU-MPI",
    ),
    "engineering_h2_pipe_rack_delayed_ignition_cross_platform": (
        Path("docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cross_platform_20260805/engineering_h2_pipe_rack_delayed_ignition_cross_platform_report.json"),
        "PASS-H2-PIPE-RACK-DELAYED-IGNITION-CPU-GPU-PARITY",
    ),
    "h2_fire_exp002_pressure_cfd_proxy": (
        Path("docs/codex_audit/evidence/h2_fire_exp002_pressure_cfd_proxy_20260805/h2_fire_exp002_pressure_cfd_proxy_report.json"),
        "PASS-H2-FIRE-EXP002-PRESSURE-CFD-PROXY",
    ),
    "h2_fire_plotfile_sensor_sampling_contract": (
        Path("docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_contract_20260807/h2_fire_plotfile_sensor_sampling_contract_report.json"),
        "PASS-H2-FIRE-PLOTFILE-SENSOR-SAMPLING-CONTRACT",
    ),
    "h2_fire_plotfile_sensor_sampling_negative_selftest": (
        Path("docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/h2_fire_plotfile_sensor_sampling_negative_selftest_report.json"),
        "PASS-H2-FIRE-PLOTFILE-SENSOR-SAMPLING-NEGATIVE-SELFTEST",
    ),
    "h2_fire_mdpi_radiation_cfd_proxy": (
        Path("docs/codex_audit/evidence/h2_fire_mdpi_radiation_cfd_proxy_20260805/h2_fire_mdpi_radiation_cfd_proxy_report.json"),
        "PASS-H2-FIRE-MDPI-RADIATION-CFD-PROXY",
    ),
    "h2_fire_mdpi_radiation_integrated_cfd_proxy": (
        Path("docs/codex_audit/evidence/h2_fire_mdpi_radiation_integrated_cfd_proxy_20260807/h2_fire_mdpi_radiation_integrated_cfd_proxy_report.json"),
        "PASS-H2-FIRE-MDPI-RADIATION-INTEGRATED-CFD-PROXY",
    ),
    "h2_fire_calibration_residual_budget": (
        Path("docs/codex_audit/evidence/h2_fire_calibration_residual_budget_20260811/h2_fire_calibration_residual_budget_report.json"),
        "TRIAGED-H2-FIRE-CALIBRATION-RESIDUAL-BUDGET",
    ),
    "engineering_h2_fire_exp002_delayed_ignition_bridge": (
        Path("docs/codex_audit/evidence/engineering_h2_fire_exp002_delayed_ignition_bridge_20260805/engineering_h2_fire_exp002_delayed_ignition_bridge_report.json"),
        "PASS-H2-FIRE-EXP002-DELAYED-IGNITION-BRIDGE",
    ),
    "strict_unblock_runbook": (
        Path("docs/codex_audit/evidence/strict_master_plan_unblock_runbook_20260803/strict_master_plan_unblock_runbook_report.json"),
        "PASS-STRICT-MASTER-PLAN-UNBLOCK-RUNBOOK",
    ),
    "strict_unblock_command_inventory": (
        Path("docs/codex_audit/evidence/strict_unblock_command_inventory_20260803/strict_unblock_command_inventory_report.json"),
        "PASS-STRICT-UNBLOCK-COMMAND-INVENTORY",
    ),
    "strict_artifact_template_lint": (
        Path("docs/codex_audit/evidence/strict_artifact_template_lint_20260803/strict_artifact_template_lint_report.json"),
        "PASS-STRICT-ARTIFACT-TEMPLATE-LINT",
    ),
    "strict_artifact_drop_contract_preflight": (
        Path("docs/codex_audit/evidence/strict_artifact_drop_contract_preflight_20260803/strict_artifact_drop_contract_preflight_report.json"),
        "PASS-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT",
    ),
    "strict_artifact_drop_contract_selftest": (
        Path("docs/codex_audit/evidence/strict_artifact_drop_contract_selftest_20260803/strict_artifact_drop_contract_selftest_report.json"),
        "PASS-STRICT-ARTIFACT-DROP-CONTRACT-SELFTEST",
    ),
    "master_plan_completion_audit": (
        Path("docs/codex_audit/evidence/master_plan_completion_audit_20260803/master_plan_completion_audit_report.json"),
        "AUDITED-MASTER-PLAN-CURRENT-SCOPE-PASS-STRICT-INCOMPLETE",
    ),
    "current_status_cli": (
        Path("docs/codex_audit/evidence/current_status_cli_20260803/current_status_cli_report.json"),
        "PASS-CURRENT-STATUS-CLI",
    ),
    "current_worktree_hygiene": (
        Path("docs/codex_audit/evidence/current_worktree_hygiene_20260803/current_worktree_hygiene_report.json"),
        "AUDITED-CURRENT-WORKTREE-HYGIENE",
    ),
    "current_worktree_source_ledger": (
        Path("docs/codex_audit/evidence/current_worktree_source_ledger_20260803/current_worktree_source_ledger_report.json"),
        "AUDITED-CURRENT-WORKTREE-SOURCE-LEDGER",
    ),
    "current_case_output_cleanup_manifest": (
        Path("docs/codex_audit/evidence/current_case_output_cleanup_manifest_20260803/current_case_output_cleanup_manifest_report.json"),
        "AUDITED-CURRENT-CASE-OUTPUT-CLEANUP-MANIFEST",
    ),
    "current_disk_usage_manifest": (
        Path("docs/codex_audit/evidence/current_disk_usage_manifest_20260803/current_disk_usage_manifest_report.json"),
        "AUDITED-CURRENT-DISK-USAGE-MANIFEST",
    ),
    "current_disk_cleanup_plan": (
        Path("docs/codex_audit/evidence/current_disk_cleanup_plan_20260803/current_disk_cleanup_plan_report.json"),
        "AUDITED-CURRENT-DISK-CLEANUP-PLAN",
    ),
    "current_operator_command_inventory": (
        Path("docs/codex_audit/evidence/current_operator_command_inventory_20260803/current_operator_command_inventory_report.json"),
        "PASS-CURRENT-OPERATOR-COMMAND-INVENTORY",
    ),
    "current_verification_chain_coverage": (
        Path("docs/codex_audit/evidence/current_verification_chain_coverage_20260803/current_verification_chain_coverage_report.json"),
        "PASS-CURRENT-VERIFICATION-CHAIN-COVERAGE",
    ),
    "dataverse_open_channel_reference_package": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_reference_package_20260803/dataverse_open_channel_reference_package_report.json"),
        "PASS-DATAVERSE-OPEN-CHANNEL-H2-REFERENCE-PACKAGE",
    ),
    "dataverse_open_channel_agreement_contract": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_agreement_contract_20260803/dataverse_open_channel_agreement_contract_report.json"),
        "PASS-DATAVERSE-OPEN-CHANNEL-H2-AGREEMENT-CONTRACT",
    ),
    "dataverse_open_channel_cfd_scout": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_cfd_scout_mpi_cuda_20260803/dataverse_open_channel_cfd_scout_report.json"),
        "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
    ),
    "dataverse_open_channel_cfd_agreement_attempt": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_cfd_agreement_window_mpi_cuda_20260803/dataverse_open_channel_cfd_agreement_attempt_report.json"),
        "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
    ),
    "dataverse_open_channel_cfd_45s_agreement_attempt": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_cfd_45s_window_mpi_cuda_20260803/dataverse_open_channel_cfd_agreement_attempt_report.json"),
        "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
    ),
    "dataverse_open_channel_cfd_120s_agreement_attempt": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_cfd_120s_peak_window_mpi_cuda_20260804/dataverse_open_channel_cfd_agreement_attempt_report.json"),
        "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
    ),
    "dataverse_open_channel_120s_calibration_diagnosis": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_120s_calibration_diagnosis_20260804/dataverse_open_channel_120s_calibration_diagnosis_report.json"),
        "DIAGNOSED-DATAVERSE-OPEN-CHANNEL-H2-120S-CALIBRATION-GAPS",
    ),
    "dataverse_open_channel_45s_calibration_r005_z08": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_45s_calibration_r005_z08_screen_20260804/dataverse_open_channel_45s_calibration_r005_z08_screen_report.json"),
        "SCREENED-DATAVERSE-OPEN-CHANNEL-H2-45S-CALIBRATION-R005-Z08-NOT-PROMOTED",
    ),
    "dataverse_open_channel_45s_calibration_sweep": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_45s_calibration_sweep_20260804/dataverse_open_channel_45s_calibration_sweep_report.json"),
        "SCREENED-DATAVERSE-OPEN-CHANNEL-H2-45S-CALIBRATION-SWEEP-NO-PROMOTION",
    ),
    "dataverse_open_channel_physics_alignment": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_physics_alignment_20260804/dataverse_open_channel_physics_alignment_report.json"),
        "DIAGNOSED-DATAVERSE-OPEN-CHANNEL-H2-PHYSICS-ALIGNMENT-GAPS",
    ),
    "dataverse_open_channel_orifice_velocity_scout": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_orifice_velocity_scout_mpi_cuda_20260805/dataverse_open_channel_orifice_velocity_scout_report.json"),
        "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
    ),
    "dataverse_open_channel_open_boundary_scout": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_scout_mpi_cuda_20260805/dataverse_open_channel_open_boundary_scout_report.json"),
        "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
    ),
    "dataverse_open_channel_open_boundary_orifice_extended_01s": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_01s_mpi_cuda_20260805/dataverse_open_channel_open_boundary_orifice_velocity_extended_01s_report.json"),
        "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
    ),
    "dataverse_open_channel_open_boundary_orifice_extended_1s": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_mpi_cuda_20260805/dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_report.json"),
        "PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA",
    ),
    "dataverse_open_channel_open_boundary_orifice_extended_2s": (
        Path("docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_mpi_cuda_20260807/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_screen_report.json"),
        "PASS-DATAVERSE-OPEN-CHANNEL-OPEN-BOUNDARY-ORIFICE-EXTENDED-2S-MPI-CUDA",
    ),
    "dataverse_refined_source_projection_probe": (
        Path("docs/codex_audit/evidence/dataverse_refined_source_projection_probe_mpi_cuda_20260807/dataverse_refined_source_projection_probe_report.json"),
        "PASS-DATAVERSE-REFINED-SOURCE-PROJECTION-PROBE-MPI-CUDA",
    ),
    "dataverse_full_channel_refined_source_dx025_probe": (
        Path("docs/codex_audit/evidence/dataverse_full_channel_refined_source_dx025_probe_mpi_cuda_20260807/dataverse_full_channel_refined_source_dx025_probe_report.json"),
        "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-PROBE-MPI-CUDA",
    ),
    "dataverse_full_channel_refined_source_dx025_500step": (
        Path("docs/codex_audit/evidence/dataverse_full_channel_refined_source_dx025_500step_mpi_cuda_20260807/dataverse_full_channel_refined_source_dx025_500step_report.json"),
        "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-500STEP-MPI-CUDA",
    ),
    "dataverse_full_channel_refined_source_dx025_1000step_dt5em6": (
        Path("docs/codex_audit/evidence/dataverse_full_channel_refined_source_dx025_1000step_dt5em6_mpi_cuda_20260807/dataverse_full_channel_refined_source_dx025_1000step_dt5em6_report.json"),
        "PASS-DATAVERSE-FULL-CHANNEL-REFINED-SOURCE-DX025-1000STEP-DT5EM6-MPI-CUDA",
    ),
    "academic_gas_detonation_single_cuda": (
        Path("docs/codex_audit/evidence/academic_gas_detonation_single_cuda_20260803/academic_gas_detonation_single_cuda_report.json"),
        "PASS-ACADEMIC-GAS-DETONATION-SINGLE-CUDA",
    ),
}

KEY_ARTIFACTS = [
    Path("README.md"),
    Path("PROGRESS.md"),
    Path("docs/codex_audit/current_scope_operator_runbook.md"),
    Path("docs/codex_audit/engineering_multi_fuel_operator_runbook.md"),
    Path("docs/codex_audit/engineering_liquefied_external_vaporization_source_contract.md"),
    Path("docs/codex_audit/strict_master_plan_unblock_runbook.md"),
    Path("examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv"),
    Path("tools/codex_verify_current_scope.sh"),
    Path("tools/codex_print_current_status.py"),
    Path("tools/write_current_status_cli_report.py"),
    Path("tools/verify_current_status_cli.sh"),
    Path("tools/write_current_worktree_hygiene_report.py"),
    Path("tools/verify_current_worktree_hygiene.sh"),
    Path("tools/write_current_worktree_source_ledger_report.py"),
    Path("tools/verify_current_worktree_source_ledger.sh"),
    Path("tools/write_current_case_output_cleanup_manifest_report.py"),
    Path("tools/verify_current_case_output_cleanup_manifest.sh"),
    Path("tools/write_current_disk_usage_manifest_report.py"),
    Path("tools/verify_current_disk_usage_manifest.sh"),
    Path("tools/write_current_disk_cleanup_plan_report.py"),
    Path("tools/verify_current_disk_cleanup_plan.sh"),
    Path("tools/write_current_operator_command_inventory_report.py"),
    Path("tools/verify_current_operator_command_inventory.sh"),
    Path("tools/write_current_verification_chain_coverage_report.py"),
    Path("tools/verify_current_verification_chain_coverage.sh"),
    Path("tools/write_dataverse_open_channel_reference_package_report.py"),
    Path("tools/verify_dataverse_open_channel_reference_package.sh"),
    Path("tools/write_dataverse_open_channel_agreement_contract_report.py"),
    Path("tools/verify_dataverse_open_channel_agreement_contract.sh"),
    Path("tools/write_dataverse_open_channel_cfd_scout_report.py"),
    Path("tools/verify_dataverse_open_channel_cfd_scout.sh"),
    Path("tools/write_dataverse_open_channel_cfd_agreement_attempt_report.py"),
    Path("tools/verify_dataverse_open_channel_cfd_agreement_attempt.sh"),
    Path("tools/verify_dataverse_open_channel_cfd_45s_agreement_attempt.sh"),
    Path("tools/verify_dataverse_open_channel_cfd_120s_agreement_attempt.sh"),
    Path("tools/write_dataverse_open_channel_120s_calibration_diagnosis_report.py"),
    Path("tools/verify_dataverse_open_channel_120s_calibration_diagnosis.sh"),
    Path("tools/write_dataverse_open_channel_45s_calibration_r005_z08_report.py"),
    Path("tools/verify_dataverse_open_channel_45s_calibration_r005_z08.sh"),
    Path("tools/write_dataverse_open_channel_45s_calibration_sweep_report.py"),
    Path("tools/verify_dataverse_open_channel_45s_calibration_sweep.sh"),
    Path("tools/write_dataverse_open_channel_physics_alignment_report.py"),
    Path("tools/verify_dataverse_open_channel_physics_alignment.sh"),
    Path("tools/verify_dataverse_open_channel_orifice_velocity_scout.sh"),
    Path("tools/verify_dataverse_open_channel_open_boundary_scout.sh"),
    Path("tools/verify_dataverse_open_channel_open_boundary_orifice_extended_01s.sh"),
    Path("tools/verify_dataverse_open_channel_open_boundary_orifice_extended_1s.sh"),
    Path("tools/write_dataverse_open_channel_open_boundary_orifice_extended_2s_report.py"),
    Path("tools/verify_dataverse_open_channel_open_boundary_orifice_extended_2s.sh"),
    Path("tools/run_dataverse_open_channel_refined_source_projection_probe.sh"),
    Path("tools/write_dataverse_open_channel_refined_source_projection_probe_report.py"),
    Path("tools/verify_dataverse_open_channel_refined_source_projection_probe.sh"),
    Path("tools/run_dataverse_open_channel_full_channel_refined_source_dx025_probe.sh"),
    Path("tools/write_dataverse_open_channel_full_channel_refined_source_dx025_probe_report.py"),
    Path("tools/verify_dataverse_open_channel_full_channel_refined_source_dx025_probe.sh"),
    Path("tools/run_dataverse_open_channel_full_channel_refined_source_dx025_500step.sh"),
    Path("tools/write_dataverse_open_channel_full_channel_refined_source_dx025_500step_report.py"),
    Path("tools/verify_dataverse_open_channel_full_channel_refined_source_dx025_500step.sh"),
    Path("tools/run_dataverse_open_channel_full_channel_refined_source_dx025_1000step_dt5em6.sh"),
    Path("tools/write_dataverse_open_channel_full_channel_refined_source_dx025_1000step_dt5em6_report.py"),
    Path("tools/verify_dataverse_open_channel_full_channel_refined_source_dx025_1000step_dt5em6.sh"),
    Path("tools/codex_smoke_engineering_h2_dataverse_open_channel_scout_cuda.sh"),
    Path("tools/write_current_scope_state_snapshot_report.py"),
    Path("tools/verify_current_scope_state_snapshot.sh"),
    Path("tools/write_strict_master_plan_unblock_runbook_report.py"),
    Path("tools/verify_strict_master_plan_unblock_runbook.sh"),
    Path("tools/write_strict_unblock_command_inventory_report.py"),
    Path("tools/verify_strict_unblock_command_inventory.sh"),
    Path("tools/write_strict_artifact_template_lint_report.py"),
    Path("tools/verify_strict_artifact_template_lint.sh"),
    Path("tools/write_strict_artifact_drop_contract_preflight_report.py"),
    Path("tools/verify_strict_artifact_drop_contract_preflight.sh"),
    Path("tools/write_strict_artifact_drop_contract_selftest_report.py"),
    Path("tools/verify_strict_artifact_drop_contract_selftest.sh"),
    Path("tools/write_master_plan_completion_audit_report.py"),
    Path("tools/verify_master_plan_completion_audit.sh"),
    Path("tools/write_current_parallel_capability_matrix_report.py"),
    Path("tools/write_current_scenario_readiness_matrix_report.py"),
    Path("tools/verify_current_scenario_readiness_matrix.sh"),
    Path("tools/write_engineering_h2_real_cad_handoff_contract_report.py"),
    Path("tools/verify_engineering_h2_real_cad_handoff_contract.sh"),
    Path("tools/write_h2_fire_overpressure_dataverse_metadata_report.py"),
    Path("tools/verify_h2_fire_overpressure_dataverse_metadata.sh"),
    Path("tools/write_h2_fire_overpressure_reduced_exp002_report.py"),
    Path("tools/verify_h2_fire_overpressure_reduced_exp002.sh"),
    Path("tools/write_h2_fire_exp002_overpressure_calibration_table_report.py"),
    Path("tools/verify_h2_fire_exp002_overpressure_calibration_table.sh"),
    Path("tools/write_h2_fire_exp002_pressure_comparison_contract_report.py"),
    Path("tools/verify_h2_fire_exp002_pressure_comparison_contract.sh"),
    Path("tools/write_h2_fire_calibration_candidate_sources_20260805_report.py"),
    Path("tools/verify_h2_fire_calibration_candidate_sources_20260805.sh"),
    Path("tools/write_h2_fire_mdpi_radiation_calibration_table_report.py"),
    Path("tools/verify_h2_fire_mdpi_radiation_calibration_table.sh"),
    Path("tools/write_h2_fire_mdpi_radiation_comparison_contract_report.py"),
    Path("tools/verify_h2_fire_mdpi_radiation_comparison_contract.sh"),
    Path("tools/write_h2_fire_mdpi_radiation_screening_comparison_report.py"),
    Path("tools/verify_h2_fire_mdpi_radiation_screening_comparison.sh"),
    Path("tools/write_engineering_h2_pipe_rack_delayed_ignition_cuda_report.py"),
    Path("tools/verify_engineering_h2_pipe_rack_delayed_ignition_cuda.sh"),
    Path("tools/codex_smoke_engineering_h2_pipe_rack_delayed_ignition_mpi.sh"),
    Path("tools/write_engineering_h2_pipe_rack_delayed_ignition_mpi_report.py"),
    Path("tools/verify_engineering_h2_pipe_rack_delayed_ignition_mpi.sh"),
    Path("tools/write_engineering_h2_pipe_rack_delayed_ignition_cross_platform_report.py"),
    Path("tools/verify_engineering_h2_pipe_rack_delayed_ignition_cross_platform.sh"),
    Path("tools/write_h2_fire_exp002_pressure_cfd_proxy_report.py"),
    Path("tools/verify_h2_fire_exp002_pressure_cfd_proxy.sh"),
    Path("tools/codex_extract_plotfile_sensor_timeseries.py"),
    Path("tools/write_h2_fire_plotfile_sensor_sampling_contract_report.py"),
    Path("tools/verify_h2_fire_plotfile_sensor_sampling_contract.sh"),
    Path("tools/write_h2_fire_plotfile_sensor_sampling_negative_selftest_report.py"),
    Path("tools/verify_h2_fire_plotfile_sensor_sampling_negative_selftest.sh"),
    Path("tools/write_h2_fire_mdpi_radiation_cfd_proxy_report.py"),
    Path("tools/verify_h2_fire_mdpi_radiation_cfd_proxy.sh"),
    Path("tools/write_h2_fire_mdpi_radiation_integrated_cfd_proxy_report.py"),
    Path("tools/verify_h2_fire_mdpi_radiation_integrated_cfd_proxy.sh"),
    Path("tools/write_h2_fire_calibration_residual_budget_report.py"),
    Path("tools/verify_h2_fire_calibration_residual_budget.sh"),
    Path("tools/write_engineering_h2_fire_exp002_delayed_ignition_bridge_report.py"),
    Path("tools/verify_engineering_h2_fire_exp002_delayed_ignition_bridge.sh"),
    Path("tools/write_academic_gas_detonation_single_cuda_report.py"),
    Path("tools/verify_academic_gas_detonation_single_cuda.sh"),
    Path("tools/write_engineering_multi_fuel_capability_boundary_report.py"),
    Path("tools/verify_engineering_multi_fuel_capability_boundary.sh"),
    Path("tools/write_engineering_multi_fuel_operator_runbook_report.py"),
    Path("tools/verify_engineering_multi_fuel_operator_runbook.sh"),
    Path("tools/write_engineering_multi_fuel_template_catalog_report.py"),
    Path("tools/verify_engineering_multi_fuel_template_catalog.sh"),
    Path("tools/codex_make_external_vaporization_source_input.py"),
    Path("tools/write_engineering_liquefied_external_vaporization_contract_report.py"),
    Path("tools/verify_engineering_liquefied_external_vaporization_contract.sh"),
    Path("tools/codex_make_liquefied_release_vaporization_csv.py"),
    Path("tools/write_engineering_liquefied_release_vaporization_source_model_report.py"),
    Path("tools/verify_engineering_liquefied_release_vaporization_source_model.sh"),
    Path("tools/write_engineering_liquefied_release_vaporization_source_model_negative_selftest_report.py"),
    Path("tools/verify_engineering_liquefied_release_vaporization_source_model_negative_selftest.sh"),
    Path("tools/run_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh"),
    Path("tools/write_engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.py"),
    Path("tools/verify_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh"),
    Path("tools/write_engineering_liquefied_release_source_balance_report.py"),
    Path("tools/verify_engineering_liquefied_release_source_balance.sh"),
    Path("tools/write_engineering_liquefied_release_source_balance_negative_selftest_report.py"),
    Path("tools/verify_engineering_liquefied_release_source_balance_negative_selftest.sh"),
    Path("tools/write_engineering_liquefied_release_thermal_plausibility_report.py"),
    Path("tools/verify_engineering_liquefied_release_thermal_plausibility.sh"),
    Path("tools/write_engineering_liquefied_breach_source_contract_report.py"),
    Path("tools/verify_engineering_liquefied_breach_source_contract.sh"),
    Path("tools/write_engineering_liquefied_breach_preset_templates_report.py"),
    Path("tools/verify_engineering_liquefied_breach_preset_templates.sh"),
    Path("examples/engineering/h2_leak_3d/liquefied_breach_presets/lng_ch4_tank_breach_screening.json"),
    Path("examples/engineering/h2_leak_3d/liquefied_breach_presets/lpg_c3h8_pipe_rupture_screening.json"),
    Path("tools/write_engineering_liquefied_external_vaporization_negative_selftest_report.py"),
    Path("tools/verify_engineering_liquefied_external_vaporization_negative_selftest.sh"),
    Path("tools/write_engineering_liquefied_phase_change_overclaim_guard_report.py"),
    Path("tools/verify_engineering_liquefied_phase_change_overclaim_guard.sh"),
    Path("tools/write_dataverse_open_channel_amr_source_projection_contract_report.py"),
    Path("tools/verify_dataverse_open_channel_amr_source_projection_contract.sh"),
    Path("tools/write_dataverse_open_channel_amr_source_projection_implementation_report.py"),
    Path("tools/verify_dataverse_open_channel_amr_source_projection_implementation.sh"),
    Path("tools/codex_setup_cuda126_sundials_env.sh"),
    Path("tools/codex_build_h2_leak_mpi_cuda_repro.sh"),
    Path("tools/write_dataverse_open_channel_long_window_reconciliation_report.py"),
    Path("tools/verify_dataverse_open_channel_long_window_reconciliation.sh"),
    Path("tools/write_engineering_fixed_mass_flow_valve_schedule_report.py"),
    Path("tools/verify_engineering_fixed_mass_flow_valve_schedule.sh"),
    Path("examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_valve_schedule_smoke"),
    Path("tools/write_engineering_external_vaporization_timeseries_report.py"),
    Path("tools/verify_engineering_external_vaporization_timeseries.sh"),
    Path("tools/write_engineering_external_vaporization_timeseries_cuda_report.py"),
    Path("tools/verify_engineering_external_vaporization_timeseries_cuda.sh"),
    Path("tools/write_engineering_external_vaporization_multifuel_source_matrix_report.py"),
    Path("tools/verify_engineering_external_vaporization_multifuel_source_matrix.sh"),
    Path("tools/run_engineering_external_vaporization_ch4_timeseries_cuda.sh"),
    Path("tools/write_engineering_external_vaporization_ch4_timeseries_cuda_report.py"),
    Path("tools/verify_engineering_external_vaporization_ch4_timeseries_cuda.sh"),
    Path("tools/write_engineering_external_vaporization_c3h8_timeseries_cuda_report.py"),
    Path("tools/verify_engineering_external_vaporization_c3h8_timeseries_cuda.sh"),
    Path("examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_timeseries_smoke"),
    Path("tools/write_engineering_ch4_cold_plume_cpu_probe_report.py"),
    Path("tools/verify_engineering_ch4_cold_plume_cpu_probe.sh"),
    Path("tools/write_engineering_ch4_pipe_rack_delayed_ignition_cuda_report.py"),
    Path("tools/verify_engineering_ch4_pipe_rack_delayed_ignition_cuda.sh"),
    Path("tools/write_engineering_ch4_pipe_rack_delayed_ignition_mpi_report.py"),
    Path("tools/verify_engineering_ch4_pipe_rack_delayed_ignition_mpi.sh"),
    Path("tools/write_engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_report.py"),
    Path("tools/verify_engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda.sh"),
    Path("tools/write_engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.py"),
    Path("tools/verify_engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step.sh"),
    Path("tools/write_current_scope_operator_runbook_report.py"),
    Path("tools/write_master_plan_final_readiness_report.py"),
    Path("tools/write_master_plan_current_scope_verification_report.py"),
    Path("tools/verify_master_plan_current_scope.sh"),
]

REQUIRED_STRICT_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}


class SnapshotError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SnapshotError(message)


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
        raise SnapshotError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"invalid JSON evidence {path}: {exc}") from exc
    require(isinstance(data, dict), f"JSON evidence is not an object: {path}")
    return data


def evidence_entry(label: str, path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing evidence file: {path}")
    entry = {
        "label": label,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }
    if label in VOLATILE_HASH_LABELS:
        entry["hash_verification"] = "skipped-cycle-reference"
    return entry


def run_command(argv: list[str], timeout: int = 10) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        output = completed.stdout.strip().splitlines()
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "output_head": output[:20],
        }
    except FileNotFoundError:
        return {"argv": argv, "returncode": None, "output_head": ["COMMAND_NOT_FOUND"]}
    except subprocess.TimeoutExpired:
        return {"argv": argv, "returncode": None, "output_head": ["COMMAND_TIMEOUT"]}


def build_report() -> dict[str, Any]:
    report_statuses: dict[str, Any] = {}
    evidence_files: list[dict[str, Any]] = []

    for label, (path, expected_status) in KEY_REPORTS.items():
        data = load_json(path)
        status = data.get("status")
        report_statuses[label] = {
            "path": str(path),
            "status": status,
            "expected_status": expected_status,
            "ready": status == expected_status,
        }
        evidence_files.append(evidence_entry(label, path))

    artifact_entries = []
    for path in KEY_ARTIFACTS:
        artifact_entries.append(evidence_entry(path.as_posix(), path))

    strict = load_json(KEY_REPORTS["strict_blocker_matrix"][0])
    strict_blockers = set(strict.get("summary", {}).get("open_strict_blockers", []))

    master = load_json(KEY_REPORTS["master_current_scope"][0])
    final = load_json(KEY_REPORTS["final_readiness"][0])
    parallel = load_json(KEY_REPORTS["parallel_capability"][0])
    scenario_readiness = load_json(KEY_REPORTS["scenario_readiness_matrix"][0])
    runbook = load_json(KEY_REPORTS["operator_runbook"][0])

    commands = {
        "python_version": run_command(["python3", "--version"]),
        "git_head": run_command(["git", "rev-parse", "HEAD"]),
        "git_status_short": run_command(["git", "status", "--short"]),
        "nvcc_version": run_command(["nvcc", "--version"]),
        "nvidia_smi": run_command(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total",
                "--format=csv,noheader",
            ]
        ),
        "mpirun_version": run_command(["mpirun", "--version"]),
    }

    all_reports_ready = all(item["ready"] for item in report_statuses.values())
    strict_blockers_ok = strict_blockers == REQUIRED_STRICT_BLOCKERS
    master_ready = (
        master.get("summary", {}).get("passed_gate_count") == master.get("summary", {}).get("gate_count")
        and master.get("summary", {}).get("gate_count") == 15
    )
    final_ready = final.get("summary", {}).get("current_user_priority_ready") is True
    parallel_ready = parallel.get("summary", {}).get("current_parallel_capability_matrix_ready") is True
    scenario_readiness_ready = scenario_readiness.get("status") == "PASS-CURRENT-SCENARIO-READINESS-MATRIX"
    runbook_ready = runbook.get("summary", {}).get("operator_runbook_ready") is True

    ready = all_reports_ready and strict_blockers_ok and master_ready and final_ready and parallel_ready and scenario_readiness_ready and runbook_ready

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "current_scope_state_snapshot_ready": ready,
            "key_report_count": len(KEY_REPORTS),
            "key_artifact_count": len(KEY_ARTIFACTS),
            "all_key_reports_ready": all_reports_ready,
            "strict_blocker_set_ok": strict_blockers_ok,
            "master_current_scope_gate_count": master.get("summary", {}).get("gate_count"),
            "master_current_scope_passed_gate_count": master.get("summary", {}).get("passed_gate_count"),
            "final_current_user_priority_ready": final_ready,
            "parallel_capability_ready": parallel_ready,
            "scenario_readiness_matrix_ready": scenario_readiness_ready,
            "operator_runbook_ready": runbook_ready,
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "key_reports": report_statuses,
        "key_artifacts": artifact_entries,
        "runtime_commands": commands,
        "evidence_files": evidence_files + artifact_entries,
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_scope_state_snapshot_ready") is True, "state snapshot is not ready")
    require(summary.get("all_key_reports_ready") is True, "not all key reports are ready")
    require(summary.get("strict_blocker_set_ok") is True, "strict blocker set changed")
    require(summary.get("master_current_scope_gate_count") == 15, "unexpected master current-scope gate count")
    require(summary.get("master_current_scope_passed_gate_count") == 15, "not all master current-scope gates passed")
    require(summary.get("final_current_user_priority_ready") is True, "final readiness is not current-user ready")
    require(summary.get("parallel_capability_ready") is True, "parallel capability is not ready")
    require(summary.get("scenario_readiness_matrix_ready") is True, "scenario readiness matrix is not ready")
    require(summary.get("operator_runbook_ready") is True, "operator runbook is not ready")
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            if entry.get("label") in VOLATILE_HASH_LABELS:
                require(
                    entry.get("hash_verification") == "skipped-cycle-reference",
                    f"missing cycle-reference hash policy for {path}",
                )
                continue
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current-Scope State Snapshot",
        "",
        f"- Status: `{report['status']}`",
        f"- Key reports ready: `{summary['all_key_reports_ready']}`",
        f"- Master current-scope gates: `{summary['master_current_scope_passed_gate_count']}/{summary['master_current_scope_gate_count']}`",
        f"- Final current-user priority ready: `{summary['final_current_user_priority_ready']}`",
        f"- Parallel capability ready: `{summary['parallel_capability_ready']}`",
        f"- Scenario readiness matrix ready: `{summary['scenario_readiness_matrix_ready']}`",
        f"- Operator runbook ready: `{summary['operator_runbook_ready']}`",
        f"- Strict blocker set ok: `{summary['strict_blocker_set_ok']}`",
        "",
        "## Key Reports",
        "",
    ]
    for label, item in report["key_reports"].items():
        lines.append(f"- `{label}`: `{item['status']}`")
    lines.append("")
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
        print(f"current_scope_state_snapshot VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_scope_state_snapshot PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
