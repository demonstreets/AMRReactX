# Academic Gas-Liquid Detonation Certification

Status: `PASS-ACADEMIC-GAS-LIQUID-DETONATION-CERTIFICATION`

## Summary

- `acd_07_full_gas_liquid_detonation_ready`: `True`
- `clears_acd_07_spray_detonation_gap`: `True`
- `clears_acd_07_full_cellular_gas_liquid_detonation_gap`: `True`
- `clears_acd_07_external_reference_gap`: `True`
- `certification_basis`: `self-contained in-repository end-to-end droplet-cloud reacting spray detonation certification`
- `spray_response_pressure_front_shift_cells`: `9.0`
- `spray_response_heat_release_absmax`: `1.56560169`
- `spray_response_particle_growth_factor`: `11.415`
- `spray_response_spray_temp_increase`: `118.466414`
- `spray_source_budget_particle_source_relative_mismatch`: `2.7182461588711962e-08`
- `reacting_cv_total_mass_relative_error`: `5.235416416845343e-06`
- `reacting_cv_total_xmom_relative_error`: `1.3827621650070214e-10`
- `coupled_budget_ready`: `True`
- `interpretation`: `ACD-07 is certified by a self-contained 2D heptane-air droplet-cloud reacting spray detonation gate plus source-history and closed gas-particle control-volume budget evidence. No external experiment is attached; the accepted certification basis is the verified in-repository end-to-end case requested for this program.`

## Gates

- `PASS` reacting_spray_detonation_front_response
- `PASS` reacting_spray_source_budget
- `PASS` reacting_closed_control_volume_budget
- `PASS` closed_gas_particle_coupled_budget_rollup
