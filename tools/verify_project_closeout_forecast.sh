#!/bin/sh
set -eu
json="${1:-docs/codex_audit/evidence/project_closeout_forecast_20260812/project_closeout_forecast_report.json}"
python3 tools/write_project_closeout_forecast_report.py --verify-json "$json"
