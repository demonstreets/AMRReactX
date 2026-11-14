#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_ignition"
exe="$case_dir/codex_h2_ignition2d.gnu.ex"
log_dir="${CODEX_H2_IGNITION_HISTORY_LOG_DIR:-/tmp/codex_h2_ignition_history_$(date -u +%Y%m%dT%H%M%SZ)}"
log_dir=$(mkdir -p "$log_dir" && cd "$log_dir" && pwd)
run_dir="$log_dir/run"
run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"

mkdir -p "$run_dir"
rm -rf "$run_dir"/plt* "$run_log" "$validation_log"

printf '[codex-smoke] building PeleLMeX h2_ignition CPU history validation\n'
make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_h2_ignition USE_MPI=FALSE

printf '[codex-smoke] running 10-step PeleLMeX h2_ignition history validation\n'
cd "$run_dir"
timeout "${RUN_TIMEOUT:-180}" "$exe" "$case_dir/input.codex_history_smoke" > "$run_log" 2>&1

grep -q 'Creating ReactorBase instance: ReactorCvode' "$run_log"
grep -q 'STEP \[9\]' "$run_log"
grep -q 'Final simulation time: 1e-07' "$run_log"
grep -q 'AMReX .* finalized' "$run_log"
if grep -q 'Unused ParmParse Variables' "$run_log"; then
  echo '[codex-smoke] h2_ignition history run left unused ParmParse variables' >&2
  exit 1
fi
if [ ! -d "$run_dir/plt00000" ] || [ ! -d "$run_dir/plt00010" ]; then
  echo '[codex-smoke] missing h2_ignition history plotfiles plt00000/plt00010' >&2
  exit 1
fi

python3 "$repo_root/tools/validate_h2_ignition_history.py" \
  --run-dir "$run_dir" | tee "$validation_log"

printf '[codex-smoke] PASS h2_ignition history validation log=%s validation=%s\n' "$run_log" "$validation_log"
