#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_DIR="$ROOT/examples/academic/qlt03_lm_aux_bridge"
EVIDENCE_DIR="$ROOT/docs/codex_audit/evidence/academic_twophase_qlt03_lm_aux_bridge_smoke_20260730"
RUN_DIR="$EVIDENCE_DIR/run"
LOG="$EVIDENCE_DIR/qlt03_lm_aux_bridge_smoke.log"
REPORT="$EVIDENCE_DIR/academic_twophase_qlt03_lm_aux_bridge_smoke_report.json"

mkdir -p "$RUN_DIR"

(
  cd "$CASE_DIR"
  make -j "${CODEX_MAKE_JOBS:-4}" DIM=2 USE_MPI=FALSE USE_CUDA=FALSE USE_OMP=FALSE
)

rm -rf "$RUN_DIR"/plt* "$RUN_DIR"/chk* "$RUN_DIR"/Backtrace.*
(
  cd "$RUN_DIR"
  "$CASE_DIR/PeleLMeX2d.gnu.ex" "$CASE_DIR/inputs" > "$LOG" 2>&1
)

initial_plot=$(find "$RUN_DIR" -maxdepth 1 -type d -name "plt*" | sort | head -1)
latest_plot=$(find "$RUN_DIR" -maxdepth 1 -type d -name "plt*" | sort | tail -1)
if [[ -z "$initial_plot" || -z "$latest_plot" ]]; then
  printf "QLT-03 LM aux bridge smoke failed: no plotfile produced\n" >&2
  exit 3
fi

python3 "$ROOT/tools/validate_academic_twophase_qlt03_lm_aux_bridge.py" \
  --plotfile "$latest_plot" \
  --initial-plotfile "$initial_plot" \
  --log "$LOG" \
  --inputs "$CASE_DIR/inputs" \
  --min-time 0.1 \
  --require-field alpha \
  --output "$REPORT"

cat "$REPORT"
