#!/bin/sh
set -eu
json="${1:-docs/codex_audit/evidence/h2_fire_mdpi_radiation_screening_comparison_20260805/h2_fire_mdpi_radiation_screening_comparison_report.json}"
python3 tools/write_h2_fire_mdpi_radiation_screening_comparison_report.py --verify-json "$json"
