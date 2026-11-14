# Engineering Multi-Fuel Operator Runbook

This runbook records the evidence-backed engineering fuel scope for the h2_leak_3d example family.

## Verification Commands

```bash
python3 tools/write_engineering_gasified_lng_lpg_surrogate_report.py
bash tools/verify_engineering_gasified_lng_lpg_surrogate.sh
python3 tools/write_engineering_multi_fuel_capability_boundary_report.py
bash tools/verify_engineering_multi_fuel_capability_boundary.sh
python3 tools/codex_make_external_vaporization_source_input.py --source-csv examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv --base-input examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke --time 2.0 --output-input docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/input.codex_lng_external_vaporization_source_t2s --output-json docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/external_vaporization_source_mapping_t2s.json
python3 tools/write_engineering_liquefied_external_vaporization_contract_report.py
bash tools/verify_engineering_liquefied_external_vaporization_contract.sh
python3 tools/codex_make_liquefied_release_vaporization_csv.py --fluid LNG_CH4 --inventory-kg 25.0 --initial-pressure-Pa 650000.0 --hole-diameter-m 0.020 --duration-s 8.0 --points 9 --liquid-T-K 125.0 --vapor-T-K 285.0 --output-csv docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/lng_ch4_screening_release/lng_ch4_screening_release_source.csv --output-json docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/lng_ch4_screening_release/lng_ch4_screening_release_source_model.json
python3 tools/write_engineering_liquefied_release_vaporization_source_model_report.py
bash tools/verify_engineering_liquefied_release_vaporization_source_model.sh
python3 tools/write_engineering_liquefied_release_vaporization_source_model_negative_selftest_report.py
bash tools/verify_engineering_liquefied_release_vaporization_source_model_negative_selftest.sh
bash tools/run_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh
python3 tools/write_engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.py
bash tools/verify_engineering_liquefied_release_vaporization_source_model_cuda_smoke.sh
python3 tools/write_engineering_liquefied_external_vaporization_negative_selftest_report.py
bash tools/verify_engineering_liquefied_external_vaporization_negative_selftest.sh
python3 tools/write_engineering_fixed_mass_flow_valve_schedule_report.py
bash tools/verify_engineering_fixed_mass_flow_valve_schedule.sh
python3 tools/write_engineering_external_vaporization_timeseries_report.py
bash tools/verify_engineering_external_vaporization_timeseries.sh
python3 tools/write_engineering_external_vaporization_timeseries_cuda_report.py
bash tools/verify_engineering_external_vaporization_timeseries_cuda.sh
python3 tools/write_engineering_external_vaporization_multifuel_source_matrix_report.py
bash tools/verify_engineering_external_vaporization_multifuel_source_matrix.sh
python3 tools/write_engineering_external_vaporization_c3h8_timeseries_cuda_report.py
bash tools/verify_engineering_external_vaporization_c3h8_timeseries_cuda.sh
bash tools/codex_verify_current_scope.sh
```

Expected status for the screening liquefied-release source-model bridge: `PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL`.
Expected negative-selftest status for the screening liquefied-release source-model bridge: `PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-NEGATIVE-SELFTEST`.
Expected CUDA-smoke status for generated liquefied-release inputs: `PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE`.

## Claim Boundary Quick Reference

- Gas-phase CFD claim: H2, CH4, and C3H8 gas sources can be selected when the compiled mechanism contains the species.
- Liquid-release bridge claim: LNG_CH4 and LPG_C3H8 rupture screening can be converted to generated gas-source CSV/PeleLMeX inputs.
- CFD-internal phase-change claim: not allowed for flashing discharge, liquid pool spread, or pool evaporation.
- Generated LNG_CH4 and LPG_C3H8 source inputs have CUDA smoke evidence.

## Fuel Selection

Use `prob.fuel_species` to choose the gas-phase source species supported by the compiled chemistry mechanism.

| Fuel or surrogate | Current evidence-backed status | Production claim | Primary input/report |
|---|---|---|---|
| `H2` | `current engineering production-scope gas leak/diffusion/fire ready` | `allowed for current H2 scope` | `docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cross_platform_20260805/engineering_h2_pipe_rack_delayed_ignition_cross_platform_report.json` |
| `CH4` | `gas-phase natural-gas surrogate fire evidence exists through 500-step MPI+CUDA` | `not natural-gas production validated` | `docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_20260806/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.json` |
| `C3H8` | `gas-phase propane/LPG surrogate fire evidence exists through CPU/CPU-MPI/single-CUDA/MPI-CUDA` | `not propane production validated` | `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/engineering_c3h8_gas_phase_cpu_cuda_report.json` |
| `gasified LNG` | `cold CH4 source stable; warmed CH4 fire surrogate passes 500-step MPI+CUDA` | `not cryogenic LNG production validated` | `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/engineering_gasified_lng_lpg_surrogate_report.json` |
| `gasified LPG` | `C3H8 gasified LPG fire surrogate passes 120-step MPI+CUDA` | `not liquid LPG rupture/phase-change validated` | `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/engineering_gasified_lng_lpg_surrogate_report.json` |
| `liquefied gas rupture/flash/pool evaporation` | `not implemented internally; screening rupture-to-gas-source generator and external gas-phase vaporization source contract exist` | `not allowed for CFD-internal phase change` | `docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/engineering_liquefied_release_vaporization_source_model_report.json` |

