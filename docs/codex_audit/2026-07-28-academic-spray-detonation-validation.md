# Academic Spray Detonation Validation

Date: 2026-07-28

Status: `PASS-ACADEMIC-SPRAY-DETONATION-VALIDATION`

Evidence root:

- `docs/codex_audit/evidence/academic_spray_detonation_validation_20260728`

## Scope

This audit records the ACD-07 reacting spray/gas-liquid detonation-style gate added after the engineering H2 initial acceptance and the academic gas/two-phase foundational gates. The case is based on the maintained PeleC `examples/academic/shock_droplet` setup, upgraded to a reacting heptane-air spray-shock problem with CVODE chemistry, spray particles, KHRT breakup, evaporation/mass transfer, momentum transfer, and a propagating high-pressure/high-temperature front.

## Code Fix

The `shock_droplet` problem already had `ProbParmDevice::Y_NC7H16`, but the value was not parsed or inserted into the gas initial state. This was fixed by:

- querying `prob.Y_NC7H16` in `examples/academic/shock_droplet/prob.cpp`;
- initializing `massfrac[NC7H16_ID]` in `examples/academic/shock_droplet/prob.H`.

This makes the existing input contract usable for controlled reacting spray gates.

## Case

- Case: `reacting_spray_detonation_1000`
- Source case: `examples/academic/shock_droplet`
- Chemistry: `heptane_3sp`
- Integrator: `ReactorCvode`
- CVODE linear solve: `dense_direct`
- Spray: mobile particles, momentum transfer, mass transfer, KHRT breakup
- Max step: `1000`
- Final plot: `plt01000`

## Metrics

- Final time: `8.91915844208e-06`
- Pressure-front shift: `0.87890625`
- Pressure-front shift in cells: `9.0`
- Temperature-front shift: `0.5859375`
- Heat-release absolute maximum: `1.56560169`
- O2 consumption metric: `1.83833557e-04`
- Fuel-vapor response metric: `7.88388867e-04`
- Particle count: `200 -> 2283`
- Particle growth factor: `11.415`
- Spray mass loss relative to initial: `5.95551434e-04`
- Spray x-velocity absolute maximum: `4.82944386e+04`
- Spray temperature increase: `1.18466414e+02`
- Spray surface-area ratio: `1.19614644`
- Final max Sauter mean diameter: `4.99987684e-03`
- Species closure: `2.22044605e-16`

## Gate Result

The gate verifies that:

- the reacting spray input contract is active;
- the pressure and temperature front moves into the droplet-cloud region;
- stiff chemistry runs to completion without NaN, abort, or nonphysical gas thermodynamic states;
- heat-release and species response are nonzero;
- mobile spray particles couple to the gas;
- KHRT breakup increases particle count and spray surface area;
- droplet motion, evaporation, and thermal response are visible in Eulerian spray-derived fields;
- species closure remains bounded.

## Remaining Limits

This is an in-repository 2D reacting spray shock/detonation-style validation using simplified heptane chemistry. It is not an external experimental spray-detonation benchmark and does not certify full cellular gas-liquid detonation morphology. It is sufficient to move ACD-07 from no maintained evidence to an initial maintained end-to-end coupled reacting spray gate.
