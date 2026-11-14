# Checkpoint: QLT-03 PeleLMeX PeriodicCases CoVo self-convergence

Date: 2026-07-16
Status: PASS-SMOKE / PARTIAL-QLT-03

## Summary

Added a targeted PeleLMeX smooth-flow validation slice using `external/PeleLMeX/Exec/RegTests/PeriodicCases` with the convected-vortex (`CoVo`) setup. The smoke builds/runs 16x16, 32x32, and 64x64 periodic cases, strips known unused legacy input keys, enforces `amrex.abort_on_unused_inputs = 1`, and validates velocity-field self-convergence by comparing coarse fields against volume-restricted fine fields.

This improves QLT-03 from PeleC-only smooth-flow convergence evidence to include a maintained PeleLMeX solver-coupled smooth-flow self-convergence case. It does not claim exact-solution or MMS validation.

## Changed files / modules

- `tools/codex_smoke_engineering_pelelmex_periodic_covo.sh`
- `tools/validate_pelelmex_periodic_covo_self_convergence.py`
- `docs/codex_audit/SMOKE_MATRIX.md`
- `docs/codex_audit/MASTER_PLAN_TRACEABILITY.md`
- `CHECKPOINTS/checkpoint-20260716-173000-qlt03-pelelmex-periodic-covo-self-convergence.md`

## Verification

- `python3 -m py_compile tools/validate_pelelmex_periodic_covo_self_convergence.py`
- `bash -n tools/codex_smoke_engineering_pelelmex_periodic_covo.sh`
- `CODEX_PELELMEX_COVO_LOG_DIR=/tmp/codex_pelelmex_periodic_covo_self_convergence_20260716 JOBS=4 RUN_TIMEOUT=300 tools/codex_smoke_engineering_pelelmex_periodic_covo.sh`
- `CODEX_SKIP_BUILD=1 CODEX_PELELMEX_COVO_LOG_DIR=/tmp/codex_pelelmex_periodic_covo_self_convergence_20260716_rerun JOBS=4 RUN_TIMEOUT=300 tools/codex_smoke_engineering_pelelmex_periodic_covo.sh`

## Evidence

- `/tmp/codex_pelelmex_periodic_covo_self_convergence_20260716/validation.log`
- `/tmp/codex_pelelmex_periodic_covo_self_convergence_20260716_rerun/validation.log`
- PASS line: `pelelmex_periodic_covo_self_convergence PASS grids=16,32,64 time=2.00000000e-02 x_velocity_e16_32=1.42341799e+00 x_velocity_e32_64=5.64626225e-01 x_velocity_order=1.334 y_velocity_e16_32=1.41042611e+00 y_velocity_e32_64=5.55156638e-01 y_velocity_order=1.345`

## Known limitations

- This is self-convergence, not exact-solution or MMS validation.
- It covers the maintained PeriodicCases convected-vortex velocity fields only.
- It is targeted/heavy and not part of the default quick gate.
- QLT-03 still needs MMS, double-Mach, bubble/RT, exact/MMS PeleLMeX validation, plan-specific reference tolerances, and longer physical-time stability evidence.
