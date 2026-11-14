#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_CURRENT_SCOPE_OPERATOR_RUNBOOK_REPORT:-docs/codex_audit/evidence/current_scope_operator_runbook_20260803/current_scope_operator_runbook_report.json}

python3 tools/write_current_scope_operator_runbook_report.py --verify-json "$report"
