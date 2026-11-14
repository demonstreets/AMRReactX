#!/bin/sh
set -eu
json="${1:-docs/codex_audit/evidence/engineering_h2_real_cad_handoff_contract_20260805/real_cad_handoff_contract_report.json}"
python3 tools/write_engineering_h2_real_cad_handoff_contract_report.py --verify-json "$json"
