#!/usr/bin/env bash
set -euo pipefail

ROOT="docs/codex_audit/evidence/academic_gas_detonation_single_cuda_20260803"
REPORT="${ROOT}/academic_gas_detonation_single_cuda_report.json"

python3 tools/write_academic_gas_detonation_single_cuda_report.py --verify-json "${REPORT}"
