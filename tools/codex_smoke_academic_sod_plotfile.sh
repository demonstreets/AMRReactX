#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_DIR="$ROOT_DIR/examples/academic/shock_droplet"
EXE="$CASE_DIR/PeleC2d.gnu.ex"
INPUT="${CODEX_SOD_INPUT:-input.codex_sod_smoke}"
LOG_DIR="${CODEX_SOD_LOG_DIR:-$(mktemp -d /tmp/codex_sod_plotfile.XXXXXX)}"
RUN_DIR="$LOG_DIR/run"
RUN_TIMEOUT="${RUN_TIMEOUT:-180}"
EXPECTED_STEP="${CODEX_SOD_EXPECT_STEP:-60}"

mkdir -p "$RUN_DIR"
if [[ ! -x "$EXE" ]]; then
  echo "[codex-sod] missing executable: $EXE" >&2
  exit 1
fi
cp "$CASE_DIR/$INPUT" "$RUN_DIR/"

pushd "$RUN_DIR" >/dev/null
timeout "$RUN_TIMEOUT" "$EXE" "$INPUT" >"$LOG_DIR/run.log" 2>&1
popd >/dev/null

if grep -q "Unused ParmParse" "$LOG_DIR/run.log"; then
  echo "[codex-sod] FAIL unused ParmParse variables" >&2
  exit 1
fi
grep -q "AMReX (.*) finalized" "$LOG_DIR/run.log"
grep -q "STEP = $EXPECTED_STEP" "$LOG_DIR/run.log"
PLOT="$(printf '%s/plt%05d' "$RUN_DIR" "$EXPECTED_STEP")"
test -d "$PLOT"
python3 "$ROOT_DIR/tools/validate_sod_plotfile.py" --plotfile "$PLOT" >"$LOG_DIR/validation.log"
cat "$LOG_DIR/validation.log"
echo "[codex-sod] PASS log=$LOG_DIR/run.log validation=$LOG_DIR/validation.log plot=$PLOT input=$INPUT"
