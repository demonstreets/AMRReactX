# Checkpoint: QLT-03 PeleC Isentropic Vortex Self-Convergence

Date: 2026-07-16
Scope: QLT-03 standard validation cases; PeleC solver-coupled smooth-flow convergence diagnostics.

## What changed

- Parameterized `tools/codex_smoke_academic_pelec_isentropic_vortex_trend.sh` with environment-controlled `CODEX_VORTEX_STOP_TIME`, `CODEX_VORTEX_MAX_STEP`, `CODEX_VORTEX_CFL`, and trend-threshold options.
- Added `tools/validate_pelec_isentropic_vortex_self_convergence.py`.
  - Reads 16/32/64 final AMReX plotfiles.
  - Compares coarse fields against volume-restricted fine fields.
  - Requires near-second-order self-convergence by default (`--min-order 1.5`) for density, pressure, x/y velocity, and temperature.
- Added `tools/codex_smoke_academic_pelec_isentropic_vortex_self_convergence.sh`.
  - Runs the fixed-time 16/32/64 solver-coupled PeleC vortex workflow at `stop_time = 0.01`, `CFL = 0.2`.
  - Keeps the analytic/reference per-case smoke checks and adds self-convergence validation.
- Updated `docs/codex_audit/MASTER_PLAN_TRACEABILITY.md` and `docs/codex_audit/SMOKE_MATRIX.md`.

## Verification

Command:

```bash
CODEX_ISENTROPIC_VORTEX_SELF_CONV_LOG_DIR=/tmp/codex_pelec_isentropic_vortex_self_convergence_20260716 CODEX_SKIP_BUILD=1 JOBS=2 RUN_TIMEOUT=300 tools/codex_smoke_academic_pelec_isentropic_vortex_self_convergence.sh
```

Evidence:

- `/tmp/codex_pelec_isentropic_vortex_self_convergence_20260716/summary.tsv`
- `/tmp/codex_pelec_isentropic_vortex_self_convergence_20260716/trend_validation.log`
- `/tmp/codex_pelec_isentropic_vortex_self_convergence_20260716/self_convergence.log`
- `/tmp/codex_pelec_isentropic_vortex_self_convergence_20260716/n16/validation.log`
- `/tmp/codex_pelec_isentropic_vortex_self_convergence_20260716/n32/validation.log`
- `/tmp/codex_pelec_isentropic_vortex_self_convergence_20260716/n64/validation.log`

Key PASS line:

```text
pelec_isentropic_vortex_self_convergence PASS grids=16,32,64 time=1.00000000e-02 density_e16_32=9.30330769e-04 density_e32_64=2.37815379e-04 density_order=1.968 pressure_e16_32=9.40405438e-04 pressure_e32_64=2.37729943e-04 pressure_order=1.984 x_velocity_e16_32=6.86871698e-04 x_velocity_e32_64=1.69625560e-04 x_velocity_order=2.018 y_velocity_e16_32=6.86236442e-04 y_velocity_e32_64=1.68630484e-04 y_velocity_order=2.025 Temp_e16_32=9.47913841e-11 Temp_e32_64=2.41977519e-11 Temp_order=1.970
```

## Interpretation

This proves clean near-second-order self-convergence of the current PeleC smooth-vortex calculation under volume restriction. It is stronger evidence than comparing each resolution to the existing analytic/reference formula, whose error is flat from 32 to 64 for several fields and therefore does not yet support a strict exact Euler convergence claim.

QLT-03 remains `PARTIAL`. The next closure step should replace or supplement the current analytic/reference formula with a calibrated exact isentropic vortex or MMS case, then keep double-Mach, bubble/RT, PeleLMeX smooth-flow validation, and plan-specific reference tolerances on the open list.
