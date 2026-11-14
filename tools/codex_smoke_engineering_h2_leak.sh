#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_leak_3d"
exe="$case_dir/codex_h2_leak3d.gnu.ex"
log_file="${CODEX_RUN_LOG:-/tmp/codex_h2_leak_smoke.log}"

if [[ "${CODEX_SKIP_BUILD:-0}" == "1" ]]; then
  if [[ ! -x "$exe" ]]; then
    echo "[codex-smoke] missing executable: $exe" >&2
    exit 1
  fi
else
  echo "[codex-smoke] building PeleLMeX h2_leak_3d CPU baseline"
  make -C "$case_dir" -j "${JOBS:-4}" EBASE=codex_h2_leak USE_MPI=FALSE USE_EB=TRUE
fi

run_input=${CODEX_H2_LEAK_INPUT:-input.codex_smoke}
run_dir=${CODEX_H2_LEAK_RUN_DIR:-}
validation_log=${CODEX_H2_LEAK_VALIDATION_LOG:-}

echo "[codex-smoke] running 1-step PeleLMeX h2_leak_3d baseline input=$run_input"
if [[ -n "$run_dir" ]]; then
  rm -rf "$run_dir"
  mkdir -p "$run_dir"
  cp "$case_dir/$run_input" "$run_dir/"
  cp "$exe" "$run_dir/"
  (
    cd "$run_dir"
    timeout "${RUN_TIMEOUT:-180}" "./$(basename "$exe")" "$run_input"
  ) | tee "$log_file"
else
  cd "$case_dir"
  timeout "${RUN_TIMEOUT:-180}" "$exe" "$run_input" | tee "$log_file"
fi

grep -q 'Applying H2 leak source:' "$log_file"
grep -q 'H2 leak discrete active volume=' "$log_file"
grep -q 'mdot_vol=' "$log_file"
grep -q 'Creating ReactorBase instance: ReactorNull' "$log_file"
grep -q 'STEP \[0\]' "$log_file"
grep -q 'Final simulation time:' "$log_file"
if grep -q 'Unused ParmParse Variables' "$log_file"; then
  echo "[codex-smoke] h2_leak_3d left unused ParmParse variables" >&2
  exit 1
fi

if [[ "$run_input" == "input.codex_plume_smoke" ]]; then
  if [[ -z "$run_dir" ]]; then
    run_dir="$case_dir"
  fi
  validation_log=${validation_log:-/tmp/codex_h2_leak_plume_validation.log}
  python3 "$repo_root/tools/validate_h2_leak_plume.py"     --plotfile "$run_dir/plt00001"     --input "$run_dir/$run_input"     --log "$log_file" | tee "$validation_log"
fi
