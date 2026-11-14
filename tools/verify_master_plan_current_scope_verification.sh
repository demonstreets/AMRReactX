#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_MASTER_PLAN_CURRENT_SCOPE_VERIFICATION_REPORT:-docs/codex_audit/evidence/master_plan_current_scope_verification_20260731/master_plan_current_scope_verification_report.json}

python3 tools/write_master_plan_current_scope_verification_report.py --verify-json "$report"
echo "[master-plan-current-scope] PASS current-scope verification report"
