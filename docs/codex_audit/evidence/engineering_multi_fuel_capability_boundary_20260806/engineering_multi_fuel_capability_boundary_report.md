# Engineering Multi-Fuel Capability Boundary

- Status: `PASS-ENGINEERING-MULTI-FUEL-CAPABILITY-BOUNDARY`
- Current engineering chemistry model: `LiDryer`
- H2 engineering current scope ready: `True`
- Engineering source is H2-specific: `False`
- Source fuel species configurable: `True`
- H2 default fuel-species probe passed: `True`
- CH4 fuel-species probe passed: `True`
- CH4 CPU/MPI/CUDA cold-plume probe passed: `True`
- CH4 delayed-ignition single-CUDA fire probe passed: `True`
- CH4 delayed-ignition CPU/MPI fire probe passed: `True`
- CH4 delayed-ignition MPI+CUDA fire probe passed: `True`
- CH4 delayed-ignition MPI+CUDA 500-step fire probe passed: `True`
- C3H8 gas-phase CPU/CUDA probe passed: `True`
- C3H8 gas-phase CPU/MPI/CUDA probe passed: `True`
- C3H8 gas-phase CPU/CPU-MPI/single-CUDA/MPI-CUDA probe passed: `True`
- C3H8 propane gas-phase initial ready: `True`
- Gasified LNG/LPG surrogate boundary passed: `True`
- Gasified LNG given-source surrogate ready: `True`
- Gasified LPG given-source surrogate ready: `True`
- Gasified LNG CH4 MPI+CUDA runtime passed: `True`
- Gasified LNG CH4 cold-source sustained-fire claim allowed: `False`
- Gasified LNG CH4 warmed-vapor MPI+CUDA fire probe passed: `True`
- Gasified LNG CH4 warmed-vapor sustained-fire claim allowed: `True`
- Gasified LPG C3H8 MPI+CUDA fire probe passed: `True`
- External-vaporization CH4 time-series CUDA runtime passed: `True`
- External-vaporization C3H8 time-series CUDA runtime passed: `True`
- External-vaporization multi-fuel time-series CUDA runtime passed: `True`
- Liquefied-release source model passed: `True`
- Liquefied-release source model negative selftest passed: `True`
- Liquefied-release source model CUDA smoke passed: `True`
- Liquefied-release source balance passed: `True`
- Liquefied-release source balance negative selftest passed: `True`
- Liquefied-release source balance total gas mass kg: `6.262612621214`
- Liquefied-release source balance max inventory mass relative error: `0.06546339683315126`
- Multi-fuel production ready: `False`
- Gasified LNG production ready: `False`
- Liquefied-gas phase-change ready: `False`

## Capability Matrix

- `h2_gas_leak_dispersion_ignition_fire`: `CURRENT_SCOPE_READY`, production claim allowed: `True`
- `methane_or_natural_gas_gas_phase`: `CH4_CPU_MPI_CUDA_COLD_PLUME_AND_CPU_MPI_SINGLE_CUDA_MPI_CUDA_FIRE_PASS_BUT_NOT_PRODUCTION_VERIFIED`, production claim allowed: `False`
- `propane_gas_phase`: `INITIAL_C3H8_GAS_PHASE_CPU_CPU_MPI_SINGLE_CUDA_AND_MPI_CUDA_FIRE_PROBES_PASS_BUT_NOT_PRODUCTION_VERIFIED`, production claim allowed: `False`
- `gasified_lng_or_simplified_natural_gas_cloud`: `GASIFIED_CH4_SURROGATE_TEMPLATE_AND_MPI_CUDA_COLD_SOURCE_RUNTIME_PASS_NOT_CRYOGENIC_FIRE_PRODUCTION_VERIFIED`, production claim allowed: `False`
- `liquefied_gas_tank_rupture_flash_vaporization_pool_evaporation`: `INTERNAL_PHASE_CHANGE_NOT_IMPLEMENTED_SCREENING_RELEASE_TO_GAS_SOURCE_GENERATOR_AND_CUDA_SMOKE_PASS`, production claim allowed: `False`

## Promotion Gates

- `configurable_fuel_species_source`: `passed_for_H2_CH4_C3H8_source_selection`
- `mechanism_specific_builds`: `passed_for_CH4_and_C3H8_CPU_CPU_MPI_SINGLE_CUDA_MPI_CUDA_initial_probes`
- `fuel_specific_fire_validation`: `initial_CH4_and_C3H8_reduced_fire_probes_pass_external_thresholds_and_production_duration_missing`
- `liquefied_gas_phase_change_model`: `missing`

## Limitations

- This is a capability-boundary audit, not a multi-fuel production validation.
- H2 remains the only engineering gas leak/fire scenario with current long CPU/GPU evidence.
- CH4 has short CPU, CPU/MPI, and single-CUDA cold-plume evidence plus reduced CPU/MPI, single-CUDA, rank-mapped MPI+CUDA, and 500-step MPI+CUDA delayed-ignition fire probes, not scenario-scale natural-gas production validation.
- CH4 and C3H8 now also have CUDA runtime evidence for time-varying external-vaporization engineering sources with STL pipe-rack obstacles.
- C3H8 has gas-phase cold source plus reduced CPU, CPU/MPI, single-CUDA, rank-mapped MPI+CUDA propane_fc delayed-ignition fire probes, and external-vaporization-source CUDA evidence, not dense-gas, external-threshold, or production-duration validation.
- Gasified LNG/LPG given-source surrogates now have templates, 2-rank/2-GPU runtime evidence, CH4/C3H8 time-varying external-source CUDA evidence, generated-input CUDA smoke evidence, source-schedule mass-balance evidence, and negative selftests for the screening liquefied-release source generator; the LNG cold-source run is stable but does not claim sustained cryogenic fire validation, and internal liquefied-gas rupture, flashing, pool evaporation, and cryogenic dense-cloud production validation remain outside the current scope.
