# Academic MMS Nonconstant-Density Shim Validation

Status: `PASS-ACADEMIC-MMS-NONCONSTANT-DENSITY-SHIM-VALIDATION`

Scope: PeleC MMS RegTest validation with a generated MASA-compatible nonconstant-density, zero-velocity, constant-pressure stationary manufactured state. This exercises spatially varying exact-field evaluation, MMS source wiring, error derives, clean finalization, and relative pressure/energy residual gates without claiming external MASA coverage.

## Summary

- `clears_qlt_03_nonconstant_mms_shim_gap`: `True`
- `clears_external_nonlinear_masa_benchmark`: `False`
- `uses_external_masa`: `False`
- `manufactured_solution_kind`: `nonconstant_density_stationary`
- `max_primary_error`: `3.935420342e-13`
- `max_primary_residual`: `3.934805386e-13`
- `pressure_error_relative`: `1.94159957562e-08`
- `rhoE_residual_relative`: `1.9415995772e-08`

## Quality Gates

- `nonconstant_density_shim_built`: `PASS`
- `mms_run_finalized_without_failure_tokens`: `PASS`
- `nonconstant_density_primary_errors_near_roundoff`: `PASS`
- `pressure_and_energy_relative_residuals_bounded`: `PASS`
- `scope_guard_does_not_claim_external_masa`: `PASS`

## Limitations

- This is a nonconstant in-repository MASA-compatible shim, not the external nonlinear MASA/MetaPhysicL benchmark.
- The exact state is stationary with zero velocity and constant pressure; it strengthens MMS spatial-field coverage but does not exercise all nonlinear source terms.
- The report intentionally sets clears_external_nonlinear_masa_benchmark=false to avoid overclaiming QLT-03 closure.
