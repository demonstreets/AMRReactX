# Engineering H2 Disk Cleanup Audit

Status: `PASS-DISK-CLEANUP-AUDIT`
Destructive actions performed: `False`

## Disk Requirement

- Current free GB: `161.07`
- Required free GB: `20.00`
- Deficit GB: `0.00`
- Requirement passed: `True`

## Cleanup Review Candidates

- Candidate count: `42`
- Candidate total GB: `87.08`
- Candidates cover deficit: `True`

| Label | Class | Size GB | Age days |
| --- | --- | ---: | ---: |
| `examples` | `review_large_case_or_test_data_before_cleanup` | 59.61 | 43.8 |
| `test` | `review_large_case_or_test_data_before_cleanup` | 10.14 | 22.2 |
| `build-gpu2` | `review_generated_or_cache_directory` | 4.33 | 22.6 |
| `build-gpu-mpi` | `review_generated_or_cache_directory` | 1.63 | 22.0 |
| `build-gpu` | `review_generated_or_cache_directory` | 1.45 | 6.7 |
| `build-cpu` | `review_generated_or_cache_directory` | 0.32 | 10.6 |
| `build-cpu-mpi` | `review_generated_or_cache_directory` | 0.30 | 22.0 |
| `build_test` | `review_generated_or_cache_directory` | 0.03 | 26.2 |
| `build-codex-smoke` | `review_generated_or_cache_directory` | 0.01 | 4.0 |
| `build-gpu_BAK_20260712` | `review_generated_or_cache_directory` | 0.01 | 22.9 |
| `build` | `review_generated_or_cache_directory` | 0.00 | 42.9 |
| `backups` | `review_generated_or_cache_directory` | 0.00 | 30.9 |
| `${TMPDIR}/codex_engineering_h2_campaign_full_20260720` | `review_tmp_codex_artifact` | 1.42 | 2.1 |
| `${TMPDIR}/codex_h2_leak_open_domain_plan_amr_hybrid_largegrid_8rank_120step_20260721` | `review_tmp_codex_artifact` | 0.52 | 1.0 |
| `${TMPDIR}/codex_h2_leak_production_mesh_1200step_stability_scout_20260720` | `review_tmp_codex_artifact` | 0.50 | 2.0 |
| `${TMPDIR}/codex_h2_leak_open_domain_plan_amr_hybrid_prodmesh_8rank_600step_20260721` | `review_tmp_codex_artifact` | 0.46 | 1.1 |
| `${TMPDIR}/codex_h2_leak_open_domain_plan_amr_hybrid_prodmesh_600step_20260720` | `review_tmp_codex_artifact` | 0.46 | 1.9 |
| `${TMPDIR}/codex_h2_leak_production_mesh_600step_stability_scout_20260720` | `review_tmp_codex_artifact` | 0.46 | 2.0 |
| `${TMPDIR}/codex_h2_leak_production_mesh_8rank_600step_stability_scout_20260720` | `review_tmp_codex_artifact` | 0.46 | 2.0 |
| `${TMPDIR}/codex_engineering_h2_campaign_core_20260720` | `review_tmp_codex_artifact` | 0.41 | 2.2 |
| `${TMPDIR}/codex_engineering_h2_campaign_source_physics_20260720` | `review_tmp_codex_artifact` | 0.41 | 2.2 |
| `${TMPDIR}/codex_engineering_h2_campaign_amr_mpi_20260720` | `review_tmp_codex_artifact` | 0.25 | 2.2 |
| `${TMPDIR}/codex_h2_leak_open_domain_plan_amr_mpi_rank_sweep_20260720` | `review_tmp_codex_artifact` | 0.25 | 2.2 |
| `${TMPDIR}/codex_h2_leak_long_stability_scout_20260720` | `review_tmp_codex_artifact` | 0.25 | 2.1 |
| `${TMPDIR}/codex_h2_leak_open_domain_plan_amr_sweep_20260720_massfix` | `review_tmp_codex_artifact` | 0.24 | 2.2 |
| `${TMPDIR}/codex_h2_leak_open_domain_plan_amr_hybrid_prodmesh_8rank_20260720` | `review_tmp_codex_artifact` | 0.24 | 1.8 |
| `${TMPDIR}/codex_h2_leak_open_domain_plan_amr_hybrid_prodmesh_20260720` | `review_tmp_codex_artifact` | 0.24 | 1.9 |
| `${TMPDIR}/codex_h2_leak_production_mesh_16rank_scout_20260720` | `review_tmp_codex_artifact` | 0.24 | 1.9 |
| `${TMPDIR}/codex_h2_leak_production_mesh_scout_20260720` | `review_tmp_codex_artifact` | 0.24 | 2.1 |
| `${TMPDIR}/codex_h2_leak_production_mesh_8rank_scout_20260720` | `review_tmp_codex_artifact` | 0.24 | 2.1 |
| `${TMPDIR}/codex_pelelmex_periodic_covo_self_convergence_20260716` | `review_tmp_codex_artifact` | 0.22 | 5.9 |
| `${TMPDIR}/codex_pelelmex_periodic_covo_self_convergence_20260716_rerun` | `review_tmp_codex_artifact` | 0.22 | 5.9 |
| `${TMPDIR}/codex_h2_leak_production_scale_scout_20260720` | `review_tmp_codex_artifact` | 0.19 | 2.1 |
| `${TMPDIR}/codex_engineering_h2_campaign_geometry_20260720` | `review_tmp_codex_artifact` | 0.18 | 2.2 |
| `${TMPDIR}/codex_h2_leak_open_domain_low_wind_20260718` | `review_tmp_codex_artifact` | 0.18 | 4.0 |
| `${TMPDIR}/codex_engineering_h2_campaign_production_scout_20260720` | `review_tmp_codex_artifact` | 0.15 | 2.1 |
| `${TMPDIR}/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720` | `review_tmp_codex_artifact` | 0.15 | 2.2 |
| `${TMPDIR}/codex_h2_leak_tank_farm_amr_compare_20260718_volfrac` | `review_tmp_codex_artifact` | 0.15 | 3.9 |
| `${TMPDIR}/codex_h2_leak_tank_farm_amr_compare_20260718` | `review_tmp_codex_artifact` | 0.15 | 3.9 |
| `${TMPDIR}/codex_h2_leak_open_domain_plan_amr_mpi_20260720` | `review_tmp_codex_artifact` | 0.13 | 2.2 |
| `${TMPDIR}/codex_h2_leak_open_domain_amr_compare_20260718_final` | `review_tmp_codex_artifact` | 0.13 | 3.9 |
| `${TMPDIR}/codex_h2_leak_open_domain_amr_overhead_20260718` | `review_tmp_codex_artifact` | 0.13 | 3.9 |

## Blocking Gaps

- none
