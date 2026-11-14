#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report='docs/codex_audit/evidence/academic_current_priority_scope_20260731/academic_current_priority_scope_report.json'

python3 tools/write_academic_current_priority_scope_report.py --output "$report"
python3 tools/write_academic_current_priority_scope_report.py --verify-json "$report"

printf '[academic-current-priority] PASS academic current priority scope\n'
