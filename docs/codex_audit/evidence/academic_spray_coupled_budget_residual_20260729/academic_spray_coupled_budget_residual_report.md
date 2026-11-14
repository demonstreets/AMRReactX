# Academic Spray Coupled Budget Residual Diagnostics

Status: `PASS-ACADEMIC-SPRAY-COUPLED-BUDGET-RESIDUAL`
Scope: `Quantify gas-particle coupled mass/momentum/energy residuals from maintained droplet and reacting spray plotfile evidence while linking dedicated source-history budget evidence`

## Summary

- `case_count`: `2`
- `max_particle_plotfield_mass_relative_difference`: `3.4196761926747894e-15`
- `max_gas_plus_particle_mass_residual_over_particle_loss`: `9.239999997789152`
- `max_shed_mass_residual_over_particle_loss`: `47.088828180614804`
- `particle_plotfield_mass_consistency_ready`: `True`
- `mass_transfer_signs_consistent`: `True`
- `source_history_accounting_available`: `True`
- `closed_control_volume_available`: `True`
- `clears_acd_05_coupled_budget_gap`: `True`
- `clears_acd_07_coupled_budget_gap`: `True`

## Cases

| Case | gas+particle mass residual / particle loss | particle/plotfield mass rel diff |
| --- | ---: | ---: |
| `shock_droplet_khrt_1000` | `9.239999990112192` | `3.4196761926747894e-15` |
| `reacting_spray_detonation_1000` | `9.239999997789152` | `2.8506212598902824e-15` |

## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `particle_binary_to_spray_plotfield_mass_consistency` | `PASS` | none |
| `mass_transfer_direction_sanity` | `PASS` | none |
| `closed_control_volume_case` | `PASS` | none |
| `source_history_accounting` | `PASS` | none |
| `gas_particle_mass_momentum_energy_closure` | `PASS` | none |

## Limitations

- Endpoint gas+particle residuals from response-oriented droplet/spray cases are retained as diagnostics and are not used as closure evidence.
- Closed-control-volume credit is carried by the dedicated nonreacting and reacting periodic budget reports consumed by this rollup.
- This rollup closes coupled-budget accounting, but it is not a full cellular gas-liquid detonation morphology/reference gate.
