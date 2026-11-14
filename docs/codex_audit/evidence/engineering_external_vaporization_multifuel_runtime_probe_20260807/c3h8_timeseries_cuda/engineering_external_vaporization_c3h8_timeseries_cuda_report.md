# Engineering External Vaporization C3H8 Time Series CUDA

- Status: `PASS-ENGINEERING-EXTERNAL-VAPORIZATION-C3H8-TIMESERIES-CUDA`
- Fuel species C3H8 selected: `True`
- CUDA 12.6 environment: `True`
- CUDA SUNDIALS path used: `True`
- STL obstacles built: `True`
- Run finalized: `True`
- Steps: `[0, 1, 2, 3, 4, 5]`
- Smoke log clean: `True`
- Leak schedule unused: `False`
- Schedule mdot range: `4e-12` to `4.4e-11`
- Schedule temperature range: `285.0000003` to `285.0000033`
- Schedule radius range: `0.0800000003` to `0.0800000033`

## Evidence

- `source_matrix_report`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_source_matrix_20260807/engineering_external_vaporization_multifuel_source_matrix_report.json`
- `generated_c3h8_input`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/c3h8_timeseries_cuda/run/input.codex_c3h8_external_vaporization_timeseries`
- `stl_obstacles`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/c3h8_timeseries_cuda/run/codex_merged_pipe_rack_obstacles.stl`
- `cuda_executable`: `examples/engineering/h2_leak_3d/codex_c3h8_timeseries_probe3d.gnu.CUDA.ex`
- `environment_log`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/c3h8_timeseries_cuda/environment.log`
- `build_log`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/c3h8_timeseries_cuda/build.log`
- `run_status`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/c3h8_timeseries_cuda/run.status`
- `cuda_run_log`: `docs/codex_audit/evidence/engineering_external_vaporization_multifuel_runtime_probe_20260807/c3h8_timeseries_cuda/run.log`
