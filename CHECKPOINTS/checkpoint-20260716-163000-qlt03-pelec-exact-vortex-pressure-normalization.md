# Checkpoint: QLT-03 PeleC Exact Vortex Pressure Normalization

Date: 2026-07-16
Scope: QLT-03 PeleC standard exact isentropic-vortex convergence.

## What changed

- Parameterized `tools/codex_smoke_academic_pelec_isentropic_vortex_trend.sh` so generated trend inputs can override `prob.p_bg`, `prob.rho_bg`, `prob.u_bg`, and `prob.v_bg` through environment variables.
- Updated `tools/codex_smoke_academic_pelec_isentropic_vortex_exact_convergence.sh` defaults to the standard exact-vortex normalization:
  - `CODEX_VORTEX_BETA=5.0`
  - `CODEX_VORTEX_P_BG=1.0`
  - `CODEX_VORTEX_CFL=0.05`
  - `CODEX_VORTEX_STOP_TIME=0.01`
- Strengthened `tools/validate_pelec_isentropic_vortex_exact_convergence.py` to require 32-to-64 velocity order in addition to density and pressure order.
- Updated QLT-03 audit docs to replace the previous beta=1 / `p_bg=1/gamma` diagnostic evidence with the strict beta=5 / `p_bg=1` exact-convergence evidence.

## Verification

Formal command:

```bash
CODEX_ISENTROPIC_VORTEX_EXACT_LOG_DIR=/tmp/codex_pelec_isentropic_vortex_exact_convergence_p1_beta5_20260716 CODEX_SKIP_BUILD=1 JOBS=2 RUN_TIMEOUT=360 tools/codex_smoke_academic_pelec_isentropic_vortex_exact_convergence.sh
```

Evidence:

- `/tmp/codex_pelec_isentropic_vortex_exact_convergence_p1_beta5_20260716/summary.tsv`
- `/tmp/codex_pelec_isentropic_vortex_exact_convergence_p1_beta5_20260716/trend_validation.log`
- `/tmp/codex_pelec_isentropic_vortex_exact_convergence_p1_beta5_20260716/exact_convergence.log`
- `/tmp/codex_pelec_isentropic_vortex_exact_convergence_p1_beta5_20260716/n16/validation.log`
- `/tmp/codex_pelec_isentropic_vortex_exact_convergence_p1_beta5_20260716/n32/validation.log`
- `/tmp/codex_pelec_isentropic_vortex_exact_convergence_p1_beta5_20260716/n64/validation.log`

Key PASS line:

```text
pelec_isentropic_vortex_exact_convergence PASS grids=16,32,64 time=1.00000000e-02 density_l1=3.18963568e-05,2.42086120e-06,2.81975728e-07 pressure_l1=4.73808492e-05,4.11526417e-06,6.47008509e-07 velocity_l1=1.03101399e-04,7.25566279e-06,1.17643989e-06 density_orders=3.720,3.102 pressure_orders=3.525,2.669 velocity_orders=3.829,2.625 entropy_drop=65.224
```

## Interpretation

The earlier exact-vortex run with `p_bg=1/gamma` left velocity at a weak 32-to-64 order. With the standard pressure normalization `p_bg=1.0`, density, pressure, and velocity all show strong 32-to-64 convergence against the transported exact vortex. This indicates the previous velocity plateau was a reference/normalization mismatch, not a PeleC solver failure.

QLT-03 remains `PARTIAL` because MMS, double-Mach, bubble/RT, PeleLMeX smooth-flow validation, and plan-specific validation cases with reference tolerances remain open.
