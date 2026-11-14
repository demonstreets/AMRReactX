#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_DIR="$ROOT/examples/academic/vof_advection_1D"
EXE="$CASE_DIR/PeleC2d.gnu.ex"
INPUT_NAME="${CODEX_VOF_INPUT:-input.codex_smoke}"
INPUT="$CASE_DIR/$INPUT_NAME"
EXPECTED_STEP="${CODEX_VOF_EXPECT_STEP:-10}"
LOG_DIR="${CODEX_VOF_LOG_DIR:-/tmp/codex_vof_advection_smoke_$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$LOG_DIR"
RUN_DIR="$(mktemp -d "$LOG_DIR/run.XXXXXX")"
LOG="$LOG_DIR/run.log"

cp "$INPUT" "$RUN_DIR/$INPUT_NAME"

if [[ ! -x "$EXE" ]]; then
  echo "[codex-vof] missing executable: $EXE" >&2
  echo "[codex-vof] build it in $CASE_DIR with: make -j ${JOBS:-2}" >&2
  exit 2
fi

(
  cd "$RUN_DIR"
  "$EXE" "$INPUT_NAME"
) | tee "$LOG"

grep -q "STEP = $EXPECTED_STEP" "$LOG"
grep -q "AMReX .* finalized" "$LOG"
if grep -q "Unused ParmParse Variables" "$LOG"; then
  echo "[codex-vof] unexpected unused ParmParse variables" >&2
  exit 3
fi

latest_plot="$(find "$RUN_DIR" -maxdepth 1 -type d -name 'plt*' | sort | tail -1)"
if [[ -z "$latest_plot" ]]; then
  echo "[codex-vof] no plotfile was produced" >&2
  exit 4
fi
if [[ ! -f "$latest_plot/Header" || ! -f "$latest_plot/Level_0/Cell_H" ]]; then
  echo "[codex-vof] incomplete plotfile: $latest_plot" >&2
  exit 5
fi
grep -q "rho_adv_0" "$latest_plot/Header"

echo "[codex-vof] PASS log=$LOG run=$(basename "$RUN_DIR") plot=$(basename "$latest_plot") step=$EXPECTED_STEP input=$INPUT_NAME"
