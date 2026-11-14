#!/usr/bin/env bash
set -euo pipefail

report=${1:-docs/codex_audit/evidence/current_scenario_readiness_matrix_20260805/current_scenario_readiness_matrix_report.json}
python3 tools/write_current_scenario_readiness_matrix_report.py --verify-json "$report"
