# Engineering External Vaporization CH4 Time Series CUDA

- Status: `PASS-ENGINEERING-EXTERNAL-VAPORIZATION-CH4-TIMESERIES-CUDA`
- Fuel species CH4 selected: `True`
- CUDA 12.6 environment: `True`
- CUDA SUNDIALS path used: `True`
- STL obstacles built: `True`
- Run finalized: `True`
- Steps: `[0, 1, 2, 3, 4, 5]`
- Smoke log clean: `True`
- Leak schedule unused: `False`
- Schedule mdot range: `4e-11` to `4.4e-10`
- Schedule temperature range: `285.000003` to `285.000033`
- Schedule radius range: `0.080000003` to `0.080000033`

## Evidence

- `source_matrix_report`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/engineering_external_vaporization_multifuel_source_matrix_report.json`
- `generated_ch4_input`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/ch4_timeseries_cuda/run/input.codex_ch4_external_vaporization_timeseries`
- `stl_obstacles`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/ch4_timeseries_cuda/run/codex_merged_pipe_rack_obstacles.stl`
- `cuda_executable`: `examples/engineering/h2_leak_3d/codex_ch4_timeseries_probe3d.gnu.CUDA.ex`
- `environment_log`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/ch4_timeseries_cuda/environment.log`
- `build_log`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/ch4_timeseries_cuda/build.log`
- `run_status`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/ch4_timeseries_cuda/run.status`
- `cuda_run_log`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/ch4_timeseries_cuda/run.log`
