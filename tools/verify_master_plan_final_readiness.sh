#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_MASTER_PLAN_FINAL_REPORT:-docs/codex_audit/evidence/master_plan_final_readiness_20260731/master_plan_final_readiness_report.json}

python3 tools/write_master_plan_final_readiness_report.py --verify-json "$report"
echo "[master-plan-final] PASS final readiness report verification"
