#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_CURRENT_WORKTREE_SOURCE_LEDGER_REPORT:-docs/codex_audit/evidence/current_worktree_source_ledger_20260803/current_worktree_source_ledger_report.json}

python3 tools/write_current_worktree_source_ledger_report.py --verify-json "$report"
