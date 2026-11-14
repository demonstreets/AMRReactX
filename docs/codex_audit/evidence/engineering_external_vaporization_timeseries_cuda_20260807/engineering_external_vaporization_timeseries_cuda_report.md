# Engineering External Vaporization Time Series CUDA

- Status: `PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES-CUDA`
- CUDA 12.6 environment: `True`
- CUDA SUNDIALS path used: `True`
- Run finalized: `True`
- Steps: `[0, 1, 2, 3, 4, 5]`
- Smoke log clean: `True`
- Schedule mdot range: `5e-06` to `1.75e-05`
- Schedule temperature range: `270.0` to `310.0`
- Schedule velocity x range: `0.4375` to `1.25`
- Schedule radius range: `0.1075` to `0.1425`
- Schedule center x range: `0.4625` to `0.5875`

## Evidence

- `cpu_timeseries_report`: `docs/codex_audit/evidence/engineering_external_vaporization_timeseries_20260806/engineering_external_vaporization_timeseries_report.json`
- `smoke_input`: `examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_timeseries_smoke`
- `cuda_executable`: `examples/engineering/h2_leak_3d/PeleLMeX3d.gnu.CUDA.ex`
- `environment_log`: `docs/codex_audit/evidence/engineering_external_vaporization_timeseries_cuda_20260807/environment.log`
- `build_relink_log`: `docs/codex_audit/evidence/engineering_external_vaporization_timeseries_cuda_20260807/build_relink.log`
- `run_status`: `docs/codex_audit/evidence/engineering_external_vaporization_timeseries_cuda_20260807/run_status.txt`
- `cuda_run_log`: `docs/codex_audit/evidence/engineering_external_vaporization_timeseries_cuda_20260807/fixed_mass_flow_timeseries_cuda.log`
