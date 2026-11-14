#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_DIR="$ROOT_DIR/examples/academic/rayleigh_taylor"
EXE="$CASE_DIR/codex_rayleigh_taylor2d.gnu.ex"
INPUT="${CODEX_RAYLEIGH_TAYLOR_INPUT:-input.codex_smoke}"
LOG_DIR="${CODEX_RAYLEIGH_TAYLOR_LOG_DIR:-$(mktemp -d /tmp/codex_rayleigh_taylor.XXXXXX)}"
RUN_DIR="$LOG_DIR/run"
RUN_TIMEOUT="${RUN_TIMEOUT:-180}"
JOBS="${JOBS:-4}"
EXPECTED_STEP="${CODEX_RAYLEIGH_TAYLOR_EXPECT_STEP:-50}"

mkdir -p "$RUN_DIR"
pushd "$CASE_DIR" >/dev/null
make -j "$JOBS" DIM=2 EBASE=codex_rayleigh_taylor USE_MPI=FALSE USE_OMP=FALSE >"$LOG_DIR/build.log" 2>&1
popd >/dev/null

test -x "$EXE"
cp "$CASE_DIR/$INPUT" "$RUN_DIR/"
pushd "$RUN_DIR" >/dev/null
timeout "$RUN_TIMEOUT" "$EXE" "$INPUT" >"$LOG_DIR/run.log" 2>&1
popd >/dev/null

if grep -q "Unused ParmParse" "$LOG_DIR/run.log"; then
  echo "[codex-rayleigh-taylor] FAIL unused ParmParse variables" >&2
  exit 1
fi
grep -q "AMReX (.*) finalized" "$LOG_DIR/run.log"
grep -q "STEP = $EXPECTED_STEP" "$LOG_DIR/run.log"
INITIAL="$RUN_DIR/plt00000"
FINAL="$(printf '%s/plt%05d' "$RUN_DIR" "$EXPECTED_STEP")"
test -d "$INITIAL"
test -d "$FINAL"
python3 "$ROOT_DIR/tools/validate_rayleigh_taylor_plotfile.py" \
  --initial "$INITIAL" --final "$FINAL" >"$LOG_DIR/validation.log"
cat "$LOG_DIR/validation.log"
echo "[codex-rayleigh-taylor] PASS log=$LOG_DIR/run.log validation=$LOG_DIR/validation.log plot=$FINAL input=$INPUT"
