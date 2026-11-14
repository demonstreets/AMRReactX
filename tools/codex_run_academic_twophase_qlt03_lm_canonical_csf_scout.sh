#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_DIR="$ROOT/examples/academic/qlt03_lm_aux_bridge"
EVIDENCE_DIR="$ROOT/docs/codex_audit/evidence/academic_twophase_qlt03_lm_canonical_csf_scout_20260730"
RUN_DIR="$EVIDENCE_DIR/run"
LOG="$EVIDENCE_DIR/qlt03_lm_canonical_csf_scout.log"
INPUTS="$EVIDENCE_DIR/inputs"
BRIDGE_REPORT="$EVIDENCE_DIR/qlt03_lm_canonical_csf_bridge_report.json"
REPORT="$EVIDENCE_DIR/academic_twophase_qlt03_lm_canonical_csf_scout_report.json"

mkdir -p "$RUN_DIR"

python3 - <<'PYGEN'
from pathlib import Path

src = Path("examples/academic/qlt03_lm_aux_bridge/inputs")
dst = Path("docs/codex_audit/evidence/academic_twophase_qlt03_lm_canonical_csf_scout_20260730/inputs")
text = src.read_text()
repls = {
    "prob.surface_tension_sigma = 0.01": "prob.surface_tension_sigma = 24.5",
    "prob.surface_tension_force_cap = 1.0": "prob.surface_tension_force_cap = 0.0",
    "amr.max_step = 40": "amr.max_step = 160",
    "amr.cfl = 0.5": "amr.cfl = 0.2",
    "amr.plot_int = 40": "amr.plot_int = 120",
}
for old, new in repls.items():
    if old not in text:
        raise RuntimeError(f"missing QLT-03 input anchor: {old}")
    text = text.replace(old, new)
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(text)
PYGEN

(
  cd "$CASE_DIR"
  make -j "${CODEX_MAKE_JOBS:-4}" DIM=2 USE_MPI=FALSE USE_CUDA=FALSE USE_OMP=FALSE
)

rm -rf "$RUN_DIR"/plt* "$RUN_DIR"/chk* "$RUN_DIR"/Backtrace.*
(
  cd "$RUN_DIR"
  "$CASE_DIR/PeleLMeX2d.gnu.ex" "$INPUTS" > "$LOG" 2>&1
)

initial_plot=$(find "$RUN_DIR" -maxdepth 1 -type d -name "plt*" | sort | head -1)
latest_plot=$(find "$RUN_DIR" -maxdepth 1 -type d -name "plt*" | sort | tail -1)
if [[ -z "$initial_plot" || -z "$latest_plot" ]]; then
  printf "QLT-03 canonical CSF scout failed: no plotfile produced\n" >&2
  exit 3
fi

python3 "$ROOT/tools/validate_academic_twophase_qlt03_lm_aux_bridge.py" \
  --plotfile "$latest_plot" \
  --initial-plotfile "$initial_plot" \
  --log "$LOG" \
  --inputs "$INPUTS" \
  --min-time 0.1 \
  --require-field alpha \
  --output "$BRIDGE_REPORT"

python3 "$ROOT/tools/write_academic_twophase_qlt03_lm_canonical_csf_scout_report.py" \
  --repo-root "$ROOT" \
  --inputs "$INPUTS" \
  --bridge-report "$BRIDGE_REPORT" \
  --output "$REPORT"

cat "$REPORT"
