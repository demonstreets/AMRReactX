#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_MASTER_PLAN_FULL_REPRO_REPORT:-docs/codex_audit/evidence/master_plan_full_reproducibility_20260731/master_plan_full_reproducibility_report.json}

python3 tools/write_master_plan_full_reproducibility_report.py --verify-json "$report"
echo "[master-plan-full-repro] PASS full reproducibility report verification"
