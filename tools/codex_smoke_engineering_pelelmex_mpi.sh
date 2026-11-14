#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/bfs_kepsilon"
exe="$case_dir/codex_bfs_mpi2d.gnu.MPI.ex"
log_dir=${CODEX_SMOKE_LOG_DIR:-/tmp/codex_smoke_engineering_mpi_$(date -u +%Y%m%dT%H%M%SZ)}
run_dir=${CODEX_MPI_RUN_DIR:-/tmp/codex_bfs_mpi_smoke_run_$(date -u +%Y%m%dT%H%M%SZ)}
mkdir -p "$log_dir"

if ! command -v mpirun >/dev/null 2>&1; then
  echo "[codex-smoke-mpi] mpirun not found" >&2
  exit 127
fi

if [[ "${CODEX_SKIP_MPI_BUILD:-0}" != "1" || ! -x "$exe" ]]; then
  echo "[codex-smoke-mpi] building PeleLMeX bfs_kepsilon MPI baseline"
  make -C "$case_dir" -j "${JOBS:-2}" USE_MPI=TRUE EBASE=codex_bfs_mpi >"$log_dir/build.log" 2>&1
else
  echo "[codex-smoke-mpi] reusing existing MPI executable: $exe"
fi

rm -rf "$run_dir"
mkdir -p "$run_dir"
cp "$case_dir/input.codex_smoke" "$run_dir/"
cp "$exe" "$run_dir/"

echo "[codex-smoke-mpi] running 2-rank PeleLMeX bfs_kepsilon baseline"
(
  cd "$run_dir"
  timeout "${RUN_TIMEOUT:-180}" mpirun --oversubscribe -np "${MPI_RANKS:-2}" ./codex_bfs_mpi2d.gnu.MPI.ex input.codex_smoke
) >"$log_dir/run.log" 2>&1

grep -q "MPI initialized with ${MPI_RANKS:-2} MPI processes" "$log_dir/run.log"
grep -q "Final simulation time:" "$log_dir/run.log"
grep -q "AMReX .* finalized" "$log_dir/run.log"
python3 "$repo_root/tools/validate_parallel_smoke_log.py" --log "$log_dir/run.log" --mode mpi --solver pelelmex --expected-ranks "${MPI_RANKS:-2}" --require-final-time | tee "$log_dir/validation.log"

echo "[codex-smoke-mpi] PASS; logs: $log_dir"
