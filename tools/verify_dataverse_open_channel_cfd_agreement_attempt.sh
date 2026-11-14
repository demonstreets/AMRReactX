#!/usr/bin/env bash
set -euo pipefail

ROOT="docs/codex_audit/evidence/dataverse_open_channel_cfd_agreement_window_mpi_cuda_20260803"
REPORT="${ROOT}/dataverse_open_channel_cfd_agreement_attempt_report.json"

python3 tools/write_dataverse_open_channel_cfd_agreement_attempt_report.py --verify-json "${REPORT}"
