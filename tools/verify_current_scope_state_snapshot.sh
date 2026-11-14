#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_CURRENT_SCOPE_STATE_SNAPSHOT_REPORT:-docs/codex_audit/evidence/current_scope_state_snapshot_20260803/current_scope_state_snapshot_report.json}

python3 tools/write_current_scope_state_snapshot_report.py --verify-json "$report"
