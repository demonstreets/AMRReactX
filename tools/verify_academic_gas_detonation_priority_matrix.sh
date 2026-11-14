#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report='docs/codex_audit/evidence/academic_gas_detonation_priority_matrix_20260731/academic_gas_detonation_priority_matrix_report.json'

python3 tools/write_academic_gas_detonation_priority_matrix_report.py --output "$report"
python3 tools/write_academic_gas_detonation_priority_matrix_report.py --verify-json "$report"

printf '[academic-gas-detonation-priority] PASS gas detonation priority matrix\n'
