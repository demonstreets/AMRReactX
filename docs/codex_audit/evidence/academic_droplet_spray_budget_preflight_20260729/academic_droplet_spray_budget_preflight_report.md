# Academic Droplet/Spray Plotfield Budget Preflight

Status: `PASS-ACADEMIC-DROPLET-SPRAY-PLOTFIELD-BUDGET-PREFLIGHT`
Scope: `ACD-05/ACD-07 gas conservative field plus Eulerian spray plotfield and native AMReX particle-binary budget preflight`

## Summary

- `case_count`: `2`
- `plotfield_budget_cases_ready`: `True`
- `particle_headers_declare_required_components`: `True`
- `per_particle_binary_budget_parser_ready`: `True`
- `clears_projected_plotfield_budget_preflight`: `True`
- `clears_acd_05_closed_gas_particle_budget_gap`: `False`
- `clears_acd_07_closed_gas_particle_budget_gap`: `False`
- `clears_full_closed_gas_particle_budget_gap`: `False`
- `max_particle_plotfield_mass_relative_difference`: `3.41967619e-15`
- `droplet_spray_mass_loss_rel_plotfield`: `-2.83041623e-04`
- `droplet_particle_mass_loss_rel`: `-2.83041623e-04`
- `spray_spray_mass_loss_rel_plotfield`: `-5.95551434e-04`
- `spray_particle_mass_loss_rel`: `-5.95551434e-04`
- `spray_species_closure_absmax_final`: `2.22044605e-16`

## Budget Deltas

| Case | Gas mass rel delta | Gas energy rel delta | Spray mass rel delta | Particle mass rel delta | Particle count |
| --- | --- | --- | --- | --- | --- |
| `droplet_euler_lagrange` | `1.78803470e-07` | `-8.64994165e-07` | `-2.83041623e-04` | `-2.83041623e-04` | `200->2134` |
| `reacting_spray_detonation` | `2.59248688e-07` | `-1.13960037e-06` | `-5.95551434e-04` | `-5.95551434e-04` | `200->2283` |

## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `droplet_plotfield_budget_fields_present` | `PASS` | none |
| `spray_plotfield_budget_fields_present` | `PASS` | none |
| `finite_gas_and_spray_plotfield_integrals` | `PASS` | none |
| `particle_headers_declare_budget_components` | `PASS` | none |
| `per_particle_binary_budget_parser` | `PASS` | none |
| `particle_budget_matches_spray_plotfield_mass` | `PASS` | none |
| `closed_gas_particle_budget` | `NOT_READY` | Gas conservative fields, Eulerian spray plotfield projections, and native particle binary budgets can be integrated, but these open-boundary shock-tube cases do not include boundary-flux and coupling-source histories needed to close total gas+particle mass, momentum, and total energy. |

## Limitations

- The report integrates gas conservative variables, Eulerian spray plotfield projections, and native AMReX particle DATA budgets from maintained plotfiles.
- Particle kinetic energy and mass-temperature sums are directly reconstructed from particle DATA; full total-energy closure still needs solver coupling-source and boundary-flux histories.
- Broad ACD-05/ACD-07 budget credit remains open until an in-code budget diagnostic or closed-domain case closes gas+particle mass, momentum, and total energy including boundary/coupling terms.
