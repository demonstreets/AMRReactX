#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

run_full_verify=TRUE
skip_ctest=FALSE

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-full-verify)
      run_full_verify=FALSE
      shift
      ;;
    --skip-ctest)
      skip_ctest=TRUE
      shift
      ;;
    *)
      printf '[engineering-h2-rebuild] unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

run() {
  printf '[engineering-h2-rebuild] %s\n' "$*"
  "$@"
}

run_verify_to_log() {
  local log_path="$1"
  shift
  set +e
  "$@" 2>&1 | tee "$log_path"
  local rc=${PIPESTATUS[0]}
  set -e
  printf 'CODEX_VERIFY_RC:%s\n' "$rc" >> "$log_path"
  if [[ "$rc" -ne 0 ]]; then
    printf '[engineering-h2-rebuild] verifier failed rc=%s log=%s\n' "$rc" "$log_path" >&2
    return "$rc"
  fi
}

scorecard_json='docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json'
scorecard_md='docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.md'
integrated_scorecard_json='docs/codex_audit/evidence/engineering_production_scorecard_20260728_integrated_initial_acceptance/engineering_production_scorecard.json'
integrated_scorecard_md='docs/codex_audit/evidence/engineering_production_scorecard_20260728_integrated_initial_acceptance/engineering_production_scorecard.md'
evidence_verify_dir='docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720'
production_evidence_json="$evidence_verify_dir/production_evidence_verification_report.json"

mkdir -p "$evidence_verify_dir"

run python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py
run python3 tools/write_engineering_h2_real_cad_intake_preflight_report.py
run python3 tools/write_engineering_h2_real_cad_boundary_tag_contract_report.py

run python3 tools/write_engineering_h2_external_plume_public_source_triage_report.py
run python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py
run python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_selftest_report.py
run python3 tools/write_engineering_h2_sbepv5_digitization_preflight_report.py
run python3 tools/write_engineering_h2_sbepv5_literature_metric_preflight_report.py
run python3 tools/write_engineering_h2_sbepv5_external_dataset_report.py
run python3 tools/write_engineering_h2_sbepv5_case_package_report.py
run python3 tools/write_engineering_h2_sbepv5_case_package_preflight_report.py

run python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py
run python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_selftest_report.py
run python3 tools/write_engineering_h2_fire_calibration_digitization_preflight_report.py
run python3 tools/write_engineering_h2_fire_calibration_literature_metric_preflight_report.py
run python3 tools/write_engineering_h2_fire_calibration_package_report.py
run python3 tools/write_engineering_h2_fire_calibration_dataset_report.py

run python3 tools/write_engineering_h2_reference_agreement_report.py
run python3 tools/write_engineering_h2_external_plume_benchmark_readiness.py

run python3 tools/write_engineering_production_scorecard.py --output-json "$scorecard_json" --output-md "$scorecard_md"
run python3 tools/write_engineering_production_scorecard.py --output-json "$integrated_scorecard_json" --output-md "$integrated_scorecard_md"
run python3 tools/write_engineering_h2_blocker_clearance_preflight_report.py
run python3 tools/write_engineering_h2_production_blocker_data_room_report.py
run python3 tools/write_engineering_h2_production_blocker_closure_manifest_report.py
run python3 tools/write_engineering_h2_external_evidence_intake_kit_manifest.py
run python3 tools/write_engineering_h2_external_artifact_operator_receipt_report.py
run python3 tools/write_engineering_h2_external_artifact_operator_receipt_gate_selftest_report.py
run python3 tools/write_engineering_h2_external_artifact_drop_validator.py
run python3 tools/write_engineering_h2_external_artifact_ingestion_plan.py
run python3 tools/write_engineering_h2_external_artifact_controlled_copy_report.py
run python3 tools/write_engineering_h2_external_evidence_operations_dashboard.py
run python3 tools/write_engineering_h2_external_evidence_acceptance_worksheet.py
run python3 tools/write_engineering_h2_external_artifact_mapping_alias_report.py
run python3 tools/write_engineering_h2_external_evidence_case_validation_plan.py
run python3 tools/run_engineering_h2_external_evidence_case_validation_campaigns.py --ledger-json \
  docs/codex_audit/evidence/engineering_h2_case_validation_runner_ledger_20260724/h2_case_validation_runner_ledger.json \
  --ledger-md docs/codex_audit/evidence/engineering_h2_case_validation_runner_ledger_20260724/h2_case_validation_runner_ledger.md
