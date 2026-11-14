#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

outdir=${CODEX_MASTER_PLAN_CURRENT_SCOPE_VERIFY_DIR:-docs/codex_audit/evidence/master_plan_current_scope_verification_20260731}
logdir="$outdir/logs"
mkdir -p "$logdir"

run_gate() {
  local name=$1
  shift
  echo "[master-current-scope] START $name"
  set +e
  "$@" >"$logdir/${name}.log" 2>&1
  local rc=$?
  set -e
  echo "$rc" >"$logdir/${name}.exitcode"
  if [ "$rc" -eq 0 ]; then
    echo "[master-current-scope] PASS  $name"
  else
    echo "[master-current-scope] FAIL  $name rc=$rc"
    tail -n 80 "$logdir/${name}.log" || true
    return "$rc"
  fi
}

overall_rc=0

export CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST="${CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST:-TRUE}"

run_gate engineering_h2_production_evidence bash tools/verify_engineering_h2_production_evidence.sh || overall_rc=$?
run_gate academic_evidence bash tools/verify_academic_evidence.sh || overall_rc=$?
run_gate academic_current_priority_scope bash tools/verify_academic_current_priority_scope.sh || overall_rc=$?
run_gate strict_external_source_update bash tools/verify_master_plan_strict_external_source_update.sh || overall_rc=$?
run_gate strict_real_cad_update bash tools/verify_master_plan_strict_real_cad_update.sh || overall_rc=$?
run_gate strict_fire_calibration_update bash tools/verify_master_plan_strict_fire_calibration_update.sh || overall_rc=$?
run_gate strict_blocker_matrix bash tools/verify_master_plan_strict_blocker_matrix.sh || overall_rc=$?
run_gate strict_artifact_intake_manifest bash tools/verify_master_plan_strict_artifact_intake_manifest.sh || overall_rc=$?
run_gate strict_artifact_drop_preflight bash tools/verify_master_plan_strict_artifact_drop_preflight.sh || overall_rc=$?
run_gate gpu_runtime_recovery bash tools/verify_master_plan_gpu_runtime_recovery.sh || overall_rc=$?
run_gate cuda_revalidation bash tools/verify_master_plan_cuda_revalidation.sh || overall_rc=$?
run_gate full_reproducibility bash tools/verify_master_plan_full_reproducibility.sh || overall_rc=$?
run_gate current_parallel_capability_matrix bash tools/verify_current_parallel_capability_matrix.sh || overall_rc=$?
run_gate current_scope_operator_runbook bash tools/verify_current_scope_operator_runbook.sh || overall_rc=$?
run_gate final_readiness bash tools/verify_master_plan_final_readiness.sh || overall_rc=$?

echo "$overall_rc" >"$outdir/master_plan_current_scope_verification.exitcode"
if [ "$overall_rc" -eq 0 ]; then
  echo "[master-current-scope] PASS all current-scope verification gates"
else
  echo "[master-current-scope] FAIL current-scope verification rc=$overall_rc"
fi
exit "$overall_rc"
