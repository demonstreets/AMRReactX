#!/bin/sh
set -eu
json="${1:-docs/codex_audit/evidence/strict_master_plan_completion_gate_20260812/strict_master_plan_completion_gate_report.json}"
python3 tools/write_strict_master_plan_completion_gate_report.py --verify-json "$json"