## Gasified LNG/LPG Inputs

- `input.codex_gasified_lng_ch4_surrogate_smoke`: cold gasified LNG/CH4 source stability probe.
- `input.codex_gasified_lng_ch4_warmed_fire_surrogate_mpicuda_500step`: warmed gasified LNG/CH4 fire surrogate.
- `input.codex_gasified_lpg_c3h8_surrogate_smoke`: gasified LPG/C3H8 fire surrogate.

## External Vaporization Source Contract

- `codex_lng_external_vaporization_source_template.csv`: template for an external vaporization model time series.
- The external vaporization model supplies gas-phase source data; the CFD mapping uses `prob.leak_model = fixed_mass_flow`.
- `input.codex_fixed_mass_flow_valve_schedule_smoke` verifies scheduled fixed gas-source ramping through `fixed_mass_flow_scheduled`.
- `input.codex_fixed_mass_flow_timeseries_smoke` verifies external `mdot(t)`, `vapor_T(t)`, `velocity(t)`, and single-source `radius/location(t)` coupling through `prob.leak_schedule_times`, `prob.leak_schedule_rates`, `prob.leak_schedule_temperatures`, `prob.leak_schedule_vel_x`, `prob.leak_schedule_vel_y`, `prob.leak_schedule_vel_z`, `prob.leak_schedule_radius`, `prob.leak_schedule_x`, `prob.leak_schedule_y`, `prob.leak_schedule_z`, and `fixed_mass_flow_timeseries`.
- `PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES-CUDA` verifies the same external vaporization time-series source path on a single Tesla P100 CUDA run using CUDA 12.6 and CUDA-enabled SUNDIALS.
- `PASS-ENGINEERING-EXTERNAL-VAPORIZATION-MULTIFUEL-SOURCE-MATRIX` verifies generated external vaporization `mdot(t)` source inputs for `H2`, `CH4`, and `C3H8`; CH4/C3H8 runtime evidence remains gas-phase surrogate evidence, not liquid LNG/LPG phase-change validation.
- `PASS-ENGINEERING-EXTERNAL-VAPORIZATION-C3H8-TIMESERIES-CUDA` verifies a rebuilt `propane_fc` CUDA executable reads the generated `C3H8` external vaporization time-series source, builds the pipe-rack STL EB geometry, and completes a single-GPU runtime probe without unused `prob.leak_schedule_*` parameters.
- `cfd_solves_liquid_phase_change = false`
- `cfd_solves_flashing_discharge = false`
- `cfd_solves_pool_spread_evaporation = false`
- External source negative cases refused: negative mass flow, unknown species, nonmonotonic time, missing required columns, mixed species, and negative sample time.

## Boundaries

- `lng_lpg_production_phase_change_claim_allowed = false`
- Not implemented: liquid tank rupture mechanics.
- Not implemented: flashing two-phase discharge.
- Not implemented: liquid pool spread and evaporation.
- Not implemented: cryogenic ground/wall heat-transfer closure.

## Evidence Reports

- `multi_fuel_boundary`: `docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/engineering_multi_fuel_capability_boundary_report.json`
- `gasified_lng_lpg_surrogate`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/engineering_gasified_lng_lpg_surrogate_report.json`
- `liquefied_external_vaporization_contract`: `docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/engineering_liquefied_external_vaporization_contract_report.json`
- `liquefied_release_vaporization_source_model`: `docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/engineering_liquefied_release_vaporization_source_model_report.json`
- `liquefied_release_vaporization_source_model_negative_selftest`: `docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_negative_selftest_20260807/engineering_liquefied_release_vaporization_source_model_negative_selftest_report.json`
- `liquefied_release_vaporization_source_model_cuda_smoke`: `docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_cuda_smoke_20260807/engineering_liquefied_release_vaporization_source_model_cuda_smoke_report.json`
- `liquefied_external_vaporization_negative_selftest`: `docs/codex_audit/evidence/engineering_liquefied_external_vaporization_negative_selftest_20260806/engineering_liquefied_external_vaporization_negative_selftest_report.json`
- `fixed_mass_flow_valve_schedule`: `docs/codex_audit/evidence/engineering_fixed_mass_flow_valve_schedule_20260806/engineering_fixed_mass_flow_valve_schedule_report.json`
- `external_vaporization_timeseries`: `docs/codex_audit/evidence/engineering_external_vaporization_timeseries_20260806/engineering_external_vaporization_timeseries_report.json`
- `external_vaporization_timeseries_cuda`: `docs/codex_audit/evidence/engineering_external_vaporization_timeseries_cuda_20260807/engineering_external_vaporization_timeseries_cuda_report.json`
- `external_vaporization_multifuel_source_matrix`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/engineering_external_vaporization_multifuel_source_matrix_report.json`
- `c3h8_external_vaporization_timeseries_cuda`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/c3h8_timeseries_cuda/engineering_external_vaporization_c3h8_timeseries_cuda_report.json`
- `c3h8_matrix`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/engineering_c3h8_gas_phase_cpu_cuda_report.json`
- `ch4_500step_mpi_cuda_fire`: `docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_20260806/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.json`
- `h2_cross_platform`: `docs/codex_audit/evidence/engineering_h2_pipe_rack_delayed_ignition_cross_platform_20260805/engineering_h2_pipe_rack_delayed_ignition_cross_platform_report.json`
