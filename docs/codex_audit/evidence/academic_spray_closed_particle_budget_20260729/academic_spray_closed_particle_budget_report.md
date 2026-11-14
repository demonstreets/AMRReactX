# Academic Spray Closed Particle Budget

Status: `PASS-ACADEMIC-SPRAY-CLOSED-PARTICLE-BUDGET`
Scope: `Periodic fixed-particle spray_test case validating native AMReX particle DATA particle count, parcel-mass proxy, geometry, diameter, and thermal-proxy invariance`

## Summary

- `main_case`: `spray_closed_particle_budget`
- `particle_count0`: `100.0`
- `particle_count1`: `100.0`
- `mass_model`: `unit_parcel_number_density_fallback`
- `mass_rel_drift`: `0.0`
- `diam_rel_drift`: `0.0`
- `xcoord_abs_drift`: `0.0`
- `ycoord_abs_drift`: `0.0`
- `thermal_rel_drift`: `0.0`
- `xmom_rel_observed`: `1.0`
- `ymom_abs_observed`: `0.0`
- `mass`: `5.974262029577e-11`
- `xmom_observed`: `0.0`
- `kinetic_observed`: `0.0`
- `clears_acd_05_closed_fixed_particle_budget_subgap`: `True`
- `clears_acd_05_full_gas_particle_budget_gap`: `False`
- `clears_acd_07_full_reacting_spray_budget_gap`: `False`

## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `closed_fixed_particle_input_contract` | `PASS` | none |
| `particle_binary_budget_parser` | `PASS` | none |
| `fixed_particle_mass_geometry_thermal_budget` | `PASS` | none |
| `fixed_particle_velocity_momentum_budget` | `OBSERVED_ONLY` | The spray_test fixed_parts configuration resets particle velocity, so particle momentum is reported as an observation rather than a conservation gate. |
| `full_gas_particle_budget_with_coupling` | `NOT_READY` | This closed fixed-particle case proves particle binary budget closure, but it does not exercise evaporating/reacting gas-particle source-term closure. |

## Limitations

- This is a closed fixed-particle budget sanity gate and does not replace evaporating/reacting gas-particle source-term closure.
- The spray_test fixture writes zero number_density, so parcel mass uses a documented unit-number-density fallback from liquid density and diameter.
- Particle velocity/momentum is observed only because fixed_parts resets particle velocity in this case.
- ACD-05 full credit still needs external breakup/reference validation or a coupled gas-particle budget including source histories.
- ACD-07 full credit still needs reacting spray/gas-liquid detonation morphology and closed coupled budgets.
