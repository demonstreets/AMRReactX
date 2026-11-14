#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

skip_ctest="${CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST:-${CODEX_ENGINEERING_VERIFY_SKIP_CTEST:-FALSE}}"
skip_report="${CODEX_ENGINEERING_H2_VERIFY_SKIP_REPORT:-FALSE}"
skip_rebuild_manifest="${CODEX_ENGINEERING_H2_VERIFY_SKIP_REBUILD_MANIFEST:-FALSE}"
ctest_dir="${CODEX_ENGINEERING_H2_VERIFY_CTEST_DIR:-build-codex-smoke}"

run() {
  printf '[engineering-h2-verify] %s\n' "$*"
  "$@"
}


verify_mpi_link_shim() {
  local shim_dir libs lib
  libs=(libmpi_cxx.so libopen-rte.so libopen-pal.so libhwloc.so libevent_core.so libevent_pthreads.so)
  source tools/prepare_mpi_link_shims.sh >/tmp/codex_mpi_link_shim_verify.log
  shim_dir="${CODEX_MPI_LINK_SHIM_DIR:-$repo_root/.codex/lib/mpi-link}"
  for lib in "${libs[@]}"; do
    if [[ ! -L "$shim_dir/$lib" ]]; then
      printf '[engineering-h2-verify] FAIL MPI link shim missing symlink: %s/%s\n' "$shim_dir" "$lib" >&2
      return 1
    fi
    if [[ ! -e "$shim_dir/$lib" ]]; then
      printf '[engineering-h2-verify] FAIL MPI link shim dangling symlink: %s/%s\n' "$shim_dir" "$lib" >&2
      return 1
    fi
  done
  case ":${LIBRARY_PATH:-}:" in
    *":$shim_dir:"*) ;;
    *) printf '[engineering-h2-verify] FAIL MPI link shim not exported in LIBRARY_PATH\n' >&2; return 1 ;;
  esac
  case ":${LD_LIBRARY_PATH:-}:" in
    *":$shim_dir:"*) ;;
    *) printf '[engineering-h2-verify] FAIL MPI link shim not exported in LD_LIBRARY_PATH\n' >&2; return 1 ;;
  esac
  printf '[engineering-h2-verify] MPI link shim PASS dir=%s libs=%s\n' "$shim_dir" "${libs[*]}"
}

verify_existing() {
  local label="$1"
  local path="$2"
  if [[ ! -f "$path" ]]; then
    printf '[engineering-h2-verify] FAIL missing %s: %s\n' "$label" "$path" >&2
    return 1
  fi
}

