#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report='docs/codex_audit/evidence/academic_gas_liquid_detonation_mpi_cuda_extended_20260803/academic_gas_liquid_detonation_mpi_cuda_extended_report.json'

printf '[academic-gas-liquid-mpi-cuda-extended] verify report\n'
if [[ ! -f "$report" ]]; then
  printf '[academic-gas-liquid-mpi-cuda-extended] FAIL missing report: %s\n' "$report" >&2
  exit 1
fi

python3 tools/write_academic_gas_liquid_detonation_mpi_cuda_extended_report.py --verify-json "$report"
printf '[academic-gas-liquid-mpi-cuda-extended] PASS\n'
