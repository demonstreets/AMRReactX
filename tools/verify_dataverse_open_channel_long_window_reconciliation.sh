#!/usr/bin/env bash
set -euo pipefail

json=${1:-docs/codex_audit/evidence/dataverse_open_channel_long_window_reconciliation_20260811/dataverse_open_channel_long_window_reconciliation_report.json}
python3 tools/write_dataverse_open_channel_long_window_reconciliation_report.py --verify-json "$json"
