#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/bfs_kepsilon"
exe="$case_dir/codex_bfs_omp2d.gnu.OMP.ex"
log_dir=${CODEX_SMOKE_LOG_DIR:-/tmp/codex_smoke_engineering_omp_$(date -u +%Y%m%dT%H%M%SZ)}
run_dir=${CODEX_OMP_RUN_DIR:-/tmp/codex_bfs_omp_smoke_run_$(date -u +%Y%m%dT%H%M%SZ)}
omp_threads=${OMP_NUM_THREADS:-2}
run_timeout=${RUN_TIMEOUT:-180}
mkdir -p "$log_dir"

if [[ "${CODEX_SKIP_OMP_BUILD:-0}" != "1" || ! -x "$exe" ]]; then
  echo "[codex-smoke-omp] building PeleLMeX bfs_kepsilon OpenMP baseline"
  make -C "$case_dir" -j "${JOBS:-2}" USE_OMP=TRUE EBASE=codex_bfs_omp >"$log_dir/build.log" 2>&1
else
  echo "[codex-smoke-omp] reusing existing OpenMP executable: $exe"
fi

if [[ -f "$log_dir/build.log" ]]; then
  grep -Eq -- "-fopenmp|AMREX_USE_OMP|BL_USE_OMP" "$log_dir/build.log"
fi

rm -rf "$run_dir"
mkdir -p "$run_dir"
cp "$case_dir/input.codex_smoke" "$run_dir/"
cp "$exe" "$run_dir/"

echo "[codex-smoke-omp] running PeleLMeX bfs_kepsilon with ${omp_threads} OpenMP threads"
(
  cd "$run_dir"
  OMP_NUM_THREADS="$omp_threads" timeout "$run_timeout" ./codex_bfs_omp2d.gnu.OMP.ex input.codex_smoke
) >"$log_dir/run.log" 2>&1

grep -q "OMP initialized with ${omp_threads} OMP threads" "$log_dir/run.log"
grep -q "Final simulation time:" "$log_dir/run.log"
grep -q "AMReX .* finalized" "$log_dir/run.log"
python3 "$repo_root/tools/validate_parallel_smoke_log.py" --log "$log_dir/run.log" --mode omp --solver pelelmex --expected-threads "$omp_threads" --require-final-time | tee "$log_dir/validation.log"

echo "[codex-smoke-omp] PASS; logs: $log_dir"
