#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_MASTER_PLAN_COMPLETION_AUDIT_REPORT:-docs/codex_audit/evidence/master_plan_completion_audit_20260803/master_plan_completion_audit_report.json}

python3 tools/write_master_plan_completion_audit_report.py --verify-json "$report"
