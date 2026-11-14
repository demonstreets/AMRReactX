# Academic Reacting Spray Detonation Validation

Status: `PASS-ACADEMIC-SPRAY-DETONATION-VALIDATION`
Scope: `PeleC heptane-air reacting shock-droplet gate with CVODE chemistry, spray particles, KHRT breakup, evaporation/momentum coupling, and propagating high-pressure/high-temperature front`

## Summary

- `main_case`: `reacting_spray_detonation_1000`
- `pressure_front_shift`: `0.87890625`
- `pressure_front_shift_cells`: `9.0`
- `temp_front_shift`: `0.5859375`
- `heat_release_absmax`: `1.56560169`
- `o2_consumption`: `0.000183833557`
- `fuel_vapor_increase`: `0.000788388867`
- `particle_count0`: `200.0`
- `particle_count1`: `2283.0`
- `particle_growth_factor`: `11.415`
- `spray_mass_loss_rel`: `0.000595551434`
- `spray_x_vel_absmax`: `48294.4386`
- `spray_temp_increase`: `118.466414`
- `surface_area_ratio`: `1.19614644`
- `species_closure_rel`: `2.22044605e-16`
- `clears_acd_07_reacting_spray_response_gate`: `True`
- `clears_acd_07_closed_gas_particle_budget_gap`: `False`
- `clears_acd_07_full_cellular_gas_liquid_detonation_gap`: `False`
- `clears_acd_07_external_reference_gap`: `False`
- `clears_acd_07_spray_detonation_gap`: `False`

## Quality Gates

| Gate | Status | Evidence | Gap |
| --- | --- | --- | --- |
| `reacting_spray_input_contract` | `PASS` | docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/reacting_spray_detonation_1000/input.reacting_spray_detonation_1000 | none |
| `detonation_style_pressure_temperature_front` | `PASS` | docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/validation_reacting_spray_detonation_1000.log | none |
| `stiff_reaction_heat_release_response` | `PASS` | docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/validation_reacting_spray_detonation_1000.log | none |
| `spray_breakup_particle_growth` | `PASS` | docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/validation_reacting_spray_detonation_1000.log | none |
| `droplet_motion_evaporation_thermal_response` | `PASS` | docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/validation_reacting_spray_detonation_1000.log | none |
| `finite_conservative_species_closure` | `PASS` | docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/reacting_spray_detonation_1000/plt01000 | none |
| `closed_gas_particle_budget` | `NOT_READY` | docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/validation_reacting_spray_detonation_1000.log | The maintained case proves stable reacting spray response and gas species closure, but not a closed gas+particle mass, momentum, and total-energy budget. |
| `full_cellular_gas_liquid_detonation` | `NOT_READY` | docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/validation_reacting_spray_detonation_1000.log | The current 2D shock-droplet gate is detonation-style and does not certify full cellular gas-liquid detonation morphology. |
| `external_spray_detonation_reference` | `NOT_READY` |  | No external reacting spray detonation reference or experiment comparison is attached. |

## Cases

| Case | Front shift cells | Heat release | Particles | Spray velocity |
| --- | --- | --- | --- | --- |
| `reacting_spray_detonation_1000` | `9` | `1.56560169e+00` | `200->2283` | `4.82944386e+04` |

## Limitations

- This is an in-repository 2D reacting spray shock/detonation-style gate using the simplified heptane_3sp chemistry, not an external experimental spray-detonation benchmark.
- The gate proves coupled reacting gas plus Euler-Lagrange spray stability and front propagation; it does not certify full cellular gas-liquid detonation morphology.
- The ACD-05 droplet gate remains the focused droplet-physics validation; this ACD-07 gate exercises the coupled end-to-end path.
- The broad ACD-07 spray/gas-liquid detonation validation gap remains open until closed gas+particle budgets, cellular morphology, and/or external reference agreement are attached.
