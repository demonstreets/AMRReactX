# Checkpoint: Environment preflight gate

Date: 2026-07-16
Status: PASS-SMOKE / reproducibility preflight

## Summary

Added a maintained environment preflight command for the current `my-pele` worktree. The preflight checks core tools, release provenance strict, dependency manifest shape, relative symlinks, SUNDIALS include/lib/version/library requirements, CUDA SUNDIALS libraries, `nvcc`, `nvidia-smi`, and visible GPUs.

## Changed files / modules

- `tools/codex_preflight_environment.sh`
- `docs/codex_audit/ENVIRONMENT_PREFLIGHT.md`
- `docs/codex_audit/DEPENDENCY_AUDIT.md`
- `docs/codex_audit/SMOKE_MATRIX.md`
- `docs/codex_audit/MASTER_PLAN_TRACEABILITY.md`

## Verification

```bash
bash -n tools/codex_preflight_environment.sh
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda tools/codex_preflight_environment.sh --require-cuda
SUNDIALS_CUDA_DIR=/home/cj/local/sundials-cuda tools/codex_preflight_environment.sh --require-cuda --strict-sundials-6.4
```

## Evidence

- `/tmp/codex_preflight_environment_cuda_20260716_final.log`: `preflight SUMMARY PASS warnings=0`.
- `/tmp/codex_preflight_release_provenance.log`: release provenance strict sub-check from preflight.
- `/tmp/codex_preflight_environment_strict_sundials64_20260716.log`: intentional failure showing the server has SUNDIALS `6.7.0`, not strict master-plan `6.4.0`.

## Remaining limitations

- Preflight proves toolchain/dependency readiness, not CFD physics correctness.
- The verified server SUNDIALS version is `6.7.0`; strict 6.4 remains a documented plan deviation until either the plan is revised or a 6.4 build is reproduced.
- Final release still needs commit/tag discipline and a dependency bootstrap script or external prerequisite lock.
