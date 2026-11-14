#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_DIR="$ROOT_DIR/examples/academic/rayleigh_taylor"
EXE="$CASE_DIR/codex_rayleigh_taylor2d.gnu.ex"
LOG_DIR="${CODEX_RAYLEIGH_TAYLOR_NAME_LOG_DIR:-$(mktemp -d /tmp/codex_rayleigh_taylor_name.XXXXXX)}"
RUN_TIMEOUT="${RUN_TIMEOUT:-30}"
JOBS="${JOBS:-4}"

mkdir -p "$LOG_DIR"
pushd "$CASE_DIR" >/dev/null
make -j "$JOBS" DIM=2 EBASE=codex_rayleigh_taylor USE_MPI=FALSE USE_OMP=FALSE >"$LOG_DIR/build.log" 2>&1
popd >/dev/null

test -x "$EXE"
python3 - "$CASE_DIR/input.codex_growth" "$LOG_DIR" <<'PYINNER'
import re
import sys
from pathlib import Path

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text()
replacements = {
    r'^max_step\s*=.*$': 'max_step = 2',
    r'^stop_time\s*=.*$': 'stop_time = 4.0e-2',
    r'^amr\.n_cell\s*=.*$': 'amr.n_cell = 128 256 1',
    r'^amr\.plot_int\s*=.*$': 'amr.plot_int = 2',
    r'^pelec\.cfl\s*=.*$': 'pelec.cfl = 0.02',
    r'^prob\.p0\s*=.*$': 'prob.p0 = 50.0',
    r'^pelec\.sum_interval\s*=.*$': 'pelec.sum_interval = 1',
}
for pattern, value in replacements.items():
    text, count = re.subn(pattern, value, text, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f'FAIL: expected one replacement for {pattern}, got {count}')
for name in ('inputs_safe', 'input.codex_high'):
    case_dir = out / name
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / name).write_text(text)
PYINNER

run_case() {
  local name="$1"
  local expect="$2"
  local dir="$LOG_DIR/$name"
  local rc=0
  (cd "$dir" && timeout "$RUN_TIMEOUT" "$EXE" "$name" >"$LOG_DIR/${name}.log" 2>&1) || rc=$?
  local status=FAIL
  if grep -q "AMReX (.*) finalized" "$LOG_DIR/${name}.log" && grep -q "STEP = 2" "$LOG_DIR/${name}.log"; then
    status=PASS
  fi
  printf '%s\trc=%s\tstatus=%s\texpect=%s\n' "$name" "$rc" "$status" "$expect" | tee -a "$LOG_DIR/summary.tsv"
  if [[ "$status" != "$expect" ]]; then
    echo "[codex-rayleigh-taylor-input-name] unexpected result for $name" >&2
    tail -80 "$LOG_DIR/${name}.log" >&2
    return 1
  fi
}

: >"$LOG_DIR/summary.tsv"
run_case inputs_safe PASS
run_case input.codex_high PASS
cat "$LOG_DIR/summary.tsv"
echo "[codex-rayleigh-taylor-input-name] PASS regression log_dir=$LOG_DIR"
