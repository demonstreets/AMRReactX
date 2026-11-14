#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_CURRENT_STATUS_CLI_REPORT:-docs/codex_audit/evidence/current_status_cli_20260803/current_status_cli_report.json}

python3 tools/write_current_status_cli_report.py --verify-json "$report"
