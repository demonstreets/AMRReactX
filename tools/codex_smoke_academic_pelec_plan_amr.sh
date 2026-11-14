#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/academic/detonation_2D"
exe="$case_dir/codex_deton2d_cpu2d.gnu.ex"
log_dir="${CODEX_PELEC_PLAN_AMR_LOG_DIR:-/tmp/codex_pelec_plan_amr_$(date -u +%Y%m%dT%H%M%SZ)}"
run_dir="$log_dir/run"
run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"

mkdir -p "$run_dir"
rm -rf "$run_dir"/plt* "$run_log" "$validation_log"

printf '[codex-smoke] building PeleC detonation_2D plan-AMR validation\n'
make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_deton2d_cpu

printf '[codex-smoke] running PeleC detonation_2D plan-AMR validation\n'
cd "$run_dir"
timeout "${RUN_TIMEOUT:-180}" "$exe" "$case_dir/inputs.codex_plan_amr_smoke" > "$run_log" 2>&1

grep -q 'STEP = 2' "$run_log"
grep -Eq 'Initializing the data at level 1|Initializing data for 2 levels|Making new level 1 from scratch' "$run_log"
grep -q 'AMReX .* finalized' "$run_log"
if grep -q 'Unused ParmParse Variables' "$run_log"; then
  echo '[codex-smoke] PeleC plan-AMR run left unused ParmParse variables' >&2
  exit 1
fi
if [ ! -d "$run_dir/plt00002" ]; then
  echo '[codex-smoke] missing PeleC plan-AMR plotfile plt00002' >&2
  exit 1
fi

python3 "$repo_root/tools/validate_pelec_plan_amr.py" \
  --plotfile "$run_dir/plt00002" | tee "$validation_log"

printf '[codex-smoke] PASS PeleC plan-AMR validation log=%s validation=%s plot=%s\n' "$run_log" "$validation_log" "$run_dir/plt00002"
