#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_DIR="$ROOT_DIR/examples/academic/rayleigh_taylor"
EXE="$CASE_DIR/codex_rayleigh_taylor2d.gnu.ex"
BASE_INPUT="${CODEX_RAYLEIGH_TAYLOR_LOW_PRESSURE_INPUT:-input.codex_growth}"
LOG_DIR="${CODEX_RAYLEIGH_TAYLOR_LOW_PRESSURE_LOG_DIR:-$(mktemp -d /tmp/codex_rayleigh_taylor_lowp.XXXXXX)}"
RUN_DIR="$LOG_DIR/run"
RUN_INPUT="input.codex_low_p10"
RUN_TIMEOUT="${RUN_TIMEOUT:-120}"
JOBS="${JOBS:-4}"
NX="${CODEX_RAYLEIGH_TAYLOR_LOW_PRESSURE_NX:-128}"
NY="${CODEX_RAYLEIGH_TAYLOR_LOW_PRESSURE_NY:-256}"
MAX_STEP="${CODEX_RAYLEIGH_TAYLOR_LOW_PRESSURE_MAX_STEP:-100}"
P0="${CODEX_RAYLEIGH_TAYLOR_LOW_PRESSURE_P0:-10.0}"
CFL="${CODEX_RAYLEIGH_TAYLOR_LOW_PRESSURE_CFL:-0.05}"
MIN_PRESSURE="${CODEX_RAYLEIGH_TAYLOR_LOW_PRESSURE_MIN_PRESSURE:-1.0e-12}"

mkdir -p "$RUN_DIR"
echo "[codex-rayleigh-taylor-lowp] log_dir=$LOG_DIR grid=${NX}x${NY} max_step=$MAX_STEP p0=$P0 cfl=$CFL"
pushd "$CASE_DIR" >/dev/null
make -j "$JOBS" DIM=2 EBASE=codex_rayleigh_taylor USE_MPI=FALSE USE_OMP=FALSE >"$LOG_DIR/build.log" 2>&1
popd >/dev/null

test -x "$EXE"
python3 - "$CASE_DIR/$BASE_INPUT" "$RUN_DIR/$RUN_INPUT" "$NX" "$NY" "$MAX_STEP" "$P0" "$CFL" <<'PYINNER'
import re
import sys
from pathlib import Path

src, dst, nx, ny, max_step, p0, cfl = sys.argv[1:]
text = Path(src).read_text()
replacements = {
    r'^max_step\s*=.*$': f'max_step = {max_step}',
    r'^stop_time\s*=.*$': 'stop_time = 7.0e-2',
    r'^amr\.n_cell\s*=.*$': f'amr.n_cell = {nx} {ny} 1',
    r'^amr\.plot_int\s*=.*$': f'amr.plot_int = {max_step}',
    r'^pelec\.cfl\s*=.*$': f'pelec.cfl = {cfl}',
    r'^prob\.p0\s*=.*$': f'prob.p0 = {p0}',
    r'^pelec\.sum_interval\s*=.*$': 'pelec.sum_interval = 1',
}
for pattern, value in replacements.items():
    text, count = re.subn(pattern, value, text, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f'FAIL: expected one replacement for {pattern}, got {count}')
for key, value in {
    'pelec.allow_negative_energy': '0',
    'pelec.allow_small_energy': '0',
    'pelec.dual_energy_update_E_from_e': '1',
}.items():
    line = f'{key} = {value}'
    if re.search(rf'^{re.escape(key)}\s*=', text, flags=re.MULTILINE):
        text = re.sub(rf'^{re.escape(key)}\s*=.*$', line, text, flags=re.MULTILINE)
    else:
        text += '\n' + line + '\n'
Path(dst).write_text(text)
PYINNER

pushd "$RUN_DIR" >/dev/null
timeout "$RUN_TIMEOUT" "$EXE" "$RUN_INPUT" >"$LOG_DIR/run.log" 2>&1
popd >/dev/null

grep -q "AMReX (.*) finalized" "$LOG_DIR/run.log"
grep -q "STEP = $MAX_STEP" "$LOG_DIR/run.log"
if grep -Eiq '(^|[^[:alpha:]])(nan|inf)([^[:alpha:]]|$)' "$LOG_DIR/run.log"; then
  echo "[codex-rayleigh-taylor-lowp] non-finite token found in run log" >&2
  tail -120 "$LOG_DIR/run.log" >&2
  exit 1
fi
INITIAL="$RUN_DIR/plt00000"
FINAL="$(printf '%s/plt%05d' "$RUN_DIR" "$MAX_STEP")"
test -d "$INITIAL"
test -d "$FINAL"
python3 "$ROOT_DIR/tools/validate_rayleigh_taylor_plotfile.py" \
  --initial "$INITIAL" --final "$FINAL" >"$LOG_DIR/conservation.log"
python3 - "$LOG_DIR/run.log" "$MIN_PRESSURE" >"$LOG_DIR/positivity.log" <<'PYINNER'
import math
import re
import sys
from pathlib import Path

log = Path(sys.argv[1]).read_text()
min_pressure = float(sys.argv[2])
patterns = {
    'pressure': re.compile(r'pressure\s+MIN\s*=\s*([-+0-9.eE]+)'),
    'eint_e': re.compile(r'eint_e\s+MIN\s*=\s*([-+0-9.eE]+)'),
    'Temp': re.compile(r'Temp\s+MIN\s*=\s*([-+0-9.eE]+)'),
}
values = {}
for name, pattern in patterns.items():
    vals = [float(x) for x in pattern.findall(log)]
    if not vals:
        raise SystemExit(f'FAIL: no {name} MIN entries found')
    if not all(math.isfinite(v) for v in vals):
        raise SystemExit(f'FAIL: non-finite {name} MIN found')
    values[name] = vals[-1]
if values['pressure'] <= min_pressure or values['eint_e'] <= 0.0 or values['Temp'] <= 0.0:
    raise SystemExit(
        'FAIL: final positivity check failed '
        f"pressure_min={values['pressure']:.8g} eint_min={values['eint_e']:.8g} temp_min={values['Temp']:.8g}")
print(
    'rayleigh_taylor_low_pressure_positivity PASS '
    f"pressure_min={values['pressure']:.8g} eint_min={values['eint_e']:.8g} temp_min={values['Temp']:.8g}")
PYINNER
cat "$LOG_DIR/conservation.log"
cat "$LOG_DIR/positivity.log"
echo "[codex-rayleigh-taylor-lowp] PASS log=$LOG_DIR/run.log positivity=$LOG_DIR/positivity.log plot=$FINAL"
