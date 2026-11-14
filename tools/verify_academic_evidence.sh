#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

readiness_report='docs/codex_audit/evidence/academic_readiness_summary_20260729/academic_readiness_summary_report.json'
readiness_qlt03_closure_delta_report='docs/codex_audit/evidence/academic_readiness_qlt03_closure_delta_20260730/academic_readiness_qlt03_closure_delta_report.json'
twophase_broader_matrix_report='docs/codex_audit/evidence/academic_twophase_broader_matrix_20260730/academic_twophase_broader_matrix_report.json'
shock_bubble_operator_preflight_report='docs/codex_audit/evidence/academic_twophase_shock_bubble_operator_preflight_20260730/academic_twophase_shock_bubble_operator_preflight_report.json'
shock_bubble_cfd_scout_report='docs/codex_audit/evidence/academic_twophase_shock_bubble_cfd_scout_20260730/academic_twophase_shock_bubble_cfd_scout_report.json'
shock_bubble_validation_report='docs/codex_audit/evidence/academic_twophase_shock_bubble_validation_20260730/academic_twophase_shock_bubble_validation_report.json'
spray_residual_report='docs/codex_audit/evidence/academic_spray_coupled_budget_residual_20260729/academic_spray_coupled_budget_residual_report.json'
gas_liquid_detonation_certification_report='docs/codex_audit/evidence/academic_gas_liquid_detonation_certification_20260731/academic_gas_liquid_detonation_certification_report.json'
academic_gas_detonation_mpi_cuda_report='docs/codex_audit/evidence/academic_gas_detonation_mpi_cuda_20260731/academic_gas_detonation_mpi_cuda_report.json'
academic_gas_liquid_detonation_cuda_scout_report='docs/codex_audit/evidence/academic_gas_liquid_detonation_cuda_scout_20260731/academic_gas_liquid_detonation_cuda_scout_report.json'
academic_gas_liquid_detonation_mpi_cuda_long_report='docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_long_20260803/academic_gas_liquid_detonation_mpi_cuda_long_report.json'
academic_gas_liquid_detonation_mpi_cuda_extended_report='docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_extended_20260803/academic_gas_liquid_detonation_mpi_cuda_extended_report.json'
academic_gas_detonation_priority_matrix_report='docs/codex_audit/evidence/academic_gas_detonation_priority_matrix_20260731/academic_gas_detonation_priority_matrix_report.json'
bubble_observables_report='docs/codex_audit/evidence/academic_twophase_bubble_rise_observable_timeseries_20260729/academic_twophase_bubble_rise_observable_timeseries_report.json'
canonical_bubble_report='docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_reference_20260729/academic_twophase_canonical_bubble_rise_reference_report.json'
canonical_candidate_report='docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_candidate_20260730/canonical_bubble_rise_candidate_report.json'
canonical_final_time_scout_report='docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_final_time_scout_20260730/canonical_bubble_rise_final_time_scout_report.json'
qlt03_path_decision_report='docs/codex_audit/evidence/academic_twophase_qlt03_path_decision_20260730/academic_twophase_qlt03_path_decision_report.json'
qlt03_lm_aux_bridge_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_aux_bridge_smoke_20260730/academic_twophase_qlt03_lm_aux_bridge_smoke_report.json'
qlt03_lm_bridge_followup_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_bridge_followup_20260730/academic_twophase_qlt03_lm_bridge_followup_report.json'
qlt03_lm_canonical_csf_scout_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_canonical_csf_scout_20260730/academic_twophase_qlt03_lm_canonical_csf_scout_report.json'
qlt03_lm_t3_scout_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_t3_scout_20260730/academic_twophase_qlt03_lm_t3_scout_report.json'
qlt03_lm_grid_confirmation_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_t3_grid_confirmation_20260730/qlt03_lm_grid_confirmation_report.json'
qlt03_lm_curvature_trial_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_curvature_trials_20260730/curvature_trial_report.json'
qlt03_lm_interface_sharpness_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_interface_sharpness_20260730/interface_sharpness_report.json'
qlt03_lm_csf_balance_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_balance_diagnostic_20260730/csf_balance_diagnostic_report.json'
qlt03_lm_pressure_residual_trial_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_pressure_residual_csf_short_20260730/pressure_residual_csf_trial_report.json'
qlt03_lm_aux_density_mac_sigma_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_aux_density_mac_sigma_20260730/aux_density_mac_sigma_report.json'
qlt03_lm_force_pressure_balance_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_force_pressure_balance_diagnostic_20260730/force_pressure_balance_diagnostic_report.json'
qlt03_lm_csf_stress_candidate_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_candidate_20260730/csf_stress_candidate_report.json'
qlt03_lm_csf_stress_grid_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_grid_confirmation_20260730/csf_stress_grid_confirmation_report.json'
qlt03_lm_csf_stress_closure_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_csf_stress_closure_20260730/qlt03_lm_csf_stress_closure_report.json'
qlt03_lm_pseudo_levelset_trial_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_pseudo_levelset_curvature_trials_20260730/pseudo_levelset_curvature_trial_report.json'
qlt03_lm_transport_trial_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_transport_trials_20260730/transport_trial_report.json'
qlt03_lm_thinc_like_trial_report='docs/codex_audit/evidence/academic_twophase_qlt03_lm_thinc_like_trials_20260730/thinc_like_trial_report.json'
qlt03_route_capability_report='docs/codex_audit/evidence/academic_twophase_qlt03_route_capability_20260730/route_capability_report.json'
spray_cv_report='docs/codex_audit/evidence/academic_spray_closed_control_volume_budget_20260729/academic_spray_closed_control_volume_budget_report.json'
reacting_spray_cv_report='docs/codex_audit/evidence/academic_reacting_spray_closed_control_volume_budget_20260729/academic_reacting_spray_closed_control_volume_budget_report.json'

