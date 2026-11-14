#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_MASTER_PLAN_STRICT_REAL_CAD_UPDATE_REPORT:-docs/codex_audit/evidence/master_plan_strict_real_cad_update_20260731/master_plan_strict_real_cad_update_report.json}

python3 tools/write_master_plan_strict_real_cad_update_report.py --verify-json "$report"
echo "[master-plan-strict-real-cad] PASS strict real-CAD update report"
