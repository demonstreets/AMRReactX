#!/usr/bin/env bash
set -euo pipefail

json="docs/codex_audit/evidence/current_worktree_review_queue_20260820/current_worktree_review_queue_report.json"
python3 tools/write_current_worktree_review_queue_report.py --verify-json "$json"
echo "[current-worktree-review-queue] PASS"
