#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_CURRENT_DISK_CLEANUP_PLAN_REPORT:-docs/codex_audit/evidence/current_disk_cleanup_plan_20260803/current_disk_cleanup_plan_report.json}

python3 tools/write_current_disk_cleanup_plan_report.py --verify-json "$report"
