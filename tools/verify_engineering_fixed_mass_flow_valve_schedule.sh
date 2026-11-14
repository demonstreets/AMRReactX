#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report="docs/codex_audit/evidence/engineering_fixed_mass_flow_valve_schedule_20260806/engineering_fixed_mass_flow_valve_schedule_report.json"

if [[ ! -f "$report" ]]; then
  python3 tools/write_engineering_fixed_mass_flow_valve_schedule_report.py
fi

python3 tools/write_engineering_fixed_mass_flow_valve_schedule_report.py --verify-json "$report"
