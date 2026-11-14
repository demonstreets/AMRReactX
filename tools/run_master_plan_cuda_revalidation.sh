#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

outdir=${CODEX_MASTER_PLAN_CUDA_REVALIDATION_DIR:-docs/codex_audit/evidence/master_plan_cuda_revalidation_20260731}
logdir="$outdir/logs"
mkdir -p "$logdir"

: "${SUNDIALS_CUDA_DIR:=${SUNDIALS_DIR:-}}"
if [ -z "$SUNDIALS_CUDA_DIR" ]; then
  echo "[cuda-revalidation] set SUNDIALS_CUDA_DIR or SUNDIALS_DIR before running CUDA revalidation" >&2
  exit 2
fi
export SUNDIALS_CUDA_DIR
export SUNDIALS_DIR="${SUNDIALS_DIR:-$SUNDIALS_CUDA_DIR}"
export LD_LIBRARY_PATH="$SUNDIALS_CUDA_DIR/lib:${LD_LIBRARY_PATH:-}"
export JOBS="${JOBS:-2}"
export RUN_TIMEOUT="${RUN_TIMEOUT:-300}"

run_step() {
  local name=$1
  shift
  echo "[cuda-revalidation] START $name"
  set +e
  "$@" >"$logdir/${name}.log" 2>&1
  local rc=$?
  set -e
  echo "$rc" >"$logdir/${name}.exitcode"
  if [ "$rc" -eq 0 ]; then
    echo "[cuda-revalidation] PASS  $name"
  else
    echo "[cuda-revalidation] FAIL  $name rc=$rc"
    tail -n 80 "$logdir/${name}.log" || true
    return "$rc"
  fi
}

overall_rc=0

run_step cuda_preflight tools/codex_preflight_environment.sh --require-cuda || overall_rc=$?

if [ "$overall_rc" -eq 0 ]; then
  export CODEX_REPRO_REQUIRE_CUDA=1
  export CODEX_REPRO_SKIP_SMOKE_ALL="${CODEX_CUDA_REVALIDATION_SKIP_CPU_SMOKE_ALL:-1}"
  export CODEX_REPRO_LOG_DIR="$logdir/repro_require_cuda"
  run_step reproducible_gate_require_cuda bash tools/codex_reproducible_gate.sh || overall_rc=$?
else
  echo "[cuda-revalidation] SKIP reproducible_gate_require_cuda because cuda_preflight failed"
  echo "SKIPPED" >"$logdir/reproducible_gate_require_cuda.exitcode"
fi

if [ "${CODEX_CUDA_REVALIDATION_RUN_ENGINEERING_LONG:-0}" = "1" ] && [ "$overall_rc" -eq 0 ]; then
  export CODEX_PIPE_RACK_REACTING_LOG_ROOT="$logdir/engineering_pipe_rack_reacting_cuda"
  export CODEX_PIPE_RACK_REACTING_MAX_STEP="${CODEX_PIPE_RACK_REACTING_MAX_STEP:-30}"
  export CODEX_PIPE_RACK_REACTING_PLOT_INT="${CODEX_PIPE_RACK_REACTING_PLOT_INT:-5}"
  export CODEX_PIPE_RACK_REACTING_MIN_SUSTAINED_OUTPUTS="${CODEX_PIPE_RACK_REACTING_MIN_SUSTAINED_OUTPUTS:-4}"
  run_step engineering_pipe_rack_reacting_cuda bash tools/codex_smoke_engineering_h2_pipe_rack_reacting_cuda.sh || overall_rc=$?
  export CODEX_REACTING_MPI_CUDA_LOG_DIR="$logdir/engineering_pipe_rack_reacting_mpi_cuda"
  run_step engineering_pipe_rack_reacting_mpi_cuda bash tools/codex_smoke_engineering_h2_reacting_mpi_cuda.sh || overall_rc=$?
else
  echo "[cuda-revalidation] SKIP engineering long CUDA cases unless CODEX_CUDA_REVALIDATION_RUN_ENGINEERING_LONG=1"
fi

echo "$overall_rc" >"$outdir/cuda_revalidation.exitcode"
if [ "$overall_rc" -eq 0 ]; then
  echo "[cuda-revalidation] PASS all requested CUDA revalidation gates"
else
  echo "[cuda-revalidation] NOT_READY CUDA revalidation rc=$overall_rc"
fi
exit "$overall_rc"
