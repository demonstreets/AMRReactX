#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/academic/detonation_2D"
exe="$case_dir/codex_deton2d_mpi2d.gnu.MPI.ex"
log_dir=${CODEX_SMOKE_LOG_DIR:-/tmp/codex_smoke_academic_mpi_$(date -u +%Y%m%dT%H%M%SZ)}
run_dir=${CODEX_MPI_RUN_DIR:-/tmp/codex_deton2d_mpi_smoke_run_$(date -u +%Y%m%dT%H%M%SZ)}
run_timeout=${RUN_TIMEOUT:-240}
mpi_ranks=${MPI_RANKS:-2}
mkdir -p "$log_dir"

if ! command -v mpirun >/dev/null 2>&1; then
  echo "[codex-smoke-academic-mpi] mpirun not found" >&2
  exit 127
fi

if [[ "${CODEX_SKIP_MPI_BUILD:-0}" != "1" || ! -x "$exe" ]]; then
  echo "[codex-smoke-academic-mpi] building PeleC detonation_2D MPI baseline"
  make -C "$case_dir" -j "${JOBS:-2}" USE_MPI=TRUE EBASE=codex_deton2d_mpi >"$log_dir/build.log" 2>&1
else
  echo "[codex-smoke-academic-mpi] reusing existing MPI executable: $exe"
fi

rm -rf "$run_dir"
mkdir -p "$run_dir"
cp "$case_dir/inputs.codex_smoke" "$run_dir/"
cp "$exe" "$run_dir/"

echo "[codex-smoke-academic-mpi] running ${mpi_ranks}-rank PeleC detonation_2D baseline"
(
  cd "$run_dir"
  exec mpirun --oversubscribe -np "$mpi_ranks" ./codex_deton2d_mpi2d.gnu.MPI.ex inputs.codex_smoke
) >"$log_dir/run.log" 2>&1 &
run_pid=$!

deadline=$((SECONDS + run_timeout))
while kill -0 "$run_pid" 2>/dev/null; do
  if grep -q "AMReX .* finalized" "$log_dir/run.log"; then
    echo "[codex-smoke-academic-mpi] run finalized; terminating mpirun wrapper if still alive"
    kill "$run_pid" 2>/dev/null || true
    sleep 1
    break
  fi
  if (( SECONDS >= deadline )); then
    echo "[codex-smoke-academic-mpi] timed out after ${run_timeout}s" >&2
    kill "$run_pid" 2>/dev/null || true
    wait "$run_pid" 2>/dev/null || true
    exit 124
  fi
  sleep 1
done
wait "$run_pid" 2>/dev/null || true

grep -q "MPI initialized with ${mpi_ranks} MPI processes" "$log_dir/run.log"
grep -q "STEP = 1" "$log_dir/run.log"
grep -q "AMReX .* finalized" "$log_dir/run.log"
python3 "$repo_root/tools/validate_parallel_smoke_log.py" --log "$log_dir/run.log" --mode mpi --solver pelec --expected-ranks "$mpi_ranks" --require-step "STEP = 1" | tee "$log_dir/validation.log"

if pgrep -af 'codex_deton2d_mpi|mpirun.*codex_deton2d' >/dev/null 2>&1; then
  echo "[codex-smoke-academic-mpi] lingering MPI process detected" >&2
  pgrep -af 'codex_deton2d_mpi|mpirun.*codex_deton2d' >&2 || true
  exit 125
fi

echo "[codex-smoke-academic-mpi] PASS; logs: $log_dir"
