#!/usr/bin/env bash
# Source this script before CUDA builds that need PelePhysics/SUNDIALS.
set -euo pipefail

cuda_root=${CUDA_ROOT:-/usr/local/cuda-12.6}
sundials_cuda_root=${SUNDIALS_CUDA_DIR:-${HOME}/.local/sundials-cuda-6.4.1}

if [[ ! -x "${cuda_root}/bin/nvcc" ]]; then
  echo "CUDA toolkit not found or nvcc is not executable: ${cuda_root}/bin/nvcc" >&2
  return 1 2>/dev/null || exit 1
fi
if [[ ! -d "${sundials_cuda_root}/include" || ! -d "${sundials_cuda_root}/lib" ]]; then
  echo "SUNDIALS CUDA install is incomplete: ${sundials_cuda_root}" >&2
  return 1 2>/dev/null || exit 1
fi

export CUDA_HOME="${cuda_root}"
export CUDA_PATH="${cuda_root}"
export PATH="${cuda_root}/bin:${PATH}"
export SUNDIALS_CUDA_DIR="${sundials_cuda_root}"
export SUNDIALS_LIB_DIR="${sundials_cuda_root}/lib"
export LD_LIBRARY_PATH="${sundials_cuda_root}/lib:${cuda_root}/lib64:${LD_LIBRARY_PATH:-}"
