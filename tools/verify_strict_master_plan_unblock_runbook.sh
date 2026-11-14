#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_STRICT_MASTER_PLAN_UNBLOCK_RUNBOOK_REPORT:-docs/codex_audit/evidence/strict_master_plan_unblock_runbook_20260803/strict_master_plan_unblock_runbook_report.json}

python3 tools/write_strict_master_plan_unblock_runbook_report.py --verify-json "$report"