printf '[academic-verify] verify bubble-rise canonical observables\n'
if [[ ! -f "$bubble_observables_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$bubble_observables_report" >&2
  exit 1
fi
python3 tools/write_academic_twophase_bubble_rise_observables_report.py --verify-json "$bubble_observables_report"

printf '[academic-verify] verify canonical bubble-rise geometry/gravity candidate\n'
if [[ ! -f "$canonical_candidate_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$canonical_candidate_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_canonical_bubble_rise_candidate_report.py --verify-json "$canonical_candidate_report"

printf '[academic-verify] verify canonical bubble-rise final-time scout\n'
if [[ ! -f "$canonical_final_time_scout_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$canonical_final_time_scout_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_canonical_bubble_rise_final_time_scout_report.py --verify-json "$canonical_final_time_scout_report"

printf '[academic-verify] verify QLT-03 low-Mach canonical-strength CSF scout\n'
if [[ ! -f "$qlt03_lm_canonical_csf_scout_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_canonical_csf_scout_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_canonical_csf_scout_report.py --verify-json "$qlt03_lm_canonical_csf_scout_report"

printf '[academic-verify] verify QLT-03 low-Mach t=3 final-time scout\n'
if [[ ! -f "$qlt03_lm_t3_scout_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_t3_scout_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_t3_scout_report.py --verify-json "$qlt03_lm_t3_scout_report"

printf '[academic-verify] verify QLT-03 low-Mach grid confirmation
'
if [[ ! -f "$qlt03_lm_grid_confirmation_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s
' "$qlt03_lm_grid_confirmation_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_grid_confirmation_report.py --verify-json "$qlt03_lm_grid_confirmation_report"

printf '[academic-verify] verify QLT-03 low-Mach rejected curvature trials\n'
if [[ ! -f "$qlt03_lm_curvature_trial_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_curvature_trial_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_curvature_trial_report.py --verify-json "$qlt03_lm_curvature_trial_report"

printf '[academic-verify] verify QLT-03 low-Mach interface-sharpness diagnosis\n'
if [[ ! -f "$qlt03_lm_interface_sharpness_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_interface_sharpness_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_interface_sharpness_report.py --verify-json "$qlt03_lm_interface_sharpness_report"

printf '[academic-verify] verify QLT-03 low-Mach CSF balance diagnostic\n'
if [[ ! -f "$qlt03_lm_csf_balance_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_csf_balance_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_csf_balance_diagnostic_report.py --verify-json "$qlt03_lm_csf_balance_report"

printf '[academic-verify] verify QLT-03 low-Mach rejected pressure-residual CSF trial\n'
if [[ ! -f "$qlt03_lm_pressure_residual_trial_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_pressure_residual_trial_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_pressure_residual_csf_trial_report.py --verify-json "$qlt03_lm_pressure_residual_trial_report"

printf '[academic-verify] verify QLT-03 low-Mach Aux-density MAC sigma consistency\n'
if [[ ! -f "$qlt03_lm_aux_density_mac_sigma_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_aux_density_mac_sigma_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_aux_density_mac_sigma_report.py --verify-json "$qlt03_lm_aux_density_mac_sigma_report"

printf '[academic-verify] verify QLT-03 low-Mach force-pressure balance diagnostic\n'
if [[ ! -f "$qlt03_lm_force_pressure_balance_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_force_pressure_balance_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_force_pressure_balance_diagnostic_report.py --verify-json "$qlt03_lm_force_pressure_balance_report"

printf '[academic-verify] verify QLT-03 low-Mach CSF stress candidate promotion\n'
if [[ ! -f "$qlt03_lm_csf_stress_candidate_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_csf_stress_candidate_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_csf_stress_candidate_report.py --verify-json "$qlt03_lm_csf_stress_candidate_report"

printf '[academic-verify] verify QLT-03 low-Mach CSF stress grid confirmation\n'
if [[ ! -f "$qlt03_lm_csf_stress_grid_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_csf_stress_grid_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_csf_stress_grid_confirmation_report.py --verify-json "$qlt03_lm_csf_stress_grid_report"

printf '[academic-verify] verify QLT-03 low-Mach CSF stress closure\n'
if [[ ! -f "$qlt03_lm_csf_stress_closure_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_csf_stress_closure_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_csf_stress_closure_report.py --verify-json "$qlt03_lm_csf_stress_closure_report"

printf '[academic-verify] qlt03 lm csf stress closure confirmed\n'

printf '[academic-verify] verify QLT-03 low-Mach rejected pseudo-levelset curvature trial\n'
if [[ ! -f "$qlt03_lm_pseudo_levelset_trial_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_pseudo_levelset_trial_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_pseudo_levelset_curvature_trial_report.py --verify-json "$qlt03_lm_pseudo_levelset_trial_report"

printf '[academic-verify] verify QLT-03 low-Mach rejected transport trials\n'
if [[ ! -f "$qlt03_lm_transport_trial_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_transport_trial_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_transport_trial_report.py --verify-json "$qlt03_lm_transport_trial_report"

printf '[academic-verify] verify QLT-03 low-Mach rejected THINC-like trial\n'
if [[ ! -f "$qlt03_lm_thinc_like_trial_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_thinc_like_trial_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_thinc_like_trial_report.py --verify-json "$qlt03_lm_thinc_like_trial_report"

printf '[academic-verify] verify QLT-03 route capability audit\n'
if [[ ! -f "$qlt03_route_capability_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_route_capability_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_route_capability_report.py --verify-json "$qlt03_route_capability_report"

printf '[academic-verify] verify QLT-03 path decision\n'
if [[ ! -f "$qlt03_path_decision_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_path_decision_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_path_decision_report.py --verify-json "$qlt03_path_decision_report"

printf '[academic-verify] verify QLT-03 low-Mach aux-alpha bridge smoke\n'
if [[ ! -f "$qlt03_lm_aux_bridge_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_aux_bridge_report" >&2
  exit 2
fi
python3 tools/validate_academic_twophase_qlt03_lm_aux_bridge.py --verify-json "$qlt03_lm_aux_bridge_report"

printf '[academic-verify] verify QLT-03 low-Mach bridge follow-up gates\n'
if [[ ! -f "$qlt03_lm_bridge_followup_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$qlt03_lm_bridge_followup_report" >&2
  exit 2
fi
python3 tools/write_academic_twophase_qlt03_lm_bridge_followup_report.py --verify-json "$qlt03_lm_bridge_followup_report"

printf '[academic-verify] verify canonical bubble-rise reference preflight\n'
if [[ ! -f "$canonical_bubble_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$canonical_bubble_report" >&2
  exit 1
fi
python3 tools/write_academic_twophase_canonical_bubble_rise_reference_report.py --verify-json "$canonical_bubble_report"

printf '[academic-verify] verify spray closed control-volume budget\n'
if [[ ! -f "$spray_cv_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$spray_cv_report" >&2
  exit 1
fi
python3 tools/write_academic_spray_closed_control_volume_budget_report.py --verify-json "$spray_cv_report"

printf '[academic-verify] verify reacting spray closed control-volume budget\n'
if [[ ! -f "$reacting_spray_cv_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$reacting_spray_cv_report" >&2
  exit 1
fi
python3 tools/write_academic_reacting_spray_closed_control_volume_budget_report.py --verify-json "$reacting_spray_cv_report"

printf '[academic-verify] verify spray coupled-budget residual diagnostics\n'
if [[ ! -f "$spray_residual_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$spray_residual_report" >&2
  exit 1
fi
python3 tools/write_academic_spray_coupled_budget_residual_report.py --verify-json "$spray_residual_report"


printf '[academic-verify] verify academic gas detonation MPI+CUDA runtime\n'
if [[ ! -f "$academic_gas_detonation_mpi_cuda_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$academic_gas_detonation_mpi_cuda_report" >&2
  exit 1
fi
python3 tools/write_academic_gas_detonation_mpi_cuda_report.py --verify-json "$academic_gas_detonation_mpi_cuda_report"

printf '[academic-verify] verify academic gas detonation priority matrix\n'
if [[ ! -f "$academic_gas_detonation_priority_matrix_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$academic_gas_detonation_priority_matrix_report" >&2
  exit 1
fi
python3 tools/write_academic_gas_detonation_priority_matrix_report.py --verify-json "$academic_gas_detonation_priority_matrix_report"

printf '[academic-verify] verify academic gas-liquid detonation certification\n'
if [[ ! -f "$gas_liquid_detonation_certification_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$gas_liquid_detonation_certification_report" >&2
  exit 1
fi
python3 tools/write_academic_gas_liquid_detonation_certification_report.py --verify-json "$gas_liquid_detonation_certification_report"

printf '[academic-verify] verify academic gas-liquid detonation CUDA scout\n'
if [[ ! -f "$academic_gas_liquid_detonation_cuda_scout_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$academic_gas_liquid_detonation_cuda_scout_report" >&2
  exit 1
fi
python3 tools/write_academic_gas_liquid_detonation_cuda_scout_report.py --verify-json "$academic_gas_liquid_detonation_cuda_scout_report"

printf '[academic-verify] verify academic gas-liquid detonation MPI+CUDA long stability\n'
if [[ ! -f "$academic_gas_liquid_detonation_mpi_cuda_long_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$academic_gas_liquid_detonation_mpi_cuda_long_report" >&2
  exit 1
fi
python3 tools/write_academic_gas_liquid_detonation_mpi_cuda_long_report.py --verify-json "$academic_gas_liquid_detonation_mpi_cuda_long_report"

printf '[academic-verify] verify academic gas-liquid detonation MPI+CUDA extended stability\n'
if [[ ! -f "$academic_gas_liquid_detonation_mpi_cuda_extended_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$academic_gas_liquid_detonation_mpi_cuda_extended_report" >&2
  exit 1
fi
python3 tools/write_academic_gas_liquid_detonation_mpi_cuda_extended_report.py --verify-json "$academic_gas_liquid_detonation_mpi_cuda_extended_report"

printf '[academic-verify] verify academic readiness summary\n'
if [[ ! -f "$readiness_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$readiness_report" >&2
  exit 1
fi
python3 tools/write_academic_readiness_summary_report.py --verify-json "$readiness_report"

printf '[academic-verify] verify academic readiness QLT-03 closure delta\n'
if [[ ! -f "$readiness_qlt03_closure_delta_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$readiness_qlt03_closure_delta_report" >&2
  exit 1
fi
python3 tools/write_academic_readiness_qlt03_closure_delta_report.py --verify-json "$readiness_qlt03_closure_delta_report"

printf '[academic-verify] verify academic shock-bubble operator preflight\n'
if [[ ! -f "$shock_bubble_operator_preflight_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$shock_bubble_operator_preflight_report" >&2
  exit 1
fi
python3 tools/write_academic_twophase_shock_bubble_operator_preflight_report.py --verify-json "$shock_bubble_operator_preflight_report"

printf '[academic-verify] verify academic shock-bubble CFD scout\n'
if [[ ! -f "$shock_bubble_cfd_scout_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$shock_bubble_cfd_scout_report" >&2
  exit 1
fi
python3 tools/write_academic_twophase_shock_bubble_cfd_scout_report.py --verify --output "$shock_bubble_cfd_scout_report"

printf '[academic-verify] verify academic shock-bubble independent validation\n'
if [[ ! -f "$shock_bubble_validation_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$shock_bubble_validation_report" >&2
  exit 1
fi
python3 tools/write_academic_twophase_shock_bubble_validation_report.py --verify-json "$shock_bubble_validation_report"

printf '[academic-verify] verify academic broader two-phase matrix\n'
if [[ ! -f "$twophase_broader_matrix_report" ]]; then
  printf '[academic-verify] FAIL missing report: %s\n' "$twophase_broader_matrix_report" >&2
  exit 1
fi
python3 tools/write_academic_twophase_broader_matrix_report.py --verify-json "$twophase_broader_matrix_report"

printf '[academic-verify] PASS academic evidence verification\n'
