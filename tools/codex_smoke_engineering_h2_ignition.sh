#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_ignition"
exe="$case_dir/codex_h2_ignition2d.gnu.ex"
log_file="${CODEX_RUN_LOG:-/tmp/codex_h2_ignition_smoke.log}"

echo "[codex-smoke] building PeleLMeX h2_ignition CPU baseline"
make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_h2_ignition USE_MPI=FALSE

echo "[codex-smoke] running 1-step PeleLMeX h2_ignition baseline"
cd "$case_dir"
timeout "${RUN_TIMEOUT:-180}" "$exe" input.codex_smoke | tee "$log_file"

grep -q 'Creating ReactorBase instance: ReactorCvode' "$log_file"
grep -q 'STEP \[0\]' "$log_file"
grep -q 'Final simulation time:' "$log_file"
if grep -q 'Unused ParmParse Variables' "$log_file"; then
  echo "[codex-smoke] h2_ignition left unused ParmParse variables" >&2
  exit 1
fi
