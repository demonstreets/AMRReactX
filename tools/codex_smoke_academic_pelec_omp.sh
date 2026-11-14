#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/academic/detonation_2D"
exe="$case_dir/codex_deton2d_omp2d.gnu.OMP.ex"
log_dir=${CODEX_SMOKE_LOG_DIR:-/tmp/codex_smoke_academic_omp_$(date -u +%Y%m%dT%H%M%SZ)}
run_dir=${CODEX_OMP_RUN_DIR:-/tmp/codex_deton2d_omp_smoke_run_$(date -u +%Y%m%dT%H%M%SZ)}
omp_threads=${OMP_NUM_THREADS:-2}
run_timeout=${RUN_TIMEOUT:-240}
mkdir -p "$log_dir"

if [[ "${CODEX_SKIP_OMP_BUILD:-0}" != "1" || ! -x "$exe" ]]; then
  echo "[codex-smoke-academic-omp] building PeleC detonation_2D OpenMP baseline"
  make -C "$case_dir" -j "${JOBS:-2}" USE_OMP=TRUE EBASE=codex_deton2d_omp >"$log_dir/build.log" 2>&1
else
  echo "[codex-smoke-academic-omp] reusing existing OpenMP executable: $exe"
fi

if [[ -f "$log_dir/build.log" ]]; then
  grep -Eq -- "-fopenmp|AMREX_USE_OMP|BL_USE_OMP" "$log_dir/build.log"
fi

rm -rf "$run_dir"
mkdir -p "$run_dir"
cp "$case_dir/inputs.codex_smoke" "$run_dir/"
cp "$exe" "$run_dir/"

echo "[codex-smoke-academic-omp] running PeleC detonation_2D with ${omp_threads} OpenMP threads"
(
  cd "$run_dir"
  OMP_NUM_THREADS="$omp_threads" timeout "$run_timeout" ./codex_deton2d_omp2d.gnu.OMP.ex inputs.codex_smoke
) >"$log_dir/run.log" 2>&1

grep -q "OMP initialized with ${omp_threads} OMP threads" "$log_dir/run.log"
grep -q "STEP = 1" "$log_dir/run.log"
grep -q "AMReX .* finalized" "$log_dir/run.log"
python3 "$repo_root/tools/validate_parallel_smoke_log.py" --log "$log_dir/run.log" --mode omp --solver pelec --expected-threads "$omp_threads" --require-step "STEP = 1" | tee "$log_dir/validation.log"

echo "[codex-smoke-academic-omp] PASS; logs: $log_dir"
