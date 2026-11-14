#!/bin/bash
# Phase 4 GPU build config — PeleLMeX + CUDA for Tesla P100
export PATH=$HOME/local/cuda-12.6/bin:$PATH
export LD_LIBRARY_PATH=$HOME/local/sundials-cuda/lib:$LD_LIBRARY_PATH
cd ~/my-pele
mkdir -p build-gpu && cd build-gpu
cmake ../external/PeleLMeX \
  -DPELE_DIM=3 -DPELE_ENABLE_CUDA=ON -DPELE_ENABLE_MPI=OFF \
  -DPELE_ENABLE_OPENMP=OFF -DPELE_ENABLE_EB=ON -DPELE_ENABLE_PARTICLES=OFF \
  -DCMAKE_CUDA_ARCHITECTURES=60 \
  -DCMAKE_CUDA_COMPILER=$HOME/local/cuda-12.6/bin/nvcc \
  -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DCMAKE_CXX_FLAGS="-I$HOME/local/sundials-cuda/include" \
  -DCMAKE_CUDA_FLAGS="-I$HOME/local/sundials-cuda/include"
make -j8
