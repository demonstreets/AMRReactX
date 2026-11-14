#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
report=${CODEX_COMPLETE_WALKTHROUGH_GUIDE_REPORT:-docs/codex_audit/evidence/complete_walkthrough_guide_20260818/complete_walkthrough_guide_report.json}

python3 tools/write_complete_walkthrough_guide_report.py --verify-json "$report"
echo "[complete-walkthrough-guide] PASS complete walkthrough guide"
