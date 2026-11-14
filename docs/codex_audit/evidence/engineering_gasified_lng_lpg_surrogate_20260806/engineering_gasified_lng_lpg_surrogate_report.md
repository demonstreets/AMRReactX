# Engineering Gasified LNG/LPG Surrogate Capability Boundary

- Status: `PASS-ENGINEERING-GASIFIED-LNG-LPG-SURROGATE-BOUNDARY`
- Gasified LNG CH4 surrogate template ready: `True`
- Gasified LPG C3H8 surrogate template ready: `True`
- Given gas-source surrogate ready: `True`
- Gasified LNG CH4 MPI+CUDA cold-source runtime passed: `True`
- Gasified LNG CH4 cold-source sustained-fire claim allowed: `False`
- Gasified LNG CH4 warmed-vapor fire runtime passed: `True`
- Gasified LNG CH4 warmed-vapor sustained-fire claim allowed: `True`
- Gasified LPG C3H8 MPI+CUDA fire runtime passed: `True`
- Liquid rupture/flash/pool evaporation ready: `False`
- LNG/LPG phase-change production claim allowed: `False`

## Templates

- `gasified_lng_ch4_surrogate`: `examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke`, fuel `CH4`, leak_T `200.0`, cloud_T `220.0`
- `gasified_lng_ch4_warmed_vapor_fire_surrogate`: `examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_warmed_fire_surrogate_mpicuda_500step`, fuel `CH4`, leak_T `300.0`, cloud_T `300.0`
- `gasified_lpg_c3h8_surrogate`: `examples/engineering/h2_leak_3d/input.codex_gasified_lpg_c3h8_surrogate_smoke`, fuel `C3H8`, leak_T `300.0`, cloud_T `300.0`

## Runtime

- `gasified_lng_ch4_mpi_cuda`: peak T `733.501`, peak |HeatRelease| `0.00229351`, final Y(H2O) `3.79486e-16`, rank-mapped `True`
- `gasified_lng_ch4_warmed_vapor_fire_mpi_cuda`: peak T `2460.18`, peak |HeatRelease| `3.60881e+09`, final Y(H2O) `6.32298e-05`, rank-mapped `True`
- `gasified_lpg_c3h8_mpi_cuda`: peak T `2715.91`, peak |HeatRelease| `4.02289e+08`, final Y(H2O) `2.20096e-06`, rank-mapped `True`

## Boundary

Supported now:
- gas-phase fuel source selected by prob.fuel_species
- pre-vaporized methane-rich LNG surrogate cloud/source
- pre-vaporized and warmed methane-rich LNG fire surrogate after gas has reached flammable thermal conditions
- pre-vaporized propane LPG surrogate cloud/source
- delayed ignition/fire probes when the selected chemistry mechanism supports the fuel

Not supported now:
- liquid tank rupture mechanics
- flashing two-phase discharge
- liquid pool spread and evaporation
- cryogenic ground/wall heat-transfer closure
- sustained fire validation for still-cold cryogenic LNG vapor clouds
- aerosol/droplet rainout and multi-component LNG/LPG fractionation

## Evidence

- `gasified_lng_ch4_surrogate_input`: `examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke`
- `gasified_lng_ch4_warmed_vapor_fire_input`: `examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_warmed_fire_surrogate_mpicuda_500step`
- `gasified_lpg_c3h8_surrogate_input`: `examples/engineering/h2_leak_3d/input.codex_gasified_lpg_c3h8_surrogate_smoke`
- `pelelmex_prob_H`: `examples/engineering/h2_leak_3d/pelelmex_prob.H`
- `pelelmex_prob_cpp`: `examples/engineering/h2_leak_3d/pelelmex_prob.cpp`
- `ch4_cold_plume_report`: `docs/codex_audit/evidence/engineering_ch4_cold_plume_cpu_probe_20260806/engineering_ch4_cold_plume_cpu_probe_report.json`
- `ch4_mpi_cuda_500step_fire_report`: `docs/codex_audit/evidence/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_20260806/engineering_ch4_pipe_rack_delayed_ignition_mpi_cuda_500step_report.json`
- `c3h8_cpu_cpu_mpi_single_cuda_mpi_cuda_report`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/engineering_c3h8_gas_phase_cpu_cuda_report.json`
- `lng_ch4_mpicuda_run_log`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lng_ch4_mpicuda/run.log`
- `lng_ch4_mpicuda_run_status`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lng_ch4_mpicuda/run.status`
- `lng_ch4_mpicuda_input`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lng_ch4_mpicuda/input.codex_gasified_lng_ch4_surrogate_smoke`
- `lng_ch4_mpicuda_rank_gpu_wrapper`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lng_ch4_mpicuda/rank_gpu_wrapper.sh`
- `lng_ch4_mpicuda_fextrema`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lng_ch4_mpicuda/fextrema_selected.log`
- `lng_ch4_warmed_fire_mpicuda_run_log`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lng_ch4_warmed_fire_mpicuda/run.log`
- `lng_ch4_warmed_fire_mpicuda_run_status`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lng_ch4_warmed_fire_mpicuda/run.status`
- `lng_ch4_warmed_fire_mpicuda_input`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lng_ch4_warmed_fire_mpicuda/input.codex_gasified_lng_ch4_warmed_fire_surrogate_mpicuda_500step`
- `lng_ch4_warmed_fire_mpicuda_rank_gpu_wrapper`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lng_ch4_warmed_fire_mpicuda/rank_gpu_wrapper.sh`
- `lng_ch4_warmed_fire_mpicuda_fextrema`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lng_ch4_warmed_fire_mpicuda/fextrema_selected.log`
- `lpg_c3h8_mpicuda_run_log`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lpg_c3h8_mpicuda/run.log`
- `lpg_c3h8_mpicuda_run_status`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lpg_c3h8_mpicuda/run.status`
- `lpg_c3h8_mpicuda_input`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lpg_c3h8_mpicuda/input.codex_gasified_lpg_c3h8_surrogate_smoke`
- `lpg_c3h8_mpicuda_rank_gpu_wrapper`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lpg_c3h8_mpicuda/rank_gpu_wrapper.sh`
- `lpg_c3h8_mpicuda_fextrema`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lpg_c3h8_mpicuda/fextrema_selected.log`
- `gasified_surrogate_pipe_rack_stl`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/runtime_evidence/lpg_c3h8_mpicuda/codex_merged_pipe_rack_obstacles.stl`
