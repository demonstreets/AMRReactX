#!/usr/bin/env bash
set -euo pipefail
rank=${OMPI_COMM_WORLD_LOCAL_RANK:-${MPI_LOCALRANKID:-0}}
export CUDA_VISIBLE_DEVICES=$rank
echo "rank_gpu_wrapper: local_rank=$rank CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
exec ./solver.ex "$@"
