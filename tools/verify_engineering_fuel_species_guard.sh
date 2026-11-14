#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_ENGINEERING_FUEL_SPECIES_GUARD_REPORT:-docs/codex_audit/evidence/engineering_fuel_species_guard_20260806/engineering_fuel_species_guard_report.json}

python3 tools/write_engineering_fuel_species_guard_report.py --verify-json "$report"
echo "[engineering-fuel-species-guard] PASS fuel species guard report"