release_pack='docs/codex_audit/evidence/engineering_h2_production_full_20260720/release_pack/evidence_pack_manifest.json'
acceptance_matrix='docs/codex_audit/evidence/engineering_h2_acceptance_matrix_20260720/engineering_h2_acceptance_matrix.json'
scorecard='docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json'
integrated_initial_acceptance_scorecard='docs/codex_audit/evidence/engineering_production_scorecard_20260728_integrated_initial_acceptance/engineering_production_scorecard.json'
production_evidence_verification_report='docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json'
runtime_affinity='docs/codex_audit/evidence/engineering_runtime_affinity_20260720/runtime_affinity_manifest.json'
hybrid_runtime_affinity='docs/codex_audit/evidence/engineering_runtime_affinity_hybrid_20260720/runtime_affinity_manifest.json'
scheduler_report='docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json'
ignition_report='docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/ignition_consequence_report.json'
fire_report='docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.json'
fire_calibration_public_source_triage_report='docs/codex_audit/evidence/engineering_h2_fire_calibration_public_source_triage_20260724/fire_calibration_public_source_triage_report.json'
fire_calibration_dataset_ingestion_report='docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/fire_calibration_dataset_ingestion_report.json'
fire_calibration_dataset_ingestion_selftest_report='docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_selftest_20260727/fire_calibration_dataset_ingestion_selftest_report.json'
fire_calibration_digitization_preflight_report='docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/fire_calibration_digitization_preflight_report.json'
fire_calibration_literature_metric_preflight_report='docs/codex_audit/evidence/engineering_h2_fire_calibration_literature_metric_preflight_20260724/fire_calibration_literature_metric_preflight_report.json'
fire_calibration_package_report='docs/codex_audit/evidence/engineering_h2_fire_calibration_package_20260723/fire_calibration_package_report.json'
fire_calibration_dataset_report='docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_20260723/fire_calibration_dataset_report.json'
real_cad_cleanup_package_report='docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/real_cad_cleanup_package_report.json'
real_cad_intake_preflight_report='docs/codex_audit/evidence/engineering_h2_real_cad_intake_preflight_20260724/real_cad_intake_preflight_report.json'
real_cad_boundary_tag_contract_report='docs/codex_audit/evidence/engineering_h2_real_cad_boundary_tag_contract_20260724/real_cad_boundary_tag_contract_report.json'
mpi_scaling_report='docs/codex_audit/evidence/engineering_h2_mpi_scaling_20260720/mpi_scaling_report.json'
hybrid_cfd_scout_report='docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/hybrid_cfd_scout_report.json'
hybrid_production_mesh_scout_report='docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/hybrid_production_mesh_scout_report.json'
hybrid_production_mesh_8rank_scout_report='docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/hybrid_production_mesh_8rank_scout_report.json'
hybrid_production_mesh_8rank_600step_stability_scout_report='docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_600step_stability_scout_20260721/hybrid_production_mesh_8rank_600step_stability_scout_report.json'
hybrid_production_mesh_600step_stability_scout_report='docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/hybrid_production_mesh_600step_stability_scout_report.json'
hybrid_largegrid_8rank_120step_scout_report='docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/hybrid_largegrid_8rank_120step_scout_report.json'
reference_agreement_report='docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/h2_reference_agreement_report.json'
h2_plume_observation_report='docs/codex_audit/evidence/engineering_h2_plume_observation_20260723/h2_plume_observation_report.json'
external_plume_benchmark_spec_report='docs/codex_audit/evidence/engineering_h2_external_plume_benchmark_spec_20260723/hysafe_sbepv5_d27_benchmark_spec_report.json'
external_plume_public_source_triage_report='docs/codex_audit/evidence/engineering_h2_external_plume_public_source_triage_20260724/external_plume_public_source_triage_report.json'
sbepv5_dataset_ingestion_report='docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/sbepv5_d27_dataset_ingestion_report.json'
sbepv5_dataset_ingestion_selftest_report='docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_selftest_20260724/sbepv5_d27_dataset_ingestion_selftest_report.json'
sbepv5_digitization_preflight_report='docs/codex_audit/evidence/engineering_h2_sbepv5_d27_digitization_preflight_20260724/sbepv5_d27_digitization_preflight_report.json'
sbepv5_literature_metric_preflight_report='docs/codex_audit/evidence/engineering_h2_sbepv5_d27_literature_metric_preflight_20260724/sbepv5_d27_literature_metric_preflight_report.json'
sbepv5_case_package_report='docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/sbepv5_d27_case_package_report.json'
sbepv5_case_package_preflight_report='docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_preflight_20260723/sbepv5_d27_case_package_preflight_report.json'
sbepv5_external_dataset_report='docs/codex_audit/evidence/engineering_h2_sbepv5_d27_external_dataset_20260723/sbepv5_d27_external_dataset_report.json'
sbepv5_d27_program_scout_report='docs/codex_audit/evidence/engineering_h2_sbepv5_d27_program_scout_run_20260727/sbepv5_d27_scout_run_report.json'
external_plume_benchmark_readiness_report='docs/codex_audit/evidence/engineering_h2_external_plume_benchmark_readiness_20260723/external_plume_benchmark_readiness_report.json'
integrated_initial_acceptance_report='docs/codex_audit/evidence/engineering_h2_integrated_initial_acceptance_20260728/h2_integrated_initial_acceptance_report.json'
blocker_clearance_preflight_report='docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723/h2_blocker_clearance_preflight_report.json'
production_blocker_data_room_report='docs/codex_audit/evidence/engineering_h2_production_blocker_data_room_20260724/h2_production_blocker_data_room_report.json'
production_blocker_closure_manifest_report='docs/codex_audit/evidence/engineering_h2_production_blocker_closure_manifest_20260724/h2_production_blocker_closure_manifest_report.json'
external_evidence_intake_kit_report='docs/codex_audit/evidence/engineering_h2_external_evidence_intake_kit_20260724/h2_external_evidence_intake_kit_manifest.json'
external_artifact_operator_receipt_report='docs/codex_audit/evidence/engineering_h2_external_artifact_operator_receipt_20260724/h2_external_artifact_operator_receipt_report.json'
external_artifact_operator_receipt_gate_selftest_report='docs/codex_audit/evidence/engineering_h2_external_artifact_operator_receipt_gate_selftest_20260724/h2_external_artifact_operator_receipt_gate_selftest_report.json'
external_artifact_drop_validator_report='docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/h2_external_artifact_drop_validator_report.json'
external_artifact_ingestion_plan_report='docs/codex_audit/evidence/engineering_h2_external_artifact_ingestion_plan_20260724/h2_external_artifact_ingestion_plan.json'
external_artifact_controlled_copy_report='docs/codex_audit/evidence/engineering_h2_external_artifact_controlled_copy_20260724/h2_external_artifact_controlled_copy_report.json'
external_evidence_operations_dashboard_report='docs/codex_audit/evidence/engineering_h2_external_evidence_operations_dashboard_20260724/h2_external_evidence_operations_dashboard.json'
external_evidence_acceptance_worksheet_report='docs/codex_audit/evidence/engineering_h2_external_evidence_acceptance_worksheet_20260724/h2_external_evidence_acceptance_worksheet.json'
external_artifact_mapping_alias_report='docs/codex_audit/evidence/engineering_h2_external_artifact_mapping_alias_20260724/h2_external_artifact_mapping_alias_report.json'
external_evidence_case_validation_plan_report='docs/codex_audit/evidence/engineering_h2_external_evidence_case_validation_plan_20260724/h2_external_evidence_case_validation_plan.json'
case_validation_acceptance_contract_report='docs/codex_audit/evidence/engineering_h2_case_validation_acceptance_contract_20260724/h2_case_validation_acceptance_contract_report.json'
case_validation_acceptance_evaluation_report='docs/codex_audit/evidence/engineering_h2_case_validation_acceptance_evaluation_20260724/h2_case_validation_acceptance_evaluation_report.json'
case_validation_failure_attribution_report='docs/codex_audit/evidence/engineering_h2_case_validation_failure_attribution_20260724/h2_case_validation_failure_attribution_report.json'
case_validation_closure_matrix_report='docs/codex_audit/evidence/engineering_h2_case_validation_closure_matrix_20260724/h2_case_validation_closure_matrix_report.json'
external_artifact_unlock_forecast_report='docs/codex_audit/evidence/engineering_h2_external_artifact_unlock_forecast_20260724/h2_external_artifact_unlock_forecast_report.json'
external_evidence_case_validation_plan_selftest_report='docs/codex_audit/evidence/engineering_h2_external_evidence_case_validation_plan_selftest_20260724/h2_external_evidence_case_validation_plan_selftest_report.json'
case_validation_runner_ledger='docs/codex_audit/evidence/engineering_h2_case_validation_runner_ledger_20260724/h2_case_validation_runner_ledger.json'
case_validation_runner_ledger_selftest_report='docs/codex_audit/evidence/engineering_h2_case_validation_runner_ledger_selftest_20260724/h2_case_validation_runner_ledger_selftest_report.json'
case_validation_runner_preflight_report='docs/codex_audit/evidence/engineering_h2_case_validation_runner_preflight_20260724/h2_case_validation_runner_preflight_report.json'
case_validation_command_contract_report='docs/codex_audit/evidence/engineering_h2_case_validation_command_contract_20260724/h2_case_validation_command_contract_report.json'
case_validation_command_contract_selftest_report='docs/codex_audit/evidence/engineering_h2_case_validation_command_contract_selftest_20260724/h2_case_validation_command_contract_selftest_report.json'
external_artifact_gate_selftest_report='docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/h2_external_artifact_gate_selftest_report.json'
external_artifact_gate_negative_selftest_report='docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/h2_external_artifact_gate_negative_selftest_report.json'
external_artifact_strict_qa_negative_selftest_report='docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/h2_external_artifact_strict_qa_negative_selftest_report.json'
synthetic_selftest_isolation_guard_report='docs/codex_audit/evidence/engineering_h2_synthetic_selftest_isolation_guard_20260724/h2_synthetic_selftest_isolation_guard_report.json'
evidence_chain_rebuild_manifest_report='docs/codex_audit/evidence/engineering_h2_evidence_chain_rebuild_manifest_20260724/h2_evidence_chain_rebuild_manifest.json'
production_handoff_report='docs/codex_audit/evidence/engineering_h2_production_handoff_20260723/h2_production_handoff_report.json'
master_plan_traceability_report='docs/codex_audit/evidence/engineering_h2_master_plan_traceability_20260724/h2_master_plan_traceability_report.json'
quality_review_coverage_report='docs/codex_audit/evidence/engineering_h2_quality_review_coverage_20260724/h2_quality_review_coverage_report.json'
academic_gas_cantera_ignition_reference_report='docs/codex_audit/evidence/academic_gas_cantera_ignition_reference_20260724/cantera_ignition_reference_report.json'
academic_gas_cantera_mechanism_comparison_report='docs/codex_audit/evidence/academic_gas_cantera_mechanism_comparison_20260728/cantera_mechanism_comparison_report.json'
academic_gas_pelephysics_rate_kernel_equivalence_report='docs/codex_audit/evidence/academic_gas_pelephysics_rate_kernel_equivalence_20260728/pelephysics_rate_kernel_equivalence_report.json'
academic_gas_2d_detonation_reference_report='docs/codex_audit/evidence/academic_gas_2d_detonation_reference_20260728/academic_gas_2d_detonation_reference_report.json'
academic_gas_3d_detonation_reference_report='docs/codex_audit/evidence/academic_gas_3d_detonation_reference_20260728/academic_gas_3d_detonation_reference_report.json'
academic_gas_detonation_front_amr_validation_report='docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/academic_gas_detonation_front_amr_validation_report.json'
academic_gas_detonation_readiness_report='docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724/academic_gas_detonation_readiness_report.json'
academic_weno5_convergence_validation_report='docs/codex_audit/evidence/academic_weno5_convergence_validation_20260729/academic_weno5_convergence_validation_report.json'
academic_twophase_rayleigh_taylor_validation_report='docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/academic_twophase_rayleigh_taylor_validation_report.json'
academic_twophase_interface_amr_validation_report='docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/academic_twophase_interface_amr_validation_report.json'
academic_droplet_euler_lagrange_validation_report='docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/academic_droplet_euler_lagrange_validation_report.json'
academic_spray_detonation_validation_report='docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/academic_spray_detonation_validation_report.json'
academic_droplet_spray_budget_preflight_report='docs/codex_audit/evidence/academic_droplet_spray_budget_preflight_20260729/academic_droplet_spray_budget_preflight_report.json'
academic_spray_closed_particle_budget_report='docs/codex_audit/evidence/academic_spray_closed_particle_budget_20260729/academic_spray_closed_particle_budget_report.json'
academic_gpu_environment_preflight_report='docs/codex_audit/evidence/academic_gpu_environment_preflight_20260728/academic_gpu_environment_preflight_report.json'
academic_gas_double_mach_validation_report='docs/codex_audit/evidence/academic_gas_double_mach_validation_20260728/academic_gas_double_mach_validation_report.json'
academic_twophase_bubble_rise_validation_report='docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/academic_twophase_bubble_rise_validation_report.json'
academic_mms_shim_validation_report='docs/codex_audit/evidence/academic_mms_shim_validation_20260728/academic_mms_shim_validation_report.json'
academic_mms_nonconstant_density_shim_validation_report='docs/codex_audit/evidence/academic_mms_nonconstant_density_shim_validation_20260729/academic_mms_nonconstant_density_shim_validation_report.json'
bfs_kepsilon_reference_report='docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.json'

