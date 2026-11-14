#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_DIR="$ROOT_DIR/examples/academic/rayleigh_taylor"
EXE="$CASE_DIR/codex_rayleigh_taylor2d.gnu.ex"
BASE_INPUT="${CODEX_RAYLEIGH_TAYLOR_HIGHRES_INPUT:-input.codex_growth}"
LOG_DIR="${CODEX_RAYLEIGH_TAYLOR_HIGHRES_LOG_DIR:-$(mktemp -d /tmp/codex_rayleigh_taylor_highres.XXXXXX)}"
RUN_DIR="$LOG_DIR/run"
RUN_TIMEOUT="${RUN_TIMEOUT:-180}"
JOBS="${JOBS:-4}"
NX="${CODEX_RAYLEIGH_TAYLOR_HIGHRES_NX:-128}"
NY="${CODEX_RAYLEIGH_TAYLOR_HIGHRES_NY:-256}"
MAX_STEP="${CODEX_RAYLEIGH_TAYLOR_HIGHRES_MAX_STEP:-1000}"
STOP_TIME="${CODEX_RAYLEIGH_TAYLOR_HIGHRES_STOP_TIME:-4.0e-2}"
P0="${CODEX_RAYLEIGH_TAYLOR_HIGHRES_P0:-50.0}"
CFL="${CODEX_RAYLEIGH_TAYLOR_HIGHRES_CFL:-0.02}"
MIN_GROWTH="${CODEX_RAYLEIGH_TAYLOR_HIGHRES_MIN_GROWTH:-1.02}"

RUN_INPUT="input.codex_highres"

mkdir -p "$RUN_DIR"
echo "[codex-rayleigh-taylor-highres] log_dir=$LOG_DIR grid=${NX}x${NY} max_step=$MAX_STEP stop_time=$STOP_TIME p0=$P0 cfl=$CFL"
pushd "$CASE_DIR" >/dev/null
make -j "$JOBS" DIM=2 EBASE=codex_rayleigh_taylor USE_MPI=FALSE USE_OMP=FALSE >"$LOG_DIR/build.log" 2>&1
popd >/dev/null

test -x "$EXE"
python3 - "$CASE_DIR/$BASE_INPUT" "$RUN_DIR/$RUN_INPUT" "$NX" "$NY" "$MAX_STEP" "$STOP_TIME" "$P0" "$CFL" <<'PYINNER'
import re
import sys
from pathlib import Path

src, dst, nx, ny, max_step, stop_time, p0, cfl = sys.argv[1:]
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

pushd "$RUN_DIR" >/dev/null
timeout "$RUN_TIMEOUT" "$EXE" "$RUN_INPUT" >"$LOG_DIR/run.log" 2>&1
popd >/dev/null

grep -q "AMReX (.*) finalized" "$LOG_DIR/run.log"
grep -q "STEP = $MAX_STEP" "$LOG_DIR/run.log"
INITIAL="$RUN_DIR/plt00000"
FINAL="$(printf '%s/plt%05d' "$RUN_DIR" "$MAX_STEP")"
test -d "$INITIAL"
test -d "$FINAL"
python3 "$ROOT_DIR/tools/validate_rayleigh_taylor_plotfile.py" \
  --initial "$INITIAL" --final "$FINAL" >"$LOG_DIR/conservation.log"
python3 "$ROOT_DIR/tools/validate_rayleigh_taylor_growth.py" \
  --initial "$INITIAL" --final "$FINAL" \
  --min-growth-ratio "$MIN_GROWTH" >"$LOG_DIR/growth.log"
cat "$LOG_DIR/conservation.log"
cat "$LOG_DIR/growth.log"
echo "[codex-rayleigh-taylor-highres] PASS log=$LOG_DIR/run.log growth=$LOG_DIR/growth.log plot=$FINAL"
