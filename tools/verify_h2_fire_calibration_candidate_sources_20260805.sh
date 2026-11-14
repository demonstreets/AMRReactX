#!/usr/bin/env bash
set -euo pipefail

report=${1:-docs/codex_audit/evidence/h2_fire_calibration_candidate_sources_20260805/h2_fire_calibration_candidate_sources_report.json}
python3 tools/write_h2_fire_calibration_candidate_sources_20260805_report.py --verify-json "$report"
