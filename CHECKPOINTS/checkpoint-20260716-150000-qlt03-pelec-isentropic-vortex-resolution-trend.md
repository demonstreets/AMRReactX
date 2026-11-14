# Checkpoint: QLT-03 PeleC Isentropic Vortex Resolution Trend

Date: 2026-07-16
Scope: QLT-03 standard validation cases; PeleC solver-coupled smooth Euler isentropic vortex.

## What changed

- Added `tools/codex_smoke_academic_pelec_isentropic_vortex_trend.sh`.
  - Builds or reuses `external/PeleC/Exec/RegTests/IsentropicVortex/codex_isentropic_vortex3d.gnu.ex`.
  - Generates fixed-time `stop_time = 0.003` inputs for 16x16x2, 32x32x2, and 64x64x2 single-box periodic grids.
  - Runs each case, requires AMReX finalization and no unused ParmParse/backtrace/abort markers, validates each plotfile against the exact transported vortex formula, and writes `summary.tsv`.
- Added `tools/validate_pelec_isentropic_vortex_trend.py`.
  - Checks the three fixed-time grids, initial exact-state match, mass conservation, density/pressure coarse-to-fine improvement, entropy-error reduction, and bounded/stable velocity error.
- Updated `docs/codex_audit/MASTER_PLAN_TRACEABILITY.md` and `docs/codex_audit/SMOKE_MATRIX.md` with the new QLT-03 evidence and limitations.

## Verification

Command:

```bash
CODEX_ISENTROPIC_VORTEX_TREND_LOG_DIR=/tmp/codex_pelec_isentropic_vortex_trend_20260716_rerun CODEX_SKIP_BUILD=1 JOBS=2 RUN_TIMEOUT=240 tools/codex_smoke_academic_pelec_isentropic_vortex_trend.sh
```

Evidence:

- `/tmp/codex_pelec_isentropic_vortex_trend_20260716_rerun/summary.tsv`
- `/tmp/codex_pelec_isentropic_vortex_trend_20260716_rerun/trend_validation.log`
- `/tmp/codex_pelec_isentropic_vortex_trend_20260716_rerun/n16/validation.log`
- `/tmp/codex_pelec_isentropic_vortex_trend_20260716_rerun/n32/validation.log`
- `/tmp/codex_pelec_isentropic_vortex_trend_20260716_rerun/n64/validation.log`

Key PASS line:

```text
pelec_isentropic_vortex_trend_validation PASS cases=3 grids=16,32,64 time=3.00000000e-03 density_l1=2.27476229e-05,1.84967438e-05,1.85054726e-05 pressure_l1=2.29674670e-05,1.84184748e-05,1.84508566e-05 velocity_l1=1.13132429e-04,1.12594608e-04,1.12456072e-04 entropy_drop=77.044 max_velocity_l1=1.13132429e-04 density_orders=0.298,-0.001 pressure_orders=0.318,-0.003 velocity_orders=0.007,0.002
```

## Interpretation

This is real solver-coupled PeleC evidence at three resolutions and one fixed physical time. It strengthens QLT-03 beyond a single two-step smoke by proving exact-state initialization, fixed-time transport validation, mass conservation, density/pressure coarse-to-fine improvement from 16 to 64, strong entropy-error reduction, and bounded/stable velocity error.

It is not a rigorous convergence benchmark. The 32-to-64 density/pressure observed orders are flat/slightly negative and velocity error is stable rather than meaningfully convergent. QLT-03 remains `PARTIAL` until calibrated multi-resolution convergence, MMS, double-Mach, bubble/RT, PeleLMeX smooth-flow validation, and plan-specific reference tolerances are added.
