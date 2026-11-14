#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_DIR="$ROOT_DIR/examples/academic/rayleigh_taylor"
EXE="$CASE_DIR/codex_rayleigh_taylor2d.gnu.ex"
BASE_INPUT="${CODEX_RAYLEIGH_TAYLOR_TREND_INPUT:-input.codex_growth}"
LOG_DIR="${CODEX_RAYLEIGH_TAYLOR_TREND_LOG_DIR:-$(mktemp -d /tmp/codex_rayleigh_taylor_trend.XXXXXX)}"
RUN_TIMEOUT="${RUN_TIMEOUT:-600}"
JOBS="${JOBS:-4}"
STOP_TIME="${CODEX_RAYLEIGH_TAYLOR_TREND_STOP_TIME:-1.6e-2}"
MAX_STEP="${CODEX_RAYLEIGH_TAYLOR_TREND_MAX_STEP:-4000}"
RESOLUTIONS="${CODEX_RAYLEIGH_TAYLOR_TREND_NX:-32 64 96}"
P0="${CODEX_RAYLEIGH_TAYLOR_TREND_P0:-50.0}"
CFL="${CODEX_RAYLEIGH_TAYLOR_TREND_CFL:-0.02}"

echo "[codex-rayleigh-taylor-trend] log_dir=$LOG_DIR resolutions=$RESOLUTIONS stop_time=$STOP_TIME max_step=$MAX_STEP p0=$P0 cfl=$CFL"
mkdir -p "$LOG_DIR"
pushd "$CASE_DIR" >/dev/null
make -j "$JOBS" DIM=2 EBASE=codex_rayleigh_taylor USE_MPI=FALSE USE_OMP=FALSE >"$LOG_DIR/build.log" 2>&1
popd >/dev/null

test -x "$EXE"

growth_logs=()
for nx in $RESOLUTIONS; do
  ny=$((2 * nx))
  run_dir="$LOG_DIR/run_${nx}x${ny}"
  input_name="input.codex_growth_${nx}x${ny}"
  mkdir -p "$run_dir"
  python3 - "$CASE_DIR/$BASE_INPUT" "$run_dir/$input_name" "$nx" "$ny" "$STOP_TIME" "$MAX_STEP" "$P0" "$CFL" <<'PYINNER'
import re
import sys
from pathlib import Path

src, dst, nx, ny, stop_time, max_step, p0, cfl = sys.argv[1:]
text = Path(src).read_text()
replacements = {
    r'^max_step\s*=.*$': f'max_step = {max_step}',
    r'^stop_time\s*=.*$': f'stop_time = {stop_time}',
    r'^amr\.n_cell\s*=.*$': f'amr.n_cell = {nx} {ny} 1',
    r'^amr\.plot_int\s*=.*$': f'amr.plot_int = {max_step}',
    r'^pelec\.cfl\s*=.*$': f'pelec.cfl = {cfl}',
    r'^prob\.p0\s*=.*$': f'prob.p0 = {p0}',
    r'^pelec\.sum_interval\s*=.*$': 'pelec.sum_interval = 1000',
}
for pattern, value in replacements.items():
    text, count = re.subn(pattern, value, text, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f'FAIL: expected one replacement for {pattern}, got {count}')
Path(dst).write_text(text)
PYINNER
  echo "[codex-rayleigh-taylor-trend] running ${nx}x${ny}"
  pushd "$run_dir" >/dev/null
  timeout "$RUN_TIMEOUT" "$EXE" "$input_name" >"$LOG_DIR/run_${nx}x${ny}.log" 2>&1
  popd >/dev/null
  grep -q "AMReX (.*) finalized" "$LOG_DIR/run_${nx}x${ny}.log"
  final_plot="$(find "$run_dir" -maxdepth 1 -type d -name 'plt[0-9][0-9][0-9][0-9][0-9]' | sort | tail -1)"
  test -n "$final_plot"
  test -d "$run_dir/plt00000"
  python3 "$ROOT_DIR/tools/validate_rayleigh_taylor_plotfile.py" \
    --initial "$run_dir/plt00000" --final "$final_plot" >"$LOG_DIR/conservation_${nx}x${ny}.log"
  python3 "$ROOT_DIR/tools/validate_rayleigh_taylor_growth.py" \
    --initial "$run_dir/plt00000" --final "$final_plot" >"$LOG_DIR/growth_${nx}x${ny}.log"
  cat "$LOG_DIR/growth_${nx}x${ny}.log"
  growth_logs+=("$LOG_DIR/growth_${nx}x${ny}.log")
done

python3 "$ROOT_DIR/tools/validate_rayleigh_taylor_resolution_trend.py" \
  "${growth_logs[@]}" >"$LOG_DIR/resolution_trend.log"
cat "$LOG_DIR/resolution_trend.log"
echo "[codex-rayleigh-taylor-trend] PASS log=$LOG_DIR trend=$LOG_DIR/resolution_trend.log"
