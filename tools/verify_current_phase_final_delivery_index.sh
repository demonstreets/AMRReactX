#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
report=${CODEX_CURRENT_PHASE_FINAL_DELIVERY_INDEX_REPORT:-docs/codex_audit/evidence/current_phase_final_delivery_index_20260812/current_phase_final_delivery_index_report.json}

python3 tools/write_current_phase_final_delivery_index_report.py --verify-json "$report"
echo "[current-phase-final-delivery-index] PASS final delivery index"
