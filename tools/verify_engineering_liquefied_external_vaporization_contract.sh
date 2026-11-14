#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report="docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/engineering_liquefied_external_vaporization_contract_report.json"

if [[ ! -f "$report" ]]; then
  python3 tools/write_engineering_liquefied_external_vaporization_contract_report.py
fi

python3 tools/write_engineering_liquefied_external_vaporization_contract_report.py --verify-json "$report"