run python3 tools/run_engineering_h2_external_evidence_case_validation_campaigns.py --verify-ledger \
  docs/codex_audit/evidence/engineering_h2_case_validation_runner_ledger_20260724/h2_case_validation_runner_ledger.json
run python3 tools/write_engineering_h2_case_validation_runner_ledger_selftest_report.py
run python3 tools/write_engineering_h2_case_validation_acceptance_contract_report.py
run python3 tools/write_engineering_h2_case_validation_acceptance_evaluation_report.py
run python3 tools/write_engineering_h2_case_validation_failure_attribution_report.py
run python3 tools/write_engineering_h2_case_validation_closure_matrix_report.py
run python3 tools/write_engineering_h2_external_artifact_unlock_forecast_report.py
run python3 tools/write_engineering_h2_external_evidence_case_validation_plan_selftest_report.py
run python3 tools/write_engineering_h2_case_validation_runner_preflight_report.py
run python3 tools/write_engineering_h2_case_validation_command_contract_report.py
run python3 tools/write_engineering_h2_case_validation_command_contract_selftest_report.py
run python3 tools/write_engineering_h2_external_artifact_gate_selftest_report.py
run python3 tools/write_engineering_h2_external_artifact_gate_negative_selftest_report.py
run python3 tools/write_engineering_h2_external_artifact_strict_qa_negative_selftest_report.py
run python3 tools/write_engineering_h2_synthetic_selftest_isolation_guard_report.py
run python3 tools/write_academic_droplet_spray_budget_preflight_report.py
run bash tools/codex_run_academic_spray_closed_particle_budget.sh
run python3 tools/write_academic_spray_closed_particle_budget_report.py

if [[ "$run_full_verify" != TRUE ]]; then
  printf '[engineering-h2-rebuild] PASS rebuild-only evidence chain\n'
  exit 0
fi

bootstrap_log="$evidence_verify_dir/full_verify_after_rebuild_bootstrap_20260724.log"
final_log="$evidence_verify_dir/full_verify_after_rebuild_final_20260724.log"
verify_env=(env CODEX_ENGINEERING_H2_VERIFY_SKIP_REPORT=TRUE)
final_verify_env=(env)
report_args=(--returncode 0)

if [[ "$skip_ctest" == TRUE ]]; then
  verify_env+=(CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE)
  final_verify_env+=(CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE)
  report_args+=(--no-require-ctest)
fi

verify_env+=(CODEX_ENGINEERING_H2_VERIFY_SKIP_REBUILD_MANIFEST=TRUE)

run_verify_to_log "$bootstrap_log" "${verify_env[@]}" bash tools/verify_engineering_h2_production_evidence.sh
run python3 tools/write_engineering_h2_evidence_chain_rebuild_manifest.py --bootstrap-log "$bootstrap_log"
run python3 tools/write_engineering_h2_production_evidence_verification_report.py \
  --log "$bootstrap_log" \
  "${report_args[@]}"

run python3 tools/write_engineering_h2_production_handoff_report.py
run python3 tools/write_engineering_h2_quality_review_coverage_report.py
run python3 tools/write_engineering_h2_master_plan_traceability_report.py

run_verify_to_log "$final_log" "${final_verify_env[@]}" bash tools/verify_engineering_h2_production_evidence.sh
run python3 tools/write_engineering_h2_production_evidence_verification_report.py \
  --log "$final_log" \
  "${report_args[@]}"
run python3 tools/write_engineering_h2_production_evidence_verification_report.py --verify-json "$production_evidence_json"
run python3 tools/write_engineering_h2_production_handoff_report.py
run python3 tools/write_engineering_h2_quality_review_coverage_report.py
run python3 tools/write_engineering_h2_master_plan_traceability_report.py
run python3 tools/write_engineering_h2_production_handoff_report.py --verify-json \
  docs/codex_audit/evidence/engineering_h2_production_handoff_20260723/h2_production_handoff_report.json
run python3 tools/write_engineering_h2_quality_review_coverage_report.py --verify-json \
  docs/codex_audit/evidence/engineering_h2_quality_review_coverage_20260724/h2_quality_review_coverage_report.json
run python3 tools/write_engineering_h2_master_plan_traceability_report.py --verify-json \
  docs/codex_audit/evidence/engineering_h2_master_plan_traceability_20260724/h2_master_plan_traceability_report.json

printf '[engineering-h2-rebuild] PASS full evidence rebuild and verification\n'
