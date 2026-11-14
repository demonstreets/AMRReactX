#!/usr/bin/env bash
set -euo pipefail

ROOT="docs/codex_audit/evidence/current_parallel_capability_matrix_20260803"
REPORT="${ROOT}/current_parallel_capability_matrix_report.json"

python3 tools/write_current_parallel_capability_matrix_report.py --verify-json "${REPORT}"
