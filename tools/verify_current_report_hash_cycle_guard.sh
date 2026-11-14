#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_CURRENT_REPORT_HASH_CYCLE_GUARD_REPORT:-docs/codex_audit/evidence/current_report_hash_cycle_guard_20260818/current_report_hash_cycle_guard_report.json}

python3 tools/write_current_report_hash_cycle_guard_report.py
python3 tools/write_current_report_hash_cycle_guard_report.py --verify-json "$report"
echo "[current-report-hash-cycle-guard] PASS report hash-cycle guard"
