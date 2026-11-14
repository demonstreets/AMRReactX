#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/academic/detonation_2D"
exe="$case_dir/codex_deton2d_cpu2d.gnu.ex"
log_dir="${CODEX_DETONATION_LOG_DIR:-/tmp/codex_detonation_wave_$(date -u +%Y%m%dT%H%M%SZ)}"
run_dir="$log_dir/run"
run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"

# An explicitly reused path is an error: never destroy previous evidence.
if ! mkdir "$log_dir"; then
  echo "[codex-smoke] log directory already exists or cannot be created: $log_dir" >&2
  exit 2
fi
mkdir "$run_dir"

printf '[codex-smoke] building PeleC detonation_2D wave validation\n'
make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_deton2d_cpu

printf '[codex-smoke] running 20-step PeleC detonation_2D wave validation\n'
cd "$run_dir"
timeout "${RUN_TIMEOUT:-180}" "$exe" "$case_dir/inputs.codex_wave_smoke" > "$run_log" 2>&1

grep -q 'STEP = 20' "$run_log"
grep -q 'PLOTFILE: file = plt00020' "$run_log"
grep -q 'AMReX .* finalized' "$run_log"
if grep -q 'Unused ParmParse Variables' "$run_log"; then
  echo '[codex-smoke] detonation wave run left unused ParmParse variables' >&2
  exit 1
fi
if [ ! -d "$run_dir/plt00000" ] || [ ! -d "$run_dir/plt00020" ]; then
  echo '[codex-smoke] missing detonation plotfiles plt00000/plt00020' >&2
  exit 1
fi

python3 "$repo_root/tools/validate_detonation_wave.py" \
  --initial "$run_dir/plt00000" \
  --final "$run_dir/plt00020" | tee "$validation_log"

printf '[codex-smoke] PASS detonation wave validation log=%s validation=%s\n' "$run_log" "$validation_log"
