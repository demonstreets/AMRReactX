#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_ignition"
exe="$case_dir/codex_h2_ignition2d.gnu.ex"
log_dir="${CODEX_H2_IGNITION_SDC_LOG_DIR:-/tmp/codex_h2_ignition_sdc_compare_$(date -u +%Y%m%dT%H%M%SZ)}"
log_dir=$(mkdir -p "$log_dir" && cd "$log_dir" && pwd)
sdc1_dir="$log_dir/sdc1"
sdc2_dir="$log_dir/sdc2"
sdc1_log="$log_dir/sdc1.log"
sdc2_log="$log_dir/sdc2.log"
sdc1_validation="$log_dir/sdc1_history_validation.log"
sdc2_validation="$log_dir/sdc2_history_validation.log"
compare_log="$log_dir/sdc_compare.log"

mkdir -p "$sdc1_dir" "$sdc2_dir"
rm -rf "$sdc1_dir"/plt* "$sdc2_dir"/plt* "$sdc1_log" "$sdc2_log" "$sdc1_validation" "$sdc2_validation" "$compare_log"

printf '[codex-smoke] building PeleLMeX h2_ignition CPU SDC comparison\n'
make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_h2_ignition USE_MPI=FALSE

run_case() {
  local label=$1
  local input=$2
  local run_dir=$3
  local run_log=$4
  local validation_log=$5

  printf '[codex-smoke] running H2 ignition %s\n' "$label"
  cd "$run_dir"
  timeout "${RUN_TIMEOUT:-180}" "$exe" "$input" > "$run_log" 2>&1

  grep -q 'Creating ReactorBase instance: ReactorCvode' "$run_log"
  grep -q 'STEP \[9\]' "$run_log"
  grep -q 'Final simulation time: 1e-07' "$run_log"
  grep -q 'AMReX .* finalized' "$run_log"
  if grep -q 'Unused ParmParse Variables' "$run_log"; then
    echo "[codex-smoke] $label left unused ParmParse variables" >&2
    exit 1
  fi
  if [ ! -d "$run_dir/plt00000" ] || [ ! -d "$run_dir/plt00010" ]; then
    echo "[codex-smoke] $label missing plotfiles plt00000/plt00010" >&2
    exit 1
  fi

  python3 "$repo_root/tools/validate_h2_ignition_history.py" \
    --run-dir "$run_dir" | tee "$validation_log"
}

run_case sdc1 "$case_dir/input.codex_history_smoke" "$sdc1_dir" "$sdc1_log" "$sdc1_validation"
run_case sdc2 "$case_dir/input.codex_history_sdc2_smoke" "$sdc2_dir" "$sdc2_log" "$sdc2_validation"

python3 "$repo_root/tools/validate_h2_ignition_sdc_compare.py" \
  --sdc1-final "$sdc1_dir/plt00010" \
  --sdc2-final "$sdc2_dir/plt00010" | tee "$compare_log"

printf '[codex-smoke] PASS h2_ignition SDC comparison logs=%s compare=%s\n' "$log_dir" "$compare_log"