production_reports=(
  'docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/production_scale_scout_report.json'
  'docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/long_stability_scout_report.json'
  'docs/codex_audit/evidence/engineering_h2_production_mesh_scout_20260720/production_mesh_scout_report.json'
  'docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/production_mesh_8rank_scout_report.json'
  'docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/production_mesh_16rank_scout_report.json'
  'docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/production_mesh_600step_stability_scout_report.json'
  'docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/production_mesh_1200step_stability_scout_report.json'
  'docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_600step_stability_scout_20260720/production_mesh_8rank_600step_stability_scout_report.json'
)

verify_existing 'release evidence pack manifest' "$release_pack"
verify_existing 'engineering H2 acceptance matrix' "$acceptance_matrix"
verify_existing 'engineering production scorecard' "$scorecard"
verify_existing 'engineering production scorecard with integrated initial acceptance' "$integrated_initial_acceptance_scorecard"
if [[ "$skip_report" != TRUE ]]; then
  verify_existing 'engineering H2 production evidence verification report' "$production_evidence_verification_report"
fi
verify_existing 'runtime affinity manifest' "$runtime_affinity"
verify_existing 'hybrid runtime affinity manifest' "$hybrid_runtime_affinity"
verify_existing 'scheduler run report' "$scheduler_report"
verify_existing 'ignition consequence report' "$ignition_report"
verify_existing 'fire consequence metrics report' "$fire_report"
verify_existing 'engineering H2 fire calibration public-source triage report' "$fire_calibration_public_source_triage_report"
verify_existing 'engineering H2 fire calibration dataset ingestion report' "$fire_calibration_dataset_ingestion_report"
verify_existing 'engineering H2 fire calibration dataset ingestion selftest report' "$fire_calibration_dataset_ingestion_selftest_report"
verify_existing 'engineering H2 fire calibration digitization preflight report' "$fire_calibration_digitization_preflight_report"
verify_existing 'engineering H2 fire calibration literature metric preflight report' "$fire_calibration_literature_metric_preflight_report"
verify_existing 'engineering H2 fire calibration package report' "$fire_calibration_package_report"
verify_existing 'engineering H2 fire calibration dataset builder report' "$fire_calibration_dataset_report"
verify_existing 'engineering H2 real-CAD cleanup package report' "$real_cad_cleanup_package_report"
verify_existing 'engineering H2 real-CAD intake preflight report' "$real_cad_intake_preflight_report"
verify_existing 'engineering H2 real-CAD boundary tag contract report' "$real_cad_boundary_tag_contract_report"
verify_existing 'engineering H2 MPI scaling report' "$mpi_scaling_report"
verify_existing 'engineering H2 hybrid CFD scout report' "$hybrid_cfd_scout_report"
verify_existing 'engineering H2 hybrid production-mesh scout report' "$hybrid_production_mesh_scout_report"
verify_existing 'engineering H2 hybrid production-mesh 8-rank scout report' "$hybrid_production_mesh_8rank_scout_report"
verify_existing 'engineering H2 hybrid production-mesh 8-rank 600-step stability scout report' "$hybrid_production_mesh_8rank_600step_stability_scout_report"
verify_existing 'engineering H2 hybrid production-mesh 600-step stability scout report' "$hybrid_production_mesh_600step_stability_scout_report"
verify_existing 'engineering H2 hybrid large-grid 8-rank 120-step scout report' "$hybrid_largegrid_8rank_120step_scout_report"
verify_existing 'engineering H2 reference agreement report' "$reference_agreement_report"
verify_existing 'engineering H2 plume observation report' "$h2_plume_observation_report"
verify_existing 'engineering H2 external plume benchmark spec report' "$external_plume_benchmark_spec_report"
verify_existing 'engineering H2 external plume public-source triage report' "$external_plume_public_source_triage_report"
verify_existing 'engineering H2 SBEPV5 D27 dataset ingestion report' "$sbepv5_dataset_ingestion_report"
verify_existing 'engineering H2 SBEPV5 D27 dataset ingestion selftest report' "$sbepv5_dataset_ingestion_selftest_report"
verify_existing 'engineering H2 SBEPV5 D27 digitization preflight report' "$sbepv5_digitization_preflight_report"
verify_existing 'engineering H2 SBEPV5 D27 literature metric preflight report' "$sbepv5_literature_metric_preflight_report"
verify_existing 'engineering H2 SBEPV5 D27 case package report' "$sbepv5_case_package_report"
verify_existing 'engineering H2 SBEPV5 D27 case package preflight report' "$sbepv5_case_package_preflight_report"
verify_existing 'engineering H2 SBEPV5 D27 external dataset report' "$sbepv5_external_dataset_report"
verify_existing 'engineering H2 SBEPV5 D27 program scout report' "$sbepv5_d27_program_scout_report"
verify_existing 'engineering H2 external plume benchmark readiness report' "$external_plume_benchmark_readiness_report"
verify_existing 'engineering H2 integrated initial acceptance report' "$integrated_initial_acceptance_report"
verify_existing 'engineering H2 blocker clearance preflight report' "$blocker_clearance_preflight_report"
verify_existing 'engineering H2 production blocker data-room report' "$production_blocker_data_room_report"
verify_existing 'engineering H2 production blocker closure manifest report' "$production_blocker_closure_manifest_report"
verify_existing 'engineering H2 external evidence intake kit manifest' "$external_evidence_intake_kit_report"
verify_existing 'engineering H2 external artifact operator receipt report' "$external_artifact_operator_receipt_report"
verify_existing 'engineering H2 external artifact operator receipt gate selftest report' "$external_artifact_operator_receipt_gate_selftest_report"
verify_existing 'engineering H2 external artifact drop validator report' "$external_artifact_drop_validator_report"
verify_existing 'engineering H2 external artifact ingestion plan report' "$external_artifact_ingestion_plan_report"
verify_existing 'engineering H2 external artifact controlled-copy report' "$external_artifact_controlled_copy_report"
verify_existing 'engineering H2 external evidence operations dashboard report' "$external_evidence_operations_dashboard_report"
verify_existing 'engineering H2 external evidence acceptance worksheet report' "$external_evidence_acceptance_worksheet_report"
verify_existing 'engineering H2 external artifact mapping alias report' "$external_artifact_mapping_alias_report"
verify_existing 'engineering H2 external evidence case validation plan report' "$external_evidence_case_validation_plan_report"
verify_existing 'engineering H2 case validation acceptance contract report' "$case_validation_acceptance_contract_report"
verify_existing 'engineering H2 case validation acceptance evaluation report' "$case_validation_acceptance_evaluation_report"
verify_existing 'engineering H2 case validation failure attribution report' "$case_validation_failure_attribution_report"
verify_existing 'engineering H2 case validation closure matrix report' "$case_validation_closure_matrix_report"
verify_existing 'engineering H2 external artifact unlock forecast report' "$external_artifact_unlock_forecast_report"
verify_existing 'engineering H2 external evidence case validation plan selftest report' "$external_evidence_case_validation_plan_selftest_report"
verify_existing 'engineering H2 case validation runner ledger' "$case_validation_runner_ledger"
verify_existing 'engineering H2 case validation runner ledger selftest report' "$case_validation_runner_ledger_selftest_report"
verify_existing 'engineering H2 case validation runner preflight report' "$case_validation_runner_preflight_report"
verify_existing 'engineering H2 case validation command contract report' "$case_validation_command_contract_report"
verify_existing 'engineering H2 case validation command contract selftest report' "$case_validation_command_contract_selftest_report"
verify_existing 'engineering H2 external artifact gate selftest report' "$external_artifact_gate_selftest_report"
verify_existing 'engineering H2 external artifact gate negative selftest report' "$external_artifact_gate_negative_selftest_report"
verify_existing 'engineering H2 external artifact strict QA negative selftest report' "$external_artifact_strict_qa_negative_selftest_report"
verify_existing 'engineering H2 synthetic selftest isolation guard report' "$synthetic_selftest_isolation_guard_report"
if [[ "$skip_rebuild_manifest" != TRUE ]]; then
  verify_existing 'engineering H2 evidence-chain rebuild manifest' "$evidence_chain_rebuild_manifest_report"
