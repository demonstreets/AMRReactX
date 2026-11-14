# Stale generated directory

This directory is not a maintained CPU detonation case.

Observed on 2026-07-15:

- `GNUmakefile` is a broken symlink to missing `GNUmakefile.cpu`.
- The only generated build tree is `3d.gnu.MPI.CUDA.EXE`, so the directory name does not match the stored artifacts.
- No source files or inputs are present here.

Use `../detonation_2D` plus `inputs.codex_smoke` for the maintained PeleC CPU smoke baseline.

Do not include this directory in automated build discovery until it is either repaired with real source/input files or removed from the repository.
