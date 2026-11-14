#!/usr/bin/env bash
set -euo pipefail

REPORT="docs/codex_audit/evidence/dataverse_open_channel_45s_calibration_sweep_20260804/dataverse_open_channel_45s_calibration_sweep_report.json"

python3 tools/write_dataverse_open_channel_45s_calibration_sweep_report.py
python3 tools/write_dataverse_open_channel_45s_calibration_sweep_report.py --verify-json "${REPORT}"
