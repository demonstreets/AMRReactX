# Dependency audit

Updated: 2026-07-16

This document records the current dependency layout under `/home/cj/my-pele`. It is intentionally descriptive: the external tree is dirty and symlink-heavy, so large dependency surgery should be staged after smoke coverage is stable.

## Current facts

The dependency audit can be regenerated with:

```bash
tools/codex_audit_dependencies.sh > /tmp/codex_dependency_audit_$(date -u +%Y%m%dT%H%M%SZ).log
```

Most recent evidence:

- `/tmp/codex_dependency_audit_20260715.log`
- `/tmp/codex_preflight_environment_cuda_20260716_final.log`
- `/tmp/codex_release_provenance_final_strict_20260716.log`

Observed external roots:

| Path | Resolved path | HEAD | Dirty entries | Note |
| --- | --- | --- | --- | --- |
| `external/amrex` | `/home/cj/my-pele/external/amrex` | `0ec1056ff13bba9ee4062713938d55a75efc93dd` | 60 | Local shared worktree, not an independent submodule checkout. |
| `external/PelePhysics` | `/home/cj/my-pele/external/PelePhysics` | `0ec1056ff13bba9ee4062713938d55a75efc93dd` | 60 | Local shared worktree view. |
| `external/PeleC` | `/home/cj/my-pele/external/PeleC` | `0ec1056ff13bba9ee4062713938d55a75efc93dd` | 60 | Local shared worktree view. |
| `external/PeleLMeX` | `/home/cj/my-pele/external/PeleLMeX` | `0ec1056ff13bba9ee4062713938d55a75efc93dd` | 60 | Local shared worktree view. |
| `external/PeleLMeX/Submodules/AMReX-Hydro` | same path | `9446740c59feca3bf007a6e6d95a6080816c33ec` | 0 | Actual gitlink/submodule-like checkout. |

Important symlinks and local dependency declarations:

- `external/PeleC/Submodules/PelePhysics -> ../../PelePhysics`
- `external/PeleLMeX/Submodules/PelePhysics -> ../../PelePhysics`
- `external/PelePhysics/Submodules/amrex -> ../../amrex`
- `external/PelePhysics/Submodules/sundials` is now a local CMake shim directory requiring `SUNDIALS_CUDA_DIR` or `SUNDIALS_DIR`.
- `docs/codex_audit/DEPENDENCY_PROVENANCE.tsv` records these dependency shapes separately from real git submodules.

## Release risks

- The main external components are still a shared dirty local worktree state, not clean independent release pins. A release commit/tag is still required.
- `.gitmodules` currently only covers `external/PeleLMeX/Submodules/AMReX-Hydro`; non-submodule local dependencies are now explicitly documented in `docs/codex_audit/DEPENDENCY_PROVENANCE.tsv`.
- `external/PelePhysics/ThirdParty/INSTALL/gnu/lib` contains many symlinks to `/home/cj/.local/lib`. Current CUDA smokes use the explicit `SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda` install instead; this external prerequisite must be documented or bootstrapped for release packaging.
- `examples/academic/deton_cpu_build/GNUmakefile` is a broken symlink to missing `GNUmakefile.cpu`; the directory contains stale CUDA/MPI object output and should not be treated as a maintained CPU case.
- `external/PeleLMeX_BAK_20260708` is a backup tree under `external`; scripts and audits should avoid treating it as a live dependency.

## Current policy

- Keep smoke scripts using repository-relative source paths.
- Do not rely on `/tmp/PeleC_clean` or other transient absolute source paths.
- Treat `deton_cpu_build` as stale until repaired or removed.
- Before a release claim, commit the relative symlink/configurable dependency layout and add a dependency bootstrap script or external prerequisite lock.
- Run `SUNDIALS_CUDA_DIR=<install> tools/codex_preflight_environment.sh --require-cuda` before CUDA smokes on a new machine.

## Newly observed build artifact risk - 2026-07-15

- `external/amrex/build/lib/cmake/AMReX/AMReXTargets.cmake` imports `AMReX::amrex_3d` from stale absolute path `/home/demonstreets/projects/amrex-development/build/Src/libamrex_3d.a`, which does not exist on this server. The EB2/STL smoke therefore links the actual local archive at `external/amrex/build/Src/libamrex_3d.a` directly. Before release packaging, regenerate or remove stale AMReX CMake package files.

## Build-system fix - 2026-07-15

- `external/PeleLMeX/Exec/Make.PeleLMeX` now adds AMReX `Src/EB/Make.package` when `USE_EB=TRUE`. Before this fix, rebuilding `EB_FlowPastCylinder` failed at link time with undefined `EBFArrayBoxFactory`, `EBDataCollection`, `EBCellFlagFab`, and `MultiCutFab` symbols even though an old executable was present. Evidence: failing `/tmp/codex_engineering_eb_build_20260715.log`; passing `/tmp/codex_engineering_eb_build_fixed_20260715.log`.

## Environment preflight - 2026-07-16

- Added `tools/codex_preflight_environment.sh` as a fast reproducibility gate for the current worktree.
- Passing evidence: `/tmp/codex_preflight_environment_cuda_20260716_final.log` reports `preflight SUMMARY PASS warnings=0`.
- The script checks release provenance strict, dependency manifest shape, core build tools, SUNDIALS headers/libs, CUDA SUNDIALS libraries, `nvcc`, `nvidia-smi`, and visible GPUs when `--require-cuda` is used.
- Version evidence: current validated server configuration is SUNDIALS `6.7.0`, CUDA toolkit `12.6.85`, and Tesla P100 compute capability `6.0`. This is a documented deviation from the master-plan text that mentioned strict SUNDIALS 6.4.
