#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_DIR="$ROOT_DIR/external/PeleC/Exec/RegTests/DoubleMachReflection"
EXE="$CASE_DIR/codex_double_mach3d.gnu.ex"
INPUT="${CODEX_DOUBLE_MACH_INPUT:-input.codex_smoke}"
LOG_DIR="${CODEX_DOUBLE_MACH_LOG_DIR:-$(mktemp -d /tmp/codex_double_mach.XXXXXX)}"
RUN_DIR="$LOG_DIR/run"
RUN_TIMEOUT="${RUN_TIMEOUT:-180}"
JOBS="${JOBS:-4}"
EXPECTED_STEP="${CODEX_DOUBLE_MACH_EXPECT_STEP:-8}"

mkdir -p "$RUN_DIR"
LOG_DIR="$(cd "$LOG_DIR" && pwd)"
RUN_DIR="$LOG_DIR/run"

pushd "$CASE_DIR" >/dev/null
make -j "$JOBS" DIM=3 Chemistry_Model=Null Eos_Model=GammaLaw USE_MPI=FALSE USE_OMP=FALSE EBASE=codex_double_mach >"$LOG_DIR/build.log" 2>&1
popd >/dev/null

test -x "$EXE"
cp "$CASE_DIR/$INPUT" "$RUN_DIR/"

pushd "$RUN_DIR" >/dev/null
timeout "$RUN_TIMEOUT" "$EXE" "$INPUT" >"$LOG_DIR/run.log" 2>&1
popd >/dev/null

if grep -q "Unused ParmParse" "$LOG_DIR/run.log"; then
  echo "[codex-double-mach] FAIL unused ParmParse variables" >&2
  exit 1
fi
grep -q "AMReX (.*) finalized" "$LOG_DIR/run.log"
grep -q "STEP = $EXPECTED_STEP" "$LOG_DIR/run.log"
PLOT="$(printf '%s/plt%05d' "$RUN_DIR" "$EXPECTED_STEP")"
test -d "$PLOT"
python3 "$ROOT_DIR/tools/validate_double_mach_plotfile.py" --plotfile "$PLOT" >"$LOG_DIR/validation.log"
cat "$LOG_DIR/validation.log"
echo "[codex-double-mach] PASS log=$LOG_DIR/run.log validation=$LOG_DIR/validation.log plot=$PLOT input=$INPUT"
