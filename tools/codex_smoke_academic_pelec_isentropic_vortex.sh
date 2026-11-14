#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/external/PeleC/Exec/RegTests/IsentropicVortex"
exe="$case_dir/codex_isentropic_vortex3d.gnu.ex"
log_dir=${CODEX_ISENTROPIC_VORTEX_LOG_DIR:-/tmp/codex_pelec_isentropic_vortex_$(date -u +%Y%m%dT%H%M%SZ)}
run_dir="$log_dir/run"
mkdir -p "$log_dir"

if [[ "${CODEX_SKIP_BUILD:-0}" != "1" || ! -x "$exe" ]]; then
  echo "[codex-isentropic-vortex] building PeleC IsentropicVortex"
  make -C "$case_dir" -j "${JOBS:-2}" EBASE=codex_isentropic_vortex >"$log_dir/build.log" 2>&1
else
  echo "[codex-isentropic-vortex] reusing existing executable: $exe"
fi

rm -rf "$run_dir"
mkdir -p "$run_dir"
cp "$case_dir/input.codex_smoke" "$run_dir/"
cp "$exe" "$run_dir/"

echo "[codex-isentropic-vortex] running two-step PeleC isentropic vortex smoke"
(
  cd "$run_dir"
  timeout "${RUN_TIMEOUT:-180}" ./codex_isentropic_vortex3d.gnu.ex input.codex_smoke
) >"$log_dir/run.log" 2>&1

grep -q "STEP = 2" "$log_dir/run.log"
grep -q "PLOTFILE: file = plt00000" "$log_dir/run.log"
grep -q "PLOTFILE: file = plt00002" "$log_dir/run.log"
grep -q "AMReX .* finalized" "$log_dir/run.log"
if grep -Eq "Unused ParmParse Variables|Backtrace|SIGABRT|Abort::" "$log_dir/run.log"; then
  echo "[codex-isentropic-vortex] run log contains abort/unused/backtrace marker" >&2
  exit 1
fi

python3 "$repo_root/tools/validate_pelec_isentropic_vortex.py" \
  --initial "$run_dir/plt00000" \
  --final "$run_dir/plt00002" \
  --run-log "$log_dir/run.log" \
  --input "$case_dir/input.codex_smoke" \
  | tee "$log_dir/validation.log"

echo "[codex-isentropic-vortex] PASS; logs: $log_dir"
