#!/usr/bin/env bash
set -euo pipefail

report=${1:-docs/codex_audit/evidence/h2_fire_calibration_residual_budget_20260811/h2_fire_calibration_residual_budget_report.json}
python3 tools/write_h2_fire_calibration_residual_budget_report.py --verify-json "$report"
