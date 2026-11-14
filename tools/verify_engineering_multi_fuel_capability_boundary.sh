#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_ENGINEERING_MULTI_FUEL_CAPABILITY_BOUNDARY_REPORT:-docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/engineering_multi_fuel_capability_boundary_report.json}

python3 tools/write_engineering_multi_fuel_capability_boundary_report.py --verify-json "$report"
echo "[engineering-multi-fuel-capability-boundary] PASS capability boundary report"
