# Academic gas-liquid detonation CUDA scout report

- status: PASS-ACADEMIC-GAS-LIQUID-DETONATION-CUDA-SCOUT
- case: academic_shock_droplet_reacting_spray_detonation_cuda_scout
- run_root: /home/cj/my-pele/docs/codex_audit/evidence/academic_gas_liquid_detonation_cuda_scout_20260731

## Runs

- single_gpu_reacting_spray_detonation_40step: 1 MPI ranks, 1 CUDA devices, max_step=40, final_time=8.98783206e-07
- mpi_cuda_reacting_spray_detonation_40step: 2 MPI ranks, 2 CUDA devices, max_step=40, final_time=8.98783206e-07

## Limitations

- Scout gate only: 40-step reduced-resolution run, not a long-duration two-phase detonation validation.
- This complements, but does not replace, the existing CPU gas-liquid detonation certification and budget evidence.
- The case proves CUDA/MPI+CUDA runtime viability for reacting spray physics; production-grade two-phase detonation still needs longer stability and quantitative validation windows.
