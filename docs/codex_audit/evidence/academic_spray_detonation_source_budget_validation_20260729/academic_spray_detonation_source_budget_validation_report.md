# Academic Reacting Spray Detonation Source Budget Validation

Status: `PASS-ACADEMIC-SPRAY-DETONATION-SOURCE-BUDGET-VALIDATION`

Key metrics:
- plot count: `301`
- final time: `2.574275786269e-06`
- integrated `spray_rho_src`: `1.9486847519734861e-09`
- particle mass delta: `-1.9030125048276705e-10`
- particle/source relative mismatch: `2.718246e-08`
- 2D spray effective thickness factor: `9.765625e-02`
- `heatRelease` absmax: `1.111023e+01`
- `rhoe_dot` absmax: `3.941140e+00`
- O2 consumption signal: `3.413909e-06`
- fuel vapor response: `1.464664e-05`
- pressure front shift cells: `3.000000e+00`
- species closure absmax: `2.220446e-16`

Readiness:
- ACD-07 reacting spray source-budget subgate: `True`
- full cellular gas-liquid detonation gap: `False`
- external reference gap: `False`

Quality gates:

| Gate | Status | Metric |
| --- | --- | --- |
| `input_reacting_spray_source_budget_contract` | `PASS` | `[]` |
| `run_finalized_without_failure_markers` | `PASS` | `"AMReX finalized and log has no failure markers"` |
| `finite_positive_gas_state` | `PASS` | `{"min_density": 0.0012259159629601484, "min_pressure": 1012999.9948617159, "min_temp": 299.99999960182885}` |
| `source_fields_present_and_nonzero` | `PASS` | `{"max_abs_mom_src": 0.00013244295323736402, "max_abs_rho_src": 0.0007570678866415355}` |
| `pure_heptane_rho_source_maps_to_rhoY_source` | `PASS` | `0.0` |
| `particle_mass_closes_to_spray_rho_source` | `PASS` | `{"particle_comparable_rho_source_integral": 1.9030124530991076e-10, "particle_mass_delta": -1.9030125048276705e-10, "particle_source_relative_mismatch": 2.7182461588711962e-08, "spray_particle_mass_measure_factor": 0.09765625}` |
| `gas_mass_closes_to_spray_rho_source` | `PASS` | `2.3034119333453103e-08` |
| `gas_fuel_closes_to_spray_rhoY_source` | `PASS` | `2.036351269856256e-08` |
| `gas_total_energy_closes_to_spray_energy_source` | `PASS` | `2.020533301214868e-08` |
| `stiff_reaction_heat_release_present` | `PASS` | `{"heatRelease_absmax": 11.110226624283513, "rhoe_dot_absmax": 3.941140141665528}` |
| `reacting_species_response_present` | `PASS` | `{"fuel_vapor_increase": 1.4646638382451171e-05, "o2_consumption": 3.4139090846485587e-06}` |
| `detonation_style_front_response_present` | `PASS` | `{"pressure_front_shift": 0.29296875, "pressure_front_shift_cells": 3.0, "temp_front_shift": 0.1953125}` |
| `species_mass_fraction_closure` | `PASS` | `2.220446049250313e-16` |
