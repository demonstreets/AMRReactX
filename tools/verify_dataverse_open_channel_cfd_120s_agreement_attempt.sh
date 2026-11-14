#!/usr/bin/env bash
set -euo pipefail

ROOT="docs/codex_audit/evidence/dataverse_open_channel_cfd_120s_peak_window_mpi_cuda_20260804"
REPORT="${ROOT}/dataverse_open_channel_cfd_agreement_attempt_report.json"

python3 tools/write_dataverse_open_channel_cfd_agreement_attempt_report.py \
  --simulation-long-csv "${ROOT}/sensor_timeseries.csv" \
  --plume-report "${ROOT}/h2_plume_observation_report.json" \
  --validation-log "${ROOT}/validation.log" \
  --run-log "${ROOT}/run.log" \
  --input "${ROOT}/input.dataverse_open_channel_h2_scout_3d" \
  --output-json "${REPORT}" \
  --output-md "${ROOT}/dataverse_open_channel_cfd_agreement_attempt_report.md"

python3 tools/write_dataverse_open_channel_cfd_agreement_attempt_report.py \
  --verify-json "${REPORT}"
