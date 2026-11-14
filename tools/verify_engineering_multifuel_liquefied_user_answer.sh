#!/usr/bin/env bash
set -euo pipefail

report=${1:-docs/codex_audit/evidence/engineering_multifuel_liquefied_user_answer_20260811/engineering_multifuel_liquefied_user_answer_report.json}
python3 tools/write_engineering_multifuel_liquefied_user_answer_report.py --verify-json "$report"