fi
if [[ "$skip_report" != TRUE ]]; then
  verify_existing 'engineering H2 production handoff report' "$production_handoff_report"
  verify_existing 'engineering H2 master plan traceability report' "$master_plan_traceability_report"
  verify_existing 'engineering H2 quality review coverage report' "$quality_review_coverage_report"
fi
verify_existing 'academic gas Cantera ignition reference report' "$academic_gas_cantera_ignition_reference_report"
verify_existing 'academic gas Cantera mechanism comparison report' "$academic_gas_cantera_mechanism_comparison_report"
verify_existing 'academic gas PelePhysics rate-kernel equivalence report' "$academic_gas_pelephysics_rate_kernel_equivalence_report"
verify_existing 'academic gas 2D detonation reference report' "$academic_gas_2d_detonation_reference_report"
verify_existing 'academic gas 3D detonation reference report' "$academic_gas_3d_detonation_reference_report"
verify_existing 'academic gas detonation-front AMR validation report' "$academic_gas_detonation_front_amr_validation_report"
verify_existing 'academic gas detonation readiness report' "$academic_gas_detonation_readiness_report"
verify_existing 'academic WENO5 convergence validation report' "$academic_weno5_convergence_validation_report"
verify_existing 'academic two-phase Rayleigh-Taylor validation report' "$academic_twophase_rayleigh_taylor_validation_report"
verify_existing 'academic two-phase interface AMR validation report' "$academic_twophase_interface_amr_validation_report"
verify_existing 'academic droplet Euler-Lagrange validation report' "$academic_droplet_euler_lagrange_validation_report"
verify_existing 'academic spray detonation validation report' "$academic_spray_detonation_validation_report"
verify_existing 'academic droplet/spray budget preflight report' "$academic_droplet_spray_budget_preflight_report"
verify_existing 'academic spray closed particle budget report' "$academic_spray_closed_particle_budget_report"
verify_existing 'academic GPU environment preflight report' "$academic_gpu_environment_preflight_report"
verify_existing 'academic gas Double-Mach validation report' "$academic_gas_double_mach_validation_report"
verify_existing 'academic two-phase bubble-rise validation report' "$academic_twophase_bubble_rise_validation_report"
verify_existing 'academic MMS nonconstant-density shim validation report' "$academic_mms_nonconstant_density_shim_validation_report"
verify_existing 'engineering BFS k-epsilon reference report' "$bfs_kepsilon_reference_report"
for report in "${production_reports[@]}"; do
  verify_existing 'production scout report' "$report"
