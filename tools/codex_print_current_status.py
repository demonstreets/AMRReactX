#!/usr/bin/env python3
"""Print the current evidence-backed project status."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPORTS = {
    "completion": Path(
        "docs/codex_audit/evidence/master_plan_completion_audit_20260803/"
        "master_plan_completion_audit_report.json"
    ),
    "current_scope": Path(
        "docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/"
        "master_plan_current_scope_verification_report.json"
    ),
    "final": Path(
        "docs/codex_audit/evidence/master_plan_final_readiness_20260731/"
        "master_plan_final_readiness_report.json"
    ),
    "parallel": Path(
        "docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/"
        "current_parallel_capability_matrix_report.json"
    ),
    "snapshot": Path(
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
    "strict_external_artifact_drop_checklist": Path(
        "docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812/"
        "strict_external_artifact_drop_checklist_report.json"
    ),
    "strict_external_evidence_receiving_pack": Path(
        "docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812/"
        "strict_external_evidence_receiving_pack_report.json"
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
    "multi_fuel": Path(
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
    "strict_fire": Path(
        "docs/codex_audit/evidence/master_plan_strict_fire_calibration_update_20260731/"
        "master_plan_strict_fire_calibration_update_report.json"
    ),
    "fire_residual_budget": Path(
        "docs/codex_audit/evidence/h2_fire_calibration_residual_budget_20260811/"
        "h2_fire_calibration_residual_budget_report.json"
    ),
    "strict_external": Path(
        "docs/codex_audit/evidence/master_plan_strict_external_source_update_20260731/"
        "master_plan_strict_external_source_update_report.json"
    ),
    "amr_source_projection_implementation": Path(
        "docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_implementation_20260811/"
        "dataverse_open_channel_amr_source_projection_implementation_report.json"
    ),
    "strict_real_cad": Path(
        "docs/codex_audit/evidence/master_plan_strict_real_cad_update_20260731/"
        "master_plan_strict_real_cad_update_report.json"
    ),
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"report is not a JSON object: {path}")
    return data


def yes_no(value: Any) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return str(value)


def build_status() -> dict[str, Any]:
    reports = {name: load_json(path) for name, path in REPORTS.items()}

    completion = reports["completion"]
    current_scope = reports["current_scope"]
    final = reports["final"]
    parallel = reports["parallel"]
    snapshot = reports["snapshot"]
    release_candidate = reports["release_candidate_handoff"]
    closeout = reports["project_closeout_forecast"]
    acceptance_gate = reports["project_closeout_acceptance_gate"]
    strict_completion_gate = reports["strict_master_plan_completion_gate"]
    strict_drop_index = reports["strict_external_artifact_drop_index"]
    strict_drop_checklist = reports["strict_external_artifact_drop_checklist"]
    strict_receiving_pack = reports["strict_external_evidence_receiving_pack"]
    strict_closeout_action_pack = reports["strict_master_plan_closeout_action_pack"]
    delivery = reports["current_scope_delivery_package"]
    final_handoff = reports["current_scope_final_handoff_note"]
    closure_certificate = reports["current_phase_closure_certificate"]
    release_manifest = reports["current_phase_release_manifest"]
    operator_inventory = reports["operator_command_inventory"]
    sundials_audit = reports["sundials_local_link_audit"]
    multi_fuel = reports["multi_fuel"]
    multi_fuel_template_catalog = reports["multi_fuel_template_catalog"]
    liquefied_source_balance = reports["liquefied_source_balance"]
    liquefied_source_balance_negative = reports["liquefied_source_balance_negative"]
    liquefied_phase_change_guard = reports["liquefied_phase_change_overclaim_guard"]
    liquefied_thermal = reports["liquefied_thermal_plausibility"]
    liquefied_breach = reports["liquefied_breach_source_contract"]
    liquefied_breach_presets = reports["liquefied_breach_preset_templates"]
    strict_fire = reports["strict_fire"]
    fire_residual = reports["fire_residual_budget"]
    strict_external = reports["strict_external"]
    amr_source_projection = reports["amr_source_projection_implementation"]
    strict_real_cad = reports["strict_real_cad"]

    csum = completion["summary"]
    msum = current_scope["summary"]
    fsum = final["summary"]
    psum = parallel["summary"]
    ssum = snapshot["summary"]
    rcsum = release_candidate["summary"]
    closeoutsum = closeout["summary"]
    acceptancesum = acceptance_gate["summary"]
    strictgatesum = strict_completion_gate["summary"]
    strictdropindexsum = strict_drop_index["summary"]
    strictdropchecklistsum = strict_drop_checklist["summary"]
    strictreceivingpacksum = strict_receiving_pack["summary"]
    strictcloseoutactionsum = strict_closeout_action_pack["summary"]
    deliverysum = delivery["summary"]
    handoffsum = final_handoff["summary"]
    closuresum = closure_certificate["summary"]
    manifestsum = release_manifest["summary"]
    inventorysum = operator_inventory["summary"]
    sundialssum = sundials_audit["summary"]
    multisum = multi_fuel["summary"]
    catalogsum = multi_fuel_template_catalog["summary"]
    lsum = liquefied_source_balance["summary"]
    lneg = liquefied_source_balance_negative["summary"]
    pguardsum = liquefied_phase_change_guard["summary"]
    thermsum = liquefied_thermal["summary"]
    bsum = liquefied_breach["summary"]
    bpresetsum = liquefied_breach_presets["summary"]
    firesum = strict_fire["summary"]
    fire_residual_sum = fire_residual["summary"]
    extsum = strict_external["summary"]
    amrsum = amr_source_projection["summary"]
    cadsum = strict_real_cad["summary"]
    ch4_gas_fire_probe_ready = all(
        multisum.get(key) is True
        for key in [
            "ch4_fuel_species_probe_passed",
            "ch4_delayed_ignition_cpu_mpi_fire_probe_passed",
            "ch4_delayed_ignition_single_cuda_fire_probe_passed",
            "ch4_delayed_ignition_mpi_cuda_fire_probe_passed",
            "ch4_delayed_ignition_mpi_cuda_500step_fire_probe_passed",
        ]
    )
    c3h8_gas_fire_probe_ready = all(
        multisum.get(key) is True
        for key in [
            "c3h8_gas_phase_cpu_cuda_probe_passed",
            "c3h8_gas_phase_cpu_mpi_cuda_probe_passed",
            "c3h8_gas_phase_cpu_cpu_mpi_single_cuda_mpi_cuda_probe_passed",
        ]
    )

    return {
        "completion_audit_status": completion["status"],
        "current_scope_verification_status": current_scope["status"],
        "current_scope_gate_count": msum["gate_count"],
        "current_scope_passed_gate_count": msum["passed_gate_count"],
        "final_readiness_status": final["status"],
        "state_snapshot_status": snapshot["status"],
        "release_candidate_handoff_status": release_candidate["status"],
        "release_candidate_handoff_ready": rcsum["release_candidate_handoff_ready"],
        "release_candidate_current_scope_ready": rcsum["current_scope_ready"],
        "release_candidate_can_be_used_for_current_priority_scope": rcsum[
            "release_candidate_can_be_used_for_current_priority_scope"
        ],
        "release_candidate_is_full_strict_master_plan_completion": rcsum[
            "release_candidate_is_full_strict_master_plan_completion"
        ],
        "release_candidate_open_strict_blocker_count": rcsum["open_strict_blocker_count"],
        "project_closeout_forecast_status": closeout["status"],
        "project_closeout_current_release_candidate_ready": closeoutsum["current_release_candidate_ready"],
        "project_closeout_current_scope_can_be_closed_now": closeoutsum["current_scope_can_be_closed_now"],
        "project_closeout_current_scope_closeout_estimate": closeoutsum["current_scope_closeout_estimate"],
        "project_closeout_strict_master_plan_can_be_closed_now": closeoutsum[
            "strict_master_plan_can_be_closed_now"
        ],
        "project_closeout_strict_closeout_requires_external_artifacts": closeoutsum[
            "strict_closeout_requires_external_artifacts"
        ],
        "project_closeout_strict_closeout_estimate_after_artifacts": closeoutsum[
            "strict_closeout_estimate_after_artifacts"
        ],
        "project_closeout_acceptance_gate_status": acceptance_gate["status"],
        "project_closeout_acceptance_gate_ready": acceptancesum[
            "project_closeout_acceptance_gate_ready"
        ],
        "project_closeout_current_phase_acceptance_allowed": acceptancesum[
            "current_phase_acceptance_allowed"
        ],
        "project_closeout_strict_final_acceptance_allowed": acceptancesum[
            "strict_final_acceptance_allowed"
        ],
        "project_closeout_strict_external_artifact_done_count": acceptancesum[
            "strict_external_artifact_done_count"
        ],
        "project_closeout_strict_external_artifact_missing_count": acceptancesum[
            "strict_external_artifact_missing_count"
        ],
        "strict_master_plan_completion_gate_status": strict_completion_gate["status"],
        "strict_master_plan_completion_gate_ready": strictgatesum[
            "strict_master_plan_completion_gate_ready"
        ],
        "strict_completion_current_scope_closure_allowed": strictgatesum[
            "current_scope_closure_allowed"
        ],
        "strict_completion_allowed": strictgatesum["strict_master_plan_completion_allowed"],
        "strict_completion_external_artifacts_missing": strictgatesum["strict_external_artifacts_missing"],
        "strict_external_artifact_drop_index_status": strict_drop_index["status"],
        "strict_external_artifact_drop_index_ready": strictdropindexsum[
            "strict_external_artifact_drop_index_ready"
        ],
        "strict_external_artifact_drop_index_domain_count": strictdropindexsum["domain_count"],
        "strict_external_artifact_drop_index_template_count": strictdropindexsum["template_count"],
        "strict_external_artifact_drop_index_contract_check_count": strictdropindexsum[
            "contract_check_count"
        ],
        "strict_external_artifact_drop_index_present_artifact_count": strictdropindexsum[
            "present_contract_artifact_count"
        ],
        "strict_external_artifact_drop_index_awaiting_missing_artifact_count": strictdropindexsum[
            "awaiting_missing_artifact_count"
        ],
        "strict_external_artifact_drop_checklist_status": strict_drop_checklist["status"],
        "strict_external_artifact_drop_checklist_ready": strictdropchecklistsum[
            "strict_external_artifact_drop_checklist_ready"
        ],
        "strict_external_artifact_drop_checklist_required_file_count": strictdropchecklistsum[
            "required_file_count"
        ],
        "strict_external_artifact_drop_checklist_done_count": strictdropchecklistsum[
            "checklist_done_count"
        ],
        "strict_external_artifact_drop_checklist_missing_file_count": strictdropchecklistsum[
            "missing_file_count"
        ],
        "strict_external_evidence_receiving_pack_status": strict_receiving_pack["status"],
        "strict_external_evidence_receiving_pack_ready": strictreceivingpacksum[
            "strict_external_evidence_receiving_pack_ready"
        ],
        "strict_external_evidence_receiving_pack_required_file_count": strictreceivingpacksum[
            "required_file_count"
        ],
        "strict_external_evidence_receiving_pack_present_file_count": strictreceivingpacksum[
            "present_file_count"
        ],
        "strict_external_evidence_receiving_pack_missing_file_count": strictreceivingpacksum[
            "missing_file_count"
        ],
        "strict_external_evidence_receiving_pack_completion_allowed": strictreceivingpacksum[
            "strict_completion_allowed"
        ],
        "strict_external_evidence_receiving_pack_still_open": strictreceivingpacksum[
            "strict_master_plan_still_open"
        ],
        "strict_master_plan_closeout_action_pack_status": strict_closeout_action_pack["status"],
        "strict_master_plan_closeout_action_pack_ready": strictcloseoutactionsum[
            "strict_master_plan_closeout_action_pack_ready"
        ],
        "strict_master_plan_closeout_action_pack_current_phase_closeable": strictcloseoutactionsum[
            "current_phase_closeable"
        ],
        "strict_master_plan_closeout_action_pack_completion_allowed": strictcloseoutactionsum[
            "strict_master_plan_completion_allowed"
        ],
        "strict_master_plan_closeout_action_pack_still_open": strictcloseoutactionsum[
            "strict_master_plan_still_open"
        ],
        "strict_master_plan_closeout_action_pack_done_count": strictcloseoutactionsum[
            "done_action_item_count"
        ],
        "strict_master_plan_closeout_action_pack_missing_count": strictcloseoutactionsum[
            "missing_action_item_count"
        ],
        "current_scope_delivery_package_status": delivery["status"],
        "current_scope_delivery_package_ready": deliverysum["current_scope_delivery_package_ready"],
        "current_scope_delivery_package_current_scope_can_be_closed_now": deliverysum[
            "current_scope_can_be_closed_now"
        ],
        "current_scope_delivery_package_last_full_log_passed": deliverysum[
            "last_full_current_scope_log_passed"
        ],
        "current_scope_delivery_package_missing_required_operator_command_count": deliverysum[
            "missing_required_operator_command_count"
        ],
        "current_scope_final_handoff_note_status": final_handoff["status"],
        "current_scope_final_handoff_note_ready": handoffsum["current_scope_final_handoff_note_ready"],
        "current_scope_final_handoff_note_readme_missing_snippet_count": handoffsum[
            "readme_missing_snippet_count"
        ],
        "current_scope_final_handoff_note_runbook_missing_snippet_count": handoffsum[
            "runbook_missing_snippet_count"
        ],
        "current_phase_closure_certificate_status": closure_certificate["status"],
        "current_phase_closure_certificate_ready": closuresum[
            "current_phase_closure_certificate_ready"
        ],
        "current_phase_closeable": closuresum["current_phase_closeable"],
        "closure_certificate_strict_master_plan_closure_allowed": closuresum[
            "strict_master_plan_closure_allowed"
        ],
        "closure_certificate_strict_master_plan_still_open": closuresum[
            "strict_master_plan_still_open"
        ],
        "closure_certificate_last_full_current_scope_log": closuresum[
            "last_full_current_scope_log"
        ],
        "closure_certificate_last_full_current_scope_log_passed": closuresum[
            "last_full_current_scope_log_passed"
        ],
        "current_phase_release_manifest_status": release_manifest["status"],
        "current_phase_release_manifest_ready": manifestsum[
            "current_phase_release_manifest_ready"
        ],
        "current_phase_release_manifest_hashed_artifact_count": manifestsum[
            "hashed_artifact_count"
        ],
        "current_phase_release_manifest_latest_full_log_passed": manifestsum[
            "latest_full_current_scope_log_passed"
        ],
        "current_phase_release_manifest_current_phase_closeable": manifestsum[
            "current_phase_closeable"
        ],
        "current_phase_release_manifest_strict_master_plan_closure_allowed": manifestsum[
            "strict_master_plan_closure_allowed"
        ],
        "operator_command_inventory_status": operator_inventory["status"],
        "operator_command_inventory_ready": inventorysum[
            "current_operator_command_inventory_ready"
        ],
        "operator_command_inventory_source_file_count": inventorysum["source_file_count"],
        "operator_command_inventory_command_count": inventorysum["command_count"],
        "operator_command_inventory_required_snippet_count": inventorysum[
            "required_snippet_count"
        ],
        "operator_command_inventory_missing_required_snippet_count": inventorysum[
            "missing_required_snippet_count"
        ],
        "operator_command_inventory_missing_tool_count": inventorysum["missing_tool_count"],
        "operator_command_inventory_syntax_failure_count": inventorysum["syntax_failure_count"],
        "sundials_local_link_audit_status": sundials_audit["status"],
        "sundials_local_link_audit_ready": sundialssum["audit_ready"],
        "sundials_local_link_drift_present": sundialssum["local_link_drift_present"],
        "sundials_local_link_current_kind": sundialssum["current_replacement_kind"],
        "sundials_local_link_expected_target_exists": sundialssum["expected_target_exists"],
        "sundials_local_link_cuda_ready_candidate_count": sundialssum[
            "cuda_sundials_ready_candidate_count"
        ],
        "sundials_local_link_safe_to_auto_restore": sundialssum["safe_to_auto_restore"],
        "sundials_restore_requires_explicit_operator_review": sundialssum[
            "restore_requires_explicit_operator_review"
        ],
        "current_user_priority_ready": fsum["current_user_priority_ready"],
        "cpu_mpi_ready_for_all_current_scenarios": psum["cpu_mpi_ready_for_all_current_scenarios"],
        "single_gpu_ready_for_all_current_scenarios": psum["single_gpu_ready_for_all_current_scenarios"],
        "multi_gpu_mpi_cuda_ready_for_all_current_scenarios": psum["multi_gpu_mpi_cuda_ready_for_all_current_scenarios"],
        "goal_complete": csum["goal_complete"],
        "strict_master_plan_complete": csum["strict_master_plan_complete"],
        "open_strict_blocker_count": csum["open_strict_blocker_count"],
        "open_strict_blockers": completion["open_strict_blockers"],
        "strict_unblock_runbook": completion["next_action_runbook"],
        "snapshot_key_report_count": ssum["key_report_count"],
        "multi_fuel_capability_status": multi_fuel["status"],
        "multi_fuel_template_catalog_status": multi_fuel_template_catalog["status"],
        "multi_fuel_template_catalog_ready": catalogsum["multi_fuel_template_catalog_ready"],
        "multi_fuel_template_catalog_template_count": catalogsum["template_count"],
        "multi_fuel_template_catalog_fuel_species_seen": catalogsum["fuel_species_seen"],
        "multi_fuel_template_catalog_csv_template_ready": catalogsum["csv_template_ready"],
        "multi_fuel_template_catalog_liquefied_nonclaim_comments_present": catalogsum[
            "liquefied_nonclaim_comments_present"
        ],
        "multi_fuel_template_catalog_cfd_internal_liquid_phase_change_claim_allowed": catalogsum[
            "cfd_internal_liquid_phase_change_claim_allowed"
        ],
        "liquefied_release_source_balance_status": liquefied_source_balance["status"],
        "liquefied_release_source_balance_ready": lsum["liquefied_release_source_balance_ready"],
        "liquefied_release_source_balance_case_count": lsum["case_count"],
        "liquefied_release_source_balance_species": lsum["species"],
        "liquefied_release_source_balance_total_gas_mass_integral_kg": lsum["total_gas_mass_integral_kg"],
        "liquefied_release_source_balance_max_inventory_mass_relative_error": lsum[
            "max_inventory_mass_relative_error"
        ],
        "liquefied_release_source_balance_mapping_schedule_matches_csv": lsum["mapping_schedule_matches_csv"],
        "liquefied_release_source_balance_generated_input_matches_mapping": lsum["generated_input_matches_mapping"],
        "liquefied_release_source_balance_negative_selftest_status": liquefied_source_balance_negative["status"],
        "liquefied_release_source_balance_negative_selftest_ready": lneg[
            "liquefied_release_source_balance_negative_selftest_ready"
        ],
        "liquefied_release_source_balance_negative_case_count": lneg["negative_case_count"],
        "liquefied_release_source_balance_negative_rejected_count": lneg["negative_rejected_count"],
        "liquefied_release_source_balance_expected_fragment_seen_count": lneg["expected_fragment_seen_count"],
        "liquefied_release_source_balance_guards_negative_mdot": lneg["guards_negative_mdot"],
        "liquefied_release_source_balance_guards_species_drift": lneg["guards_species_drift"],
        "liquefied_release_source_balance_guards_schedule_rate_mismatch": lneg["guards_schedule_rate_mismatch"],
        "liquefied_release_source_balance_guards_phase_change_overclaim": lneg["guards_phase_change_overclaim"],
        "liquefied_release_source_balance_guards_generated_input_species_mismatch": lneg[
            "guards_generated_input_species_mismatch"
        ],
        "liquefied_release_thermal_plausibility_status": liquefied_thermal["status"],
        "liquefied_release_thermal_plausibility_ready": thermsum[
            "liquefied_release_thermal_plausibility_ready"
        ],
        "liquefied_release_thermal_species": ", ".join(thermsum["species"]),
        "liquefied_release_thermal_vaporized_fraction_formula_ok": thermsum[
            "all_vaporized_fraction_matches_screening_formula"
        ],
        "liquefied_release_thermal_heat_loads_positive": thermsum["all_heat_loads_positive"],
        "liquefied_release_thermal_max_gas_mass_relative_error": thermsum["max_gas_mass_relative_error"],
        "liquefied_breach_source_contract_status": liquefied_breach["status"],
        "liquefied_breach_source_contract_ready": bsum["liquefied_breach_source_contract_ready"],
        "liquefied_breach_source_contract_case_count": bsum["case_count"],
        "liquefied_breach_source_contract_fluids": bsum["fluids"],
        "liquefied_breach_source_contract_species": bsum["species"],
        "liquefied_breach_source_contract_accepts_screening_breach_inputs": bsum[
            "contract_accepts_screening_breach_inputs"
        ],
        "liquefied_breach_source_contract_generates_external_gas_source": bsum[
            "generates_external_gas_source_schedule"
        ],
        "liquefied_breach_source_contract_max_gas_mass_relative_error": bsum["max_gas_mass_relative_error"],
        "liquefied_breach_source_contract_max_peak_jet_speed_m_s": bsum["max_peak_jet_speed_m_s"],
        "liquefied_breach_source_contract_production_phase_change_claim_allowed": bsum[
            "production_phase_change_claim_allowed"
        ],
        "liquefied_breach_source_contract_cfd_solves_liquid_phase_change": bsum[
            "cfd_solves_liquid_phase_change"
        ],
        "liquefied_breach_source_contract_cfd_solves_pool_spread_evaporation": bsum[
            "cfd_solves_pool_spread_evaporation"
        ],
        "liquefied_breach_source_contract_cfd_solves_flashing_discharge": bsum[
            "cfd_solves_flashing_discharge"
        ],
        "liquefied_breach_preset_templates_status": liquefied_breach_presets["status"],
        "liquefied_breach_preset_templates_ready": bpresetsum[
            "liquefied_breach_preset_templates_ready"
        ],
        "liquefied_breach_preset_templates_editable_json_presets": bpresetsum["editable_json_presets"],
        "liquefied_breach_preset_templates_preset_count": bpresetsum["preset_count"],
        "liquefied_breach_preset_templates_fluids": bpresetsum["fluids"],
        "liquefied_breach_preset_templates_species": bpresetsum["species"],
        "liquefied_breach_preset_templates_generates_cfd_source_csv": bpresetsum[
            "generates_cfd_source_csv"
        ],
        "liquefied_breach_preset_templates_max_peak_gas_mdot_kg_s": bpresetsum[
            "max_peak_gas_mdot_kg_s"
        ],
        "liquefied_breach_preset_templates_production_phase_change_claim_allowed": bpresetsum[
            "production_phase_change_claim_allowed"
        ],
        "liquefied_phase_change_overclaim_guard_status": liquefied_phase_change_guard["status"],
        "liquefied_phase_change_overclaim_guard_ready": pguardsum["phase_change_overclaim_guard_ready"],
        "liquefied_phase_change_gasified_lng_lpg_bridge_ready": pguardsum[
            "gasified_lng_lpg_bridge_ready"
        ],
        "liquefied_phase_change_external_vaporization_bridge_ready": pguardsum[
            "external_vaporization_bridge_ready"
        ],
        "liquefied_phase_change_screening_source_ready": pguardsum[
            "liquefied_release_screening_source_ready"
        ],
        "liquefied_phase_change_cuda_runtime_ready": pguardsum["liquefied_release_cuda_runtime_ready"],
        "liquefied_phase_change_production_claim_allowed": pguardsum["production_phase_change_claim_allowed"],
        "liquefied_phase_change_cfd_solves_liquid_phase_change": pguardsum["cfd_solves_liquid_phase_change"],
        "liquefied_phase_change_cfd_solves_pool_spread_evaporation": pguardsum[
            "cfd_solves_pool_spread_evaporation"
        ],
        "liquefied_phase_change_cfd_solves_flashing_discharge": pguardsum["cfd_solves_flashing_discharge"],
        "source_fuel_species_configurable": multisum["source_fuel_species_configurable"],
        "h2_engineering_current_scope_ready": multisum["h2_engineering_current_scope_ready"],
        "ch4_gas_fire_probe_ready": ch4_gas_fire_probe_ready,
        "c3h8_gas_fire_probe_ready": c3h8_gas_fire_probe_ready,
        "gasified_lng_given_source_surrogate_ready": multisum["gasified_lng_given_source_surrogate_ready"],
        "gasified_lpg_given_source_surrogate_ready": multisum["gasified_lpg_given_source_surrogate_ready"],
        "external_vaporization_multifuel_timeseries_cuda_passed": multisum[
            "external_vaporization_multifuel_timeseries_cuda_passed"
        ],
        "liquefied_release_vaporization_source_model_cuda_smoke_passed": multisum[
            "liquefied_release_vaporization_source_model_cuda_smoke_passed"
        ],
        "liquefied_gas_phase_change_ready": multisum["liquefied_gas_phase_change_ready"],
        "multi_fuel_production_ready": multisum["multi_fuel_production_ready"],
        "prevents_overclaim": multisum["prevents_overclaim"],
        "strict_external_plume_status": strict_external["status"],
        "external_plume_blocker_present": extsum["external_plume_blocker_present"],
        "strict_external_plume_blocker_cleared": extsum["strict_external_plume_blocker_cleared"],
        "public_machine_readable_external_plume_timeseries_found": extsum[
            "public_machine_readable_external_plume_timeseries_found"
        ],
        "public_sbepv5_d27_geometry_and_release_conditions_found": extsum[
            "public_sbepv5_d27_geometry_and_release_conditions_found"
        ],
        "dataverse_full_dataset_all_files_ready": extsum["dataverse_full_dataset_all_files_ready"],
        "dataverse_full_dataset_ready_file_count": extsum["dataverse_full_dataset_ready_file_count"],
        "dataverse_reference_sensor_time_sample_count": extsum["dataverse_reference_sensor_time_sample_count"],
        "dataverse_reference_sensor_record_count": extsum["dataverse_reference_sensor_record_count"],
        "dataverse_agreement_ready_for_cfd_scoring": extsum["dataverse_agreement_ready_for_cfd_scoring"],
        "dataverse_agreement_sensor_count": extsum["dataverse_agreement_sensor_count"],
        "dataverse_cfd_45s_agreement_attempt_status": extsum["dataverse_cfd_45s_agreement_attempt_status"],
        "dataverse_cfd_45s_agreement_attempt_failed_sensor_count": extsum[
            "dataverse_cfd_45s_agreement_attempt_failed_sensor_count"
        ],
        "dataverse_cfd_45s_agreement_attempt_simulation_time_end_s": extsum[
            "dataverse_cfd_45s_agreement_attempt_simulation_time_end_s"
        ],
        "dataverse_cfd_120s_agreement_attempt_status": extsum["dataverse_cfd_120s_agreement_attempt_status"],
        "dataverse_cfd_120s_agreement_attempt_failed_sensor_count": extsum[
            "dataverse_cfd_120s_agreement_attempt_failed_sensor_count"
        ],
        "dataverse_cfd_120s_agreement_attempt_simulation_time_end_s": extsum[
            "dataverse_cfd_120s_agreement_attempt_simulation_time_end_s"
        ],
        "dataverse_long_window_reconciliation_status": extsum["dataverse_long_window_reconciliation_status"],
        "dataverse_existing_120s_reaches_peak_interval": extsum[
            "dataverse_existing_120s_reaches_peak_interval"
        ],
        "dataverse_existing_120s_all_sensors_passed": extsum[
            "dataverse_existing_120s_all_sensors_passed"
        ],
        "dataverse_existing_120s_failed_sensor_count": extsum[
            "dataverse_existing_120s_failed_sensor_count"
        ],
        "dataverse_current_refined_source_long_window_time_end_s": extsum[
            "dataverse_current_refined_source_long_window_time_end_s"
        ],
        "dataverse_current_refined_source_steps_to_113s": extsum[
            "dataverse_current_refined_source_steps_to_113s"
        ],
        "dataverse_amr_source_projection_current_single_level": extsum[
            "dataverse_amr_source_projection_current_single_level"
        ],
        "dataverse_amr_source_projection_lacks_level_aware_mask": extsum[
            "dataverse_amr_source_projection_lacks_level_aware_mask"
        ],
        "dataverse_amr_source_projection_finest_available_level_only": extsum[
            "dataverse_amr_source_projection_finest_available_level_only"
        ],
        "dataverse_amr_source_projection_implementation_status": amr_source_projection["status"],
        "dataverse_amr_source_projection_implementation_ready": amrsum[
            "amr_source_projection_implementation_ready"
        ],
        "dataverse_amr_source_projection_mpi_cuda_linked_executable": amrsum[
            "mpi_cuda_linked_executable"
        ],
        "dataverse_amr_source_projection_mpi_cuda_reproducible_build_entrypoint_ready": amrsum[
            "mpi_cuda_reproducible_build_entrypoint_ready"
        ],
        "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_cuda_12_6": amrsum[
            "mpi_cuda_reproducible_build_uses_cuda_12_6"
        ],
        "dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_local_sundials_cuda": amrsum[
            "mpi_cuda_reproducible_build_uses_local_sundials_cuda"
        ],
        "dataverse_geometry_ready_for_sensor_sampling_map": extsum[
            "dataverse_geometry_ready_for_sensor_sampling_map"
        ],
        "dataverse_geometry_ready_for_full_mesh_parity": extsum["dataverse_geometry_ready_for_full_mesh_parity"],
        "dataverse_geometry_obstacle_exact_bounds_available": extsum[
            "dataverse_geometry_obstacle_exact_bounds_available"
        ],
        "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_strict_blocker_still_open": extsum[
            "dataverse_full_channel_refined_source_dx025_1000step_dt5em6_strict_blocker_still_open"
        ],
        "strict_real_cad_status": strict_real_cad["status"],
        "real_cad_blocker_present": cadsum["real_cad_blocker_present"],
        "strict_real_cad_blocker_cleared": cadsum["strict_real_cad_blocker_cleared"],
        "real_cad_handoff_contract_status": cadsum["handoff_contract_status"],
        "real_cad_handoff_contract_ready": cadsum["handoff_contract_ready"],
        "real_cad_source_cad_file_count": cadsum["source_cad_file_count"],
        "real_cad_cleaned_geometry_file_count": cadsum["cleaned_geometry_file_count"],
        "real_cad_boundary_contract_status": cadsum["boundary_contract_status"],
        "real_cad_boundary_contract_ready_for_credit": cadsum["boundary_contract_ready_for_credit"],
        "real_cad_negative_selftest_status": cadsum.get("negative_selftest_status"),
        "real_cad_negative_selftest_ready": cadsum.get("negative_selftest_ready"),
        "real_cad_negative_selftest_rejected_count": cadsum.get("negative_selftest_rejected_count"),
        "real_cad_negative_selftest_case_count": cadsum.get("negative_selftest_case_count"),
        "real_cad_negative_selftest_expected_fragment_seen_count": cadsum.get(
            "negative_selftest_expected_fragment_seen_count"
        ),
        "real_cad_guards_synthetic_manifest": cadsum.get("guards_synthetic_manifest"),
        "real_cad_guards_missing_provenance": cadsum.get("guards_missing_provenance"),
        "real_cad_guards_source_hash_mismatch": cadsum.get("guards_source_hash_mismatch"),
        "real_cad_guards_large_layout_too_few_geometries": cadsum.get("guards_large_layout_too_few_geometries"),
        "real_cad_guards_data_room_bad_hash": cadsum.get("guards_data_room_bad_hash"),
        "real_cad_guards_cleanup_quality_false_check": cadsum.get("guards_cleanup_quality_false_check"),
        "real_cad_guards_boundary_placeholder": cadsum.get("guards_boundary_placeholder"),
        "real_cad_guards_boundary_missing_required_role": cadsum.get("guards_boundary_missing_required_role"),
        "strict_fire_calibration_status": strict_fire["status"],
        "strict_fire_calibration_blocker_present": firesum["fire_calibration_blocker_present"],
        "strict_fire_calibration_blocker_cleared": firesum["strict_fire_calibration_blocker_cleared"],
        "fire_candidate_sources_both_metric_families_available": firesum[
            "candidate_sources_20260805_both_metric_families_available"
        ],
        "fire_candidate_sources_repository_package_ready": firesum["candidate_sources_20260805_repository_package_ready"],
        "exp002_reduced_overpressure_status": firesum["exp002_reduced_overpressure_status"],
        "exp002_source_csv_md5_verified": firesum["exp002_source_csv_md5_verified"],
        "exp002_pressure_channel_count": firesum["exp002_pressure_channel_count"],
        "exp002_overpressure_metric_count": firesum["exp002_overpressure_metric_count"],
        "exp002_pressure_cfd_proxy_extracted": firesum["exp002_pressure_cfd_proxy_extracted"],
        "exp002_pressure_cfd_proxy_cpu_gpu_parity_passed": firesum[
            "exp002_pressure_cfd_proxy_cpu_gpu_parity_passed"
        ],
        "exp002_pressure_cfd_proxy_cpu_gpu_rel_diff": firesum["exp002_pressure_cfd_proxy_cpu_gpu_rel_diff"],
        "exp002_cfd_outputs_sufficient_for_pressure_agreement": firesum[
            "exp002_cfd_outputs_sufficient_for_pressure_agreement"
        ],
        "plotfile_sensor_sampling_contract_ready": firesum["plotfile_sensor_sampling_contract_ready"],
        "plotfile_sensor_sampling_row_count": firesum["plotfile_sensor_sampling_row_count"],
        "plotfile_sensor_sampling_uses_synthetic_sensor_coordinates": firesum[
            "plotfile_sensor_sampling_uses_synthetic_sensor_coordinates"
        ],
        "plotfile_sensor_sampling_negative_refused_count": firesum[
            "plotfile_sensor_sampling_negative_refused_count"
        ],
        "plotfile_sensor_sampling_negative_case_count": firesum["plotfile_sensor_sampling_negative_case_count"],
        "mdpi_radiation_metric_count": firesum["mdpi_radiation_metric_count"],
        "mdpi_radiation_integrated_cfd_proxy_extracted": firesum[
            "mdpi_radiation_integrated_cfd_proxy_extracted"
        ],
        "mdpi_radiation_integrated_cfd_proxy_plotfile_count": firesum[
            "mdpi_radiation_integrated_cfd_proxy_plotfile_count"
        ],
        "mdpi_radiation_integrated_cfd_proxy_virtual_radiometer_flux_generated": firesum[
            "mdpi_radiation_integrated_cfd_proxy_virtual_radiometer_flux_generated"
        ],
        "mdpi_radiation_integrated_cfd_proxy_peak_radiative_power_w": firesum[
            "mdpi_radiation_integrated_cfd_proxy_peak_radiative_power_w"
        ],
        "mdpi_radiation_integrated_cfd_proxy_outputs_sufficient_for_mdpi_agreement": firesum[
            "mdpi_radiation_integrated_cfd_proxy_outputs_sufficient_for_mdpi_agreement"
        ],
        "fire_residual_budget_status": fire_residual["status"],
        "fire_residual_budget_ready": fire_residual_sum["fire_calibration_residual_budget_ready"],
        "fire_residual_budget_clears_strict_blocker": fire_residual_sum[
            "residual_budget_clears_strict_blocker"
        ],
        "fire_residual_budget_pressure_agreement_ready": fire_residual_sum["pressure_agreement_ready"],
        "fire_residual_budget_radiation_agreement_ready": fire_residual_sum["radiation_agreement_ready"],
        "fire_residual_budget_pressure_missing_artifact_count": fire_residual_sum[
            "pressure_missing_artifact_count"
        ],
        "fire_residual_budget_radiation_missing_artifact_count": fire_residual_sum[
            "radiation_missing_artifact_count"
        ],
        "fire_residual_budget_production_claim_allowed": fire_residual_sum[
            "production_fire_calibration_claim_allowed"
        ],
    }


def print_text(status: dict[str, Any]) -> None:
    print("my-pele current evidence-backed status")
    print("======================================")
    print(f"completion audit: {status['completion_audit_status']}")
    print(f"current-scope verification: {status['current_scope_verification_status']}")
    print(f"current-scope gates: {status['current_scope_passed_gate_count']}/{status['current_scope_gate_count']}")
    print(f"final readiness: {status['final_readiness_status']}")
    print(f"state snapshot: {status['state_snapshot_status']}")
    print()
    print("Current-scope capability")
    print("------------------------")
    print(f"release-candidate handoff: {status['release_candidate_handoff_status']}")
    print(f"release-candidate handoff ready: {yes_no(status['release_candidate_handoff_ready'])}")
    print(
        "release-candidate current scope ready: "
        f"{yes_no(status['release_candidate_current_scope_ready'])}"
    )
    print(
        "release-candidate usable for current priority scope: "
        f"{yes_no(status['release_candidate_can_be_used_for_current_priority_scope'])}"
    )
    print(
        "release-candidate is full strict master-plan completion: "
        f"{yes_no(status['release_candidate_is_full_strict_master_plan_completion'])}"
    )
    print(
        "release-candidate open strict blockers: "
        f"{status['release_candidate_open_strict_blocker_count']}"
    )
    print(f"project closeout forecast: {status['project_closeout_forecast_status']}")
    print(
        "current scope can be closed now: "
        f"{yes_no(status['project_closeout_current_scope_can_be_closed_now'])}"
    )
    print(
        "current scope closeout estimate: "
        f"{status['project_closeout_current_scope_closeout_estimate']}"
    )
    print(
        "strict master-plan can be closed now: "
        f"{yes_no(status['project_closeout_strict_master_plan_can_be_closed_now'])}"
    )
    print(
        "strict closeout requires external artifacts: "
        f"{yes_no(status['project_closeout_strict_closeout_requires_external_artifacts'])}"
    )
    print(
        "strict closeout estimate after artifacts: "
        f"{status['project_closeout_strict_closeout_estimate_after_artifacts']}"
    )
    print(f"project closeout acceptance gate: {status['project_closeout_acceptance_gate_status']}")
    print(
        "project closeout acceptance gate ready: "
        f"{yes_no(status['project_closeout_acceptance_gate_ready'])}"
    )
    print(
        "current phase acceptance allowed: "
        f"{yes_no(status['project_closeout_current_phase_acceptance_allowed'])}"
    )
    print(
        "strict final acceptance allowed: "
        f"{yes_no(status['project_closeout_strict_final_acceptance_allowed'])}"
    )
    print(
        "strict external artifacts done/missing: "
        f"{status['project_closeout_strict_external_artifact_done_count']}/"
        f"{status['project_closeout_strict_external_artifact_missing_count']}"
    )
    print(f"strict completion gate: {status['strict_master_plan_completion_gate_status']}")
    print(
        "strict completion gate ready: "
        f"{yes_no(status['strict_master_plan_completion_gate_ready'])}"
    )
    print(
        "strict completion allowed: "
        f"{yes_no(status['strict_completion_allowed'])}"
    )
    print(
        "strict completion external artifacts missing: "
        f"{yes_no(status['strict_completion_external_artifacts_missing'])}"
    )
    print(f"strict external artifact drop index: {status['strict_external_artifact_drop_index_status']}")
    print(
        "strict external artifact drop index ready: "
        f"{yes_no(status['strict_external_artifact_drop_index_ready'])}"
    )
    print(
        "strict external artifact domains: "
        f"{status['strict_external_artifact_drop_index_domain_count']}"
    )
    print(
        "strict external artifact required files: "
        f"{status['strict_external_artifact_drop_index_contract_check_count']}"
    )
    print(
        "strict external artifact files present: "
        f"{status['strict_external_artifact_drop_index_present_artifact_count']}"
    )
    print(
        "strict external artifact files still missing: "
        f"{status['strict_external_artifact_drop_index_awaiting_missing_artifact_count']}"
    )
    print(f"strict external artifact drop checklist: {status['strict_external_artifact_drop_checklist_status']}")
    print(
        "strict external artifact checklist ready: "
        f"{yes_no(status['strict_external_artifact_drop_checklist_ready'])}"
    )
    print(
        "strict external artifact checklist done files: "
        f"{status['strict_external_artifact_drop_checklist_done_count']}"
    )
    print(
        "strict external artifact checklist missing files: "
        f"{status['strict_external_artifact_drop_checklist_missing_file_count']}"
    )
    print(
        "strict external evidence receiving pack: "
        f"{status['strict_external_evidence_receiving_pack_status']}"
    )
    print(
        "strict external evidence receiving pack ready: "
        f"{yes_no(status['strict_external_evidence_receiving_pack_ready'])}"
    )
    print(
        "strict external evidence receiving pack present/missing: "
        f"{status['strict_external_evidence_receiving_pack_present_file_count']}/"
        f"{status['strict_external_evidence_receiving_pack_missing_file_count']}"
    )
    print(
        "strict external evidence receiving pack completion allowed: "
        f"{yes_no(status['strict_external_evidence_receiving_pack_completion_allowed'])}"
    )
    print(
        "strict master-plan closeout action pack: "
        f"{status['strict_master_plan_closeout_action_pack_status']}"
    )
    print(
        "strict master-plan closeout action pack ready: "
        f"{yes_no(status['strict_master_plan_closeout_action_pack_ready'])}"
    )
    print(
        "strict master-plan action items done/missing: "
        f"{status['strict_master_plan_closeout_action_pack_done_count']}/"
        f"{status['strict_master_plan_closeout_action_pack_missing_count']}"
    )
    print(
        "strict master-plan action pack completion allowed: "
        f"{yes_no(status['strict_master_plan_closeout_action_pack_completion_allowed'])}"
    )
    print(
        "strict master-plan action pack still open: "
        f"{yes_no(status['strict_master_plan_closeout_action_pack_still_open'])}"
    )
    print(f"current-scope delivery package: {status['current_scope_delivery_package_status']}")
    print(
        "current-scope delivery package ready: "
        f"{yes_no(status['current_scope_delivery_package_ready'])}"
    )
    print(
        "current-scope delivery package can be closed now: "
        f"{yes_no(status['current_scope_delivery_package_current_scope_can_be_closed_now'])}"
    )
    print(
        "current-scope delivery package full log passed: "
        f"{yes_no(status['current_scope_delivery_package_last_full_log_passed'])}"
    )
    print(
        "current-scope delivery package missing required commands: "
        f"{status['current_scope_delivery_package_missing_required_operator_command_count']}"
    )
    print(f"current-scope final handoff note: {status['current_scope_final_handoff_note_status']}")
    print(
        "current-scope final handoff note ready: "
        f"{yes_no(status['current_scope_final_handoff_note_ready'])}"
    )
    print(
        "current-scope final handoff note README missing snippets: "
        f"{status['current_scope_final_handoff_note_readme_missing_snippet_count']}"
    )
    print(
        "current-scope final handoff note runbook missing snippets: "
        f"{status['current_scope_final_handoff_note_runbook_missing_snippet_count']}"
    )
    print(f"current phase closure certificate: {status['current_phase_closure_certificate_status']}")
    print(
        "current phase closure certificate ready: "
        f"{yes_no(status['current_phase_closure_certificate_ready'])}"
    )
    print(f"current phase closeable: {yes_no(status['current_phase_closeable'])}")
    print(
        "closure certificate strict master-plan closure allowed: "
        f"{yes_no(status['closure_certificate_strict_master_plan_closure_allowed'])}"
    )
    print(
        "closure certificate strict master-plan still open: "
        f"{yes_no(status['closure_certificate_strict_master_plan_still_open'])}"
    )
    print(
        "closure certificate last full current-scope log passed: "
        f"{yes_no(status['closure_certificate_last_full_current_scope_log_passed'])}"
    )
    print(f"current phase release manifest: {status['current_phase_release_manifest_status']}")
    print(
        "current phase release manifest ready: "
        f"{yes_no(status['current_phase_release_manifest_ready'])}"
    )
    print(
        "current phase release manifest hashed artifacts: "
        f"{status['current_phase_release_manifest_hashed_artifact_count']}"
    )
    print(
        "current phase release manifest latest full log passed: "
        f"{yes_no(status['current_phase_release_manifest_latest_full_log_passed'])}"
    )
    print(
        "current phase release manifest strict master-plan closure allowed: "
        f"{yes_no(status['current_phase_release_manifest_strict_master_plan_closure_allowed'])}"
    )
    print(f"operator command inventory: {status['operator_command_inventory_status']}")
    print(f"operator command inventory ready: {yes_no(status['operator_command_inventory_ready'])}")
    print(
        "operator command inventory source files: "
        f"{status['operator_command_inventory_source_file_count']}"
    )
    print(
        "operator command inventory commands: "
        f"{status['operator_command_inventory_command_count']}"
    )
    print(
        "operator command inventory required snippets: "
        f"{status['operator_command_inventory_required_snippet_count']}"
    )
    print(
        "operator command inventory missing required snippets: "
        f"{status['operator_command_inventory_missing_required_snippet_count']}"
    )
    print(
        "operator command inventory missing tools: "
        f"{status['operator_command_inventory_missing_tool_count']}"
    )
    print(
        "operator command inventory syntax failures: "
        f"{status['operator_command_inventory_syntax_failure_count']}"
    )
    print(f"SUNDIALS local link audit: {status['sundials_local_link_audit_status']}")
    print(f"SUNDIALS local link audit ready: {yes_no(status['sundials_local_link_audit_ready'])}")
    print(f"SUNDIALS local link drift present: {yes_no(status['sundials_local_link_drift_present'])}")
    print(f"SUNDIALS local link current kind: {status['sundials_local_link_current_kind']}")
    print(
        "SUNDIALS expected tracked target exists: "
        f"{yes_no(status['sundials_local_link_expected_target_exists'])}"
    )
    print(
        "SUNDIALS CUDA-ready install candidates: "
        f"{status['sundials_local_link_cuda_ready_candidate_count']}"
    )
    print(
        "SUNDIALS safe to auto-restore: "
        f"{yes_no(status['sundials_local_link_safe_to_auto_restore'])}"
    )
    print(
        "SUNDIALS restore requires operator review: "
        f"{yes_no(status['sundials_restore_requires_explicit_operator_review'])}"
    )
    print(f"current user-priority ready: {yes_no(status['current_user_priority_ready'])}")
    print(f"CPU/MPI all scenarios: {yes_no(status['cpu_mpi_ready_for_all_current_scenarios'])}")
    print(f"single GPU all scenarios: {yes_no(status['single_gpu_ready_for_all_current_scenarios'])}")
    print(f"multi-GPU MPI+CUDA all scenarios: {yes_no(status['multi_gpu_mpi_cuda_ready_for_all_current_scenarios'])}")
    print()
    print("Fuel and liquefied-gas boundary")
    print("-------------------------------")
    print(f"multi-fuel capability: {status['multi_fuel_capability_status']}")
    print(f"multi-fuel template catalog: {status['multi_fuel_template_catalog_status']}")
    print(f"multi-fuel template catalog ready: {yes_no(status['multi_fuel_template_catalog_ready'])}")
    print(f"multi-fuel template count: {status['multi_fuel_template_catalog_template_count']}")
    print(
        "multi-fuel template species: "
        f"{', '.join(status['multi_fuel_template_catalog_fuel_species_seen'])}"
    )
    print(
        "multi-fuel template CSV ready: "
        f"{yes_no(status['multi_fuel_template_catalog_csv_template_ready'])}"
    )
    print(
        "multi-fuel template liquefied nonclaim comments: "
        f"{yes_no(status['multi_fuel_template_catalog_liquefied_nonclaim_comments_present'])}"
    )
    print(f"configurable fuel species: {yes_no(status['source_fuel_species_configurable'])}")
    print(f"H2 current engineering scope: {yes_no(status['h2_engineering_current_scope_ready'])}")
    print(f"CH4 gas/fire probes: {yes_no(status['ch4_gas_fire_probe_ready'])}")
    print(f"C3H8 gas/fire probes: {yes_no(status['c3h8_gas_fire_probe_ready'])}")
    print(f"gasified LNG surrogate boundary: {yes_no(status['gasified_lng_given_source_surrogate_ready'])}")
    print(f"gasified LPG surrogate boundary: {yes_no(status['gasified_lpg_given_source_surrogate_ready'])}")
    print(f"external vaporization multi-fuel CUDA: {yes_no(status['external_vaporization_multifuel_timeseries_cuda_passed'])}")
    print(
        "liquefied release source-model CUDA smoke: "
        f"{yes_no(status['liquefied_release_vaporization_source_model_cuda_smoke_passed'])}"
    )
    print(f"liquefied release source balance: {yes_no(status['liquefied_release_source_balance_ready'])}")
    print(
        "liquefied release source balance status: "
        f"{status['liquefied_release_source_balance_status']}"
    )
    print(
        "liquefied release source balance species: "
        f"{', '.join(status['liquefied_release_source_balance_species'])}"
    )
    print(
        "liquefied release source total gas mass kg: "
        f"{status['liquefied_release_source_balance_total_gas_mass_integral_kg']}"
    )
    print(
        "liquefied release source max inventory mass relative error: "
        f"{status['liquefied_release_source_balance_max_inventory_mass_relative_error']}"
    )
    print(
        "liquefied release source mapping schedule matches CSV: "
        f"{yes_no(status['liquefied_release_source_balance_mapping_schedule_matches_csv'])}"
    )
    print(
        "liquefied release source generated input matches mapping: "
        f"{yes_no(status['liquefied_release_source_balance_generated_input_matches_mapping'])}"
    )
    print(
        "liquefied release source balance negative selftest: "
        f"{yes_no(status['liquefied_release_source_balance_negative_selftest_ready'])}"
    )
    print(
        "liquefied release source balance negative selftest status: "
        f"{status['liquefied_release_source_balance_negative_selftest_status']}"
    )
    print(
        "liquefied release source balance negative cases rejected: "
        f"{status['liquefied_release_source_balance_negative_rejected_count']}/"
        f"{status['liquefied_release_source_balance_negative_case_count']}"
    )
    print(
        "liquefied release source balance expected diagnostics: "
        f"{status['liquefied_release_source_balance_expected_fragment_seen_count']}/"
        f"{status['liquefied_release_source_balance_negative_case_count']}"
    )
    print(
        "liquefied release source guard negative mdot: "
        f"{yes_no(status['liquefied_release_source_balance_guards_negative_mdot'])}"
    )
    print(
        "liquefied release source guard species drift: "
        f"{yes_no(status['liquefied_release_source_balance_guards_species_drift'])}"
    )
    print(
        "liquefied release source guard schedule mismatch: "
        f"{yes_no(status['liquefied_release_source_balance_guards_schedule_rate_mismatch'])}"
    )
    print(
        "liquefied release source guard phase-change overclaim: "
        f"{yes_no(status['liquefied_release_source_balance_guards_phase_change_overclaim'])}"
    )
    print(
        "liquefied release source guard generated-input species mismatch: "
        f"{yes_no(status['liquefied_release_source_balance_guards_generated_input_species_mismatch'])}"
    )
    print(
        "liquefied release thermal plausibility status: "
        f"{status['liquefied_release_thermal_plausibility_status']}"
    )
    print(
        "liquefied release thermal plausibility ready: "
        f"{yes_no(status['liquefied_release_thermal_plausibility_ready'])}"
    )
    print(f"liquefied release thermal species: {status['liquefied_release_thermal_species']}")
    print(
        "liquefied release vaporized fraction formula: "
        f"{yes_no(status['liquefied_release_thermal_vaporized_fraction_formula_ok'])}"
    )
    print(
        "liquefied release heat loads positive: "
        f"{yes_no(status['liquefied_release_thermal_heat_loads_positive'])}"
    )
    print(
        "liquefied release thermal max gas mass relative error: "
        f"{status['liquefied_release_thermal_max_gas_mass_relative_error']}"
    )
    print(
        "liquefied breach source contract status: "
        f"{status['liquefied_breach_source_contract_status']}"
    )
    print(
        "liquefied breach source contract ready: "
        f"{yes_no(status['liquefied_breach_source_contract_ready'])}"
    )
    print(
        "liquefied breach source contract cases: "
        f"{status['liquefied_breach_source_contract_case_count']}"
    )
    print(
        "liquefied breach source contract fluids: "
        f"{', '.join(status['liquefied_breach_source_contract_fluids'])}"
    )
    print(
        "liquefied breach source contract species: "
        f"{', '.join(status['liquefied_breach_source_contract_species'])}"
    )
    print(
        "liquefied breach source accepts screening breach inputs: "
        f"{yes_no(status['liquefied_breach_source_contract_accepts_screening_breach_inputs'])}"
    )
    print(
        "liquefied breach source generates external gas source: "
        f"{yes_no(status['liquefied_breach_source_contract_generates_external_gas_source'])}"
    )
    print(
        "liquefied breach source max gas mass relative error: "
        f"{status['liquefied_breach_source_contract_max_gas_mass_relative_error']}"
    )
    print(
        "liquefied breach source production phase-change claim allowed: "
        f"{yes_no(status['liquefied_breach_source_contract_production_phase_change_claim_allowed'])}"
    )
    print(
        "liquefied breach preset templates status: "
        f"{status['liquefied_breach_preset_templates_status']}"
    )
    print(
        "liquefied breach preset templates ready: "
        f"{yes_no(status['liquefied_breach_preset_templates_ready'])}"
    )
    print(
        "liquefied breach preset templates editable JSON: "
        f"{yes_no(status['liquefied_breach_preset_templates_editable_json_presets'])}"
    )
    print(
        "liquefied breach preset templates count: "
        f"{status['liquefied_breach_preset_templates_preset_count']}"
    )
    print(
        "liquefied breach preset templates fluids: "
        f"{', '.join(status['liquefied_breach_preset_templates_fluids'])}"
    )
    print(
        "liquefied breach preset templates species: "
        f"{', '.join(status['liquefied_breach_preset_templates_species'])}"
    )
    print(
        "liquefied breach preset templates generate CFD CSV: "
        f"{yes_no(status['liquefied_breach_preset_templates_generates_cfd_source_csv'])}"
    )
    print(
        "liquefied breach preset templates production phase-change claim allowed: "
        f"{yes_no(status['liquefied_breach_preset_templates_production_phase_change_claim_allowed'])}"
    )
    print(
        "liquefied phase-change overclaim guard status: "
        f"{status['liquefied_phase_change_overclaim_guard_status']}"
    )
    print(
        "liquefied phase-change overclaim guard ready: "
        f"{yes_no(status['liquefied_phase_change_overclaim_guard_ready'])}"
    )
    print(
        "liquefied gasified LNG/LPG bridge ready: "
        f"{yes_no(status['liquefied_phase_change_gasified_lng_lpg_bridge_ready'])}"
    )
    print(
        "liquefied external vaporization bridge ready: "
        f"{yes_no(status['liquefied_phase_change_external_vaporization_bridge_ready'])}"
    )
    print(
        "liquefied screening source ready: "
        f"{yes_no(status['liquefied_phase_change_screening_source_ready'])}"
    )
    print(
        "liquefied CUDA source runtime ready: "
        f"{yes_no(status['liquefied_phase_change_cuda_runtime_ready'])}"
    )
    print(
        "liquefied production phase-change claim allowed: "
        f"{yes_no(status['liquefied_phase_change_production_claim_allowed'])}"
    )
    print(
        "liquefied CFD solves liquid phase-change: "
        f"{yes_no(status['liquefied_phase_change_cfd_solves_liquid_phase_change'])}"
    )
    print(
        "liquefied CFD solves pool spread/boiling: "
        f"{yes_no(status['liquefied_phase_change_cfd_solves_pool_spread_evaporation'])}"
    )
    print(
        "liquefied CFD solves flashing discharge: "
        f"{yes_no(status['liquefied_phase_change_cfd_solves_flashing_discharge'])}"
    )
    print(f"internal liquid phase-change CFD: {yes_no(status['liquefied_gas_phase_change_ready'])}")
    print(f"multi-fuel production-ready claim: {yes_no(status['multi_fuel_production_ready'])}")
    print(f"overclaim guard: {yes_no(status['prevents_overclaim'])}")
    print()
    print("External plume reference boundary")
    print("---------------------------------")
    print(f"strict external plume status: {status['strict_external_plume_status']}")
    print(f"external plume blocker present: {yes_no(status['external_plume_blocker_present'])}")
    print(f"external plume blocker cleared: {yes_no(status['strict_external_plume_blocker_cleared'])}")
    print(
        "public machine-readable plume time series found: "
        f"{yes_no(status['public_machine_readable_external_plume_timeseries_found'])}"
    )
    print(
        "public SBEPV5/D27 geometry and release conditions found: "
        f"{yes_no(status['public_sbepv5_d27_geometry_and_release_conditions_found'])}"
    )
    print(f"Dataverse full dataset all files ready: {yes_no(status['dataverse_full_dataset_all_files_ready'])}")
    print(f"Dataverse ready file count: {status['dataverse_full_dataset_ready_file_count']}")
    print(f"Dataverse reference sensor time samples: {status['dataverse_reference_sensor_time_sample_count']}")
    print(f"Dataverse reference sensor records: {status['dataverse_reference_sensor_record_count']}")
    print(f"Dataverse agreement ready for CFD scoring: {yes_no(status['dataverse_agreement_ready_for_cfd_scoring'])}")
    print(f"Dataverse agreement sensor count: {status['dataverse_agreement_sensor_count']}")
    print(f"Dataverse 45s agreement attempt status: {status['dataverse_cfd_45s_agreement_attempt_status']}")
    print(
        "Dataverse 45s agreement failed sensors: "
        f"{status['dataverse_cfd_45s_agreement_attempt_failed_sensor_count']}"
    )
    print(
        "Dataverse 45s simulation end s: "
        f"{status['dataverse_cfd_45s_agreement_attempt_simulation_time_end_s']}"
    )
    print(f"Dataverse 120s agreement attempt status: {status['dataverse_cfd_120s_agreement_attempt_status']}")
    print(
        "Dataverse 120s agreement failed sensors: "
        f"{status['dataverse_cfd_120s_agreement_attempt_failed_sensor_count']}"
    )
    print(
        "Dataverse 120s simulation end s: "
        f"{status['dataverse_cfd_120s_agreement_attempt_simulation_time_end_s']}"
    )
    print(f"Dataverse long-window reconciliation: {status['dataverse_long_window_reconciliation_status']}")
    print(
        "Dataverse existing 120s reaches experimental peak interval: "
        f"{yes_no(status['dataverse_existing_120s_reaches_peak_interval'])}"
    )
    print(
        "Dataverse existing 120s all sensors passed: "
        f"{yes_no(status['dataverse_existing_120s_all_sensors_passed'])}"
    )
    print(
        "Dataverse existing 120s failed sensors: "
        f"{status['dataverse_existing_120s_failed_sensor_count']}"
    )
    print(
        "Dataverse current refined-source time end s: "
        f"{status['dataverse_current_refined_source_long_window_time_end_s']}"
    )
    print(
        "Dataverse current refined-source steps to 113s: "
        f"{status['dataverse_current_refined_source_steps_to_113s']}"
    )
    print(
        "Dataverse AMR current projection single-level: "
        f"{yes_no(status['dataverse_amr_source_projection_current_single_level'])}"
    )
    print(
        "Dataverse AMR lacks level-aware mask: "
        f"{yes_no(status['dataverse_amr_source_projection_lacks_level_aware_mask'])}"
    )
    print(
        "Dataverse AMR finest-owner projection: "
        f"{yes_no(status['dataverse_amr_source_projection_finest_available_level_only'])}"
    )
    print(
        "Dataverse AMR implementation status: "
        f"{status['dataverse_amr_source_projection_implementation_status']}"
    )
    print(
        "Dataverse AMR implementation ready: "
        f"{yes_no(status['dataverse_amr_source_projection_implementation_ready'])}"
    )
    print(
        "Dataverse AMR MPI+CUDA linked executable: "
        f"{yes_no(status['dataverse_amr_source_projection_mpi_cuda_linked_executable'])}"
    )
    print(
        "Dataverse AMR MPI+CUDA reproducible build entrypoint: "
        f"{yes_no(status['dataverse_amr_source_projection_mpi_cuda_reproducible_build_entrypoint_ready'])}"
    )
    print(
        "Dataverse AMR MPI+CUDA reproducible build uses CUDA 12.6: "
        f"{yes_no(status['dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_cuda_12_6'])}"
    )
    print(
        "Dataverse AMR MPI+CUDA reproducible build uses local SUNDIALS-CUDA: "
        f"{yes_no(status['dataverse_amr_source_projection_mpi_cuda_reproducible_build_uses_local_sundials_cuda'])}"
    )
    print(
        "Dataverse geometry ready for sensor sampling map: "
        f"{yes_no(status['dataverse_geometry_ready_for_sensor_sampling_map'])}"
    )
    print(
        "Dataverse geometry ready for full mesh parity: "
        f"{yes_no(status['dataverse_geometry_ready_for_full_mesh_parity'])}"
    )
    print(
        "Dataverse obstacle exact bounds available: "
        f"{yes_no(status['dataverse_geometry_obstacle_exact_bounds_available'])}"
    )
    print(
        "Dataverse refined-source strict blocker still open: "
        f"{yes_no(status['dataverse_full_channel_refined_source_dx025_1000step_dt5em6_strict_blocker_still_open'])}"
    )
    print()
    print("Real CAD boundary")
    print("-----------------")
    print(f"strict real CAD status: {status['strict_real_cad_status']}")
    print(f"real CAD blocker present: {yes_no(status['real_cad_blocker_present'])}")
    print(f"real CAD blocker cleared: {yes_no(status['strict_real_cad_blocker_cleared'])}")
    print(f"real CAD handoff contract status: {status['real_cad_handoff_contract_status']}")
    print(f"real CAD handoff contract ready: {yes_no(status['real_cad_handoff_contract_ready'])}")
    print(f"real CAD source CAD files: {status['real_cad_source_cad_file_count']}")
    print(f"real CAD cleaned geometry files: {status['real_cad_cleaned_geometry_file_count']}")
    print(f"real CAD boundary contract status: {status['real_cad_boundary_contract_status']}")
    print(
        "real CAD boundary contract ready for credit: "
        f"{yes_no(status['real_cad_boundary_contract_ready_for_credit'])}"
    )
    print(f"real CAD negative selftest status: {status['real_cad_negative_selftest_status']}")
    print(f"real CAD negative selftest ready: {yes_no(status['real_cad_negative_selftest_ready'])}")
    print(
        "real CAD negative cases rejected: "
        f"{status['real_cad_negative_selftest_rejected_count']}/"
        f"{status['real_cad_negative_selftest_case_count']}"
    )
    print(
        "real CAD expected diagnostics: "
        f"{status['real_cad_negative_selftest_expected_fragment_seen_count']}/"
        f"{status['real_cad_negative_selftest_case_count']}"
    )
    print(f"real CAD guard synthetic manifest: {yes_no(status['real_cad_guards_synthetic_manifest'])}")
    print(f"real CAD guard missing provenance: {yes_no(status['real_cad_guards_missing_provenance'])}")
    print(f"real CAD guard source hash mismatch: {yes_no(status['real_cad_guards_source_hash_mismatch'])}")
    print(
        "real CAD guard large-layout too few geometries: "
        f"{yes_no(status['real_cad_guards_large_layout_too_few_geometries'])}"
    )
    print(f"real CAD guard data-room bad hash: {yes_no(status['real_cad_guards_data_room_bad_hash'])}")
    print(
        "real CAD guard cleanup quality false check: "
        f"{yes_no(status['real_cad_guards_cleanup_quality_false_check'])}"
    )
    print(f"real CAD guard boundary placeholder: {yes_no(status['real_cad_guards_boundary_placeholder'])}")
    print(
        "real CAD guard boundary missing required role: "
        f"{yes_no(status['real_cad_guards_boundary_missing_required_role'])}"
    )
    print()
    print("Fire consequence calibration boundary")
    print("-------------------------------------")
    print(f"strict fire calibration status: {status['strict_fire_calibration_status']}")
    print(f"fire calibration blocker present: {yes_no(status['strict_fire_calibration_blocker_present'])}")
    print(f"fire calibration blocker cleared: {yes_no(status['strict_fire_calibration_blocker_cleared'])}")
    print(
        "fire candidate radiation+overpressure sources available: "
        f"{yes_no(status['fire_candidate_sources_both_metric_families_available'])}"
    )
    print(
        "fire candidate repository package ready: "
        f"{yes_no(status['fire_candidate_sources_repository_package_ready'])}"
    )
    print(f"EXP002 reduced overpressure status: {status['exp002_reduced_overpressure_status']}")
    print(f"EXP002 source CSV MD5 verified: {yes_no(status['exp002_source_csv_md5_verified'])}")
    print(f"EXP002 pressure channels: {status['exp002_pressure_channel_count']}")
    print(f"EXP002 overpressure metrics: {status['exp002_overpressure_metric_count']}")
    print(f"EXP002 pressure CFD proxy extracted: {yes_no(status['exp002_pressure_cfd_proxy_extracted'])}")
    print(
        "EXP002 pressure CFD proxy CPU/GPU parity: "
        f"{yes_no(status['exp002_pressure_cfd_proxy_cpu_gpu_parity_passed'])}"
    )
    print(
        "EXP002 pressure CFD proxy CPU/GPU rel diff: "
        f"{status['exp002_pressure_cfd_proxy_cpu_gpu_rel_diff']}"
    )
    print(
        "EXP002 CFD outputs sufficient for pressure agreement: "
        f"{yes_no(status['exp002_cfd_outputs_sufficient_for_pressure_agreement'])}"
    )
    print(f"plotfile sensor sampling contract: {yes_no(status['plotfile_sensor_sampling_contract_ready'])}")
    print(f"plotfile sensor sampling rows: {status['plotfile_sensor_sampling_row_count']}")
    print(
        "plotfile sensor sampling uses synthetic coordinates: "
        f"{yes_no(status['plotfile_sensor_sampling_uses_synthetic_sensor_coordinates'])}"
    )
    print(
        "plotfile sensor sampling negative cases rejected: "
        f"{status['plotfile_sensor_sampling_negative_refused_count']}/"
        f"{status['plotfile_sensor_sampling_negative_case_count']}"
    )
    print(f"MDPI radiation metrics: {status['mdpi_radiation_metric_count']}")
    print(
        "MDPI integrated radiation CFD proxy extracted: "
        f"{yes_no(status['mdpi_radiation_integrated_cfd_proxy_extracted'])}"
    )
    print(
        "MDPI integrated radiation proxy plotfiles: "
        f"{status['mdpi_radiation_integrated_cfd_proxy_plotfile_count']}"
    )
    print(
        "MDPI virtual radiometer flux generated: "
        f"{yes_no(status['mdpi_radiation_integrated_cfd_proxy_virtual_radiometer_flux_generated'])}"
    )
    print(
        "MDPI integrated radiation peak radiative power W: "
        f"{status['mdpi_radiation_integrated_cfd_proxy_peak_radiative_power_w']}"
    )
    print(
        "MDPI CFD outputs sufficient for radiation agreement: "
        f"{yes_no(status['mdpi_radiation_integrated_cfd_proxy_outputs_sufficient_for_mdpi_agreement'])}"
    )
    print(f"fire residual budget status: {status['fire_residual_budget_status']}")
    print(f"fire residual budget ready: {yes_no(status['fire_residual_budget_ready'])}")
    print(
        "fire residual budget clears strict blocker: "
        f"{yes_no(status['fire_residual_budget_clears_strict_blocker'])}"
    )
    print(
        "fire residual budget pressure agreement ready: "
        f"{yes_no(status['fire_residual_budget_pressure_agreement_ready'])}"
    )
    print(
        "fire residual budget radiation agreement ready: "
        f"{yes_no(status['fire_residual_budget_radiation_agreement_ready'])}"
    )
    print(
        "fire residual budget pressure missing artifacts: "
        f"{status['fire_residual_budget_pressure_missing_artifact_count']}"
    )
    print(
        "fire residual budget radiation missing artifacts: "
        f"{status['fire_residual_budget_radiation_missing_artifact_count']}"
    )
    print(
        "fire residual budget production claim allowed: "
        f"{yes_no(status['fire_residual_budget_production_claim_allowed'])}"
    )
    print()
    print("Strict master-plan boundary")
    print("---------------------------")
    print(f"goal complete: {yes_no(status['goal_complete'])}")
    print(f"strict master-plan complete: {yes_no(status['strict_master_plan_complete'])}")
    print(f"open strict blocker count: {status['open_strict_blocker_count']}")
    for blocker in status["open_strict_blockers"]:
        print(f"- {blocker}")
    print()
    print("Next action")
    print("-----------")
    print(f"strict unblock runbook: {status['strict_unblock_runbook']}")
    print(f"snapshot key reports: {status['snapshot_key_report_count']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()

    status = build_status()
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print_text(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
