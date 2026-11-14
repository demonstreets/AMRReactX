#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

json="docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/engineering_liquefied_breach_source_contract_report.json"
python3 tools/write_engineering_liquefied_breach_source_contract_report.py --verify-json "$json"
