#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_CURRENT_OPERATOR_COMMAND_INVENTORY_REPORT:-docs/codex_audit/evidence/current_operator_command_inventory_20260803/current_operator_command_inventory_report.json}

python3 tools/write_current_operator_command_inventory_report.py --verify-json "$report"
