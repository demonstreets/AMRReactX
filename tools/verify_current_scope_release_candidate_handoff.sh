#!/usr/bin/env bash
set -euo pipefail

report=${1:-docs/codex_audit/evidence/current_scope_release_candidate_handoff_20260812/current_scope_release_candidate_handoff_report.json}
python3 tools/write_current_scope_release_candidate_handoff_report.py --verify-json "$report"
