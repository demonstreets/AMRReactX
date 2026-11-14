# Engineering External Vaporization Multi-Fuel Source Matrix

- Status: `PASS-ENGINEERING-EXTERNAL-VAPORIZATION-MULTIFUEL-SOURCE-MATRIX`
- Supported species: `C3H8, CH4, H2`
- All species schedule generation ready: `True`
- Phase change not claimed: `True`
- H2 CUDA time-series runtime passed: `True`
- CH4 runtime evidence passed: `True`
- C3H8 runtime evidence passed: `True`

## Species Matrix

- `H2`: schedule_ready=`True`, point_count=`4`
- `CH4`: schedule_ready=`True`, point_count=`4`
- `C3H8`: schedule_ready=`True`, point_count=`4`

## Evidence

- `converter`: `tools/codex_make_external_vaporization_source_input.py`
- `h2_timeseries_cuda_report`: `docs/codex_audit/evidence/engineering_external_vaporization_timeseries_cuda_20260807/engineering_external_vaporization_timeseries_cuda_report.json`
- `ch4_500step_report`: `docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_20260806/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.json`
- `c3h8_matrix_report`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/engineering_c3h8_gas_phase_cpu_cuda_report.json`
- `liquefied_external_vaporization_contract`: `docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/engineering_liquefied_external_vaporization_contract_report.json`
- `H2_base_input`: `examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_timeseries_smoke`
- `H2_source_csv`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/h2_external_vaporization_timeseries.csv`
- `H2_generated_input`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/input.codex_h2_external_vaporization_timeseries`
- `H2_mapping_json`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/h2_external_vaporization_timeseries_mapping.json`
- `CH4_base_input`: `examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke`
- `CH4_source_csv`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/ch4_external_vaporization_timeseries.csv`
- `CH4_generated_input`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/input.codex_ch4_external_vaporization_timeseries`
- `CH4_mapping_json`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/ch4_external_vaporization_timeseries_mapping.json`
- `C3H8_base_input`: `examples/engineering/h2_leak_3d/input.codex_gasified_lpg_c3h8_surrogate_smoke`
- `C3H8_source_csv`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/c3h8_external_vaporization_timeseries.csv`
- `C3H8_generated_input`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/input.codex_c3h8_external_vaporization_timeseries`
- `C3H8_mapping_json`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/c3h8_external_vaporization_timeseries_mapping.json`
