# Checkpoint: Release provenance relative symlink repair

Date: 2026-07-16
Status: PARTIAL / release portability still blocked

## Summary

Converted two repo-internal worktree dependency symlinks from machine-absolute targets to relative targets and updated the release provenance checker so equivalent relative worktree symlinks are reported as INFO instead of new warnings. The audit warning count dropped from 11 to 9. Strict provenance still fails, so this is a risk reduction checkpoint, not a release-ready claim.

## Changed files / modules

- `external/PelePhysics/Submodules/amrex` now points to `../../amrex` in the worktree.
- `external/PeleLMeX/Submodules/PelePhysics` now points to `../../PelePhysics` in the worktree.
- `tools/check_release_provenance.py` accepts equivalent relative worktree symlinks while still warning that `HEAD` records absolute targets.
- `docs/codex_audit/RELEASE_PROVENANCE.md`, `docs/codex_audit/SMOKE_MATRIX.md`, and `docs/codex_audit/MASTER_PLAN_TRACEABILITY.md` record the latest 9-warning state.

## Verification

```bash
python3 tools/check_release_provenance.py
python3 tools/check_release_provenance.py --strict
python3 -m py_compile tools/check_release_provenance.py
bash -n tools/codex_smoke_engineering_pelelmex_yaml.sh
CODEX_RUN_LOG=/tmp/codex_bfs_from_yaml_after_relative_symlinks_20260716.log CODEX_PROFILE_RUN_LOG=/tmp/codex_bfs_profile_from_yaml_after_relative_symlinks_20260716.log JOBS=4 RUN_TIMEOUT=120 tools/codex_smoke_engineering_pelelmex_yaml.sh
```

## Evidence

- `/tmp/codex_release_provenance_after_relative_symlinks_20260716.log`: `release_provenance PASS-WARN warnings=9`.
- `/tmp/codex_release_provenance_after_relative_symlinks_strict_20260716.log`: strict mode exits nonzero as intended while warnings remain.
- `/tmp/codex_bfs_from_yaml_after_relative_symlinks_20260716.log`: generated-YAML uniform BFS run finalizes.
- `/tmp/codex_bfs_profile_from_yaml_after_relative_symlinks_20260716.log`: generated-YAML log-law BFS run finalizes and emits `Velocity: 0.3922899764 0`.

## Remaining limitations

- `.gitmodules` is incomplete for tracked dependency paths.
- `HEAD` still records absolute symlink targets until the dependency layout is normalized in version control.
- `external/PelePhysics/Submodules/sundials` is tracked as a symlink-like entry but the worktree contains a directory.
- The SUNDIALS CUDA shim still hard-codes `/home/cj/local/sundials-cuda`.
- `tools/check_release_provenance.py --strict` must pass before any release-portability claim.