done

run verify_mpi_link_shim
run python3 tools/package_engineering_h2_release_evidence.py verify --pack-manifest "$release_pack"
run python3 tools/write_engineering_h2_acceptance_matrix.py --verify-json "$acceptance_matrix"
run python3 tools/write_engineering_production_scorecard.py --verify-json "$scorecard"
run python3 tools/write_engineering_production_scorecard.py --verify-json "$integrated_initial_acceptance_scorecard"
if [[ "$skip_report" == TRUE ]]; then
  printf '[engineering-h2-verify] skipping production evidence verification report because CODEX_ENGINEERING_H2_VERIFY_SKIP_REPORT=TRUE\n'
else
  run python3 tools/write_engineering_h2_production_evidence_verification_report.py --verify-json "$production_evidence_verification_report"
fi
run python3 tools/write_engineering_runtime_affinity_manifest.py --verify-json "$runtime_affinity"
run python3 tools/write_engineering_runtime_affinity_manifest.py --verify-json "$hybrid_runtime_affinity"
run python3 tools/verify_engineering_scheduler_run.py --verify-json "$scheduler_report"
run python3 tools/write_engineering_h2_ignition_consequence_report.py --verify-json "$ignition_report"
run python3 tools/write_engineering_h2_fire_consequence_metrics_report.py --verify-json "$fire_report"
run python3 tools/write_engineering_h2_fire_calibration_public_source_triage_report.py --verify-json "$fire_calibration_public_source_triage_report"
run python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py --verify-json "$fire_calibration_dataset_ingestion_report"
run python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_selftest_report.py --verify-json "$fire_calibration_dataset_ingestion_selftest_report"
run python3 tools/write_engineering_h2_fire_calibration_digitization_preflight_report.py --verify-json "$fire_calibration_digitization_preflight_report"
run python3 tools/write_engineering_h2_fire_calibration_literature_metric_preflight_report.py --verify-json "$fire_calibration_literature_metric_preflight_report"
run python3 tools/write_engineering_h2_fire_calibration_package_report.py --verify-json "$fire_calibration_package_report"
run python3 tools/write_engineering_h2_fire_calibration_dataset_report.py --verify-json "$fire_calibration_dataset_report"
run python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py --verify-json "$real_cad_cleanup_package_report"
run python3 tools/write_engineering_h2_real_cad_intake_preflight_report.py --verify-json "$real_cad_intake_preflight_report"
run python3 tools/write_engineering_h2_real_cad_boundary_tag_contract_report.py --verify-json "$real_cad_boundary_tag_contract_report"
run python3 tools/write_engineering_h2_mpi_scaling_report.py --verify-json "$mpi_scaling_report"
run python3 tools/write_engineering_h2_hybrid_cfd_scout_report.py --verify-json "$hybrid_cfd_scout_report"
run python3 tools/write_engineering_h2_hybrid_cfd_scout_report.py --verify-json "$hybrid_production_mesh_scout_report"
run python3 tools/write_engineering_h2_hybrid_cfd_scout_report.py --verify-json "$hybrid_production_mesh_8rank_scout_report"
run python3 tools/write_engineering_h2_hybrid_cfd_scout_report.py --verify-json "$hybrid_production_mesh_8rank_600step_stability_scout_report"
run python3 tools/write_engineering_h2_hybrid_cfd_scout_report.py --verify-json "$hybrid_production_mesh_600step_stability_scout_report"
run python3 tools/write_engineering_h2_hybrid_cfd_scout_report.py --verify-json "$hybrid_largegrid_8rank_120step_scout_report" --min-ranks 8 --min-threads 2 --min-max-step 120 --min-plotfiles 5 --max-cloud-rel-diff 0.20 --max-peak-rel-diff 0.20 --max-centroid-abs-diff 0.02 --max-downstream-abs-diff 0.02 --max-advance-seconds-ratio 4.0
run python3 tools/write_engineering_h2_reference_agreement_report.py --verify-json "$reference_agreement_report"
run python3 tools/write_engineering_h2_plume_observation_report.py --verify-json "$h2_plume_observation_report"
run python3 tools/write_engineering_h2_external_plume_benchmark_spec.py --verify-json "$external_plume_benchmark_spec_report"
run python3 tools/write_engineering_h2_external_plume_public_source_triage_report.py --verify-json "$external_plume_public_source_triage_report"
run python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py --verify-json "$sbepv5_dataset_ingestion_report"
run python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_selftest_report.py --verify-json "$sbepv5_dataset_ingestion_selftest_report"
run python3 tools/write_engineering_h2_sbepv5_digitization_preflight_report.py --verify-json "$sbepv5_digitization_preflight_report"
run python3 tools/write_engineering_h2_sbepv5_literature_metric_preflight_report.py --verify-json "$sbepv5_literature_metric_preflight_report"
run python3 tools/write_engineering_h2_sbepv5_case_package_report.py --verify-json "$sbepv5_case_package_report"
run python3 tools/write_engineering_h2_sbepv5_case_package_preflight_report.py --verify-json "$sbepv5_case_package_preflight_report"
run python3 tools/write_engineering_h2_sbepv5_external_dataset_report.py --verify-json "$sbepv5_external_dataset_report"
run python3 tools/write_engineering_h2_sbepv5_d27_scout_run_report.py --verify-json "$sbepv5_d27_program_scout_report"
run python3 tools/write_engineering_h2_external_plume_benchmark_readiness.py --verify-json "$external_plume_benchmark_readiness_report"
run python3 tools/write_engineering_h2_integrated_initial_acceptance_report.py --verify-json "$integrated_initial_acceptance_report"
run python3 tools/write_engineering_h2_blocker_clearance_preflight_report.py --verify-json "$blocker_clearance_preflight_report"
run python3 tools/write_engineering_h2_production_blocker_data_room_report.py --verify-json "$production_blocker_data_room_report"
run python3 tools/write_engineering_h2_production_blocker_closure_manifest_report.py --verify-json "$production_blocker_closure_manifest_report"
run python3 tools/write_engineering_h2_external_evidence_intake_kit_manifest.py --verify-json "$external_evidence_intake_kit_report"
run python3 tools/write_engineering_h2_external_artifact_operator_receipt_report.py --verify-json "$external_artifact_operator_receipt_report"
run python3 tools/write_engineering_h2_external_artifact_operator_receipt_gate_selftest_report.py --verify-json "$external_artifact_operator_receipt_gate_selftest_report"
run python3 tools/write_engineering_h2_external_artifact_drop_validator.py --verify-json "$external_artifact_drop_validator_report"
run python3 tools/write_engineering_h2_external_artifact_ingestion_plan.py --verify-json "$external_artifact_ingestion_plan_report"
run python3 tools/write_engineering_h2_external_artifact_controlled_copy_report.py --verify-json "$external_artifact_controlled_copy_report"
run python3 tools/write_engineering_h2_external_evidence_operations_dashboard.py --verify-json "$external_evidence_operations_dashboard_report"
run python3 tools/write_engineering_h2_external_evidence_acceptance_worksheet.py --verify-json "$external_evidence_acceptance_worksheet_report"
run python3 tools/write_engineering_h2_external_artifact_mapping_alias_report.py --verify-json "$external_artifact_mapping_alias_report"
run python3 tools/write_engineering_h2_external_evidence_case_validation_plan.py --verify-json "$external_evidence_case_validation_plan_report"
run python3 tools/write_engineering_h2_case_validation_acceptance_contract_report.py --verify-json "$case_validation_acceptance_contract_report"
run python3 tools/write_engineering_h2_case_validation_acceptance_evaluation_report.py --verify-json "$case_validation_acceptance_evaluation_report"
run python3 tools/write_engineering_h2_case_validation_failure_attribution_report.py --verify-json "$case_validation_failure_attribution_report"
run python3 tools/write_engineering_h2_case_validation_closure_matrix_report.py --verify-json "$case_validation_closure_matrix_report"
run python3 tools/write_engineering_h2_external_artifact_unlock_forecast_report.py --verify-json "$external_artifact_unlock_forecast_report"
run python3 tools/write_engineering_h2_external_evidence_case_validation_plan_selftest_report.py --verify-json "$external_evidence_case_validation_plan_selftest_report"
run python3 tools/run_engineering_h2_external_evidence_case_validation_campaigns.py --verify-ledger "$case_validation_runner_ledger"
run python3 tools/write_engineering_h2_case_validation_runner_ledger_selftest_report.py --verify-json "$case_validation_runner_ledger_selftest_report"
run python3 tools/write_engineering_h2_case_validation_runner_preflight_report.py --verify-json "$case_validation_runner_preflight_report"
run python3 tools/write_engineering_h2_case_validation_command_contract_report.py --verify-json "$case_validation_command_contract_report"
run python3 tools/write_engineering_h2_case_validation_command_contract_selftest_report.py --verify-json "$case_validation_command_contract_selftest_report"
run python3 tools/write_engineering_h2_external_artifact_gate_selftest_report.py --verify-json "$external_artifact_gate_selftest_report"
run python3 tools/write_engineering_h2_external_artifact_gate_negative_selftest_report.py --verify-json "$external_artifact_gate_negative_selftest_report"
run python3 tools/write_engineering_h2_external_artifact_strict_qa_negative_selftest_report.py --verify-json "$external_artifact_strict_qa_negative_selftest_report"
run python3 tools/write_engineering_h2_synthetic_selftest_isolation_guard_report.py --verify-json "$synthetic_selftest_isolation_guard_report"
if [[ "$skip_rebuild_manifest" == TRUE ]]; then
  printf '[engineering-h2-verify] skipping evidence-chain rebuild manifest because CODEX_ENGINEERING_H2_VERIFY_SKIP_REBUILD_MANIFEST=TRUE\n'
