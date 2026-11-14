#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_ENGINEERING_CH4_PIPE_RACK_DELAYED_IGNITION_MPI_CUDA_REPORT:-docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_20260806/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_report.json}

python3 tools/write_engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_report.py --verify-json "$report"
echo "[engineering-ch4-pipe-rack-delayed-ignition-mpi-cuda] PASS CH4 delayed ignition rank-mapped MPI+CUDA report"
