# AMRReactX

AMRReactX is the working name for a research-oriented AMReX-based compressible
flow and reacting-flow solver.

The current version is a minimal AMReX/MPI smoke test. It initializes a simple
three-dimensional gas-cloud field and writes an AMReX plotfile with:

- `rho`: density
- `u`, `v`, `w`: velocity components
- `Y_leak`: leaked-gas mass-fraction-like scalar

This first program verifies the development chain:

- WSL Ubuntu 24.04
- CMake
- OpenMPI
- AMReX
- AMReX plotfile output

## Build

```bash
cmake -S . -B build \
  -DCMAKE_PREFIX_PATH=/home/demonstreets/amrex-install \
  -DCMAKE_BUILD_TYPE=Release

cmake --build build -j $(nproc)
```

## Run

```bash
mpirun -np 2 ./build/amrreactx inputs/mini_plot.in
```

The output directory is `plt_mini_leak`.
