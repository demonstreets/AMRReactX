#!/usr/bin/env bash
set -euo pipefail
json="${1:-docs/codex_audit/evidence/project_closeout_acceptance_gate_20260812/project_closeout_acceptance_gate_report.json}"
python3 tools/write_project_closeout_acceptance_gate_report.py --verify-json "$json"
