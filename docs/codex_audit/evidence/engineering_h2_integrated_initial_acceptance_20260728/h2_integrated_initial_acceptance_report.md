# Engineering H2 Integrated Initial Acceptance

- Status: `PASS-H2-INTEGRATED-ENGINEERING-INITIAL-ACCEPTANCE`
- Clears initial integrated engineering goal: `True`
- Clears full production certification: `False`

## Scope

Complex-obstacle open-area H2 leak, dispersion, ignition, sustained reacting fire, CPU/GPU/MPI-CUDA stability, and conservation/physical-law sanity checks.

## Criteria

### complex_obstacle_open_area_leak_dispersion_fire
- `status`: `PASS-H2-PIPE-RACK-GPU-FIRE-OBSTACLE-SMOKE`
- `cpu_mass_ratio`: `1.00000188`
- `gpu_mass_ratio`: `1.00000188`
- `mpi_cuda_mass_ratio`: `1.00000188`
- `mpi_cuda_ranks`: `2`
- `mpi_cuda_devices`: `2`
- `obstacle_sources`: `['codex_cube_block.stl', 'codex_vertical_cylinder.stl', 'codex_pipe_rack.stl']`
- `fire_screening_status`: `PASS-SCREENING`

### large_amr_engineering_conservation
- `status`: `PASS-H2-LARGE-ENGINEERING-ACCEPTANCE`
- `max_step`: `120`
- `base_cell_count`: `221184`
- `equivalent_finest_cell_count`: `1769472`
- `baseline_final_mass_ratio`: `1.0`
- `amr_final_mass_ratio`: `1.00001907`
- `amr_regrid_count`: `59`

### single_cuda_stiff_reacting_fire_2000step
- `status`: `PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-SUSTAINED`
- `max_step`: `2000`
- `mpi_ranks`: `1`
- `cuda_devices`: `1`
- `plotfile_count`: `9`
- `sustained_output_count`: `8`
- `final_time`: `2.000000000000062e-05`
- `final_y_h2o_max`: `0.1502349990492146`

### mpi_cuda_stiff_reacting_fire_2000step
- `status`: `PASS-H2-PIPE-RACK-DIRECT-REACTING-MPI-CUDA-SUSTAINED`
- `max_step`: `2000`
- `mpi_ranks`: `2`
- `cuda_devices`: `2`
- `plotfile_count`: `9`
- `sustained_output_count`: `8`
- `final_time`: `2.000000000000062e-05`
- `final_y_h2o_max`: `0.15023479617720176`

### largegrid_single_cuda_reacting
- `status`: `PASS-H2-PIPE-RACK-DIRECT-REACTING-SINGLE-CUDA-SUSTAINED`
- `max_step`: `300`
- `mpi_ranks`: `1`
- `cuda_devices`: `1`
- `plotfile_count`: `5`
- `sustained_output_count`: `4`
- `final_time`: `2.9999999999999814e-06`
- `final_y_h2o_max`: `0.016843226873608983`

### largegrid_mpi_cuda_reacting
- `status`: `PASS-H2-PIPE-RACK-DIRECT-REACTING-MPI-CUDA-SUSTAINED`
- `max_step`: `300`
- `mpi_ranks`: `2`
- `cuda_devices`: `2`
- `plotfile_count`: `5`
- `sustained_output_count`: `4`
- `final_time`: `2.9999999999999814e-06`
- `final_y_h2o_max`: `0.016843226873556934`

### mpi_cuda_checkpoint_restart
- `status`: `PASS-H2-PIPE-RACK-DIRECT-REACTING-MPI-CUDA-RESTART-SUSTAINED`
- `mpi_ranks`: `2`
- `cuda_devices`: `2`
- `post_restart_sustained_output_count`: `4`
- `final_y_h2o_max`: `0.13344498290244958`

### fire_consequence_formula_traceability
- `status`: `PASS-H2-FIRE-CONSEQUENCE-TRACEABILITY`
- `formula_check_count`: `16`
- `distance_check_count`: `2`
- `direct_reacting_check_count`: `3`
- `calibrated_fire_or_blast_model`: `False`

## Deferred Items

- real plant CAD ingestion and boundary-tag QA
- external SBEPV5 or field-test plume time-series agreement
- calibrated radiation/overpressure/fire consequence validation
- production GPU scaling curve beyond the current 2-rank MPI+CUDA gates
