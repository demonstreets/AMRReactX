# Academic Droplet Euler-Lagrange Validation

Status: `PASS-ACADEMIC-DROPLET-EULER-LAGRANGE-VALIDATION`
Scope: `PeleC spray-particle shock-droplet KHRT breakup, droplet motion, evaporation/thermal response, and Eulerian spray-field coupling gate`

## Summary

- `main_case`: `shock_droplet_khrt_1000`
- `particle_count0`: `200.0`
- `particle_count1`: `2134.0`
- `particle_growth_factor`: `10.67`
- `spray_mass_loss_rel`: `0.000283041623`
- `spray_x_vel_absmax`: `3066.97552`
- `spray_temp_max`: `304.386794`
- `surface_area_ratio`: `1.14071382`
- `d32_max`: `0.00499981357`
- `gas_fuel_sum`: `-8.01161646e-25`
- `clears_acd_05_response_gate`: `True`
- `clears_acd_05_closed_gas_particle_budget_gap`: `False`
- `clears_acd_05_external_reference_gap`: `False`
- `clears_acd_05_euler_lagrange_gap`: `False`

## Quality Gates

| Gate | Status | Evidence | Gap |
| --- | --- | --- | --- |
| `spray_particle_path_enabled` | `PASS` | docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/shock_droplet_khrt_1000/input.shock_droplet_khrt_1000 | none |
| `khrt_breakup_particle_growth` | `PASS` | docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/validation_shock_droplet_khrt_1000.log | none |
| `droplet_motion_response` | `PASS` | docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/validation_shock_droplet_khrt_1000.log | none |
| `evaporation_heat_mass_response` | `PASS` | docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/validation_shock_droplet_khrt_1000.log | none |
| `eulerian_spray_fields_finite` | `PASS` | docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/shock_droplet_khrt_1000/plt01000 | none |
| `closed_gas_particle_budget` | `NOT_READY` | docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728/validation_shock_droplet_khrt_1000.log | The maintained case proves finite response and scalar closure, but does not yet compute a closed gas+particle mass, momentum, and total-energy budget. |
| `external_breakup_reference` | `NOT_READY` |  | No external shock-droplet breakup or evaporation reference comparison is attached. |

## Cases

| Case | Particles | Growth | Mass loss | Velocity | Surface area ratio |
| --- | --- | --- | --- | --- | --- |
| `shock_droplet_khrt_1000` | `200->2134` | `10.67` | `2.83041623e-04` | `3.06697552e+03` | `1.14071382e+00` |

## Limitations

- This validates a maintained shock-droplet spray-particle case; it is not yet an end-to-end gas-liquid detonation.
- The gate proves KHRT breakup and Eulerian spray-field coupling through PeleC derived fields and particle headers, not an external experimental breakup benchmark.
- The D2-law unit evidence remains the maintained analytic evaporation check; this gate adds motion, breakup, and two-way-coupling evidence for ACD-05.
- The broad ACD-05 Euler-Lagrange validation gap remains open until a closed gas+particle mass, momentum, and total-energy budget or external reference comparison is attached.
