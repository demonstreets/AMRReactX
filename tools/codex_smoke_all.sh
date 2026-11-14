#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir=${CODEX_SMOKE_LOG_DIR:-/tmp/codex_smoke_all_$(date -u +%Y%m%dT%H%M%SZ)}
mkdir -p "$log_dir"

echo "[codex-smoke-all] logs: $log_dir"
export CODEX_SMOKE_STEP_LOG_DIR="$log_dir"

run_step() {
  local name=$1
  shift
  echo "[codex-smoke-all] START $name"
  (cd "$repo_root" && "$@") >"$log_dir/${name}.log" 2>&1
  echo "[codex-smoke-all] PASS  $name"
}

run_step gpu_source_audit_rules bash tools/test_gpu_source_audit_rules.sh
run_step gpu_source_audit python3 tools/check_gpu_source_audit.py
run_step gpu_source_audit_extended python3 tools/check_gpu_source_audit.py --profile extended
run_step cmake_weno bash -lc 'cmake -S . -B build-codex-smoke -DMYPELE_ENABLE_UNIT_SMOKE=ON && cmake --build build-codex-smoke -j "${JOBS:-4}" && ctest --test-dir build-codex-smoke --output-on-failure'
run_step engineering_pelelmex bash -lc 'JOBS="${JOBS:-4}" RUN_TIMEOUT="${RUN_TIMEOUT:-120}" tools/codex_smoke_engineering_pelelmex.sh'
run_step engineering_yaml_pelelmex bash -lc 'JOBS="${JOBS:-4}" RUN_TIMEOUT="${RUN_TIMEOUT:-120}" CODEX_GENERATED_INPUT="$CODEX_SMOKE_STEP_LOG_DIR/bfs_from_yaml.inputs" CODEX_RUN_LOG="$CODEX_SMOKE_STEP_LOG_DIR/bfs_from_yaml.run.log" tools/codex_smoke_engineering_pelelmex_yaml.sh'
run_step engineering_h2_ignition_plotfile bash -lc 'JOBS="${JOBS:-4}" RUN_TIMEOUT="${RUN_TIMEOUT:-180}" CODEX_H2_IGNITION_LOG_DIR="$CODEX_SMOKE_STEP_LOG_DIR/engineering_h2_ignition_plotfile" tools/codex_smoke_engineering_h2_ignition_plotfile.sh'
run_step engineering_h2_ignition_history bash -lc 'JOBS="${JOBS:-4}" RUN_TIMEOUT="${RUN_TIMEOUT:-180}" CODEX_H2_IGNITION_HISTORY_LOG_DIR="$CODEX_SMOKE_STEP_LOG_DIR/engineering_h2_ignition_history" tools/codex_smoke_engineering_h2_ignition_history.sh'
run_step engineering_h2_ignition_sdc_compare bash -lc 'JOBS="${JOBS:-4}" RUN_TIMEOUT="${RUN_TIMEOUT:-180}" CODEX_H2_IGNITION_SDC_LOG_DIR="$CODEX_SMOKE_STEP_LOG_DIR/engineering_h2_ignition_sdc_compare" tools/codex_smoke_engineering_h2_ignition_sdc_compare.sh'
run_step engineering_h2_ignition_delay bash -lc 'JOBS="${JOBS:-4}" RUN_TIMEOUT="${RUN_TIMEOUT:-180}" CODEX_H2_IGNITION_DELAY_LOG_DIR="$CODEX_SMOKE_STEP_LOG_DIR/engineering_h2_ignition_delay" tools/codex_smoke_engineering_h2_ignition_delay.sh'
run_step academic_pelec bash -lc 'JOBS="${JOBS:-4}" RUN_TIMEOUT="${RUN_TIMEOUT:-120}" tools/codex_smoke_academic_pelec.sh'
run_step academic_detonation_wave bash -lc 'JOBS="${JOBS:-4}" RUN_TIMEOUT="${RUN_TIMEOUT:-180}" CODEX_DETONATION_LOG_DIR="$CODEX_SMOKE_STEP_LOG_DIR/academic_detonation_wave" tools/codex_smoke_academic_detonation_wave.sh'
run_step academic_double_mach bash -lc 'JOBS="${JOBS:-4}" RUN_TIMEOUT="${RUN_TIMEOUT:-180}" CODEX_DOUBLE_MACH_LOG_DIR="$CODEX_SMOKE_STEP_LOG_DIR/academic_double_mach" tools/codex_smoke_academic_double_mach.sh'
run_step academic_rayleigh_taylor bash -lc 'JOBS="${JOBS:-4}" RUN_TIMEOUT="${RUN_TIMEOUT:-180}" CODEX_RAYLEIGH_TAYLOR_LOG_DIR="$CODEX_SMOKE_STEP_LOG_DIR/academic_rayleigh_taylor" tools/codex_smoke_academic_rayleigh_taylor.sh'
run_step academic_rayleigh_taylor_growth bash -lc 'JOBS="${JOBS:-4}" RUN_TIMEOUT="${RUN_TIMEOUT:-300}" CODEX_RAYLEIGH_TAYLOR_GROWTH_LOG_DIR="$CODEX_SMOKE_STEP_LOG_DIR/academic_rayleigh_taylor_growth" tools/codex_smoke_academic_rayleigh_taylor_growth.sh'
run_step academic_rayleigh_taylor_low_pressure bash -lc 'JOBS="${JOBS:-4}" RUN_TIMEOUT="${RUN_TIMEOUT:-180}" CODEX_RAYLEIGH_TAYLOR_LOW_PRESSURE_LOG_DIR="$CODEX_SMOKE_STEP_LOG_DIR/academic_rayleigh_taylor_low_pressure" tools/codex_smoke_academic_rayleigh_taylor_low_pressure.sh'
run_step academic_pelec_plan_amr bash -lc 'JOBS="${JOBS:-4}" RUN_TIMEOUT="${RUN_TIMEOUT:-180}" CODEX_PELEC_PLAN_AMR_LOG_DIR="$CODEX_SMOKE_STEP_LOG_DIR/academic_pelec_plan_amr" tools/codex_smoke_academic_pelec_plan_amr.sh'
run_step academic_sod_plotfile bash -lc 'RUN_TIMEOUT="${RUN_TIMEOUT:-120}" CODEX_SOD_LOG_DIR="$CODEX_SMOKE_STEP_LOG_DIR/academic_sod_plotfile" tools/codex_smoke_academic_sod_plotfile.sh'

echo "[codex-smoke-all] all smoke checks passed"
