#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_MASTER_PLAN_STRICT_EXTERNAL_SOURCE_UPDATE_REPORT:-docs/codex_audit/evidence/master_plan_strict_external_source_update_20260731/master_plan_strict_external_source_update_report.json}

python3 tools/write_master_plan_strict_external_source_update_report.py --verify-json "$report"
echo "[master-plan-strict-external-source] PASS strict external source update report"
