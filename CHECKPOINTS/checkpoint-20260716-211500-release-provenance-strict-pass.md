# Checkpoint: Release provenance strict pass

Date: 2026-07-16
Status: PASS-SMOKE / worktree-level release provenance gate

## Summary

Moved the release-provenance gate from PASS-WARN to strict PASS for the current worktree. Repo-internal PeleC/PeleLMeX/PelePhysics dependency symlinks are now relative in the worktree, SUNDIALS CUDA paths are explicit through `SUNDIALS_CUDA_DIR` or `SUNDIALS_DIR`, and the provenance checker uses `docs/codex_audit/DEPENDENCY_PROVENANCE.tsv` rather than treating non-submodule local dependencies as missing `.gitmodules` entries.

## Changed files / modules

- `external/PeleC/Submodules/PelePhysics` now points to `../../PelePhysics`.
- `external/PelePhysics/Submodules/sundials/CMakeLists.txt` no longer hard-codes `/home/cj/local/sundials-cuda`; it requires `SUNDIALS_CUDA_DIR` or `SUNDIALS_DIR`.
- `external/PeleLMeX/CMake/BuildPelePhysicsLib.cmake` no longer links hard-coded `/home/cj/local/sundials-cuda` libraries; it reads the configured SUNDIALS CUDA install path.
- `tools/codex_smoke_academic_pelec_cuda.sh` and `tools/codex_smoke_engineering_pelelmex_cuda.sh` now require/export explicit SUNDIALS CUDA configuration.
- `tools/check_release_provenance.py` now checks the current worktree dependency shape, dependency provenance manifest, and machine-local SUNDIALS path leaks.
- `docs/codex_audit/DEPENDENCY_PROVENANCE.tsv` records local dependency shapes separately from true git submodules.

## Verification

```bash
python3 -m py_compile tools/check_release_provenance.py
python3 tools/check_release_provenance.py
python3 tools/check_release_provenance.py --strict
bash -n tools/codex_smoke_academic_pelec_cuda.sh
bash -n tools/codex_smoke_engineering_pelelmex_cuda.sh
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda CODEX_PELEC_CUDA_LOG_DIR=/tmp/codex_pelec_cuda_after_sundials_config_20260716 JOBS=2 RUN_TIMEOUT=240 tools/codex_smoke_academic_pelec_cuda.sh
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda CODEX_PELELMEX_CUDA_LOG_DIR=/tmp/codex_pelelmex_cuda_after_sundials_config_20260716 JOBS=1 RUN_TIMEOUT=240 tools/codex_smoke_engineering_pelelmex_cuda.sh
CODEX_RUN_LOG=/tmp/codex_bfs_from_yaml_after_sundials_config_20260716.log CODEX_PROFILE_RUN_LOG=/tmp/codex_bfs_profile_from_yaml_after_sundials_config_20260716.log JOBS=4 RUN_TIMEOUT=120 tools/codex_smoke_engineering_pelelmex_yaml.sh
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda cmake -S external/PeleLMeX -B /tmp/codex_pelelmex_cmake_after_sundials_config_20260716 -DPELE_ENABLE_PARTICLES=OFF -DPELE_ENABLE_FCOMPARE=OFF -DPELE_DIM=2
```

## Evidence

- `/tmp/codex_release_provenance_configurable_sundials_20260716_rerun.log`: `release_provenance PASS warnings=0`.
- `/tmp/codex_release_provenance_configurable_sundials_strict_20260716_rerun.log`: strict mode PASS, exit code 0.
- `/tmp/codex_pelec_cuda_after_sundials_config_20260716/validation.log`: PeleC CUDA smoke PASS.
- `/tmp/codex_pelelmex_cuda_after_sundials_config_20260716/validation.log`: PeleLMeX CUDA smoke PASS.
- `/tmp/codex_bfs_from_yaml_after_sundials_config_20260716.log`: generated-YAML uniform BFS run finalizes.
- `/tmp/codex_bfs_profile_from_yaml_after_sundials_config_20260716.log`: generated-YAML log-law BFS run finalizes and emits `Velocity: 0.3922899764 0`.
- `/tmp/codex_pelelmex_cmake_after_sundials_config_20260716.log`: PeleLMeX CMake configure exits 0.

## Remaining limitations

- This is a current-worktree provenance pass. A real release still needs commit/tag discipline so `HEAD` no longer records the old absolute symlink targets.
- SUNDIALS remains an explicit external prerequisite; final packaging still needs a setup script or dependency lock.
- This checkpoint does not expand CFD validation coverage; it removes a reproducibility blocker while preserving existing smoke evidence.
