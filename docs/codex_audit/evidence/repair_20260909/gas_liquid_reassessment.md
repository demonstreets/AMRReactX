# Academic Gas-Liquid Detonation Certification

Status: `NOT_READY-ACADEMIC-GAS-LIQUID-DETONATION`

## Summary

- `acd_07_full_gas_liquid_detonation_ready`: `False`
- `clears_acd_07_spray_detonation_gap`: `False`
- `clears_acd_07_full_cellular_gas_liquid_detonation_gap`: `False`
- `clears_acd_07_external_reference_gap`: `False`
- `certification_basis`: `raw chemistry and physical evidence required; existing budget rollups are insufficient`
- `chemistry_checks`: `[{'name': 'heptane_3sp', 'gas_reactions': 0, 'job_info': 'docs/codex_audit/evidence/academic_spray_detonation_validation_20260728/reacting_spray_detonation_1000/plt01000/job_info', 'mechanism_source': '/home/cj/my-pele/external/PeleC/Submodules/PelePhysics/Mechanisms/heptane_3sp/mechanism.H', 'source_sha256': 'aefd60b24205bbfa89b51302ac6205770c4d7ee0613ca6bc15e5efa11fa4299a', 'binary_provenance_verified': False}]`
- `spray_response_pressure_front_shift_cells`: `9.0`
- `spray_response_heat_release_absmax`: `1.56560169`
- `spray_response_particle_growth_factor`: `11.415`
- `spray_response_spray_temp_increase`: `118.466414`
- `spray_source_budget_particle_source_relative_mismatch`: `2.7182461588711962e-08`
- `reacting_cv_total_mass_relative_error`: `5.235416416845343e-06`
- `reacting_cv_total_xmom_relative_error`: `1.3827621650070214e-10`
- `coupled_budget_ready`: `True`
- `interpretation`: `NOT_READY: existing shock/particle transport budgets do not certify gas-liquid detonation. The archived heptane_3sp run is nonreacting; cellular and independent reference validation are absent. Historical metrics are retained as diagnostics.`

## Gates

- `NOT_READY` nonzero_gas_chemistry
- `NOT_READY` cellular_structure_reference
- `NOT_READY` external_reference
- `PASS` reacting_spray_detonation_front_response
- `PASS` reacting_spray_source_budget
- `PASS` reacting_closed_control_volume_budget
- `PASS` closed_gas_particle_coupled_budget_rollup
