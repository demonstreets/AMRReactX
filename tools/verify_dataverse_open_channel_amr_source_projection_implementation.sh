#!/usr/bin/env bash
set -euo pipefail

json=${1:-docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_implementation_20260811/dataverse_open_channel_amr_source_projection_implementation_report.json}
python3 tools/write_dataverse_open_channel_amr_source_projection_implementation_report.py --verify-json "$json"
