#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/bfs_kepsilon"
exe="$case_dir/codex_bfs_hybrid2d.gnu.MPI.OMP.ex"
log_dir=${CODEX_SMOKE_LOG_DIR:-/tmp/codex_smoke_engineering_hybrid_$(date -u +%Y%m%dT%H%M%SZ)}
run_dir=${CODEX_HYBRID_RUN_DIR:-/tmp/codex_bfs_hybrid_smoke_run_$(date -u +%Y%m%dT%H%M%SZ)}
run_timeout=${RUN_TIMEOUT:-240}
mpi_ranks=${MPI_RANKS:-2}
omp_threads=${OMP_NUM_THREADS:-2}
mkdir -p "$log_dir"

if ! command -v mpirun >/dev/null 2>&1; then
  echo "[codex-smoke-engineering-hybrid] mpirun not found" >&2
  exit 127
fi

if [[ "${CODEX_SKIP_HYBRID_BUILD:-0}" != "1" || ! -x "$exe" ]]; then
  echo "[codex-smoke-engineering-hybrid] building PeleLMeX bfs_kepsilon MPI+OpenMP baseline"
  make -C "$case_dir" -j "${JOBS:-2}" USE_MPI=TRUE USE_OMP=TRUE EBASE=codex_bfs_hybrid >"$log_dir/build.log" 2>&1
else
  echo "[codex-smoke-engineering-hybrid] reusing existing MPI+OpenMP executable: $exe"
fi

if [[ -f "$log_dir/build.log" ]]; then
  grep -Eq 'mpicxx|AMREX_USE_MPI|BL_USE_MPI' "$log_dir/build.log"
  grep -Eq -- '-fopenmp|AMREX_USE_OMP|BL_USE_OMP' "$log_dir/build.log"
fi

rm -rf "$run_dir"
mkdir -p "$run_dir"
cp "$case_dir/input.codex_smoke" "$run_dir/"
cp "$exe" "$run_dir/"

echo "[codex-smoke-engineering-hybrid] running ${mpi_ranks}-rank x ${omp_threads}-thread PeleLMeX bfs_kepsilon baseline"
(
  cd "$run_dir"
  OMP_NUM_THREADS="$omp_threads" exec mpirun --oversubscribe -np "$mpi_ranks" ./codex_bfs_hybrid2d.gnu.MPI.OMP.ex input.codex_smoke
) >"$log_dir/run.log" 2>&1 &
run_pid=$!

deadline=$((SECONDS + run_timeout))
while kill -0 "$run_pid" 2>/dev/null; do
  if grep -Eq 'AMReX .* finalized' "$log_dir/run.log"; then
    sleep 1
    if kill -0 "$run_pid" 2>/dev/null; then
      echo "[codex-smoke-engineering-hybrid] run finalized; terminating mpirun wrapper if still alive"
      kill "$run_pid" 2>/dev/null || true
      sleep 1
    fi
    break
  fi
  if (( SECONDS >= deadline )); then
    echo "[codex-smoke-engineering-hybrid] timed out after ${run_timeout}s" >&2
    kill "$run_pid" 2>/dev/null || true
    wait "$run_pid" 2>/dev/null || true
    exit 124
  fi
  sleep 1
done
wait "$run_pid" 2>/dev/null || true

grep -q "MPI initialized with ${mpi_ranks} MPI processes" "$log_dir/run.log"
grep -q "OMP initialized with ${omp_threads} OMP threads" "$log_dir/run.log"
grep -q "Final simulation time:" "$log_dir/run.log"
grep -Eq 'AMReX .* finalized' "$log_dir/run.log"
python3 "$repo_root/tools/validate_parallel_smoke_log.py" --log "$log_dir/run.log" --mode hybrid --solver pelelmex --expected-ranks "$mpi_ranks" --expected-threads "$omp_threads" --require-final-time --allow-thread-support-zero | tee "$log_dir/validation.log"

if pgrep -af 'codex_bfs_hybrid|mpirun.*codex_bfs_hybrid' >/dev/null 2>&1; then
  echo "[codex-smoke-engineering-hybrid] lingering MPI process detected" >&2
  pgrep -af 'codex_bfs_hybrid|mpirun.*codex_bfs_hybrid' >&2 || true
  exit 125
fi

echo "[codex-smoke-engineering-hybrid] PASS; logs: $log_dir"
