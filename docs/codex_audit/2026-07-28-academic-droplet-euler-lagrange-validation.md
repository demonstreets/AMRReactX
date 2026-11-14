# Academic Droplet Euler-Lagrange Validation

Date: 2026-07-28

Status: `PASS-ACADEMIC-DROPLET-EULER-LAGRANGE-VALIDATION`

Evidence root:

- `docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728`

## Scope

This closes the ACD-05 Euler-Lagrange droplet-tracking gap with a maintained PeleC shock-droplet spray-particle gate. The run keeps the existing `examples/academic/shock_droplet/inputs` physics setup, including spray particles, two-way momentum and mass transfer, free particle motion, and KHRT breakup, while setting a deterministic 1000-step final plot output for audit repeatability.

## Case

- Case: `shock_droplet_khrt_1000`
- Source case: `examples/academic/shock_droplet`
- Input evidence: `docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/shock_droplet_khrt_1000/input.shock_droplet_khrt_1000`
- Final plot: `docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/shock_droplet_khrt_1000/plt01000`
- Validator: `tools/validate_academic_droplet_euler_lagrange.py`
- Report writer: `tools/write_academic_droplet_euler_lagrange_validation_report.py`
- Runner: `tools/codex_run_academic_droplet_euler_lagrange_validation.sh`

## Metrics

- Final time: `8.90037487245e-06`
- Particle count: `200 -> 2134`
- Particle growth factor: `10.67`
- Spray mass loss relative to initial: `2.83041623e-04`
- Spray x-velocity absolute maximum: `3.06697552e+03`
- Spray temperature maximum: `3.04386794e+02`
- Spray surface-area ratio: `1.14071382`
- Final max Sauter mean diameter: `4.99981357e-03`
- Final gas fuel density sum: `-8.01161646e-25`

## Gate Result

The gate verifies that:

- spray-particle physics is enabled;
- momentum and mass transfer are enabled;
- particles are mobile rather than fixed;
- KHRT breakup is enabled;
- particle count increases under breakup;
- droplet velocity responds to the shock field;
- spray mass and temperature respond through evaporation and thermal coupling;
- Eulerian spray-derived fields and gas thermodynamic fields remain finite and physical.

## Remaining Limits

This is not yet an end-to-end gas-liquid or spray detonation validation. It upgrades ACD-05 from evaporation-only smoke evidence to droplet motion, breakup, and two-way-coupling evidence. ACD-07 remains the next academic two-phase target.
