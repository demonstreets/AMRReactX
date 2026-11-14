#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_ENGINEERING_CH4_PIPE_RACK_DELAYED_IGNITION_MPI_CUDA_500STEP_REPORT:-docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_20260806/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.json}

python3 tools/write_engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.py --verify-json "$report"
echo "[engineering-ch4-pipe-rack-delayed-ignition-mpi-cuda-500step] PASS CH4 delayed ignition 500-step rank-mapped MPI+CUDA report"
