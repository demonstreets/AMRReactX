#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_ENGINEERING_MULTI_FUEL_OPERATOR_RUNBOOK_REPORT:-docs/codex_audit/evidence/engineering_multi_fuel_operator_runbook_20260806/engineering_multi_fuel_operator_runbook_report.json}

python3 tools/write_engineering_multi_fuel_operator_runbook_report.py --verify-json "$report"
echo "[engineering-multi-fuel-operator-runbook] PASS operator runbook report"
