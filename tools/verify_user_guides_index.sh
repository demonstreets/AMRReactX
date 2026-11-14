#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
report=${CODEX_USER_GUIDES_INDEX_REPORT:-docs/codex_audit/evidence/user_guides_index_20260818/user_guides_index_report.json}

python3 tools/write_user_guides_index_report.py --verify-json "$report"
echo "[user-guides-index] PASS user guides index"
