#!/bin/bash
export CUDA_VISIBLE_DEVICES=1
: "${SUNDIALS_CUDA_DIR:=${SUNDIALS_DIR:-}}"
: "${CUDA_HOME:=/usr/local/cuda}"
if [ -n "$SUNDIALS_CUDA_DIR" ]; then
  export LD_LIBRARY_PATH="$SUNDIALS_CUDA_DIR/lib:$CUDA_HOME/targets/x86_64-linux/lib:${LD_LIBRARY_PATH:-}"
else
  export LD_LIBRARY_PATH="$CUDA_HOME/targets/x86_64-linux/lib:${LD_LIBRARY_PATH:-}"
fi
./PeleLMeX2d.gnu.CUDA.ex inputs.2d
