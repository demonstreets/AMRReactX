#!/usr/bin/env bash
set -euo pipefail
rank=${OMPI_COMM_WORLD_LOCAL_RANK:-${MV2_COMM_WORLD_LOCAL_RANK:-0}}
export CUDA_VISIBLE_DEVICES=$rank
echo "rank_gpu_wrapper: local_rank=$rank CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES" >&2
exec ./codex_ch4_leak_fuel_species_mpicuda_probe3d.gnu.MPI.CUDA.ex input.codex_ch4_pipe_rack_delayed_ignition_mpi_cuda_rankmapped_120step
