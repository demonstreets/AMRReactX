# Release provenance audit

Updated: 2026-07-16

This note records repository-state risks that affect reproducibility and release packaging. These findings do not invalidate the current server smoke evidence, but they mean the tree is not yet cleanly portable to another machine.

## Current check

```bash
python3 tools/check_release_provenance.py
python3 tools/check_release_provenance.py --strict
```

Latest evidence:

- Non-strict audit: `/tmp/codex_release_provenance_configurable_sundials_20260716_rerun.log`
- Strict audit: `/tmp/codex_release_provenance_configurable_sundials_strict_20260716_rerun.log`

Current result:

- Non-strict mode: `release_provenance PASS warnings=0`
- Strict mode: `release_provenance PASS warnings=0`, exits with status `0`

## Findings

- `.gitmodules` only declares `external/PeleLMeX/Submodules/AMReX-Hydro`; it does not declare tracked dependency paths for `external/PelePhysics/Submodules/amrex`, `external/PelePhysics/Submodules/sundials`, or `external/PeleLMeX/Submodules/PelePhysics`.
- `external/PelePhysics/Submodules/amrex` is a relative worktree symlink to `../../amrex`. `HEAD` still records the old absolute target until this worktree is committed.
- `external/PeleLMeX/Submodules/PelePhysics` is a relative worktree symlink to `../../PelePhysics`. `HEAD` still records the old absolute target until this worktree is committed.
- `external/PeleC/Submodules/PelePhysics` is now a relative worktree symlink to `../../PelePhysics`.
- `external/PelePhysics/Submodules/sundials` is intentionally represented in the worktree as a local CMake shim directory. `docs/codex_audit/DEPENDENCY_PROVENANCE.tsv` records this as an explicit dependency shape.
- The current SUNDIALS shim at `external/PelePhysics/Submodules/sundials/CMakeLists.txt` now requires `SUNDIALS_CUDA_DIR` or `SUNDIALS_DIR`; no machine-local CUDA SUNDIALS path is hard-coded in the checked source paths covered by the provenance gate.
- Repository-local installed SUNDIALS libraries are present under `external/PelePhysics/ThirdParty/INSTALL/gnu/lib`, but this installed tree is generated binary provenance, not a clean source dependency declaration.

## Impact

The current server can build and run the maintained smoke evidence, including CUDA smokes. CUDA SUNDIALS is now supplied explicitly through `SUNDIALS_CUDA_DIR`/`SUNDIALS_DIR`; repo-internal PeleC/PeleLMeX/PelePhysics symlinks are relative in the worktree. A fresh clone or release bundle may fail unless the same absolute paths and generated third-party install tree are recreated. This was a release blocker, not a solver-physics failure; the current worktree-level provenance gate is now strict-clean, while commit/tag discipline is still required before an actual release claim.

## Required release cleanup

1. Commit the relative symlink/worktree dependency layout so `HEAD` no longer records old absolute targets.
2. Decide whether SUNDIALS should be source-built, vendored, or documented as an external prerequisite for final release packaging.
3. Add a reproducible setup script or documented dependency lock for CPU and CUDA SUNDIALS variants.
4. Keep `python3 tools/check_release_provenance.py --strict` passing before claiming release-ready packaging.

## Relationship to smoke gates

The default full smoke gate passed after the ENG-09 BFS log-law fix at `/tmp/codex_smoke_all_post_bfs_loglaw_profile_20260716/gate.log`. After the configurable-SUNDIALS/provenance repair, PeleC CUDA passed in `/tmp/codex_pelec_cuda_after_sundials_config_20260716/validation.log`, PeleLMeX CUDA passed in `/tmp/codex_pelelmex_cuda_after_sundials_config_20260716/validation.log`, generated-YAML BFS passed in `/tmp/codex_bfs_from_yaml_after_sundials_config_20260716.log` and `/tmp/codex_bfs_profile_from_yaml_after_sundials_config_20260716.log`, and PeleLMeX CMake configure passed in `/tmp/codex_pelelmex_cmake_after_sundials_config_20260716.log`. That proves the current server state remains runnable. This provenance audit now proves that the current worktree dependency paths are clean at the configured-source level; final release still needs a commit/tag and dependency setup documentation.