else
  run python3 tools/write_engineering_h2_evidence_chain_rebuild_manifest.py --verify-json "$evidence_chain_rebuild_manifest_report"
fi
if [[ "$skip_report" == TRUE ]]; then
  printf '[engineering-h2-verify] skipping terminal production summary reports because CODEX_ENGINEERING_H2_VERIFY_SKIP_REPORT=TRUE\n'
else
  run python3 tools/write_engineering_h2_production_handoff_report.py --verify-json "$production_handoff_report"
  run python3 tools/write_engineering_h2_master_plan_traceability_report.py --verify-json "$master_plan_traceability_report"
  run python3 tools/write_engineering_h2_quality_review_coverage_report.py --verify-json "$quality_review_coverage_report"
fi
run python3 tools/write_academic_gas_cantera_ignition_reference_report.py --verify-json "$academic_gas_cantera_ignition_reference_report"
run python3 tools/write_academic_gas_cantera_mechanism_comparison_report.py --verify-json "$academic_gas_cantera_mechanism_comparison_report"
run python3 tools/write_academic_gas_pelephysics_rate_kernel_equivalence_report.py --verify-json "$academic_gas_pelephysics_rate_kernel_equivalence_report"
run python3 tools/write_academic_gas_2d_detonation_reference_report.py --verify-json "$academic_gas_2d_detonation_reference_report"
run python3 tools/write_academic_gas_3d_detonation_reference_report.py --verify-json "$academic_gas_3d_detonation_reference_report"
run python3 tools/write_academic_gas_detonation_front_amr_validation_report.py --verify-json "$academic_gas_detonation_front_amr_validation_report"
run python3 tools/write_academic_gas_detonation_readiness_report.py --verify-json "$academic_gas_detonation_readiness_report"
run python3 tools/write_academic_weno5_convergence_validation_report.py --verify-json "$academic_weno5_convergence_validation_report"
run python3 tools/write_academic_twophase_rayleigh_taylor_validation_report.py --verify-json "$academic_twophase_rayleigh_taylor_validation_report"
run python3 tools/write_academic_twophase_interface_amr_validation_report.py --verify-json "$academic_twophase_interface_amr_validation_report"
run python3 tools/write_academic_droplet_euler_lagrange_validation_report.py --verify-json "$academic_droplet_euler_lagrange_validation_report"
run python3 tools/write_academic_spray_detonation_validation_report.py --verify-json "$academic_spray_detonation_validation_report"
run python3 tools/write_academic_droplet_spray_budget_preflight_report.py --verify-json "$academic_droplet_spray_budget_preflight_report"
run python3 tools/write_academic_spray_closed_particle_budget_report.py --verify-json "$academic_spray_closed_particle_budget_report"
run python3 tools/write_academic_gpu_environment_preflight_report.py --verify-json "$academic_gpu_environment_preflight_report"
run python3 tools/write_academic_gas_double_mach_validation_report.py --verify-json "$academic_gas_double_mach_validation_report"
run python3 tools/write_academic_twophase_bubble_rise_validation_report.py --verify-json "$academic_twophase_bubble_rise_validation_report"
run python3 tools/write_academic_mms_shim_validation_report.py --verify-json "$academic_mms_shim_validation_report"
run python3 tools/write_academic_mms_nonconstant_density_shim_validation_report.py --verify-json "$academic_mms_nonconstant_density_shim_validation_report"
run python3 tools/write_engineering_bfs_kepsilon_reference_report.py --verify-json "$bfs_kepsilon_reference_report"

for report in "${production_reports[@]}"; do
  run python3 tools/write_engineering_h2_production_scale_scout_report.py --verify-json "$report"
done

run python3 tools/check_machine_local_paths.py --strict

if [[ "$skip_ctest" == TRUE ]]; then
  printf '[engineering-h2-verify] skipping CTest because CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE\n'
else
  if [[ ! -d "$ctest_dir" ]]; then
    printf '[engineering-h2-verify] FAIL missing CTest build directory: %s\n' "$ctest_dir" >&2
    exit 1
  fi
  run ctest --test-dir "$ctest_dir" --output-on-failure
fi

printf '[engineering-h2-verify] PASS engineering H2 production evidence verification\n'
