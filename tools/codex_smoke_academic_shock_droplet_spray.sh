#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/academic/shock_droplet"
exe="$case_dir/PeleC2d.gnu.ex"
input="$case_dir/input.codex_spray_smoke"
log_dir="${CODEX_SHOCK_DROPLET_LOG_DIR:-/tmp/codex_shock_droplet_spray_$(date -u +%Y%m%dT%H%M%SZ)}"
run_dir="$log_dir/run"
build_log="$log_dir/build.log"
run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"

mkdir -p "$run_dir"
rm -rf "$run_dir"/plt* "$run_dir"/chk* "$build_log" "$run_log" "$validation_log"

printf '[codex-smoke] building shock_droplet spray executable
'
make -C "$case_dir" -j "${JOBS:-4}" > "$build_log" 2>&1

cp "$case_dir/initspraydata_2d_single.dat" "$run_dir/"

printf '[codex-smoke] running 5-step shock_droplet spray smoke
'
cd "$run_dir"
timeout "${RUN_TIMEOUT:-180}" "$exe" "$input" > "$run_log" 2>&1

grep -q 'STEP = 5' "$run_log"
grep -q 'PLOTFILE: file = plt00005' "$run_log"
grep -q 'AMReX .* finalized' "$run_log"
if grep -q 'Unused ParmParse Variables' "$run_log"; then
  echo '[codex-smoke] shock_droplet spray run left unused ParmParse variables' >&2
  exit 1
fi
if [ ! -d "$run_dir/plt00005" ]; then
  echo '[codex-smoke] missing shock_droplet spray plotfile plt00005' >&2
  exit 1
fi

python3 "$repo_root/tools/validate_shock_droplet_spray.py"   --plotfile "$run_dir/plt00005" | tee "$validation_log"

printf '[codex-smoke] PASS shock_droplet spray build=%s log=%s validation=%s
' "$build_log" "$run_log" "$validation_log"
