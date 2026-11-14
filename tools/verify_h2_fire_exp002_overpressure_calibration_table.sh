#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

json="docs/codex_audit/evidence/h2_fire_exp002_overpressure_calibration_table_20260805/h2_fire_exp002_overpressure_calibration_table_report.json"

python3 tools/write_h2_fire_exp002_overpressure_calibration_table_report.py --verify-json "$json"
