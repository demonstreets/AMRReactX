#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
report=${CODEX_STRICT_MASTER_PLAN_CLOSEOUT_ACTION_PACK_REPORT:-docs/codex_audit/evidence/strict_master_plan_closeout_action_pack_20260812/strict_master_plan_closeout_action_pack_report.json}

python3 tools/write_strict_master_plan_closeout_action_pack_report.py --verify-json "$report"
echo "[strict-master-plan-closeout-action-pack] PASS action pack"
