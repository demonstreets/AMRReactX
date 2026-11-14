#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/external/PeleLMeX/Exec/RegTests/EB_FlowPastCylinder"
exe="$case_dir/PeleLMeX2d.gnu.MPI.ex"
log_dir=${CODEX_SMOKE_LOG_DIR:-/tmp/codex_smoke_engineering_eb_$(date -u +%Y%m%dT%H%M%SZ)}
run_dir=${CODEX_EB_RUN_DIR:-/tmp/codex_eb_flowpast_smoke_run_$(date -u +%Y%m%dT%H%M%SZ)}
mpi_ranks=${MPI_RANKS:-1}
run_timeout=${RUN_TIMEOUT:-180}
mkdir -p "$log_dir"

if ! command -v mpirun >/dev/null 2>&1; then
  echo "[codex-smoke-engineering-eb] mpirun not found" >&2
  exit 127
fi

if [[ ! -x "$exe" || "${CODEX_FORCE_EB_BUILD:-0}" == "1" ]]; then
  echo "[codex-smoke-engineering-eb] building PeleLMeX EB_FlowPastCylinder baseline"
  make -C "$case_dir" -j "${JOBS:-2}" USE_MPI=TRUE USE_OMP=FALSE >"$log_dir/build.log" 2>&1
else
  echo "[codex-smoke-engineering-eb] reusing existing executable: $exe"
fi

rm -rf "$run_dir"
mkdir -p "$run_dir"
cp "$case_dir/input.codex_smoke" "$run_dir/"
cp "$exe" "$run_dir/"

(
  cd "$run_dir"
  OMP_NUM_THREADS=1 timeout "$run_timeout" mpirun --oversubscribe -np "$mpi_ranks" ./PeleLMeX2d.gnu.MPI.ex input.codex_smoke
) >"$log_dir/run.log" 2>&1

grep -q "MPI initialized with ${mpi_ranks} MPI processes" "$log_dir/run.log"
grep -q "Resetting fine-covered cells mask" "$log_dir/run.log"
grep -q "STEP \[0\]" "$log_dir/run.log"
grep -q "Final simulation time:" "$log_dir/run.log"
grep -Eq 'AMReX .* finalized' "$log_dir/run.log"
if grep -q "Unused ParmParse Variables" "$log_dir/run.log"; then
  echo "[codex-smoke-engineering-eb] unused ParmParse variables detected" >&2
  grep -A40 "Unused ParmParse Variables" "$log_dir/run.log" >&2
  exit 3
fi

echo "[codex-smoke-engineering-eb] PASS; logs: $log_dir"
