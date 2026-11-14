#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_DATAVERSE_OPEN_CHANNEL_TIMESERIES_INDEX_REPORT:-docs/codex_audit/evidence/dataverse_open_channel_timeseries_index_20260803/dataverse_open_channel_timeseries_index_report.json}

python3 tools/write_dataverse_open_channel_timeseries_index_report.py --verify-json "$report"
echo "[dataverse-open-channel-timeseries-index] PASS timeseries index report"
