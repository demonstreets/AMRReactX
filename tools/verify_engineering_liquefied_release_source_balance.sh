#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_ENGINEERING_LIQUEFIED_RELEASE_SOURCE_BALANCE_REPORT:-docs/codex_audit/evidence/engineering_liquefied_release_source_balance_20260807/engineering_liquefied_release_source_balance_report.json}

python3 tools/write_engineering_liquefied_release_source_balance_report.py --verify-json "$report"
