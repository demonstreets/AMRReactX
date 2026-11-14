#!/usr/bin/env bash
set -euo pipefail

json=${1:-docs/codex_audit/evidence/engineering_liquefied_release_thermal_plausibility_20260811/engineering_liquefied_release_thermal_plausibility_report.json}
python3 tools/write_engineering_liquefied_release_thermal_plausibility_report.py --verify-json "$json"
