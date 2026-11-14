# Checkpoint: QLT-03 PeleC Exact Isentropic Vortex Convergence

Date: 2026-07-16
Scope: QLT-03 standard validation cases; calibrated PeleC smooth-flow exact-reference convergence.

## What changed

- Added opt-in standard exact isentropic-vortex initialization to `external/PeleC/Exec/RegTests/IsentropicVortex`:
  - `prob.exact_vortex = 1` selects the standard smooth ideal-gas Euler isentropic-vortex profile.
  - `prob.vortex_beta` controls the standard vortex strength.
  - The legacy profile remains the default (`prob.exact_vortex = 0`) so existing smoke inputs remain compatible.
- Extended `tools/validate_pelec_isentropic_vortex.py` to select the matching reference formula from the input file.
- Parameterized `tools/codex_smoke_academic_pelec_isentropic_vortex_trend.sh` with exact-mode controls.
- Added `tools/validate_pelec_isentropic_vortex_exact_convergence.py`.
- Added `tools/codex_smoke_academic_pelec_isentropic_vortex_exact_convergence.sh`.
- Updated `docs/codex_audit/MASTER_PLAN_TRACEABILITY.md` and `docs/codex_audit/SMOKE_MATRIX.md`.

## Verification

Formal exact-reference command:

```bash
CODEX_ISENTROPIC_VORTEX_EXACT_LOG_DIR=/tmp/codex_pelec_isentropic_vortex_exact_convergence_20260716 CODEX_SKIP_BUILD=1 JOBS=2 RUN_TIMEOUT=360 tools/codex_smoke_academic_pelec_isentropic_vortex_exact_convergence.sh
```

Evidence:

- `/tmp/codex_pelec_isentropic_vortex_exact_convergence_20260716/summary.tsv`
- `/tmp/codex_pelec_isentropic_vortex_exact_convergence_20260716/trend_validation.log`
- `/tmp/codex_pelec_isentropic_vortex_exact_convergence_20260716/exact_convergence.log`
- `/tmp/codex_pelec_isentropic_vortex_exact_convergence_20260716/n16/validation.log`
- `/tmp/codex_pelec_isentropic_vortex_exact_convergence_20260716/n32/validation.log`
- `/tmp/codex_pelec_isentropic_vortex_exact_convergence_20260716/n64/validation.log`

Key PASS line:

```text
pelec_isentropic_vortex_exact_convergence PASS grids=16,32,64 time=1.00000000e-02 density_l1=4.60892329e-06,1.48519123e-07,4.64777466e-08 pressure_l1=4.77886297e-06,1.80797353e-07,4.87255761e-08 velocity_l1=1.74304501e-05,3.72774377e-06,3.49811257e-06 density_orders=4.956,1.676 pressure_orders=4.724,1.892 velocity_orders=2.225,0.092 entropy_drop=24.702
```

Compatibility command:

```bash
CODEX_ISENTROPIC_VORTEX_LOG_DIR=/tmp/codex_pelec_isentropic_vortex_legacy_after_exact_20260716 CODEX_SKIP_BUILD=1 JOBS=2 RUN_TIMEOUT=180 tools/codex_smoke_academic_pelec_isentropic_vortex.sh
```

Compatibility evidence:

- `/tmp/codex_pelec_isentropic_vortex_legacy_after_exact_20260716/validation.log`

## Interpretation

This closes a calibrated PeleC exact smooth-flow slice for QLT-03 density, pressure, entropy, exact initialization, and mass conservation. It also explains the earlier flat legacy-reference behavior: the legacy profile was useful as a smoke but was not the standard exact Euler vortex.

QLT-03 remains `PARTIAL`. Velocity error is bounded and improves from 16 to 32, but its 32-to-64 observed order is weak in this run, so velocity convergence remains diagnostic. MMS, double-Mach, bubble/RT, PeleLMeX smooth-flow validation, and plan-specific validation cases with reference tolerances remain open.
