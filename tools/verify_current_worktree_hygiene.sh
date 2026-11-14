#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_CURRENT_WORKTREE_HYGIENE_REPORT:-docs/codex_audit/evidence/current_worktree_hygiene_20260803/current_worktree_hygiene_report.json}

python3 tools/write_current_worktree_hygiene_report.py --verify-json "$report"
