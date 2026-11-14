#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_STRICT_UNBLOCK_COMMAND_INVENTORY_REPORT:-docs/codex_audit/evidence/strict_unblock_command_inventory_20260803/strict_unblock_command_inventory_report.json}

python3 tools/write_strict_unblock_command_inventory_report.py --verify-json "$report"
