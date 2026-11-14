# Engineering C3H8 Gas-Phase CPU/MPI/CUDA Evidence

- Status: `PASS-ENGINEERING-C3H8-GAS-PHASE-CPU-CPU-MPI-SINGLE-CUDA-MPI-CUDA`
- C3H8 cold plume CPU passed: `True`
- C3H8 propane_fc CPU fire passed: `True`
- C3H8 propane_fc CPU/MPI fire passed: `True`
- C3H8 propane_fc CUDA fire passed: `True`
- C3H8 propane_fc MPI+CUDA fire passed: `True`
- C3H8 rank-mapped two-GPU MPI+CUDA passed: `True`
- Propane gas-phase production ready: `False`
- LPG/liquefied propane phase-change ready: `False`

## Fire Metrics

| Platform | Peak T [K] | Peak abs HeatRelease | Final max Y(H2O) | Final max Y(CO2) | Min I_R(C3H8) |
| --- | ---: | ---: | ---: | ---: | ---: |
| CPU | 2715.91 | 4.02292e+08 | 2.20609e-06 | 1.95309e-08 | -85.3911 |
| CPU/MPI | 2715.91 | 4.02292e+08 | 2.20609e-06 | 1.9531e-08 | -85.3911 |
| CUDA | 2715.91 | 4.02294e+08 | 2.20103e-06 | 1.94374e-08 | -85.3914 |
| MPI+CUDA | 2715.91 | 4.02291e+08 | 2.2011e-06 | 1.94401e-08 | -85.3911 |

## Limitations

- This validates gas-phase C3H8 source injection and reduced pipe-rack ignition/fire probes only.
- It does not validate LPG tank rupture, flashing, liquid-pool evaporation, droplet breakup, or cold dense-gas ground slumping.
- External propane fire/plume comparison thresholds remain required before a production propane safety claim.

## Evidence

- `cold_cpu_run_log`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/cold_cpu/run.log` sha256=`03ec8160bbf08eeace2dffd714768adb8e7722ec00c1c64ef346ca2f6a459782`
- `cold_cpu_input`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/cold_cpu/input.c3h8_cold_plume_10step` sha256=`8825ce2aac8e7b9912d4e9391a3646d3d0adcb778dd6dd94432ff1f827a38eef`
- `cpu_fire_run_log`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_cpu/run.log` sha256=`04ed976602577fb9b2a5d96f89161ad2f1034351ea6909047fab34744c49f9df`
- `cpu_fire_input`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_cpu/input.codex_c3h8_pipe_rack_delayed_ignition_cpu_120step` sha256=`821416aa6e05a6681586047480d2bfd8a9cb98ba9ffb310a31013c1b123bed05`
- `cpu_fire_fextrema`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_cpu/fextrema_selected.log` sha256=`54138c10d317c35533c2e3bb4634f046d0b6c4f8d05514e3c5b2eb19c09e0ed6`
- `mpi_fire_run_log`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_mpi/run.log` sha256=`d6d4e0f3e3e914fca2fa8e0566df87b4663109425a279b4029e1bd5b455aa973`
- `mpi_fire_input`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_mpi/input.codex_c3h8_pipe_rack_delayed_ignition_mpi_120step` sha256=`72e8fd9d44c3952309153e4dcfd9b84769e712d3c4a4bd1d2cb53aabc1e169ae`
- `mpi_fire_fextrema`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_mpi/fextrema_selected.log` sha256=`d44f04d80ea5cf8ca8c71d46eac6d23c87bd9200c4894d5fe05a964c12b900ab`
- `cuda_fire_run_log`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_cuda/run.log` sha256=`922c4589842652680a14dcc8f1696c31f278a25b644cc52a014d2c2b52d36c72`
- `cuda_fire_input`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_cuda/input.codex_c3h8_pipe_rack_delayed_ignition_cuda_120step` sha256=`bfd2a7419dacbcf74405885e3f4bd7a566d260ba90790d5ff77614e5c18951dc`
- `cuda_fire_fextrema`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_cuda/fextrema_selected.log` sha256=`324476c78ec8a669cdcb77a1674076c3d513988927e5191cc1c197dc5b8ca4f1`
- `mpicuda_fire_run_log`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_mpicuda/run.log` sha256=`86781ac2df11abfb0ca5a3f0513a59104dfbabb25988f8e3de310dd8576690c7`
- `mpicuda_fire_input`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_mpicuda/input.codex_c3h8_pipe_rack_delayed_ignition_mpicuda_rankmapped_120step` sha256=`3337d5d15e4aea617d4fffafc028f9a7261f0f803e1f175e5445080d9bf16f20`
- `mpicuda_fire_fextrema`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_mpicuda/fextrema_selected.log` sha256=`90d690925a598473d461239d3a349497a0c62e77304a5ebb6b5e37cf2689c278`
- `mpicuda_rank_gpu_wrapper`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_mpicuda/rank_gpu_wrapper.sh` sha256=`4fe1a317eb3055d2be75a0b37994573abc533931c19284e8ae66dec760d92fd0`
- `propane_fc_cpu_clean_build`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_cpu/propane_fc_cpu_clean_build.log` sha256=`608190e93bf965bfdcd080d6817e603f63475e6262f27536dfffd8c817fab569`
- `propane_fc_mpi_clean_build`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_mpi/propane_fc_mpi_clean_build.log` sha256=`e94e0fc4e63a7c8f44c1b25379c671907441a8e6b712f7c7732216015feedf68`
- `propane_fc_cuda_clean_build`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_cuda/propane_fc_cuda_clean_build.log` sha256=`f6d42fe81b043c35bdf46f2f30a3f84eab9bfb5009add0cd359376a66e992c88`
- `propane_fc_mpicuda_clean_build`: `docs/codex_audit/evidence/engineering_c3h8_gas_phase_cpu_cuda_20260806/runtime_evidence/fire_mpicuda/propane_fc_mpicuda_clean_build.log` sha256=`3a3f5b3c14f53b95c42669da0127874159f4c449adeef5c4a4cfb13f80e9d4a8`
