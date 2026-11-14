#!/usr/bin/env bash
set -euo pipefail
cd /home/cj/my-pele
export PATH=/usr/local/cuda-12.6/bin:/usr/local/cuda/bin:/usr/bin:/bin:/usr/local/bin
rel=docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_mpi_cuda_20260805
root=/home/cj/my-pele/$rel
echo "RUNNING $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$root/status.txt"
{
  CODEX_DATAVERSE_OPEN_CHANNEL_SCOUT_LOG_ROOT="$root" \
  CODEX_DATAVERSE_OPEN_CHANNEL_MAX_STEP=10000 \
  CODEX_DATAVERSE_OPEN_CHANNEL_PLOT_INT=1000 \
  CODEX_DATAVERSE_OPEN_CHANNEL_FIXED_DT=1.0e-4 \
  CODEX_DATAVERSE_OPEN_CHANNEL_MPI_RANKS=2 \
  CODEX_DATAVERSE_OPEN_CHANNEL_USE_CUDA=TRUE \
  CODEX_DATAVERSE_OPEN_CHANNEL_LEAK_RADIUS=0.04 \
  CODEX_DATAVERSE_OPEN_CHANNEL_LEAK_ZC=0.775 \
  CODEX_DATAVERSE_OPEN_CHANNEL_LEAK_VEL_X=656.7687631723272 \
  CODEX_DATAVERSE_OPEN_CHANNEL_LO_BC="Outflow NoSlipWallAdiab NoSlipWallAdiab" \
  CODEX_DATAVERSE_OPEN_CHANNEL_HI_BC="Outflow NoSlipWallAdiab NoSlipWallAdiab" \
  CODEX_DATAVERSE_OPEN_CHANNEL_MAX_CENTER_OFFSET=80.0 \
  CODEX_DATAVERSE_OPEN_CHANNEL_SKIP_BUILD=TRUE \
  RUN_TIMEOUT=7200 \
  JOBS=4 \
    bash tools/codex_smoke_engineering_h2_dataverse_open_channel_scout_cuda.sh

  python3 tools/write_dataverse_open_channel_cfd_scout_report.py \
    --run-log "$root/run.log" \
    --validation-log "$root/validation.log" \
    --plume-report "$root/h2_plume_observation_report.json" \
    --agreement-attempt "$root/agreement_attempt_status.json" \
    --input "$root/input.dataverse_open_channel_h2_scout_3d" \
    --sensors "$root/sensors.dataverse_open_channel_solver_coords.json" \
    --output-json "$root/dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_report.json" \
    --output-md "$root/dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_report.md"

  python3 tools/write_dataverse_open_channel_cfd_scout_report.py \
    --verify-json "$root/dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_report.json"

  echo "DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$root/status.txt"
} > "$root/background.log" 2>&1 || {
  rc=$?
  echo "FAILED $rc $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$root/status.txt"
  exit "$rc"
}
