#!/usr/bin/env python3
"""Write/verify the current status CLI self-check report."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STATUS_PASS = "PASS-CURRENT-STATUS-CLI"
STATUS_NOT_READY = "NOT_READY-CURRENT-STATUS-CLI"

DEFAULT_ROOT = Path("docs/codex_audit/evidence/current_status_cli_20260803")
DEFAULT_OUTPUT_JSON = DEFAULT_ROOT / "current_status_cli_report.json"
DEFAULT_OUTPUT_MD = DEFAULT_ROOT / "current_status_cli_report.md"

CLI = Path("tools/codex_print_current_status.py")
SNAPSHOT_WRITER = Path("tools/write_current_scope_state_snapshot_report.py")

SOURCE_REPORTS = {
    "completion_audit": Path(
        "docs/codex_audit/evidence/master_plan_completion_audit_20260803/"
        "master_plan_completion_audit_report.json"
    ),
    "current_scope_verification": Path(
        "docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/"
        "master_plan_current_scope_verification_report.json"
    ),
    "final_readiness": Path(
        "docs/codex_audit/evidence/master_plan_final_readiness_20260731/"
        "master_plan_final_readiness_report.json"
    ),
    "parallel_capability": Path(
        "docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/"
        "current_parallel_capability_matrix_report.json"
    ),
    "state_snapshot": Path(
        "docs/codex_audit/evidence/current_scope_state_snapshot_20260803/"
        "current_scope_state_snapshot_report.json"
    ),
    "release_candidate_handoff": Path(
        "docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812/"
        "current_scope_release_candidate_handoff_report.json"
    ),
    "project_closeout_forecast": Path(
        "docs/codex_audit/evidence/project_closeout_forecast_20260812/"
        "project_closeout_forecast_report.json"
    ),
    "project_closeout_acceptance_gate": Path(
        "docs/codex_audit/evidence/project_closeout_acceptance_gate_20260812/"
        "project_closeout_acceptance_gate_report.json"
    ),
    "strict_master_plan_completion_gate": Path(
        "docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812/"
        "strict_master_plan_completion_gate_report.json"
    ),
    "strict_external_artifact_drop_index": Path(
        "docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/"
        "strict_external_artifact_drop_index_report.json"
    ),
    "strict_master_plan_closeout_action_pack": Path(
        "docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812/"
        "strict_master_plan_closeout_action_pack_report.json"
    ),
    "current_scope_delivery_package": Path(
        "docs/codex_audit/evidence/current_scope_delivery_package_20260812/"
        "current_scope_delivery_package_report.json"
    ),
    "current_scope_final_handoff_note": Path(
        "docs/codex_audit/evidence/current_scope_final_handoff_note_20260812/"
        "current_scope_final_handoff_note_report.json"
    ),
    "current_phase_closure_certificate": Path(
        "docs/codex_audit/evidence/current_phase_closure_certificate_20260812/"
        "current_phase_closure_certificate_report.json"
    ),
    "current_phase_release_manifest": Path(
        "docs/codex_audit/evidence/current_phase_release_manifest_20260812/"
        "current_phase_release_manifest_report.json"
    ),
    "operator_command_inventory": Path(
        "docs/codex_audit/evidence/current_operator_command_inventory_20260803/"
        "current_operator_command_inventory_report.json"
    ),
    "sundials_local_link_audit": Path(
        "docs/codex_audit/evidence/sundials_local_link_audit_20260820/"
        "sundials_local_link_audit_report.json"
    ),
    "multi_fuel_capability": Path(
        "docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/"
        "engineering_multi_fuel_capability_boundary_report.json"
    ),
    "multi_fuel_template_catalog": Path(
        "docs/codex_audit/evidence/engineering_multi_fuel_template_catalog_20260811/"
        "engineering_multi_fuel_template_catalog_report.json"
    ),
    "liquefied_source_balance": Path(
        "docs/codex_audit/evidence/engineering_liquefied_release_source_balance_20260807/"
        "engineering_liquefied_release_source_balance_report.json"
    ),
    "liquefied_source_balance_negative": Path(
        "docs/codex_audit/evidence/engineering_liquefied_release_source_balance_negative_selftest_20260807/"
        "engineering_liquefied_release_source_balance_negative_selftest_report.json"
    ),
    "liquefied_phase_change_overclaim_guard": Path(
        "docs/codex_audit/evidence/engineering_liquefied_phase_change_overclaim_guard_20260811/"
        "engineering_liquefied_phase_change_overclaim_guard_report.json"
    ),
    "liquefied_thermal_plausibility": Path(
        "docs/codex_audit/evidence/engineering_liquefied_release_thermal_plausibility_20260811/"
        "engineering_liquefied_release_thermal_plausibility_report.json"
    ),
    "liquefied_breach_source_contract": Path(
        "docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/"
        "engineering_liquefied_breach_source_contract_report.json"
    ),
    "liquefied_breach_preset_templates": Path(
        "docs/codex_audit/evidence/engineering_liquefied_breach_preset_templates_20260811/"
        "engineering_liquefied_breach_preset_templates_report.json"
    ),
    "strict_fire_calibration_update": Path(
        "docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731/"
        "master_plan_strict_fire_calibration_update_report.json"
    ),
    "h2_fire_calibration_residual_budget": Path(
        "docs/codex_audit/evidence/h2_fire_calibration_residual_budget_20260811/"
        "h2_fire_calibration_residual_budget_report.json"
    ),
    "strict_external_source_update": Path(
        "docs/codex_audit/evidence/master_plan_strict_external_source_update_20260731/"
        "master_plan_strict_external_source_update_report.json"
    ),
    "dataverse_amr_source_projection_implementation": Path(
        "docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_implementation_20260811/"
        "dataverse_open_channel_amr_source_projection_implementation_report.json"
    ),
    "dataverse_long_window_reconciliation": Path(
        "docs/codex_audit/evidence/dataverse_open_channel_long_window_reconciliation_20260811/"
        "dataverse_open_channel_long_window_reconciliation_report.json"
    ),
    "strict_real_cad_update": Path(
        "docs/codex_audit/evidence/master_plan_strict_real_cad_update_20260731/"
        "master_plan_strict_real_cad_update_report.json"
    ),
}

EXPECTED_STATUS = {
    "completion_audit_status": "AUDITED-MASTER-PLAN-CURRENT-SCOPE-PASS-STRICT-INCOMPLETE",
    "current_scope_verification_status": "PASS-MASTER-PLAN-CURRENT-SCOPE-VERIFICATION",
    "final_readiness_status": "PASS-MASTER-PLAN-CURRENT-USER-SCOPE-READINESS",
    "state_snapshot_status": "PASS-CURRENT-SCOPE-STATE-SNAPSHOT",
    "release_candidate_handoff_status": "PASS-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF",
    "project_closeout_forecast_status": "PASS-PROJECT-CLOSEOUT-FORECAST",
    "project_closeout_acceptance_gate_status": "PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE",
    "strict_master_plan_completion_gate_status": (
        "AWAITING-STRICT-MASTER-PLAN-COMPLETION-GATE-EXTERNAL-ARTIFACTS"
    ),
    "strict_external_artifact_drop_index_status": "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX",
    "strict_external_evidence_receiving_pack_status": "PASS-STRICT-EXTERNAL-EVIDENCE-RECEIVING-PACK",
    "strict_master_plan_closeout_action_pack_status": "PASS-STRICT-MASTER-PLAN-CLOSEOUT-ACTION-PACK",
    "current_scope_delivery_package_status": "PASS-CURRENT-SCOPE-DELIVERY-PACKAGE",
    "current_scope_final_handoff_note_status": "PASS-CURRENT-SCOPE-FINAL-HANDOFF-NOTE",
    "current_phase_closure_certificate_status": "PASS-CURRENT-PHASE-CLOSURE-CERTIFICATE",
    "current_phase_release_manifest_status": "PASS-CURRENT-PHASE-RELEASE-MANIFEST",
    "operator_command_inventory_status": "PASS-CURRENT-OPERATOR-COMMAND-INVENTORY",
    "sundials_local_link_audit_status": "PASS-SUNDIALS-LOCAL-LINK-AUDIT",
    "multi_fuel_capability_status": "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY",
    "multi_fuel_template_catalog_status": "PASS-ENGINEERING-MULTI-FUEL-TEMPLATE-CATALOG",
    "liquefied_release_source_balance_status": "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE",
    "liquefied_release_source_balance_negative_selftest_status": (
        "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE-NEGATIVE-SELFTEST"
    ),
    "liquefied_phase_change_overclaim_guard_status": (
        "PASS-ENGINEERING-LIQUEFIED-PHASE-CHANGE-OVERCLAIM-GUARD"
    ),
    "liquefied_release_thermal_plausibility_status": (
        "PASS-ENGINEERING-LIQUEFIED-RELEASE-THERMAL-PLAUSIBILITY"
    ),
    "liquefied_breach_source_contract_status": "PASS-ENGINEERING-LIQUEFIED-BREACH-SOURCE-CONTRACT",
    "liquefied_breach_preset_templates_status": "PASS-ENGINEERING-LIQUEFIED-BREACH-PRESET-TEMPLATES",
    "strict_fire_calibration_status": "TRIAGED-MASTER-PLAN-STRICT-FIRE-CALIBRATION-PARTIAL-DATA-BRIDGED",
    "fire_residual_budget_status": "TRIAGED-H2-FIRE-CALIBRATION-RESIDUAL-BUDGET",
    "exp002_reduced_overpressure_status": "PASS-H2-FIRE-OVERPRESSURE-REDUCED-EXP002",
    "strict_external_plume_status": "TRIAGED-MASTER-PLAN-STRICT-EXTERNAL-SOURCES-PUBLIC-DATA-INCOMPLETE",
    "dataverse_cfd_45s_agreement_attempt_status": "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
    "dataverse_cfd_120s_agreement_attempt_status": "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
    "dataverse_long_window_reconciliation_status": "TRIAGED-DATAVERSE-OPEN-CHANNEL-LONG-WINDOW-REFINED-SOURCE-GAP",
    "dataverse_amr_source_projection_implementation_status": (
        "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-IMPLEMENTATION"
    ),
    "strict_real_cad_status": "TRIAGED-MASTER-PLAN-STRICT-REAL-CAD-ARTIFACTS-MISSING",
    "real_cad_handoff_contract_status": "PASS-H2-REAL-CAD-HANDOFF-CONTRACT",
    "real_cad_boundary_contract_status": "NOT_READY-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT",
    "real_cad_negative_selftest_status": "PASS-H2-REAL-CAD-GUARD-NEGATIVE-SELFTEST",
}

EXPECTED_BOOL_TRUE = [
    "current_user_priority_ready",
    "release_candidate_handoff_ready",
    "release_candidate_current_scope_ready",
    "release_candidate_can_be_used_for_current_priority_scope",
    "project_closeout_current_release_candidate_ready",
    "project_closeout_current_scope_can_be_closed_now",
    "project_closeout_strict_closeout_requires_external_artifacts",
    "project_closeout_acceptance_gate_ready",
    "project_closeout_current_phase_acceptance_allowed",
    "strict_master_plan_completion_gate_ready",
    "strict_completion_current_scope_closure_allowed",
    "strict_completion_external_artifacts_missing",
    "strict_external_artifact_drop_index_ready",
    "strict_external_evidence_receiving_pack_ready",
    "strict_external_evidence_receiving_pack_still_open",
    "strict_master_plan_closeout_action_pack_ready",
    "strict_master_plan_closeout_action_pack_current_phase_closeable",
    "strict_master_plan_closeout_action_pack_still_open",
    "current_scope_delivery_package_ready",
    "current_scope_delivery_package_current_scope_can_be_closed_now",
    "current_scope_delivery_package_last_full_log_passed",
    "current_scope_final_handoff_note_ready",
    "current_phase_closure_certificate_ready",
    "current_phase_closeable",
    "closure_certificate_strict_master_plan_still_open",
    "closure_certificate_last_full_current_scope_log_passed",
    "current_phase_release_manifest_ready",
    "current_phase_release_manifest_latest_full_log_passed",
    "current_phase_release_manifest_current_phase_closeable",
    "operator_command_inventory_ready",
    "sundials_local_link_audit_ready",
    "sundials_local_link_drift_present",
    "sundials_restore_requires_explicit_operator_review",
    "cpu_mpi_ready_for_all_current_scenarios",
    "single_gpu_ready_for_all_current_scenarios",
    "multi_gpu_mpi_cuda_ready_for_all_current_scenarios",
    "source_fuel_species_configurable",
    "multi_fuel_template_catalog_ready",
    "multi_fuel_template_catalog_csv_template_ready",
    "multi_fuel_template_catalog_liquefied_nonclaim_comments_present",
    "h2_engineering_current_scope_ready",
    "ch4_gas_fire_probe_ready",
    "c3h8_gas_fire_probe_ready",
    "gasified_lng_given_source_surrogate_ready",
    "gasified_lpg_given_source_surrogate_ready",
    "external_vaporization_multifuel_timeseries_cuda_passed",
    "liquefied_release_vaporization_source_model_cuda_smoke_passed",
    "liquefied_release_source_balance_ready",
    "liquefied_release_source_balance_mapping_schedule_matches_csv",
    "liquefied_release_source_balance_generated_input_matches_mapping",
    "liquefied_release_source_balance_negative_selftest_ready",
    "liquefied_release_source_balance_guards_negative_mdot",
    "liquefied_release_source_balance_guards_species_drift",
    "liquefied_release_source_balance_guards_schedule_rate_mismatch",
    "liquefied_release_source_balance_guards_phase_change_overclaim",
    "liquefied_release_source_balance_guards_generated_input_species_mismatch",
    "liquefied_release_thermal_plausibility_ready",
    "liquefied_release_thermal_vaporized_fraction_formula_ok",
    "liquefied_release_thermal_heat_loads_positive",
    "liquefied_breach_source_contract_ready",
    "liquefied_breach_source_contract_accepts_screening_breach_inputs",
    "liquefied_breach_source_contract_generates_external_gas_source",
    "liquefied_breach_preset_templates_ready",
    "liquefied_breach_preset_templates_editable_json_presets",
    "liquefied_breach_preset_templates_generates_cfd_source_csv",
    "liquefied_phase_change_overclaim_guard_ready",
    "liquefied_phase_change_gasified_lng_lpg_bridge_ready",
    "liquefied_phase_change_external_vaporization_bridge_ready",
    "liquefied_phase_change_screening_source_ready",
    "liquefied_phase_change_cuda_runtime_ready",
    "prevents_overclaim",
    "strict_fire_calibration_blocker_present",
    "fire_residual_budget_ready",
    "fire_candidate_sources_both_metric_families_available",
    "exp002_source_csv_md5_verified",
    "exp002_pressure_cfd_proxy_extracted",
    "exp002_pressure_cfd_proxy_cpu_gpu_parity_passed",
    "plotfile_sensor_sampling_contract_ready",
    "mdpi_radiation_integrated_cfd_proxy_extracted",
    "mdpi_radiation_integrated_cfd_proxy_virtual_radiometer_flux_generated",
    "external_plume_blocker_present",
    "public_machine_readable_external_plume_timeseries_found",
    "public_sbepv5_d27_geometry_and_release_conditions_found",
    "dataverse_full_dataset_all_files_ready",
    "dataverse_agreement_ready_for_cfd_scoring",
    "dataverse_existing_120s_reaches_peak_interval",
    "dataverse_amr_source_projection_finest_available_level_only",
    "dataverse_amr_source_projection_implementation_ready",
    "dataverse_amr_source_projection_mpi_cuda_linked_executable",
    "dataverse_amr_source_projection_mpi_cuda_reproducible_build_entrypoint_ready",
    "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_cuda_12_6",
    "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_local_sundials_cuda",
    "dataverse_geometry_ready_for_sensor_sampling_map",
    "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_strict_blocker_still_open",
    "real_cad_blocker_present",
    "real_cad_handoff_contract_ready",
    "real_cad_negative_selftest_ready",
    "real_cad_guards_synthetic_manifest",
    "real_cad_guards_missing_provenance",
    "real_cad_guards_source_hash_mismatch",
    "real_cad_guards_large_layout_too_few_geometries",
    "real_cad_guards_data_room_bad_hash",
    "real_cad_guards_cleanup_quality_false_check",
    "real_cad_guards_boundary_placeholder",
    "real_cad_guards_boundary_missing_required_role",
]

EXPECTED_BOOL_FALSE = [
    "goal_complete",
    "strict_master_plan_complete",
    "release_candidate_is_full_strict_master_plan_completion",
    "project_closeout_strict_master_plan_can_be_closed_now",
    "project_closeout_strict_final_acceptance_allowed",
    "strict_completion_allowed",
    "strict_external_evidence_receiving_pack_completion_allowed",
    "strict_master_plan_closeout_action_pack_completion_allowed",
    "closure_certificate_strict_master_plan_closure_allowed",
    "current_phase_release_manifest_strict_master_plan_closure_allowed",
    "sundials_local_link_expected_target_exists",
    "sundials_local_link_safe_to_auto_restore",
    "liquefied_gas_phase_change_ready",
    "multi_fuel_template_catalog_cfd_internal_liquid_phase_change_claim_allowed",
    "liquefied_phase_change_production_claim_allowed",
    "liquefied_phase_change_cfd_solves_liquid_phase_change",
    "liquefied_phase_change_cfd_solves_pool_spread_evaporation",
    "liquefied_phase_change_cfd_solves_flashing_discharge",
    "liquefied_breach_source_contract_production_phase_change_claim_allowed",
    "liquefied_breach_source_contract_cfd_solves_liquid_phase_change",
    "liquefied_breach_source_contract_cfd_solves_pool_spread_evaporation",
    "liquefied_breach_source_contract_cfd_solves_flashing_discharge",
    "liquefied_breach_preset_templates_production_phase_change_claim_allowed",
    "multi_fuel_production_ready",
    "strict_fire_calibration_blocker_cleared",
    "fire_residual_budget_clears_strict_blocker",
    "fire_residual_budget_pressure_agreement_ready",
    "fire_residual_budget_radiation_agreement_ready",
    "fire_residual_budget_production_claim_allowed",
    "fire_candidate_sources_repository_package_ready",
    "exp002_cfd_outputs_sufficient_for_pressure_agreement",
    "mdpi_radiation_integrated_cfd_proxy_outputs_sufficient_for_mdpi_agreement",
    "strict_external_plume_blocker_cleared",
    "dataverse_existing_120s_all_sensors_passed",
    "dataverse_amr_source_projection_current_single_level",
    "dataverse_amr_source_projection_lacks_level_aware_mask",
    "dataverse_geometry_ready_for_full_mesh_parity",
    "dataverse_geometry_obstacle_exact_bounds_available",
    "strict_real_cad_blocker_cleared",
    "real_cad_boundary_contract_ready_for_credit",
]

EXPECTED_STRICT_BLOCKERS = {
    "reference_agreement_is_threshold_only_not_external_plume_shape_dataset",
    "geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup",
    "fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure",
}

REQUIRED_TEXT_SNIPPETS = [
    "my-pele current evidence-backed status",
    "current-scope gates: 15/15",
    "current user-priority ready: yes",
    "CPU/MPI all scenarios: yes",
    "single GPU all scenarios: yes",
    "multi-GPU MPI+CUDA all scenarios: yes",
    "release-candidate handoff: PASS-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF",
    "release-candidate handoff ready: yes",
    "release-candidate current scope ready: yes",
    "release-candidate usable for current priority scope: yes",
    "release-candidate is full strict master-plan completion: no",
    "release-candidate open strict blockers: 3",
    "project closeout forecast: PASS-PROJECT-CLOSEOUT-FORECAST",
    "project closeout acceptance gate: PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE",
    "current phase acceptance allowed: yes",
    "strict final acceptance allowed: no",
    "current scope can be closed now: yes",
    "strict master-plan can be closed now: no",
    "strict closeout requires external artifacts: yes",
    "strict completion gate: AWAITING-STRICT-MASTER-PLAN-COMPLETION-GATE-EXTERNAL-ARTIFACTS",
    "strict completion gate ready: yes",
    "strict completion allowed: no",
    "strict completion external artifacts missing: yes",
    "strict external artifact drop index: PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX",
    "strict external artifact drop index ready: yes",
    "strict external artifact domains: 3",
    "strict external artifact required files: 14",
    "strict external artifact files still missing:",
    "strict external evidence receiving pack: PASS-STRICT-EXTERNAL-EVIDENCE-RECEIVING-PACK",
    "strict external evidence receiving pack ready: yes",
    "strict external evidence receiving pack present/missing:",
    "strict external evidence receiving pack completion allowed: no",
    "strict master-plan closeout action pack: PASS-STRICT-MASTER-PLAN-CLOSEOUT-ACTION-PACK",
    "strict master-plan closeout action pack ready: yes",
    "strict master-plan action items done/missing:",
    "strict master-plan action pack completion allowed: no",
    "strict master-plan action pack still open: yes",
    "current-scope delivery package: PASS-CURRENT-SCOPE-DELIVERY-PACKAGE",
    "current-scope delivery package ready: yes",
    "current-scope delivery package can be closed now: yes",
    "current-scope delivery package full log passed: yes",
    "current-scope delivery package missing required commands: 0",
    "current-scope final handoff note: PASS-CURRENT-SCOPE-FINAL-HANDOFF-NOTE",
    "current-scope final handoff note ready: yes",
    "current phase closure certificate: PASS-CURRENT-PHASE-CLOSURE-CERTIFICATE",
    "current phase closure certificate ready: yes",
    "current phase closeable: yes",
    "closure certificate strict master-plan closure allowed: no",
    "closure certificate strict master-plan still open: yes",
    "closure certificate last full current-scope log passed: yes",
    "current phase release manifest: PASS-CURRENT-PHASE-RELEASE-MANIFEST",
    "current phase release manifest ready: yes",
    "current phase release manifest latest full log passed: yes",
    "current phase release manifest strict master-plan closure allowed: no",
    "operator command inventory: PASS-CURRENT-OPERATOR-COMMAND-INVENTORY",
    "operator command inventory ready: yes",
    "operator command inventory missing required snippets: 0",
    "operator command inventory missing tools: 0",
    "operator command inventory syntax failures: 0",
    "SUNDIALS local link audit: PASS-SUNDIALS-LOCAL-LINK-AUDIT",
    "SUNDIALS local link audit ready: yes",
    "SUNDIALS local link drift present: yes",
    "SUNDIALS local link current kind:",
    "SUNDIALS safe to auto-restore: no",
    "SUNDIALS restore requires operator review: yes",
    "current-scope final handoff note README missing snippets: 0",
    "current-scope final handoff note runbook missing snippets: 0",
    "Fuel and liquefied-gas boundary",
    "multi-fuel capability: PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY",
    "multi-fuel template catalog: PASS-ENGINEERING-MULTI-FUEL-TEMPLATE-CATALOG",
    "multi-fuel template catalog ready: yes",
    "multi-fuel template count: 5",
    "multi-fuel template species: C3H8, CH4, H2",
    "multi-fuel template CSV ready: yes",
    "multi-fuel template liquefied nonclaim comments: yes",
    "configurable fuel species: yes",
    "H2 current engineering scope: yes",
    "CH4 gas/fire probes: yes",
    "C3H8 gas/fire probes: yes",
    "gasified LNG surrogate boundary: yes",
    "gasified LPG surrogate boundary: yes",
    "external vaporization multi-fuel CUDA: yes",
    "liquefied release source-model CUDA smoke: yes",
    "liquefied release source balance: yes",
    "liquefied release source balance status: PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE",
    "liquefied release source balance species: C3H8, CH4",
    "liquefied release source mapping schedule matches CSV: yes",
    "liquefied release source generated input matches mapping: yes",
    "liquefied release source balance negative selftest: yes",
    "liquefied release source balance negative selftest status: PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE-NEGATIVE-SELFTEST",
    "liquefied release source balance negative cases rejected: 5/5",
    "liquefied release source balance expected diagnostics: 5/5",
    "liquefied release source guard negative mdot: yes",
    "liquefied release source guard species drift: yes",
    "liquefied release source guard schedule mismatch: yes",
    "liquefied release source guard phase-change overclaim: yes",
    "liquefied release source guard generated-input species mismatch: yes",
    "liquefied release thermal plausibility status: PASS-ENGINEERING-LIQUEFIED-RELEASE-THERMAL-PLAUSIBILITY",
    "liquefied release thermal plausibility ready: yes",
    "liquefied release thermal species: C3H8, CH4",
    "liquefied release vaporized fraction formula: yes",
    "liquefied release heat loads positive: yes",
    "liquefied breach source contract status: PASS-ENGINEERING-LIQUEFIED-BREACH-SOURCE-CONTRACT",
    "liquefied breach source contract ready: yes",
    "liquefied breach source contract cases: 2",
    "liquefied breach source contract fluids: LNG_CH4, LPG_C3H8",
    "liquefied breach source contract species: C3H8, CH4",
    "liquefied breach source accepts screening breach inputs: yes",
    "liquefied breach source generates external gas source: yes",
    "liquefied breach source production phase-change claim allowed: no",
    "liquefied breach preset templates status: PASS-ENGINEERING-LIQUEFIED-BREACH-PRESET-TEMPLATES",
    "liquefied breach preset templates ready: yes",
    "liquefied breach preset templates editable JSON: yes",
    "liquefied breach preset templates count: 2",
    "liquefied breach preset templates fluids: LNG_CH4, LPG_C3H8",
    "liquefied breach preset templates species: C3H8, CH4",
    "liquefied breach preset templates generate CFD CSV: yes",
    "liquefied breach preset templates production phase-change claim allowed: no",
    "liquefied phase-change overclaim guard status: PASS-ENGINEERING-LIQUEFIED-PHASE-CHANGE-OVERCLAIM-GUARD",
    "liquefied phase-change overclaim guard ready: yes",
    "liquefied gasified LNG/LPG bridge ready: yes",
    "liquefied external vaporization bridge ready: yes",
    "liquefied screening source ready: yes",
    "liquefied CUDA source runtime ready: yes",
    "liquefied production phase-change claim allowed: no",
    "liquefied CFD solves liquid phase-change: no",
    "liquefied CFD solves pool spread/boiling: no",
    "liquefied CFD solves flashing discharge: no",
    "internal liquid phase-change CFD: no",
    "multi-fuel production-ready claim: no",
    "overclaim guard: yes",
    "External plume reference boundary",
    "strict external plume status: TRIAGED-MASTER-PLAN-STRICT-EXTERNAL-SOURCES-PUBLIC-DATA-INCOMPLETE",
    "external plume blocker present: yes",
    "external plume blocker cleared: no",
    "public machine-readable plume time series found: yes",
    "public SBEPV5/D27 geometry and release conditions found: yes",
    "Dataverse full dataset all files ready: yes",
    "Dataverse agreement ready for CFD scoring: yes",
    "Dataverse agreement sensor count: 29",
    "Dataverse 45s agreement attempt status: QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
    "Dataverse 45s agreement failed sensors: 28",
    "Dataverse 120s agreement attempt status: QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
    "Dataverse 120s agreement failed sensors: 29",
    "Dataverse long-window reconciliation: TRIAGED-DATAVERSE-OPEN-CHANNEL-LONG-WINDOW-REFINED-SOURCE-GAP",
    "Dataverse existing 120s reaches experimental peak interval: yes",
    "Dataverse existing 120s all sensors passed: no",
    "Dataverse existing 120s failed sensors: 29",
    "Dataverse current refined-source time end s: 0.005",
    "Dataverse current refined-source steps to 113s: 22600000",
    "Dataverse AMR current projection single-level: no",
    "Dataverse AMR lacks level-aware mask: no",
    "Dataverse AMR finest-owner projection: yes",
    "Dataverse AMR implementation status: PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-IMPLEMENTATION",
    "Dataverse AMR implementation ready: yes",
    "Dataverse AMR MPI+CUDA linked executable: yes",
    "Dataverse AMR MPI+CUDA reproducible build entrypoint: yes",
    "Dataverse AMR MPI+CUDA reproducible build uses CUDA 12.6: yes",
    "Dataverse AMR MPI+CUDA reproducible build uses local SUNDIALS-CUDA: yes",
    "Dataverse geometry ready for sensor sampling map: yes",
    "Dataverse geometry ready for full mesh parity: no",
    "Dataverse obstacle exact bounds available: no",
    "Dataverse refined-source strict blocker still open: yes",
    "Real CAD boundary",
    "strict real CAD status: TRIAGED-MASTER-PLAN-STRICT-REAL-CAD-ARTIFACTS-MISSING",
    "real CAD blocker present: yes",
    "real CAD blocker cleared: no",
    "real CAD handoff contract status: PASS-H2-REAL-CAD-HANDOFF-CONTRACT",
    "real CAD handoff contract ready: yes",
    "real CAD source CAD files: 0",
    "real CAD cleaned geometry files: 0",
    "real CAD boundary contract status: NOT_READY-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT",
    "real CAD boundary contract ready for credit: no",
    "real CAD negative selftest status: PASS-H2-REAL-CAD-GUARD-NEGATIVE-SELFTEST",
    "real CAD negative selftest ready: yes",
    "real CAD negative cases rejected: 8/8",
    "real CAD expected diagnostics: 8/8",
    "real CAD guard synthetic manifest: yes",
    "real CAD guard missing provenance: yes",
    "real CAD guard source hash mismatch: yes",
    "real CAD guard large-layout too few geometries: yes",
    "real CAD guard data-room bad hash: yes",
    "real CAD guard cleanup quality false check: yes",
    "real CAD guard boundary placeholder: yes",
    "real CAD guard boundary missing required role: yes",
    "Fire consequence calibration boundary",
    "strict fire calibration status: TRIAGED-MASTER-PLAN-STRICT-FIRE-CALIBRATION-PARTIAL-DATA-BRIDGED",
    "fire calibration blocker present: yes",
    "fire calibration blocker cleared: no",
    "fire candidate radiation+overpressure sources available: yes",
    "fire candidate repository package ready: no",
    "EXP002 reduced overpressure status: PASS-H2-FIRE-OVERPRESSURE-REDUCED-EXP002",
    "EXP002 source CSV MD5 verified: yes",
    "EXP002 pressure channels: 4",
    "EXP002 overpressure metrics: 4",
    "EXP002 pressure CFD proxy extracted: yes",
    "EXP002 pressure CFD proxy CPU/GPU parity: yes",
    "EXP002 CFD outputs sufficient for pressure agreement: no",
    "plotfile sensor sampling contract: yes",
    "plotfile sensor sampling negative cases rejected: 8/8",
    "MDPI radiation metrics: 4",
    "MDPI integrated radiation CFD proxy extracted: yes",
    "MDPI virtual radiometer flux generated: yes",
    "MDPI CFD outputs sufficient for radiation agreement: no",
    "fire residual budget status: TRIAGED-H2-FIRE-CALIBRATION-RESIDUAL-BUDGET",
    "fire residual budget ready: yes",
    "fire residual budget clears strict blocker: no",
    "fire residual budget pressure agreement ready: no",
    "fire residual budget radiation agreement ready: no",
    "fire residual budget pressure missing artifacts: 3",
    "fire residual budget radiation missing artifacts: 3",
    "fire residual budget production claim allowed: no",
    "goal complete: no",
    "strict master-plan complete: no",
    "open strict blocker count: 3",
    "strict unblock runbook: docs/codex_audit/strict_master_plan_unblock_runbook.md",
]


class CurrentStatusCliError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CurrentStatusCliError(message)


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
        raise CurrentStatusCliError(f"missing JSON evidence: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CurrentStatusCliError(f"invalid JSON evidence {path}: {exc}") from exc
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


def run_cli(argv: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        argv,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stdout_head": completed.stdout.strip().splitlines()[:80],
    }


def parse_cli_json(output: str) -> dict[str, Any]:
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise CurrentStatusCliError(f"status CLI JSON output is invalid: {exc}") from exc
    require(isinstance(data, dict), "status CLI JSON output is not an object")
    return data


def compute_expected_snapshot_key_report_count() -> int:
    require(SNAPSHOT_WRITER.is_file(), f"missing state snapshot writer: {SNAPSHOT_WRITER}")
    spec = importlib.util.spec_from_file_location("current_scope_state_snapshot", SNAPSHOT_WRITER)
    require(spec is not None and spec.loader is not None, "unable to load state snapshot writer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    key_reports = getattr(module, "KEY_REPORTS", None)
    require(isinstance(key_reports, dict), "state snapshot writer missing KEY_REPORTS dict")
    return len(key_reports)


def build_report() -> dict[str, Any]:
    require(CLI.is_file(), f"missing current status CLI: {CLI}")

    source_statuses = {}
    evidence_files = [
        evidence_entry("current_status_cli", CLI),
        evidence_entry("state_snapshot_writer", SNAPSHOT_WRITER),
    ]
    for label, path in SOURCE_REPORTS.items():
        data = load_json(path)
        source_statuses[label] = data.get("status")
        evidence_files.append(evidence_entry(label, path))

    text_run = run_cli(["python3", str(CLI)])
    json_run = run_cli(["python3", str(CLI), "--json"])
    parsed = parse_cli_json(json_run["stdout"]) if json_run["returncode"] == 0 else {}

    missing_text_snippets = [snippet for snippet in REQUIRED_TEXT_SNIPPETS if snippet not in text_run["stdout"]]
    missing_json_statuses = [
        key for key, expected in EXPECTED_STATUS.items() if parsed.get(key) != expected
    ]
    missing_json_true = [key for key in EXPECTED_BOOL_TRUE if parsed.get(key) is not True]
    missing_json_false = [key for key in EXPECTED_BOOL_FALSE if parsed.get(key) is not False]
    strict_blockers = set(parsed.get("open_strict_blockers", []))
    state_snapshot = load_json(SOURCE_REPORTS["state_snapshot"])
    state_snapshot_report_count = state_snapshot.get("summary", {}).get("key_report_count")
    expected_snapshot_key_report_count = compute_expected_snapshot_key_report_count()
    snapshot_key_report_count_matches = (
        parsed.get("snapshot_key_report_count") == expected_snapshot_key_report_count
    )
    state_snapshot_report_count_matches_writer = (
        state_snapshot_report_count == expected_snapshot_key_report_count
    )

    ready = (
        text_run["returncode"] == 0
        and json_run["returncode"] == 0
        and not missing_text_snippets
        and not missing_json_statuses
        and not missing_json_true
        and not missing_json_false
        and parsed.get("current_scope_gate_count") == 15
        and parsed.get("current_scope_passed_gate_count") == 15
        and parsed.get("open_strict_blocker_count") == 3
        and strict_blockers == EXPECTED_STRICT_BLOCKERS
        and parsed.get("strict_unblock_runbook") == "docs/codex_audit/strict_master_plan_unblock_runbook.md"
        and snapshot_key_report_count_matches
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_PASS if ready else STATUS_NOT_READY,
        "summary": {
            "current_status_cli_ready": ready,
            "text_returncode": text_run["returncode"],
            "json_returncode": json_run["returncode"],
            "missing_text_snippet_count": len(missing_text_snippets),
            "missing_json_status_count": len(missing_json_statuses),
            "missing_json_true_count": len(missing_json_true),
            "missing_json_false_count": len(missing_json_false),
            "current_scope_gate_count": parsed.get("current_scope_gate_count"),
            "current_scope_passed_gate_count": parsed.get("current_scope_passed_gate_count"),
            "open_strict_blocker_count": parsed.get("open_strict_blocker_count"),
            "strict_blocker_set_ok": strict_blockers == EXPECTED_STRICT_BLOCKERS,
            "snapshot_key_report_count_seen": parsed.get("snapshot_key_report_count"),
            "snapshot_key_report_count_expected": expected_snapshot_key_report_count,
            "snapshot_key_report_count_matches": snapshot_key_report_count_matches,
            "state_snapshot_report_key_report_count": state_snapshot_report_count,
            "state_snapshot_report_count_matches_writer": state_snapshot_report_count_matches_writer,
            "snapshot_key_report_count_expected_source": "tools/write_current_scope_state_snapshot_report.py::KEY_REPORTS",
            "goal_complete": parsed.get("goal_complete"),
            "strict_master_plan_complete": parsed.get("strict_master_plan_complete"),
            "release_candidate_handoff_status": parsed.get("release_candidate_handoff_status"),
            "release_candidate_handoff_ready": parsed.get("release_candidate_handoff_ready"),
            "release_candidate_current_scope_ready": parsed.get("release_candidate_current_scope_ready"),
            "release_candidate_can_be_used_for_current_priority_scope": parsed.get(
                "release_candidate_can_be_used_for_current_priority_scope"
            ),
            "release_candidate_is_full_strict_master_plan_completion": parsed.get(
                "release_candidate_is_full_strict_master_plan_completion"
            ),
            "release_candidate_open_strict_blocker_count": parsed.get(
                "release_candidate_open_strict_blocker_count"
            ),
            "project_closeout_forecast_status": parsed.get("project_closeout_forecast_status"),
            "project_closeout_current_release_candidate_ready": parsed.get(
                "project_closeout_current_release_candidate_ready"
            ),
            "project_closeout_current_scope_can_be_closed_now": parsed.get(
                "project_closeout_current_scope_can_be_closed_now"
            ),
            "project_closeout_current_scope_closeout_estimate": parsed.get(
                "project_closeout_current_scope_closeout_estimate"
            ),
            "project_closeout_strict_master_plan_can_be_closed_now": parsed.get(
                "project_closeout_strict_master_plan_can_be_closed_now"
            ),
            "project_closeout_strict_closeout_requires_external_artifacts": parsed.get(
                "project_closeout_strict_closeout_requires_external_artifacts"
            ),
            "project_closeout_strict_closeout_estimate_after_artifacts": parsed.get(
                "project_closeout_strict_closeout_estimate_after_artifacts"
            ),
            "project_closeout_acceptance_gate_status": parsed.get(
                "project_closeout_acceptance_gate_status"
            ),
            "project_closeout_acceptance_gate_ready": parsed.get(
                "project_closeout_acceptance_gate_ready"
            ),
            "project_closeout_current_phase_acceptance_allowed": parsed.get(
                "project_closeout_current_phase_acceptance_allowed"
            ),
            "project_closeout_strict_final_acceptance_allowed": parsed.get(
                "project_closeout_strict_final_acceptance_allowed"
            ),
            "project_closeout_strict_external_artifact_done_count": parsed.get(
                "project_closeout_strict_external_artifact_done_count"
            ),
            "project_closeout_strict_external_artifact_missing_count": parsed.get(
                "project_closeout_strict_external_artifact_missing_count"
            ),
            "strict_master_plan_completion_gate_status": parsed.get(
                "strict_master_plan_completion_gate_status"
            ),
            "strict_master_plan_completion_gate_ready": parsed.get(
                "strict_master_plan_completion_gate_ready"
            ),
            "strict_completion_current_scope_closure_allowed": parsed.get(
                "strict_completion_current_scope_closure_allowed"
            ),
            "strict_completion_allowed": parsed.get("strict_completion_allowed"),
            "strict_completion_external_artifacts_missing": parsed.get(
                "strict_completion_external_artifacts_missing"
            ),
            "strict_external_artifact_drop_index_status": parsed.get(
                "strict_external_artifact_drop_index_status"
            ),
            "strict_external_artifact_drop_index_ready": parsed.get(
                "strict_external_artifact_drop_index_ready"
            ),
            "strict_external_artifact_drop_index_domain_count": parsed.get(
                "strict_external_artifact_drop_index_domain_count"
            ),
            "strict_external_artifact_drop_index_template_count": parsed.get(
                "strict_external_artifact_drop_index_template_count"
            ),
            "strict_external_artifact_drop_index_contract_check_count": parsed.get(
                "strict_external_artifact_drop_index_contract_check_count"
            ),
            "strict_external_artifact_drop_index_awaiting_missing_artifact_count": parsed.get(
                "strict_external_artifact_drop_index_awaiting_missing_artifact_count"
            ),
            "strict_external_evidence_receiving_pack_status": parsed.get(
                "strict_external_evidence_receiving_pack_status"
            ),
            "strict_external_evidence_receiving_pack_ready": parsed.get(
                "strict_external_evidence_receiving_pack_ready"
            ),
            "strict_external_evidence_receiving_pack_required_file_count": parsed.get(
                "strict_external_evidence_receiving_pack_required_file_count"
            ),
            "strict_external_evidence_receiving_pack_present_file_count": parsed.get(
                "strict_external_evidence_receiving_pack_present_file_count"
            ),
            "strict_external_evidence_receiving_pack_missing_file_count": parsed.get(
                "strict_external_evidence_receiving_pack_missing_file_count"
            ),
            "strict_external_evidence_receiving_pack_completion_allowed": parsed.get(
                "strict_external_evidence_receiving_pack_completion_allowed"
            ),
            "strict_external_evidence_receiving_pack_still_open": parsed.get(
                "strict_external_evidence_receiving_pack_still_open"
            ),
            "strict_master_plan_closeout_action_pack_status": parsed.get(
                "strict_master_plan_closeout_action_pack_status"
            ),
            "strict_master_plan_closeout_action_pack_ready": parsed.get(
                "strict_master_plan_closeout_action_pack_ready"
            ),
            "strict_master_plan_closeout_action_pack_current_phase_closeable": parsed.get(
                "strict_master_plan_closeout_action_pack_current_phase_closeable"
            ),
            "strict_master_plan_closeout_action_pack_completion_allowed": parsed.get(
                "strict_master_plan_closeout_action_pack_completion_allowed"
            ),
            "strict_master_plan_closeout_action_pack_still_open": parsed.get(
                "strict_master_plan_closeout_action_pack_still_open"
            ),
            "strict_master_plan_closeout_action_pack_done_count": parsed.get(
                "strict_master_plan_closeout_action_pack_done_count"
            ),
            "strict_master_plan_closeout_action_pack_missing_count": parsed.get(
                "strict_master_plan_closeout_action_pack_missing_count"
            ),
            "current_scope_delivery_package_status": parsed.get("current_scope_delivery_package_status"),
            "current_scope_delivery_package_ready": parsed.get("current_scope_delivery_package_ready"),
            "current_scope_delivery_package_current_scope_can_be_closed_now": parsed.get(
                "current_scope_delivery_package_current_scope_can_be_closed_now"
            ),
            "current_scope_delivery_package_last_full_log_passed": parsed.get(
                "current_scope_delivery_package_last_full_log_passed"
            ),
            "current_scope_delivery_package_missing_required_operator_command_count": parsed.get(
                "current_scope_delivery_package_missing_required_operator_command_count"
            ),
            "current_scope_final_handoff_note_status": parsed.get("current_scope_final_handoff_note_status"),
            "current_scope_final_handoff_note_ready": parsed.get("current_scope_final_handoff_note_ready"),
            "current_scope_final_handoff_note_readme_missing_snippet_count": parsed.get(
                "current_scope_final_handoff_note_readme_missing_snippet_count"
            ),
            "current_scope_final_handoff_note_runbook_missing_snippet_count": parsed.get(
                "current_scope_final_handoff_note_runbook_missing_snippet_count"
            ),
            "current_phase_closure_certificate_status": parsed.get(
                "current_phase_closure_certificate_status"
            ),
            "current_phase_closure_certificate_ready": parsed.get(
                "current_phase_closure_certificate_ready"
            ),
            "current_phase_closeable": parsed.get("current_phase_closeable"),
            "closure_certificate_strict_master_plan_closure_allowed": parsed.get(
                "closure_certificate_strict_master_plan_closure_allowed"
            ),
            "closure_certificate_strict_master_plan_still_open": parsed.get(
                "closure_certificate_strict_master_plan_still_open"
            ),
            "closure_certificate_last_full_current_scope_log": parsed.get(
                "closure_certificate_last_full_current_scope_log"
            ),
            "closure_certificate_last_full_current_scope_log_passed": parsed.get(
                "closure_certificate_last_full_current_scope_log_passed"
            ),
            "current_phase_release_manifest_status": parsed.get(
                "current_phase_release_manifest_status"
            ),
            "current_phase_release_manifest_ready": parsed.get(
                "current_phase_release_manifest_ready"
            ),
            "current_phase_release_manifest_hashed_artifact_count": parsed.get(
                "current_phase_release_manifest_hashed_artifact_count"
            ),
            "current_phase_release_manifest_latest_full_log_passed": parsed.get(
                "current_phase_release_manifest_latest_full_log_passed"
            ),
            "current_phase_release_manifest_current_phase_closeable": parsed.get(
                "current_phase_release_manifest_current_phase_closeable"
            ),
            "current_phase_release_manifest_strict_master_plan_closure_allowed": parsed.get(
                "current_phase_release_manifest_strict_master_plan_closure_allowed"
            ),
            "operator_command_inventory_status": parsed.get("operator_command_inventory_status"),
            "operator_command_inventory_ready": parsed.get("operator_command_inventory_ready"),
            "operator_command_inventory_source_file_count": parsed.get(
                "operator_command_inventory_source_file_count"
            ),
            "operator_command_inventory_command_count": parsed.get(
                "operator_command_inventory_command_count"
            ),
            "operator_command_inventory_required_snippet_count": parsed.get(
                "operator_command_inventory_required_snippet_count"
            ),
            "operator_command_inventory_missing_required_snippet_count": parsed.get(
                "operator_command_inventory_missing_required_snippet_count"
            ),
            "operator_command_inventory_missing_tool_count": parsed.get(
                "operator_command_inventory_missing_tool_count"
            ),
            "operator_command_inventory_syntax_failure_count": parsed.get(
                "operator_command_inventory_syntax_failure_count"
            ),
            "sundials_local_link_audit_status": parsed.get("sundials_local_link_audit_status"),
            "sundials_local_link_audit_ready": parsed.get("sundials_local_link_audit_ready"),
            "sundials_local_link_drift_present": parsed.get("sundials_local_link_drift_present"),
            "sundials_local_link_current_kind": parsed.get("sundials_local_link_current_kind"),
            "sundials_local_link_expected_target_exists": parsed.get(
                "sundials_local_link_expected_target_exists"
            ),
            "sundials_local_link_cuda_ready_candidate_count": parsed.get(
                "sundials_local_link_cuda_ready_candidate_count"
            ),
            "sundials_local_link_safe_to_auto_restore": parsed.get(
                "sundials_local_link_safe_to_auto_restore"
            ),
            "sundials_restore_requires_explicit_operator_review": parsed.get(
                "sundials_restore_requires_explicit_operator_review"
            ),
            "multi_fuel_capability_status": parsed.get("multi_fuel_capability_status"),
            "multi_fuel_template_catalog_status": parsed.get("multi_fuel_template_catalog_status"),
            "multi_fuel_template_catalog_ready": parsed.get("multi_fuel_template_catalog_ready"),
            "multi_fuel_template_catalog_template_count": parsed.get("multi_fuel_template_catalog_template_count"),
            "multi_fuel_template_catalog_fuel_species_seen": parsed.get(
                "multi_fuel_template_catalog_fuel_species_seen"
            ),
            "multi_fuel_template_catalog_csv_template_ready": parsed.get(
                "multi_fuel_template_catalog_csv_template_ready"
            ),
            "multi_fuel_template_catalog_liquefied_nonclaim_comments_present": parsed.get(
                "multi_fuel_template_catalog_liquefied_nonclaim_comments_present"
            ),
            "multi_fuel_template_catalog_cfd_internal_liquid_phase_change_claim_allowed": parsed.get(
                "multi_fuel_template_catalog_cfd_internal_liquid_phase_change_claim_allowed"
            ),
            "source_fuel_species_configurable": parsed.get("source_fuel_species_configurable"),
            "h2_engineering_current_scope_ready": parsed.get("h2_engineering_current_scope_ready"),
            "ch4_gas_fire_probe_ready": parsed.get("ch4_gas_fire_probe_ready"),
            "c3h8_gas_fire_probe_ready": parsed.get("c3h8_gas_fire_probe_ready"),
            "gasified_lng_given_source_surrogate_ready": parsed.get("gasified_lng_given_source_surrogate_ready"),
            "gasified_lpg_given_source_surrogate_ready": parsed.get("gasified_lpg_given_source_surrogate_ready"),
            "external_vaporization_multifuel_timeseries_cuda_passed": parsed.get(
                "external_vaporization_multifuel_timeseries_cuda_passed"
            ),
            "liquefied_release_vaporization_source_model_cuda_smoke_passed": parsed.get(
                "liquefied_release_vaporization_source_model_cuda_smoke_passed"
            ),
            "liquefied_release_source_balance_status": parsed.get("liquefied_release_source_balance_status"),
            "liquefied_release_source_balance_ready": parsed.get("liquefied_release_source_balance_ready"),
            "liquefied_release_source_balance_case_count": parsed.get("liquefied_release_source_balance_case_count"),
            "liquefied_release_source_balance_species": parsed.get("liquefied_release_source_balance_species"),
            "liquefied_release_source_balance_total_gas_mass_integral_kg": parsed.get(
                "liquefied_release_source_balance_total_gas_mass_integral_kg"
            ),
            "liquefied_release_source_balance_max_inventory_mass_relative_error": parsed.get(
                "liquefied_release_source_balance_max_inventory_mass_relative_error"
            ),
            "liquefied_release_source_balance_mapping_schedule_matches_csv": parsed.get(
                "liquefied_release_source_balance_mapping_schedule_matches_csv"
            ),
            "liquefied_release_source_balance_generated_input_matches_mapping": parsed.get(
                "liquefied_release_source_balance_generated_input_matches_mapping"
            ),
            "liquefied_release_source_balance_negative_selftest_status": parsed.get(
                "liquefied_release_source_balance_negative_selftest_status"
            ),
            "liquefied_release_source_balance_negative_selftest_ready": parsed.get(
                "liquefied_release_source_balance_negative_selftest_ready"
            ),
            "liquefied_release_source_balance_negative_case_count": parsed.get(
                "liquefied_release_source_balance_negative_case_count"
            ),
            "liquefied_release_source_balance_negative_rejected_count": parsed.get(
                "liquefied_release_source_balance_negative_rejected_count"
            ),
            "liquefied_release_source_balance_expected_fragment_seen_count": parsed.get(
                "liquefied_release_source_balance_expected_fragment_seen_count"
            ),
            "liquefied_release_source_balance_guards_negative_mdot": parsed.get(
                "liquefied_release_source_balance_guards_negative_mdot"
            ),
            "liquefied_release_source_balance_guards_species_drift": parsed.get(
                "liquefied_release_source_balance_guards_species_drift"
            ),
            "liquefied_release_source_balance_guards_schedule_rate_mismatch": parsed.get(
                "liquefied_release_source_balance_guards_schedule_rate_mismatch"
            ),
            "liquefied_release_source_balance_guards_phase_change_overclaim": parsed.get(
                "liquefied_release_source_balance_guards_phase_change_overclaim"
            ),
            "liquefied_release_source_balance_guards_generated_input_species_mismatch": parsed.get(
                "liquefied_release_source_balance_guards_generated_input_species_mismatch"
            ),
            "liquefied_release_thermal_plausibility_status": parsed.get(
                "liquefied_release_thermal_plausibility_status"
            ),
            "liquefied_release_thermal_plausibility_ready": parsed.get(
                "liquefied_release_thermal_plausibility_ready"
            ),
            "liquefied_release_thermal_species": parsed.get("liquefied_release_thermal_species"),
            "liquefied_release_thermal_vaporized_fraction_formula_ok": parsed.get(
                "liquefied_release_thermal_vaporized_fraction_formula_ok"
            ),
            "liquefied_release_thermal_heat_loads_positive": parsed.get(
                "liquefied_release_thermal_heat_loads_positive"
            ),
            "liquefied_release_thermal_max_gas_mass_relative_error": parsed.get(
                "liquefied_release_thermal_max_gas_mass_relative_error"
            ),
            "liquefied_breach_source_contract_status": parsed.get("liquefied_breach_source_contract_status"),
            "liquefied_breach_source_contract_ready": parsed.get("liquefied_breach_source_contract_ready"),
            "liquefied_breach_source_contract_case_count": parsed.get("liquefied_breach_source_contract_case_count"),
            "liquefied_breach_source_contract_fluids": parsed.get("liquefied_breach_source_contract_fluids"),
            "liquefied_breach_source_contract_species": parsed.get("liquefied_breach_source_contract_species"),
            "liquefied_breach_source_contract_accepts_screening_breach_inputs": parsed.get(
                "liquefied_breach_source_contract_accepts_screening_breach_inputs"
            ),
            "liquefied_breach_source_contract_generates_external_gas_source": parsed.get(
                "liquefied_breach_source_contract_generates_external_gas_source"
            ),
            "liquefied_breach_source_contract_max_gas_mass_relative_error": parsed.get(
                "liquefied_breach_source_contract_max_gas_mass_relative_error"
            ),
            "liquefied_breach_source_contract_max_peak_jet_speed_m_s": parsed.get(
                "liquefied_breach_source_contract_max_peak_jet_speed_m_s"
            ),
            "liquefied_breach_source_contract_production_phase_change_claim_allowed": parsed.get(
                "liquefied_breach_source_contract_production_phase_change_claim_allowed"
            ),
            "liquefied_breach_source_contract_cfd_solves_liquid_phase_change": parsed.get(
                "liquefied_breach_source_contract_cfd_solves_liquid_phase_change"
            ),
            "liquefied_breach_source_contract_cfd_solves_pool_spread_evaporation": parsed.get(
                "liquefied_breach_source_contract_cfd_solves_pool_spread_evaporation"
            ),
            "liquefied_breach_source_contract_cfd_solves_flashing_discharge": parsed.get(
                "liquefied_breach_source_contract_cfd_solves_flashing_discharge"
            ),
            "liquefied_breach_preset_templates_status": parsed.get(
                "liquefied_breach_preset_templates_status"
            ),
            "liquefied_breach_preset_templates_ready": parsed.get(
                "liquefied_breach_preset_templates_ready"
            ),
            "liquefied_breach_preset_templates_editable_json_presets": parsed.get(
                "liquefied_breach_preset_templates_editable_json_presets"
            ),
            "liquefied_breach_preset_templates_preset_count": parsed.get(
                "liquefied_breach_preset_templates_preset_count"
            ),
            "liquefied_breach_preset_templates_fluids": parsed.get(
                "liquefied_breach_preset_templates_fluids"
            ),
            "liquefied_breach_preset_templates_species": parsed.get(
                "liquefied_breach_preset_templates_species"
            ),
            "liquefied_breach_preset_templates_generates_cfd_source_csv": parsed.get(
                "liquefied_breach_preset_templates_generates_cfd_source_csv"
            ),
            "liquefied_breach_preset_templates_max_peak_gas_mdot_kg_s": parsed.get(
                "liquefied_breach_preset_templates_max_peak_gas_mdot_kg_s"
            ),
            "liquefied_breach_preset_templates_production_phase_change_claim_allowed": parsed.get(
                "liquefied_breach_preset_templates_production_phase_change_claim_allowed"
            ),
            "liquefied_phase_change_overclaim_guard_status": parsed.get(
                "liquefied_phase_change_overclaim_guard_status"
            ),
            "liquefied_phase_change_overclaim_guard_ready": parsed.get(
                "liquefied_phase_change_overclaim_guard_ready"
            ),
            "liquefied_phase_change_gasified_lng_lpg_bridge_ready": parsed.get(
                "liquefied_phase_change_gasified_lng_lpg_bridge_ready"
            ),
            "liquefied_phase_change_external_vaporization_bridge_ready": parsed.get(
                "liquefied_phase_change_external_vaporization_bridge_ready"
            ),
            "liquefied_phase_change_screening_source_ready": parsed.get(
                "liquefied_phase_change_screening_source_ready"
            ),
            "liquefied_phase_change_cuda_runtime_ready": parsed.get(
                "liquefied_phase_change_cuda_runtime_ready"
            ),
            "liquefied_phase_change_production_claim_allowed": parsed.get(
                "liquefied_phase_change_production_claim_allowed"
            ),
            "liquefied_phase_change_cfd_solves_liquid_phase_change": parsed.get(
                "liquefied_phase_change_cfd_solves_liquid_phase_change"
            ),
            "liquefied_phase_change_cfd_solves_pool_spread_evaporation": parsed.get(
                "liquefied_phase_change_cfd_solves_pool_spread_evaporation"
            ),
            "liquefied_phase_change_cfd_solves_flashing_discharge": parsed.get(
                "liquefied_phase_change_cfd_solves_flashing_discharge"
            ),
            "liquefied_gas_phase_change_ready": parsed.get("liquefied_gas_phase_change_ready"),
            "multi_fuel_production_ready": parsed.get("multi_fuel_production_ready"),
            "prevents_overclaim": parsed.get("prevents_overclaim"),
            "strict_external_plume_status": parsed.get("strict_external_plume_status"),
            "external_plume_blocker_present": parsed.get("external_plume_blocker_present"),
            "strict_external_plume_blocker_cleared": parsed.get("strict_external_plume_blocker_cleared"),
            "public_machine_readable_external_plume_timeseries_found": parsed.get(
                "public_machine_readable_external_plume_timeseries_found"
            ),
            "public_sbepv5_d27_geometry_and_release_conditions_found": parsed.get(
                "public_sbepv5_d27_geometry_and_release_conditions_found"
            ),
            "dataverse_full_dataset_all_files_ready": parsed.get("dataverse_full_dataset_all_files_ready"),
            "dataverse_full_dataset_ready_file_count": parsed.get("dataverse_full_dataset_ready_file_count"),
            "dataverse_reference_sensor_time_sample_count": parsed.get(
                "dataverse_reference_sensor_time_sample_count"
            ),
            "dataverse_reference_sensor_record_count": parsed.get("dataverse_reference_sensor_record_count"),
            "dataverse_agreement_ready_for_cfd_scoring": parsed.get("dataverse_agreement_ready_for_cfd_scoring"),
            "dataverse_agreement_sensor_count": parsed.get("dataverse_agreement_sensor_count"),
            "dataverse_cfd_45s_agreement_attempt_status": parsed.get(
                "dataverse_cfd_45s_agreement_attempt_status"
            ),
            "dataverse_cfd_45s_agreement_attempt_failed_sensor_count": parsed.get(
                "dataverse_cfd_45s_agreement_attempt_failed_sensor_count"
            ),
            "dataverse_cfd_45s_agreement_attempt_simulation_time_end_s": parsed.get(
                "dataverse_cfd_45s_agreement_attempt_simulation_time_end_s"
            ),
            "dataverse_cfd_120s_agreement_attempt_status": parsed.get(
                "dataverse_cfd_120s_agreement_attempt_status"
            ),
            "dataverse_cfd_120s_agreement_attempt_failed_sensor_count": parsed.get(
                "dataverse_cfd_120s_agreement_attempt_failed_sensor_count"
            ),
            "dataverse_cfd_120s_agreement_attempt_simulation_time_end_s": parsed.get(
                "dataverse_cfd_120s_agreement_attempt_simulation_time_end_s"
            ),
            "dataverse_long_window_reconciliation_status": parsed.get(
                "dataverse_long_window_reconciliation_status"
            ),
            "dataverse_existing_120s_reaches_peak_interval": parsed.get(
                "dataverse_existing_120s_reaches_peak_interval"
            ),
            "dataverse_existing_120s_all_sensors_passed": parsed.get(
                "dataverse_existing_120s_all_sensors_passed"
            ),
            "dataverse_existing_120s_failed_sensor_count": parsed.get(
                "dataverse_existing_120s_failed_sensor_count"
            ),
            "dataverse_current_refined_source_long_window_time_end_s": parsed.get(
                "dataverse_current_refined_source_long_window_time_end_s"
            ),
            "dataverse_current_refined_source_steps_to_113s": parsed.get(
                "dataverse_current_refined_source_steps_to_113s"
            ),
            "dataverse_amr_source_projection_current_single_level": parsed.get(
                "dataverse_amr_source_projection_current_single_level"
            ),
            "dataverse_amr_source_projection_lacks_level_aware_mask": parsed.get(
                "dataverse_amr_source_projection_lacks_level_aware_mask"
            ),
            "dataverse_amr_source_projection_finest_available_level_only": parsed.get(
                "dataverse_amr_source_projection_finest_available_level_only"
            ),
            "dataverse_amr_source_projection_implementation_status": parsed.get(
                "dataverse_amr_source_projection_implementation_status"
            ),
            "dataverse_amr_source_projection_implementation_ready": parsed.get(
                "dataverse_amr_source_projection_implementation_ready"
            ),
            "dataverse_amr_source_projection_mpi_cuda_linked_executable": parsed.get(
                "dataverse_amr_source_projection_mpi_cuda_linked_executable"
            ),
            "dataverse_amr_source_projection_mpi_cuda_reproducible_build_entrypoint_ready": parsed.get(
                "dataverse_amr_source_projection_mpi_cuda_reproducible_build_entrypoint_ready"
            ),
            "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_cuda_12_6": parsed.get(
                "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_cuda_12_6"
            ),
            "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_local_sundials_cuda": parsed.get(
                "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_local_sundials_cuda"
            ),
            "dataverse_geometry_ready_for_sensor_sampling_map": parsed.get(
                "dataverse_geometry_ready_for_sensor_sampling_map"
            ),
            "dataverse_geometry_ready_for_full_mesh_parity": parsed.get(
                "dataverse_geometry_ready_for_full_mesh_parity"
            ),
            "dataverse_geometry_obstacle_exact_bounds_available": parsed.get(
                "dataverse_geometry_obstacle_exact_bounds_available"
            ),
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_strict_blocker_still_open": parsed.get(
                "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_strict_blocker_still_open"
            ),
            "strict_real_cad_status": parsed.get("strict_real_cad_status"),
            "real_cad_blocker_present": parsed.get("real_cad_blocker_present"),
            "strict_real_cad_blocker_cleared": parsed.get("strict_real_cad_blocker_cleared"),
            "real_cad_handoff_contract_status": parsed.get("real_cad_handoff_contract_status"),
            "real_cad_handoff_contract_ready": parsed.get("real_cad_handoff_contract_ready"),
            "real_cad_source_cad_file_count": parsed.get("real_cad_source_cad_file_count"),
            "real_cad_cleaned_geometry_file_count": parsed.get("real_cad_cleaned_geometry_file_count"),
            "real_cad_boundary_contract_status": parsed.get("real_cad_boundary_contract_status"),
            "real_cad_boundary_contract_ready_for_credit": parsed.get(
                "real_cad_boundary_contract_ready_for_credit"
            ),
            "real_cad_negative_selftest_status": parsed.get("real_cad_negative_selftest_status"),
            "real_cad_negative_selftest_ready": parsed.get("real_cad_negative_selftest_ready"),
            "real_cad_negative_selftest_rejected_count": parsed.get("real_cad_negative_selftest_rejected_count"),
            "real_cad_negative_selftest_case_count": parsed.get("real_cad_negative_selftest_case_count"),
            "real_cad_negative_selftest_expected_fragment_seen_count": parsed.get(
                "real_cad_negative_selftest_expected_fragment_seen_count"
            ),
            "real_cad_guards_synthetic_manifest": parsed.get("real_cad_guards_synthetic_manifest"),
            "real_cad_guards_missing_provenance": parsed.get("real_cad_guards_missing_provenance"),
            "real_cad_guards_source_hash_mismatch": parsed.get("real_cad_guards_source_hash_mismatch"),
            "real_cad_guards_large_layout_too_few_geometries": parsed.get(
                "real_cad_guards_large_layout_too_few_geometries"
            ),
            "real_cad_guards_data_room_bad_hash": parsed.get("real_cad_guards_data_room_bad_hash"),
            "real_cad_guards_cleanup_quality_false_check": parsed.get(
                "real_cad_guards_cleanup_quality_false_check"
            ),
            "real_cad_guards_boundary_placeholder": parsed.get("real_cad_guards_boundary_placeholder"),
            "real_cad_guards_boundary_missing_required_role": parsed.get(
                "real_cad_guards_boundary_missing_required_role"
            ),
            "strict_fire_calibration_status": parsed.get("strict_fire_calibration_status"),
            "strict_fire_calibration_blocker_present": parsed.get("strict_fire_calibration_blocker_present"),
            "strict_fire_calibration_blocker_cleared": parsed.get("strict_fire_calibration_blocker_cleared"),
            "fire_residual_budget_status": parsed.get("fire_residual_budget_status"),
            "fire_residual_budget_ready": parsed.get("fire_residual_budget_ready"),
            "fire_residual_budget_clears_strict_blocker": parsed.get(
                "fire_residual_budget_clears_strict_blocker"
            ),
            "fire_residual_budget_pressure_agreement_ready": parsed.get(
                "fire_residual_budget_pressure_agreement_ready"
            ),
            "fire_residual_budget_radiation_agreement_ready": parsed.get(
                "fire_residual_budget_radiation_agreement_ready"
            ),
            "fire_residual_budget_pressure_missing_artifact_count": parsed.get(
                "fire_residual_budget_pressure_missing_artifact_count"
            ),
            "fire_residual_budget_radiation_missing_artifact_count": parsed.get(
                "fire_residual_budget_radiation_missing_artifact_count"
            ),
            "fire_residual_budget_production_claim_allowed": parsed.get(
                "fire_residual_budget_production_claim_allowed"
            ),
            "fire_candidate_sources_both_metric_families_available": parsed.get(
                "fire_candidate_sources_both_metric_families_available"
            ),
            "fire_candidate_sources_repository_package_ready": parsed.get(
                "fire_candidate_sources_repository_package_ready"
            ),
            "exp002_reduced_overpressure_status": parsed.get("exp002_reduced_overpressure_status"),
            "exp002_source_csv_md5_verified": parsed.get("exp002_source_csv_md5_verified"),
            "exp002_pressure_channel_count": parsed.get("exp002_pressure_channel_count"),
            "exp002_overpressure_metric_count": parsed.get("exp002_overpressure_metric_count"),
            "exp002_pressure_cfd_proxy_extracted": parsed.get("exp002_pressure_cfd_proxy_extracted"),
            "exp002_pressure_cfd_proxy_cpu_gpu_parity_passed": parsed.get(
                "exp002_pressure_cfd_proxy_cpu_gpu_parity_passed"
            ),
            "exp002_pressure_cfd_proxy_cpu_gpu_rel_diff": parsed.get(
                "exp002_pressure_cfd_proxy_cpu_gpu_rel_diff"
            ),
            "exp002_cfd_outputs_sufficient_for_pressure_agreement": parsed.get(
                "exp002_cfd_outputs_sufficient_for_pressure_agreement"
            ),
            "plotfile_sensor_sampling_contract_ready": parsed.get("plotfile_sensor_sampling_contract_ready"),
            "plotfile_sensor_sampling_row_count": parsed.get("plotfile_sensor_sampling_row_count"),
            "plotfile_sensor_sampling_uses_synthetic_sensor_coordinates": parsed.get(
                "plotfile_sensor_sampling_uses_synthetic_sensor_coordinates"
            ),
            "plotfile_sensor_sampling_negative_refused_count": parsed.get(
                "plotfile_sensor_sampling_negative_refused_count"
            ),
            "plotfile_sensor_sampling_negative_case_count": parsed.get(
                "plotfile_sensor_sampling_negative_case_count"
            ),
            "mdpi_radiation_metric_count": parsed.get("mdpi_radiation_metric_count"),
            "mdpi_radiation_integrated_cfd_proxy_extracted": parsed.get(
                "mdpi_radiation_integrated_cfd_proxy_extracted"
            ),
            "mdpi_radiation_integrated_cfd_proxy_plotfile_count": parsed.get(
                "mdpi_radiation_integrated_cfd_proxy_plotfile_count"
            ),
            "mdpi_radiation_integrated_cfd_proxy_virtual_radiometer_flux_generated": parsed.get(
                "mdpi_radiation_integrated_cfd_proxy_virtual_radiometer_flux_generated"
            ),
            "mdpi_radiation_integrated_cfd_proxy_peak_radiative_power_w": parsed.get(
                "mdpi_radiation_integrated_cfd_proxy_peak_radiative_power_w"
            ),
            "mdpi_radiation_integrated_cfd_proxy_outputs_sufficient_for_mdpi_agreement": parsed.get(
                "mdpi_radiation_integrated_cfd_proxy_outputs_sufficient_for_mdpi_agreement"
            ),
        },
        "source_statuses": source_statuses,
        "parsed_status_json": parsed,
        "findings": {
            "missing_text_snippets": missing_text_snippets,
            "missing_json_statuses": missing_json_statuses,
            "missing_json_true": missing_json_true,
            "missing_json_false": missing_json_false,
        },
        "command_runs": {
            "text": {
                "argv": text_run["argv"],
                "returncode": text_run["returncode"],
                "stdout_head": text_run["stdout_head"],
            },
            "json": {
                "argv": json_run["argv"],
                "returncode": json_run["returncode"],
                "stdout_head": json_run["stdout_head"],
            },
        },
        "evidence_files": evidence_files,
    }
    validate_report(report, verify_hashes=False)
    return report


def validate_report(data: dict[str, Any], verify_hashes: bool = True) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "invalid schema_version")
    require(data.get("status") in {STATUS_PASS, STATUS_NOT_READY}, "invalid status")
    summary = data.get("summary")
    require(isinstance(summary, dict), "missing summary")
    require(summary.get("current_status_cli_ready") is True, "current status CLI is not ready")
    require(summary.get("text_returncode") == 0, "text CLI invocation failed")
    require(summary.get("json_returncode") == 0, "JSON CLI invocation failed")
    require(summary.get("missing_text_snippet_count") == 0, "text CLI output is missing required snippets")
    require(summary.get("missing_json_status_count") == 0, "JSON CLI output has unexpected statuses")
    require(summary.get("missing_json_true_count") == 0, "JSON CLI output is missing required true flags")
    require(summary.get("missing_json_false_count") == 0, "JSON CLI output is missing required false flags")
    require(summary.get("current_scope_gate_count") == 15, "unexpected current-scope gate count")
    require(summary.get("current_scope_passed_gate_count") == 15, "not all current-scope gates passed")
    require(summary.get("open_strict_blocker_count") == 3, "unexpected strict blocker count")
    require(summary.get("strict_blocker_set_ok") is True, "strict blocker set changed")
    require(summary.get("snapshot_key_report_count_matches") is True, "snapshot key report count does not match state snapshot")
    require(summary.get("state_snapshot_report_count_matches_writer") is True, "state snapshot report count does not match snapshot writer")
    require(summary.get("goal_complete") is False, "goal completion boundary changed unexpectedly")
    require(summary.get("strict_master_plan_complete") is False, "strict master-plan completion boundary changed unexpectedly")
    require(
        summary.get("release_candidate_handoff_status") == "PASS-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF",
        "release-candidate handoff status is not passing",
    )
    require(summary.get("release_candidate_handoff_ready") is True, "release-candidate handoff is not ready")
    require(
        summary.get("release_candidate_current_scope_ready") is True,
        "release-candidate current scope is not ready",
    )
    require(
        summary.get("release_candidate_can_be_used_for_current_priority_scope") is True,
        "release candidate is not usable for current priority scope",
    )
    require(
        summary.get("release_candidate_is_full_strict_master_plan_completion") is False,
        "release candidate overclaims strict master-plan completion",
    )
    require(summary.get("release_candidate_open_strict_blocker_count") == 3, "unexpected release-candidate blocker count")
    require(
        summary.get("project_closeout_forecast_status") == "PASS-PROJECT-CLOSEOUT-FORECAST",
        "project closeout forecast status is not passing",
    )
    require(
        summary.get("project_closeout_current_release_candidate_ready") is True,
        "project closeout release-candidate readiness missing",
    )
    require(
        summary.get("project_closeout_current_scope_can_be_closed_now") is True,
        "project closeout current-scope closure flag missing",
    )
    require(
        summary.get("project_closeout_strict_master_plan_can_be_closed_now") is False,
        "project closeout overclaims strict master-plan closure",
    )
    require(
        summary.get("project_closeout_strict_closeout_requires_external_artifacts") is True,
        "project closeout external-artifact boundary missing",
    )
    require(
        summary.get("project_closeout_acceptance_gate_status")
        == "PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE",
        "project closeout acceptance gate status is not passing",
    )
    require(
        summary.get("project_closeout_acceptance_gate_ready") is True,
        "project closeout acceptance gate readiness missing",
    )
    require(
        summary.get("project_closeout_current_phase_acceptance_allowed") is True,
        "project closeout current phase acceptance not allowed",
    )
    require(
        summary.get("project_closeout_strict_final_acceptance_allowed") is False,
        "project closeout overclaims strict final acceptance",
    )
    project_strict_done_count = summary.get("project_closeout_strict_external_artifact_done_count")
    project_strict_missing_count = summary.get("project_closeout_strict_external_artifact_missing_count")
    require(isinstance(project_strict_done_count, int), "project closeout strict done count is not an integer")
    require(isinstance(project_strict_missing_count, int), "project closeout strict missing count is not an integer")
    require(
        project_strict_done_count + project_strict_missing_count == 14,
        "project closeout strict counts do not sum to required total",
    )
    require(project_strict_done_count >= 1, "project closeout did not preserve the delivered strict artifact")
    require(project_strict_missing_count > 0, "project closeout unexpectedly cleared all strict blockers")
    require(
        summary.get("strict_master_plan_completion_gate_status")
        == "AWAITING-STRICT-MASTER-PLAN-COMPLETION-GATE-EXTERNAL-ARTIFACTS",
        "strict master-plan completion gate status is unexpected",
    )
    require(
        summary.get("strict_master_plan_completion_gate_ready") is True,
        "strict master-plan completion gate is not ready",
    )
    require(
        summary.get("strict_completion_current_scope_closure_allowed") is True,
        "strict completion gate no longer allows current-scope closure",
    )
    require(
        summary.get("strict_completion_allowed") is False,
        "strict completion gate overclaims strict master-plan completion",
    )
    require(
        summary.get("strict_completion_external_artifacts_missing") is True,
        "strict completion gate external-artifact boundary missing",
    )
    require(
        summary.get("strict_external_artifact_drop_index_status") == "PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX",
        "strict external artifact drop index status is not passing",
    )
    require(
        summary.get("strict_external_artifact_drop_index_ready") is True,
        "strict external artifact drop index is not ready",
    )
    require(
        summary.get("strict_external_artifact_drop_index_domain_count") == 3,
        "unexpected strict external artifact domain count",
    )
    require(
        summary.get("strict_external_artifact_drop_index_template_count") == 16,
        "unexpected strict external artifact template count",
    )
    require(
        summary.get("strict_external_artifact_drop_index_contract_check_count") == 14,
        "unexpected strict external artifact required file count",
    )
    strict_required_count = summary.get("strict_external_artifact_drop_index_contract_check_count")
    drop_index_missing_count = summary.get("strict_external_artifact_drop_index_awaiting_missing_artifact_count")
    receiving_required_count = summary.get("strict_external_evidence_receiving_pack_required_file_count")
    receiving_present_count = summary.get("strict_external_evidence_receiving_pack_present_file_count")
    receiving_missing_count = summary.get("strict_external_evidence_receiving_pack_missing_file_count")
    action_done_count = summary.get("strict_master_plan_closeout_action_pack_done_count")
    action_missing_count = summary.get("strict_master_plan_closeout_action_pack_missing_count")
    require(isinstance(drop_index_missing_count, int), "strict external artifact missing count is not an integer")
    require(isinstance(receiving_required_count, int), "receiving pack required count is not an integer")
    require(isinstance(receiving_present_count, int), "receiving pack present count is not an integer")
    require(isinstance(receiving_missing_count, int), "receiving pack missing count is not an integer")
    require(isinstance(action_done_count, int), "strict action pack done count is not an integer")
    require(isinstance(action_missing_count, int), "strict action pack missing count is not an integer")
    require(receiving_required_count == strict_required_count, "receiving pack required count changed")
    require(drop_index_missing_count == receiving_missing_count, "drop index and receiving pack missing counts differ")
    require(
        receiving_present_count + receiving_missing_count == strict_required_count,
        "receiving pack present/missing counts do not sum to required total",
    )
    require(receiving_present_count >= 1, "receiving pack did not preserve the delivered strict artifact")
    require(receiving_missing_count > 0, "receiving pack unexpectedly cleared all strict blockers")
    require(project_strict_done_count == receiving_present_count, "project closeout done count differs from receiving pack")
    require(
        project_strict_missing_count == receiving_missing_count,
        "project closeout missing count differs from receiving pack",
    )
    require(
        summary.get("strict_master_plan_closeout_action_pack_status")
        == "PASS-STRICT-MASTER-PLAN-CLOSEOUT-ACTION-PACK",
        "strict closeout action pack status is not passing",
    )
    require(
        summary.get("strict_external_evidence_receiving_pack_status")
        == "PASS-STRICT-EXTERNAL-EVIDENCE-RECEIVING-PACK",
        "strict external evidence receiving pack status is not passing",
    )
    require(
        summary.get("strict_external_evidence_receiving_pack_ready") is True,
        "strict external evidence receiving pack is not ready",
    )
    require(
        summary.get("strict_external_evidence_receiving_pack_completion_allowed") is False,
        "receiving pack overclaimed strict completion",
    )
    require(
        action_done_count + action_missing_count == strict_required_count,
        "strict action pack done/missing counts do not sum to required total",
    )
    require(action_done_count == receiving_present_count, "strict action pack done count does not match received files")
    require(
        action_missing_count == receiving_missing_count,
        "strict action pack missing count does not match receiving pack",
    )
    require(
        summary.get("strict_master_plan_closeout_action_pack_completion_allowed") is False,
        "strict closeout action pack overclaimed completion",
    )
    require(
        summary.get("current_scope_delivery_package_status") == "PASS-CURRENT-SCOPE-DELIVERY-PACKAGE",
        "current-scope delivery package status is not passing",
    )
    require(
        summary.get("current_scope_delivery_package_ready") is True,
        "current-scope delivery package is not ready",
    )
    require(
        summary.get("current_scope_delivery_package_current_scope_can_be_closed_now") is True,
        "current-scope delivery package closure flag missing",
    )
    require(
        summary.get("current_scope_delivery_package_last_full_log_passed") is True,
        "current-scope delivery package full-log gate is not passing",
    )
    require(
        summary.get("current_scope_delivery_package_missing_required_operator_command_count") == 0,
        "current-scope delivery package is missing required commands",
    )
    require(
        summary.get("current_scope_final_handoff_note_status") == "PASS-CURRENT-SCOPE-FINAL-HANDOFF-NOTE",
        "current-scope final handoff note status is not passing",
    )
    require(
        summary.get("current_scope_final_handoff_note_ready") is True,
        "current-scope final handoff note is not ready",
    )
    require(
        summary.get("current_scope_final_handoff_note_readme_missing_snippet_count") == 0,
        "current-scope final handoff note README snippets missing",
    )
    require(
        summary.get("current_scope_final_handoff_note_runbook_missing_snippet_count") == 0,
        "current-scope final handoff note runbook snippets missing",
    )
    require(
        summary.get("current_phase_closure_certificate_status") == "PASS-CURRENT-PHASE-CLOSURE-CERTIFICATE",
        "current phase closure certificate status is not passing",
    )
    require(
        summary.get("current_phase_closure_certificate_ready") is True,
        "current phase closure certificate is not ready",
    )
    require(summary.get("current_phase_closeable") is True, "current phase is not closeable")
    require(
        summary.get("closure_certificate_strict_master_plan_closure_allowed") is False,
        "closure certificate overclaims strict master-plan closure",
    )
    require(
        summary.get("closure_certificate_strict_master_plan_still_open") is True,
        "closure certificate strict master-plan boundary missing",
    )
    require(
        summary.get("closure_certificate_last_full_current_scope_log_passed") is True,
        "closure certificate last full current-scope log is not passing",
    )
    require(
        summary.get("current_phase_release_manifest_status") == "PASS-CURRENT-PHASE-RELEASE-MANIFEST",
        "current phase release manifest status is not passing",
    )
    require(
        summary.get("current_phase_release_manifest_ready") is True,
        "current phase release manifest is not ready",
    )
    require(
        isinstance(summary.get("current_phase_release_manifest_hashed_artifact_count"), int)
        and summary.get("current_phase_release_manifest_hashed_artifact_count") >= 20,
        "current phase release manifest hash count is too small",
    )
    require(
        summary.get("current_phase_release_manifest_latest_full_log_passed") is True,
        "current phase release manifest latest full log is not passing",
    )
    require(
        summary.get("current_phase_release_manifest_current_phase_closeable") is True,
        "current phase release manifest does not mark current phase closeable",
    )
    require(
        summary.get("current_phase_release_manifest_strict_master_plan_closure_allowed") is False,
        "current phase release manifest overclaims strict master-plan closure",
    )
    require(
        summary.get("operator_command_inventory_status") == "PASS-CURRENT-OPERATOR-COMMAND-INVENTORY",
        "operator command inventory status is not passing",
    )
    require(
        summary.get("operator_command_inventory_ready") is True,
        "operator command inventory is not ready",
    )
    require(
        isinstance(summary.get("operator_command_inventory_source_file_count"), int)
        and summary.get("operator_command_inventory_source_file_count") >= 15,
        "operator command inventory source-file count is too small",
    )
    require(
        isinstance(summary.get("operator_command_inventory_command_count"), int)
        and summary.get("operator_command_inventory_command_count") >= 300,
        "operator command inventory command count is too small",
    )
    require(
        isinstance(summary.get("operator_command_inventory_required_snippet_count"), int)
        and summary.get("operator_command_inventory_required_snippet_count") >= 60,
        "operator command inventory required-snippet count is too small",
    )
    require(
        summary.get("operator_command_inventory_missing_required_snippet_count") == 0,
        "operator command inventory is missing required snippets",
    )
    require(
        summary.get("operator_command_inventory_missing_tool_count") == 0,
        "operator command inventory has missing tools",
    )
    require(
        summary.get("operator_command_inventory_syntax_failure_count") == 0,
        "operator command inventory has syntax failures",
    )
    require(
        summary.get("sundials_local_link_audit_status") == "PASS-SUNDIALS-LOCAL-LINK-AUDIT",
        "SUNDIALS local link audit status is not passing",
    )
    require(summary.get("sundials_local_link_audit_ready") is True, "SUNDIALS local link audit is not ready")
    require(
        summary.get("sundials_local_link_drift_present") is True,
        "SUNDIALS local link drift is not exposed in status",
    )
    require(
        summary.get("sundials_local_link_current_kind") in {"directory", "symlink", "file", "missing", "other_existing_path"},
        "SUNDIALS local link current kind is invalid",
    )
    require(
        summary.get("sundials_local_link_expected_target_exists") is False,
        "SUNDIALS expected target existence changed; rerun the local link audit review",
    )
    require(
        isinstance(summary.get("sundials_local_link_cuda_ready_candidate_count"), int)
        and summary.get("sundials_local_link_cuda_ready_candidate_count") >= 1,
        "SUNDIALS CUDA-ready candidate count is missing",
    )
    require(
        summary.get("sundials_local_link_safe_to_auto_restore") is False,
        "SUNDIALS local link auto-restore guard is missing",
    )
    require(
        summary.get("sundials_restore_requires_explicit_operator_review") is True,
        "SUNDIALS restore explicit-review guard is missing",
    )
    require(
        summary.get("multi_fuel_capability_status") == "PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY",
        "multi-fuel capability boundary status is not passing",
    )
    require(
        summary.get("multi_fuel_template_catalog_status") == "PASS-ENGINEERING-MULTI-FUEL-TEMPLATE-CATALOG",
        "multi-fuel template catalog status is not passing",
    )
    require(summary.get("multi_fuel_template_catalog_ready") is True, "multi-fuel template catalog is not ready")
    require(summary.get("multi_fuel_template_catalog_template_count") == 5, "unexpected multi-fuel template count")
    require(
        summary.get("multi_fuel_template_catalog_fuel_species_seen") == ["C3H8", "CH4", "H2"],
        "unexpected multi-fuel template species set",
    )
    require(
        summary.get("multi_fuel_template_catalog_csv_template_ready") is True,
        "multi-fuel CSV template is not ready",
    )
    require(
        summary.get("multi_fuel_template_catalog_liquefied_nonclaim_comments_present") is True,
        "multi-fuel liquefied nonclaim comments are incomplete",
    )
    require(
        summary.get("multi_fuel_template_catalog_cfd_internal_liquid_phase_change_claim_allowed") is False,
        "multi-fuel template catalog overclaimed liquid phase-change CFD",
    )
    require(summary.get("source_fuel_species_configurable") is True, "fuel species source is not configurable")
    require(summary.get("h2_engineering_current_scope_ready") is True, "H2 engineering current scope is not ready")
    require(summary.get("ch4_gas_fire_probe_ready") is True, "CH4 gas/fire probe boundary is not ready")
    require(summary.get("c3h8_gas_fire_probe_ready") is True, "C3H8 gas/fire probe boundary is not ready")
    require(
        summary.get("gasified_lng_given_source_surrogate_ready") is True,
        "gasified LNG surrogate boundary is not ready",
    )
    require(
        summary.get("gasified_lpg_given_source_surrogate_ready") is True,
        "gasified LPG surrogate boundary is not ready",
    )
    require(
        summary.get("external_vaporization_multifuel_timeseries_cuda_passed") is True,
        "multi-fuel external vaporization CUDA evidence is not passing",
    )
    require(
        summary.get("liquefied_release_vaporization_source_model_cuda_smoke_passed") is True,
        "liquefied-release source-model CUDA smoke evidence is not passing",
    )
    require(
        summary.get("liquefied_release_source_balance_status") == "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE",
        "liquefied-release source balance status is not passing",
    )
    require(summary.get("liquefied_release_source_balance_ready") is True, "liquefied-release source balance is not ready")
    require(summary.get("liquefied_release_source_balance_case_count") == 2, "unexpected liquefied-release balance case count")
    require(
        summary.get("liquefied_release_source_balance_species") == ["C3H8", "CH4"],
        "unexpected liquefied-release balance species set",
    )
    require(
        isinstance(summary.get("liquefied_release_source_balance_total_gas_mass_integral_kg"), (int, float))
        and summary.get("liquefied_release_source_balance_total_gas_mass_integral_kg") > 0.0,
        "liquefied-release source balance gas mass is not positive",
    )
    require(
        isinstance(summary.get("liquefied_release_source_balance_max_inventory_mass_relative_error"), (int, float))
        and summary.get("liquefied_release_source_balance_max_inventory_mass_relative_error") <= 0.20,
        "liquefied-release source balance mass error is too large",
    )
    require(
        summary.get("liquefied_release_source_balance_mapping_schedule_matches_csv") is True,
        "liquefied-release source balance mapping schedule does not match CSV",
    )
    require(
        summary.get("liquefied_release_source_balance_generated_input_matches_mapping") is True,
        "liquefied-release source balance generated input does not match mapping",
    )
    require(
        summary.get("liquefied_release_source_balance_negative_selftest_status")
        == "PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE-NEGATIVE-SELFTEST",
        "liquefied-release source balance negative selftest status is not passing",
    )
    require(
        summary.get("liquefied_release_source_balance_negative_selftest_ready") is True,
        "liquefied-release source balance negative selftest is not ready",
    )
    require(summary.get("liquefied_release_source_balance_negative_case_count") == 5, "unexpected negative case count")
    require(summary.get("liquefied_release_source_balance_negative_rejected_count") == 5, "not all negative cases were rejected")
    require(summary.get("liquefied_release_source_balance_expected_fragment_seen_count") == 5, "not all expected diagnostics were seen")
    for key in (
        "liquefied_release_source_balance_guards_negative_mdot",
        "liquefied_release_source_balance_guards_species_drift",
        "liquefied_release_source_balance_guards_schedule_rate_mismatch",
        "liquefied_release_source_balance_guards_phase_change_overclaim",
        "liquefied_release_source_balance_guards_generated_input_species_mismatch",
        "liquefied_release_thermal_plausibility_ready",
        "liquefied_release_thermal_vaporized_fraction_formula_ok",
        "liquefied_release_thermal_heat_loads_positive",
        "liquefied_breach_source_contract_ready",
        "liquefied_breach_source_contract_accepts_screening_breach_inputs",
        "liquefied_breach_source_contract_generates_external_gas_source",
        "liquefied_breach_preset_templates_ready",
        "liquefied_breach_preset_templates_editable_json_presets",
        "liquefied_breach_preset_templates_generates_cfd_source_csv",
        "liquefied_phase_change_overclaim_guard_ready",
        "liquefied_phase_change_gasified_lng_lpg_bridge_ready",
        "liquefied_phase_change_external_vaporization_bridge_ready",
        "liquefied_phase_change_screening_source_ready",
        "liquefied_phase_change_cuda_runtime_ready",
    ):
        require(summary.get(key) is True, f"{key} is not active")
    require(
        summary.get("liquefied_phase_change_overclaim_guard_status")
        == "PASS-ENGINEERING-LIQUEFIED-PHASE-CHANGE-OVERCLAIM-GUARD",
        "liquefied phase-change overclaim guard status is not passing",
    )
    require(
        summary.get("liquefied_release_thermal_plausibility_status")
        == "PASS-ENGINEERING-LIQUEFIED-RELEASE-THERMAL-PLAUSIBILITY",
        "liquefied release thermal plausibility status is not passing",
    )
    require(
        summary.get("liquefied_breach_source_contract_status")
        == "PASS-ENGINEERING-LIQUEFIED-BREACH-SOURCE-CONTRACT",
        "liquefied breach source contract status is not passing",
    )
    require(
        summary.get("liquefied_breach_preset_templates_status")
        == "PASS-ENGINEERING-LIQUEFIED-BREACH-PRESET-TEMPLATES",
        "liquefied breach preset templates status is not passing",
    )
    require(summary.get("liquefied_breach_source_contract_case_count") == 2, "unexpected breach source contract case count")
    require(
        summary.get("liquefied_breach_source_contract_fluids") == ["LNG_CH4", "LPG_C3H8"],
        "unexpected breach source contract fluids",
    )
    require(
        summary.get("liquefied_breach_source_contract_species") == ["C3H8", "CH4"],
        "unexpected breach source contract species",
    )
    require(
        isinstance(summary.get("liquefied_breach_source_contract_max_gas_mass_relative_error"), (int, float))
        and summary.get("liquefied_breach_source_contract_max_gas_mass_relative_error") <= 0.20,
        "liquefied breach source contract mass error is too large",
    )
    require(summary.get("liquefied_breach_preset_templates_preset_count") == 2, "unexpected breach preset count")
    require(
        summary.get("liquefied_breach_preset_templates_fluids") == ["LNG_CH4", "LPG_C3H8"],
        "unexpected breach preset fluids",
    )
    require(
        summary.get("liquefied_breach_preset_templates_species") == ["C3H8", "CH4"],
        "unexpected breach preset species",
    )
    require(
        isinstance(summary.get("liquefied_breach_preset_templates_max_peak_gas_mdot_kg_s"), (int, float))
        and summary.get("liquefied_breach_preset_templates_max_peak_gas_mdot_kg_s") > 0.0,
        "liquefied breach preset peak mdot is not positive",
    )
    require(summary.get("liquefied_release_thermal_species") == "C3H8, CH4", "unexpected thermal species")
    require(
        isinstance(summary.get("liquefied_release_thermal_max_gas_mass_relative_error"), (int, float))
        and summary.get("liquefied_release_thermal_max_gas_mass_relative_error") <= 0.20,
        "liquefied thermal max gas mass relative error is too large",
    )
    for key in (
        "liquefied_phase_change_production_claim_allowed",
        "liquefied_phase_change_cfd_solves_liquid_phase_change",
        "liquefied_phase_change_cfd_solves_pool_spread_evaporation",
        "liquefied_phase_change_cfd_solves_flashing_discharge",
        "liquefied_breach_source_contract_production_phase_change_claim_allowed",
        "liquefied_breach_source_contract_cfd_solves_liquid_phase_change",
        "liquefied_breach_source_contract_cfd_solves_pool_spread_evaporation",
        "liquefied_breach_source_contract_cfd_solves_flashing_discharge",
        "liquefied_breach_preset_templates_production_phase_change_claim_allowed",
    ):
        require(summary.get(key) is False, f"{key} boundary changed unexpectedly")
    require(
        summary.get("liquefied_gas_phase_change_ready") is False,
        "internal liquid phase-change CFD boundary changed unexpectedly",
    )
    require(
        summary.get("multi_fuel_production_ready") is False,
        "multi-fuel production-ready claim boundary changed unexpectedly",
    )
    require(summary.get("prevents_overclaim") is True, "multi-fuel/liquefied-gas overclaim guard is not active")
    require(
        summary.get("strict_external_plume_status")
        == "TRIAGED-MASTER-PLAN-STRICT-EXTERNAL-SOURCES-PUBLIC-DATA-INCOMPLETE",
        "strict external plume update status changed",
    )
    require(summary.get("external_plume_blocker_present") is True, "external plume blocker is not present")
    require(summary.get("strict_external_plume_blocker_cleared") is False, "external plume blocker was overclaimed")
    require(
        summary.get("public_machine_readable_external_plume_timeseries_found") is True,
        "public machine-readable external plume time series missing",
    )
    require(
        summary.get("public_sbepv5_d27_geometry_and_release_conditions_found") is True,
        "public SBEPV5/D27 geometry/release condition source missing",
    )
    require(
        summary.get("dataverse_full_dataset_all_files_ready") is True,
        "Dataverse full dataset is not ready",
    )
    require(
        summary.get("dataverse_full_dataset_ready_file_count") >= 20,
        "Dataverse ready file count is too small",
    )
    require(
        summary.get("dataverse_reference_sensor_time_sample_count") >= 500,
        "Dataverse reference time sample count is too small",
    )
    require(
        summary.get("dataverse_reference_sensor_record_count") >= 10000,
        "Dataverse reference sensor record count is too small",
    )
    require(
        summary.get("dataverse_agreement_ready_for_cfd_scoring") is True,
        "Dataverse agreement contract is not ready for CFD scoring",
    )
    require(summary.get("dataverse_agreement_sensor_count") == 29, "unexpected Dataverse agreement sensor count")
    require(
        summary.get("dataverse_cfd_45s_agreement_attempt_status")
        == "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
        "Dataverse 45s agreement attempt status changed",
    )
    require(
        summary.get("dataverse_cfd_45s_agreement_attempt_failed_sensor_count") >= 1,
        "Dataverse 45s agreement attempt should not be overclaimed",
    )
    require(
        summary.get("dataverse_cfd_45s_agreement_attempt_simulation_time_end_s") >= 44.0,
        "Dataverse 45s agreement attempt did not reach the expected window",
    )
    require(
        summary.get("dataverse_cfd_120s_agreement_attempt_status")
        == "QUANTIFIED-DATAVERSE-OPEN-CHANNEL-H2-CFD-AGREEMENT-NOT-PASSING",
        "Dataverse 120s agreement attempt status changed",
    )
    require(
        summary.get("dataverse_cfd_120s_agreement_attempt_failed_sensor_count") >= 1,
        "Dataverse 120s agreement attempt should not be overclaimed",
    )
    require(
        summary.get("dataverse_cfd_120s_agreement_attempt_simulation_time_end_s") >= 119.0,
        "Dataverse 120s agreement attempt did not reach the expected window",
    )
    require(
        summary.get("dataverse_long_window_reconciliation_status")
        == "TRIAGED-DATAVERSE-OPEN-CHANNEL-LONG-WINDOW-REFINED-SOURCE-GAP",
        "Dataverse long-window reconciliation status changed",
    )
    require(
        summary.get("dataverse_existing_120s_reaches_peak_interval") is True,
        "existing 120s Dataverse run no longer reaches the experimental peak interval",
    )
    require(
        summary.get("dataverse_existing_120s_all_sensors_passed") is False,
        "existing 120s Dataverse run should not be credited as passing all sensors",
    )
    require(
        summary.get("dataverse_existing_120s_failed_sensor_count") >= 1,
        "existing 120s Dataverse failed-sensor count should keep blocker explicit",
    )
    require(
        summary.get("dataverse_current_refined_source_long_window_time_end_s") == 0.005,
        "current refined-source Dataverse long-window end time changed unexpectedly",
    )
    require(
        summary.get("dataverse_current_refined_source_steps_to_113s") >= 22000000,
        "current refined-source Dataverse step estimate to 113s changed unexpectedly",
    )
    require(
        summary.get("dataverse_amr_source_projection_current_single_level") is False,
        "Dataverse AMR source projection should no longer be single-level",
    )
    require(
        summary.get("dataverse_amr_source_projection_lacks_level_aware_mask") is False,
        "Dataverse AMR source projection level-aware mask should be implemented",
    )
    require(
        summary.get("dataverse_amr_source_projection_finest_available_level_only") is True,
        "Dataverse AMR finest-owner projection is not active",
    )
    require(
        summary.get("dataverse_amr_source_projection_implementation_status")
        == "PASS-DATAVERSE-OPEN-CHANNEL-AMR-SOURCE-PROJECTION-IMPLEMENTATION",
        "Dataverse AMR source projection implementation status is not passing",
    )
    for key in (
        "dataverse_amr_source_projection_implementation_ready",
        "dataverse_amr_source_projection_mpi_cuda_linked_executable",
        "dataverse_amr_source_projection_mpi_cuda_reproducible_build_entrypoint_ready",
        "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_cuda_12_6",
        "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_local_sundials_cuda",
    ):
        require(summary.get(key) is True, f"{key} is not active")
    require(
        summary.get("dataverse_geometry_ready_for_sensor_sampling_map") is True,
        "Dataverse geometry is not ready for sensor sampling map",
    )
    require(
        summary.get("dataverse_geometry_ready_for_full_mesh_parity") is False,
        "Dataverse full mesh parity should not be claimed",
    )
    require(
        summary.get("dataverse_geometry_obstacle_exact_bounds_available") is False,
        "Dataverse obstacle exact bounds should not be claimed",
    )
    require(
        summary.get("dataverse_full_channel_refined_source_dx025_1000step_dt5em6_strict_blocker_still_open") is True,
        "Dataverse refined-source strict blocker boundary changed unexpectedly",
    )
    require(
        summary.get("strict_real_cad_status") == "TRIAGED-MASTER-PLAN-STRICT-REAL-CAD-ARTIFACTS-MISSING",
        "strict real CAD update status changed",
    )
    require(summary.get("real_cad_blocker_present") is True, "real CAD blocker is not present")
    require(summary.get("strict_real_cad_blocker_cleared") is False, "real CAD blocker was overclaimed")
    require(
        summary.get("real_cad_handoff_contract_status") == "PASS-H2-REAL-CAD-HANDOFF-CONTRACT",
        "real CAD handoff contract status is not passing",
    )
    require(summary.get("real_cad_handoff_contract_ready") is True, "real CAD handoff contract is not ready")
    require(summary.get("real_cad_source_cad_file_count") == 0, "real CAD source files appeared unexpectedly")
    require(summary.get("real_cad_cleaned_geometry_file_count") == 0, "real CAD cleaned geometry appeared unexpectedly")
    require(
        summary.get("real_cad_boundary_contract_status") == "NOT_READY-H2-REAL-CAD-BOUNDARY-TAG-CONTRACT",
        "real CAD boundary tag contract status changed",
    )
    require(
        summary.get("real_cad_boundary_contract_ready_for_credit") is False,
        "real CAD boundary contract credit should not be claimed",
    )
    require(
        summary.get("real_cad_negative_selftest_status") == "PASS-H2-REAL-CAD-GUARD-NEGATIVE-SELFTEST",
        "real CAD negative selftest status is not passing",
    )
    require(summary.get("real_cad_negative_selftest_ready") is True, "real CAD negative selftest is not ready")
    require(summary.get("real_cad_negative_selftest_case_count") == 8, "unexpected real CAD negative case count")
    require(summary.get("real_cad_negative_selftest_rejected_count") == 8, "not all real CAD negative cases rejected")
    require(
        summary.get("real_cad_negative_selftest_expected_fragment_seen_count") == 8,
        "real CAD negative diagnostics changed",
    )
    for key in (
        "real_cad_guards_synthetic_manifest",
        "real_cad_guards_missing_provenance",
        "real_cad_guards_source_hash_mismatch",
        "real_cad_guards_large_layout_too_few_geometries",
        "real_cad_guards_data_room_bad_hash",
        "real_cad_guards_cleanup_quality_false_check",
        "real_cad_guards_boundary_placeholder",
        "real_cad_guards_boundary_missing_required_role",
    ):
        require(summary.get(key) is True, f"{key} is not active")
    require(
        summary.get("strict_fire_calibration_status")
        == "TRIAGED-MASTER-PLAN-STRICT-FIRE-CALIBRATION-PARTIAL-DATA-BRIDGED",
        "strict fire calibration update status changed",
    )
    require(summary.get("strict_fire_calibration_blocker_present") is True, "strict fire blocker is not present")
    require(summary.get("strict_fire_calibration_blocker_cleared") is False, "strict fire blocker was overclaimed")
    require(
        summary.get("fire_residual_budget_status") == "TRIAGED-H2-FIRE-CALIBRATION-RESIDUAL-BUDGET",
        "fire residual budget status changed",
    )
    require(summary.get("fire_residual_budget_ready") is True, "fire residual budget is not ready")
    require(
        summary.get("fire_residual_budget_clears_strict_blocker") is False,
        "fire residual budget overclaimed strict blocker clearance",
    )
    require(
        summary.get("fire_residual_budget_pressure_agreement_ready") is False,
        "fire residual budget overclaimed pressure agreement",
    )
    require(
        summary.get("fire_residual_budget_radiation_agreement_ready") is False,
        "fire residual budget overclaimed radiation agreement",
    )
    require(
        summary.get("fire_residual_budget_pressure_missing_artifact_count") == 3,
        "unexpected pressure missing artifact count",
    )
    require(
        summary.get("fire_residual_budget_radiation_missing_artifact_count") == 3,
        "unexpected radiation missing artifact count",
    )
    require(
        summary.get("fire_residual_budget_production_claim_allowed") is False,
        "fire residual budget overclaimed production calibration",
    )
    require(
        summary.get("fire_candidate_sources_both_metric_families_available") is True,
        "fire consequence candidate sources do not cover both metric families",
    )
    require(
        summary.get("fire_candidate_sources_repository_package_ready") is False,
        "fire consequence candidate sources should not claim repository package readiness",
    )
    require(
        summary.get("exp002_reduced_overpressure_status") == "PASS-H2-FIRE-OVERPRESSURE-REDUCED-EXP002",
        "EXP002 reduced overpressure status is not passing",
    )
    require(summary.get("exp002_source_csv_md5_verified") is True, "EXP002 source CSV MD5 is not verified")
    require(summary.get("exp002_pressure_channel_count") == 4, "unexpected EXP002 pressure channel count")
    require(summary.get("exp002_overpressure_metric_count") == 4, "unexpected EXP002 overpressure metric count")
    require(summary.get("exp002_pressure_cfd_proxy_extracted") is True, "EXP002 pressure CFD proxy was not extracted")
    require(
        summary.get("exp002_pressure_cfd_proxy_cpu_gpu_parity_passed") is True,
        "EXP002 pressure CFD proxy CPU/GPU parity is not passing",
    )
    require(
        isinstance(summary.get("exp002_pressure_cfd_proxy_cpu_gpu_rel_diff"), (int, float))
        and summary.get("exp002_pressure_cfd_proxy_cpu_gpu_rel_diff") < 0.01,
        "EXP002 pressure CFD proxy CPU/GPU relative difference is too large",
    )
    require(
        summary.get("exp002_cfd_outputs_sufficient_for_pressure_agreement") is False,
        "EXP002 pressure agreement should not be claimed from current outputs",
    )
    require(summary.get("plotfile_sensor_sampling_contract_ready") is True, "plotfile sensor sampling contract missing")
    require(summary.get("plotfile_sensor_sampling_row_count") >= 8, "plotfile sensor sampling row count too small")
    require(
        summary.get("plotfile_sensor_sampling_uses_synthetic_sensor_coordinates") is True,
        "plotfile sampling synthetic-coordinate boundary changed",
    )
    require(
        summary.get("plotfile_sensor_sampling_negative_refused_count")
        == summary.get("plotfile_sensor_sampling_negative_case_count")
        == 8,
        "plotfile sensor sampling negative selftest did not reject all cases",
    )
    require(summary.get("mdpi_radiation_metric_count") == 4, "unexpected MDPI radiation metric count")
    require(
        summary.get("mdpi_radiation_integrated_cfd_proxy_extracted") is True,
        "MDPI integrated radiation CFD proxy was not extracted",
    )
    require(
        summary.get("mdpi_radiation_integrated_cfd_proxy_plotfile_count") >= 3,
        "MDPI integrated radiation proxy plotfile count too small",
    )
    require(
        summary.get("mdpi_radiation_integrated_cfd_proxy_virtual_radiometer_flux_generated") is True,
        "MDPI virtual radiometer flux was not generated",
    )
    require(
        isinstance(summary.get("mdpi_radiation_integrated_cfd_proxy_peak_radiative_power_w"), (int, float))
        and summary.get("mdpi_radiation_integrated_cfd_proxy_peak_radiative_power_w") > 0.0,
        "MDPI integrated radiation peak radiative power is not positive",
    )
    require(
        summary.get("mdpi_radiation_integrated_cfd_proxy_outputs_sufficient_for_mdpi_agreement") is False,
        "MDPI radiation agreement should not be claimed from current outputs",
    )
    if verify_hashes:
        for entry in data.get("evidence_files", []):
            require(isinstance(entry, dict), "invalid evidence entry")
            path = Path(str(entry.get("path", "")))
            require(path.is_file(), f"missing evidence file: {path}")
            require(sha256_file(path) == entry.get("sha256"), f"evidence hash mismatch: {path}")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Current Status CLI Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Text return code: `{summary['text_returncode']}`",
        f"- JSON return code: `{summary['json_returncode']}`",
        f"- Current-scope gates: `{summary['current_scope_passed_gate_count']}/{summary['current_scope_gate_count']}`",
        f"- Open strict blockers: `{summary['open_strict_blocker_count']}`",
        f"- Strict blocker set ok: `{summary['strict_blocker_set_ok']}`",
        f"- Snapshot key reports seen: `{summary['snapshot_key_report_count_seen']}`",
        f"- Snapshot key reports expected: `{summary['snapshot_key_report_count_expected']}`",
        f"- Snapshot key report count matches: `{summary['snapshot_key_report_count_matches']}`",
        f"- State snapshot report key reports: `{summary['state_snapshot_report_key_report_count']}`",
        f"- State snapshot report count matches writer: `{summary['state_snapshot_report_count_matches_writer']}`",
        f"- Goal complete: `{summary['goal_complete']}`",
        f"- Strict master-plan complete: `{summary['strict_master_plan_complete']}`",
        f"- Release-candidate handoff: `{summary['release_candidate_handoff_status']}`",
        f"- Release-candidate handoff ready: `{summary['release_candidate_handoff_ready']}`",
        f"- Release-candidate current scope ready: `{summary['release_candidate_current_scope_ready']}`",
        f"- Release-candidate usable for current priority scope: `{summary['release_candidate_can_be_used_for_current_priority_scope']}`",
        f"- Release-candidate is full strict master-plan completion: `{summary['release_candidate_is_full_strict_master_plan_completion']}`",
        f"- Release-candidate open strict blockers: `{summary['release_candidate_open_strict_blocker_count']}`",
        f"- Project closeout forecast: `{summary['project_closeout_forecast_status']}`",
        f"- Project closeout current scope can be closed now: `{summary['project_closeout_current_scope_can_be_closed_now']}`",
        f"- Project closeout strict master-plan can be closed now: `{summary['project_closeout_strict_master_plan_can_be_closed_now']}`",
        f"- Project closeout strict external artifacts required: `{summary['project_closeout_strict_closeout_requires_external_artifacts']}`",
        f"- Project closeout acceptance gate: `{summary['project_closeout_acceptance_gate_status']}`",
        f"- Project closeout current phase acceptance allowed: `{summary['project_closeout_current_phase_acceptance_allowed']}`",
        f"- Project closeout strict final acceptance allowed: `{summary['project_closeout_strict_final_acceptance_allowed']}`",
        f"- Project closeout strict external artifacts done/missing: `{summary['project_closeout_strict_external_artifact_done_count']}/{summary['project_closeout_strict_external_artifact_missing_count']}`",
        f"- Strict external evidence receiving pack: `{summary['strict_external_evidence_receiving_pack_status']}`",
        f"- Strict external evidence receiving pack ready: `{summary['strict_external_evidence_receiving_pack_ready']}`",
        f"- Strict external evidence receiving pack present/missing: `{summary['strict_external_evidence_receiving_pack_present_file_count']}/{summary['strict_external_evidence_receiving_pack_missing_file_count']}`",
        f"- Strict external evidence receiving pack completion allowed: `{summary['strict_external_evidence_receiving_pack_completion_allowed']}`",
        f"- Strict closeout action pack: `{summary['strict_master_plan_closeout_action_pack_status']}`",
        f"- Strict closeout action pack ready: `{summary['strict_master_plan_closeout_action_pack_ready']}`",
        f"- Strict closeout action pack done/missing: `{summary['strict_master_plan_closeout_action_pack_done_count']}/{summary['strict_master_plan_closeout_action_pack_missing_count']}`",
        f"- Strict closeout action pack completion allowed: `{summary['strict_master_plan_closeout_action_pack_completion_allowed']}`",
        f"- Current-scope delivery package: `{summary['current_scope_delivery_package_status']}`",
        f"- Current-scope delivery package ready: `{summary['current_scope_delivery_package_ready']}`",
        f"- Current-scope delivery package full log passed: `{summary['current_scope_delivery_package_last_full_log_passed']}`",
        f"- Current-scope delivery package missing required commands: `{summary['current_scope_delivery_package_missing_required_operator_command_count']}`",
        f"- Current-scope final handoff note: `{summary['current_scope_final_handoff_note_status']}`",
        f"- Current-scope final handoff note ready: `{summary['current_scope_final_handoff_note_ready']}`",
        f"- Current-scope final handoff note README missing snippets: `{summary['current_scope_final_handoff_note_readme_missing_snippet_count']}`",
        f"- Current-scope final handoff note runbook missing snippets: `{summary['current_scope_final_handoff_note_runbook_missing_snippet_count']}`",
        f"- Current phase closure certificate: `{summary['current_phase_closure_certificate_status']}`",
        f"- Current phase closure certificate ready: `{summary['current_phase_closure_certificate_ready']}`",
        f"- Current phase closeable: `{summary['current_phase_closeable']}`",
        f"- Closure certificate strict master-plan closure allowed: `{summary['closure_certificate_strict_master_plan_closure_allowed']}`",
        f"- Closure certificate strict master-plan still open: `{summary['closure_certificate_strict_master_plan_still_open']}`",
        f"- Closure certificate full log passed: `{summary['closure_certificate_last_full_current_scope_log_passed']}`",
        f"- Current phase release manifest: `{summary['current_phase_release_manifest_status']}`",
        f"- Current phase release manifest ready: `{summary['current_phase_release_manifest_ready']}`",
        f"- Current phase release manifest hashed artifacts: `{summary['current_phase_release_manifest_hashed_artifact_count']}`",
        f"- Current phase release manifest full log passed: `{summary['current_phase_release_manifest_latest_full_log_passed']}`",
        f"- Current phase release manifest strict closure allowed: `{summary['current_phase_release_manifest_strict_master_plan_closure_allowed']}`",
        f"- Operator command inventory: `{summary['operator_command_inventory_status']}`",
        f"- Operator command inventory ready: `{summary['operator_command_inventory_ready']}`",
        f"- Operator command inventory source files: `{summary['operator_command_inventory_source_file_count']}`",
        f"- Operator command inventory commands: `{summary['operator_command_inventory_command_count']}`",
        f"- Operator command inventory required snippets: `{summary['operator_command_inventory_required_snippet_count']}`",
        f"- Operator command inventory missing required snippets: `{summary['operator_command_inventory_missing_required_snippet_count']}`",
        f"- Operator command inventory missing tools: `{summary['operator_command_inventory_missing_tool_count']}`",
        f"- Operator command inventory syntax failures: `{summary['operator_command_inventory_syntax_failure_count']}`",
        f"- SUNDIALS local link audit: `{summary['sundials_local_link_audit_status']}`",
        f"- SUNDIALS local link audit ready: `{summary['sundials_local_link_audit_ready']}`",
        f"- SUNDIALS local link drift present: `{summary['sundials_local_link_drift_present']}`",
        f"- SUNDIALS local link current kind: `{summary['sundials_local_link_current_kind']}`",
        f"- SUNDIALS expected target exists: `{summary['sundials_local_link_expected_target_exists']}`",
        f"- SUNDIALS CUDA-ready install candidates: `{summary['sundials_local_link_cuda_ready_candidate_count']}`",
        f"- SUNDIALS safe to auto-restore: `{summary['sundials_local_link_safe_to_auto_restore']}`",
        f"- SUNDIALS restore requires operator review: `{summary['sundials_restore_requires_explicit_operator_review']}`",
        f"- Multi-fuel capability: `{summary['multi_fuel_capability_status']}`",
        f"- Multi-fuel template catalog: `{summary['multi_fuel_template_catalog_status']}`",
        f"- Multi-fuel template species: `{', '.join(summary['multi_fuel_template_catalog_fuel_species_seen'])}`",
        f"- CH4 gas/fire probes: `{summary['ch4_gas_fire_probe_ready']}`",
        f"- C3H8 gas/fire probes: `{summary['c3h8_gas_fire_probe_ready']}`",
        f"- Gasified LNG surrogate boundary: `{summary['gasified_lng_given_source_surrogate_ready']}`",
        f"- Gasified LPG surrogate boundary: `{summary['gasified_lpg_given_source_surrogate_ready']}`",
        f"- External vaporization multi-fuel CUDA: `{summary['external_vaporization_multifuel_timeseries_cuda_passed']}`",
        f"- Liquefied-release source-model CUDA smoke: `{summary['liquefied_release_vaporization_source_model_cuda_smoke_passed']}`",
        f"- Liquefied-release source balance: `{summary['liquefied_release_source_balance_status']}`",
        f"- Liquefied-release source balance ready: `{summary['liquefied_release_source_balance_ready']}`",
        f"- Liquefied-release source balance gas mass kg: `{summary['liquefied_release_source_balance_total_gas_mass_integral_kg']}`",
        f"- Liquefied-release source balance max mass error: `{summary['liquefied_release_source_balance_max_inventory_mass_relative_error']}`",
        f"- Liquefied-release source balance negative selftest: `{summary['liquefied_release_source_balance_negative_selftest_status']}`",
        f"- Liquefied-release source balance negative cases rejected: `{summary['liquefied_release_source_balance_negative_rejected_count']}/{summary['liquefied_release_source_balance_negative_case_count']}`",
        f"- Liquefied-release source balance expected diagnostics: `{summary['liquefied_release_source_balance_expected_fragment_seen_count']}/{summary['liquefied_release_source_balance_negative_case_count']}`",
        f"- Liquefied breach source contract: `{summary['liquefied_breach_source_contract_status']}`",
        f"- Liquefied breach source contract ready: `{summary['liquefied_breach_source_contract_ready']}`",
        f"- Liquefied breach source cases: `{summary['liquefied_breach_source_contract_case_count']}`",
        f"- Liquefied breach source max mass error: `{summary['liquefied_breach_source_contract_max_gas_mass_relative_error']}`",
        f"- Liquefied breach preset templates: `{summary['liquefied_breach_preset_templates_status']}`",
        f"- Liquefied breach preset templates ready: `{summary['liquefied_breach_preset_templates_ready']}`",
        f"- Liquefied breach preset templates generate CFD CSV: `{summary['liquefied_breach_preset_templates_generates_cfd_source_csv']}`",
        f"- Internal liquid phase-change CFD: `{summary['liquefied_gas_phase_change_ready']}`",
        f"- Multi-fuel production-ready claim: `{summary['multi_fuel_production_ready']}`",
        f"- Overclaim guard: `{summary['prevents_overclaim']}`",
        f"- Fire residual budget: `{summary['fire_residual_budget_status']}`",
        f"- Fire residual budget ready: `{summary['fire_residual_budget_ready']}`",
        f"- Fire residual budget clears strict blocker: `{summary['fire_residual_budget_clears_strict_blocker']}`",
        f"- Dataverse long-window reconciliation: `{summary['dataverse_long_window_reconciliation_status']}`",
        f"- Dataverse existing 120s reaches peak interval: `{summary['dataverse_existing_120s_reaches_peak_interval']}`",
        f"- Dataverse existing 120s all sensors passed: `{summary['dataverse_existing_120s_all_sensors_passed']}`",
        f"- Dataverse refined-source time end s: `{summary['dataverse_current_refined_source_long_window_time_end_s']}`",
        f"- Dataverse refined-source steps to 113s: `{summary['dataverse_current_refined_source_steps_to_113s']}`",
        f"- Dataverse AMR projection implementation: `{summary['dataverse_amr_source_projection_implementation_status']}`",
        f"- Dataverse AMR MPI+CUDA linked executable: `{summary['dataverse_amr_source_projection_mpi_cuda_linked_executable']}`",
        f"- Dataverse AMR CUDA 12.6 reproducible build: `{summary['dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_cuda_12_6']}`",
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
        print(f"current_status_cli VERIFY-PASS json={args.verify_json} status={data.get('status')}")
        return 0

    report = build_report()
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, output_md)
    print(f"current_status_cli PASS json={output_json} md={output_md} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
