#!/bin/sh
set -eu
json="${1:-docs/codex_audit/evidence/current_scope_final_handoff_note_20260812/current_scope_final_handoff_note_report.json}"
python3 tools/write_current_scope_final_handoff_note_report.py --verify-json "$json"
