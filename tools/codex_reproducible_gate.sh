#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir=${CODEX_REPRO_LOG_DIR:-/tmp/codex_reproducible_gate_$(date -u +%Y%m%dT%H%M%SZ)}
require_cuda=${CODEX_REPRO_REQUIRE_CUDA:-0}
skip_smoke_all=${CODEX_REPRO_SKIP_SMOKE_ALL:-0}

mkdir -p "$log_dir"
export CODEX_REPRO_LOG_DIR="$log_dir"
cd "$repo_root"

echo "[codex-repro] logs: $log_dir"

run_step() {
  local name=$1
  shift
  echo "[codex-repro] START $name"
  "$@" >"$log_dir/${name}.log" 2>&1
  echo "[codex-repro] PASS  $name"
}

preflight_args=()
if [ "$require_cuda" = "1" ]; then
  preflight_args+=(--require-cuda)
fi

run_step preflight tools/codex_preflight_environment.sh "${preflight_args[@]}"
run_step release_provenance_strict python3 tools/check_release_provenance.py --strict

if [ "$skip_smoke_all" = "1" ]; then
  echo "[codex-repro] SKIP smoke_all because CODEX_REPRO_SKIP_SMOKE_ALL=1"
else
  run_step smoke_all bash -lc 'CODEX_SMOKE_LOG_DIR="$CODEX_REPRO_LOG_DIR/smoke_all" JOBS="${JOBS:-2}" RUN_TIMEOUT="${RUN_TIMEOUT:-180}" tools/codex_smoke_all.sh'
fi

if [ "$require_cuda" = "1" ]; then
  run_step pelec_cuda bash -lc 'CODEX_PELEC_CUDA_LOG_DIR="$CODEX_REPRO_LOG_DIR/pelec_cuda" JOBS="${JOBS:-2}" RUN_TIMEOUT="${RUN_TIMEOUT:-240}" tools/codex_smoke_academic_pelec_cuda.sh'
  run_step pelelmex_cuda bash -lc 'CODEX_PELELMEX_CUDA_LOG_DIR="$CODEX_REPRO_LOG_DIR/pelelmex_cuda" JOBS="${JOBS:-1}" RUN_TIMEOUT="${RUN_TIMEOUT:-240}" tools/codex_smoke_engineering_pelelmex_cuda.sh'
fi

echo "[codex-repro] all requested reproducibility checks passed"
