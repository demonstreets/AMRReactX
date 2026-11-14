#!/usr/bin/env bash
set -euo pipefail

json=${1:-docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/engineering_c3h8_gas_phase_cpu_cuda_report.json}
python3 tools/write_engineering_c3h8_gas_phase_cpu_cuda_report.py --verify-json "$json"
