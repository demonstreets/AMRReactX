# Engineering Production Scorecard

Status: `NOT_PRODUCTION_READY`

## Scores

- Engineering functional coverage: `96.9%`
- Engineering production credibility: `82.2%`

## Gates

| Gate | Status | Functional pts | Production pts | Main gaps |
| --- | --- | ---: | ---: | --- |
| `reproducible_release_evidence` | `PASS-SMOKE` | 10.0/10.0 | 9.0/10.0 | smoke-scale pack, no full plotfile archive |
| `h2_leak_source_physics_chain` | `PASS-SMOKE+` | 15.2/16.0 | 9.6/12.0 | isothermal/lumped/steady approximations remain for several source models |
| `h2_dispersion_and_hazard_outputs` | `PASS-SMOKE+` | 13.3/14.0 | 9.0/12.0 | Gaussian-profile smoke only; no experimental or field reference agreement |
| `h2_engineering_scene_large_acceptance_clearance` | `PASS-LARGE-CASE` | 0.0/0.0 | 0.0/0.0 | GPU execution is not validated by this large acceptance run; large coupled ignition/fire is not validated by this large acceptance run; external plume benchmarks remain non-blocking calibration/publication follow-up for this engineering-scene clearance |
| `obstacle_geometry_and_stl_pipeline` | `PASS-CPU-GPU-PIPE-RACK-SMOKE` | 11.8/12.0 | 8.2/10.0 | synthetic cube/cylinder/pipe-rack STL validated on CPU and single-GPU CUDA; real CAD cleanup, GPU scaling, and larger plant-layout repeats remain open |
| `h2_pipe_rack_gpu_fire_obstacle_clearance` | `PASS-CPU-GPU-FIRE-SCREENING` | 0.0/0.0 | 0.0/0.0 | direct coupled 3D calibrated fire propagation is not claimed by this gate; GPU evidence includes 2-rank MPI+CUDA smoke/stability, not a production GPU scaling curve; pipe-rack case is engineering synthetic geometry, not customer plant CAD |
| `engineering_amr_mpi_efficiency` | `PASS-SMOKE++++++` | 13.7/14.0 | 12.3/14.0 | Scheduler handoff, production-mesh full-duration campaign evidence, 8-rank/600-step stability, 16-rank scout, 8x2 large-grid hybrid, and 4/8/16 short MPI scaling scouts exist; remaining AMR/MPI credibility gaps are production-scale scaling curves and broader plant-layout repeats |
| `ignition_fire_consequence_chain` | `PARTIAL+++++++++++` | 10.0/10.0 | 10.3/12.0 | direct pipe-rack leak-cloud reacting CUDA sustained-fire gates now pass on single GPU, 2-rank MPI+CUDA, and 64x32x32 large-grid single-GPU; full-duration flame spread, flame speed, calibrated radiation, calibrated overpressure, and validated fire metrics remain missing |
| `runtime_affinity_and_scheduler_handoff` | `PASS` | 8.0/8.0 | 8.5/10.0 | none recorded |
| `long_duration_stability` | `PASS-FULL-DURATION` | 7.8/8.0 | 10.3/12.0 | production-mesh full-duration evidence exists; remaining stability credibility gaps are repeat campaigns on real CAD layouts and external field/experiment agreement |
| `production_scale_and_reference_accuracy` | `PARTIAL++++` | 7.0/8.0 | 5.0/8.0 | H2 LEL/UEL and ALOHA LOC threshold agreement exists, but external plume-shape datasets and case-specific acceptance tolerances remain missing |

## Blocking Gaps

- `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`
- `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`
- `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`

## Evidence Files

- `campaign_manifest`: `docs/codex_audit/evidence/engineering_h2_production_full_20260720/campaign_manifest.json` sha256 `97dfe6b8ef872b5e`
- `release_pack`: `docs/codex_audit/evidence/engineering_h2_production_full_20260720/release_pack/evidence_pack_manifest.json` sha256 `e4e427f9041bc1d8`
- `runtime_affinity_manifest`: `docs/codex_audit/evidence/engineering_runtime_affinity_20260720/runtime_affinity_manifest.json` sha256 `8baa9ff21cf2694e`
- `hybrid_runtime_affinity_manifest`: `docs/codex_audit/evidence/engineering_runtime_affinity_hybrid_20260720/runtime_affinity_manifest.json` sha256 `c3707d1611d611a5`
- `scheduler_run_report`: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json` sha256 `262da4919c55fc24`
- `ignition_consequence_report`: `docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/ignition_consequence_report.json` sha256 `3f1eb940bc75c59e`
- `fire_consequence_metrics_report`: `docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.json` sha256 `f1e4bb21fb6166d3`
- `production_scale_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/production_scale_scout_report.json` sha256 `378ef270a2e8ca67`
- `long_stability_scout_report`: `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/long_stability_scout_report.json` sha256 `27fb942118a0302e`
- `production_mesh_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_scout_20260720/production_mesh_scout_report.json` sha256 `ea806a6dd56bb0ed`
- `production_mesh_8rank_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/production_mesh_8rank_scout_report.json` sha256 `6b4c05d1d48a0205`
- `production_mesh_16rank_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/production_mesh_16rank_scout_report.json` sha256 `976464cb31a86f6c`
- `production_mesh_8rank_600step_stability_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_600step_stability_scout_20260720/production_mesh_8rank_600step_stability_scout_report.json` sha256 `76cf3ad46f4f9720`
- `production_mesh_600step_stability_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/production_mesh_600step_stability_scout_report.json` sha256 `11e1114eeebb8ab4`
- `production_mesh_1200step_stability_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/production_mesh_1200step_stability_scout_report.json` sha256 `1d0f9891d1ef7700`
- `engineering_h2_production_mesh_campaign_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_campaign_20260722/production_mesh_campaign_report.json` sha256 `8981aa62e1abd4e5`
- `engineering_h2_full_duration_candidate_report`: `docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/full_duration_candidate_report.json` sha256 `891075fa3d539aad`
- `engineering_h2_acceptance_matrix`: `docs/codex_audit/evidence/engineering_h2_acceptance_matrix_20260720/engineering_h2_acceptance_matrix.json` sha256 `06df00684202b1c7`
- `engineering_h2_mpi_scaling_report`: `docs/codex_audit/evidence/engineering_h2_mpi_scaling_20260720/mpi_scaling_report.json` sha256 `e175591c7b4ee68a`
- `engineering_h2_hybrid_cfd_scout_report`: `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/hybrid_cfd_scout_report.json` sha256 `faef5650a6bbc49b`
- `engineering_h2_hybrid_production_mesh_scout_report`: `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/hybrid_production_mesh_scout_report.json` sha256 `a1904e6a386548aa`
- `engineering_h2_hybrid_production_mesh_8rank_scout_report`: `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/hybrid_production_mesh_8rank_scout_report.json` sha256 `6f782b257dade094`
- `engineering_h2_hybrid_production_mesh_600step_stability_scout_report`: `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/hybrid_production_mesh_600step_stability_scout_report.json` sha256 `47a64264ae2a4220`
- `engineering_h2_hybrid_largegrid_8rank_120step_scout_report`: `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/hybrid_largegrid_8rank_120step_scout_report.json` sha256 `c542c808e81dc86f`
- `engineering_h2_reference_agreement_report`: `docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/h2_reference_agreement_report.json` sha256 `e89a986961ee9cd6`
- `engineering_bfs_kepsilon_reference_report`: `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.json` sha256 `d6ed7e0a4a5793d7`
- `engineering_h2_engineering_scene_clearance_report`: `docs/codex_audit/evidence/engineering_h2_engineering_scene_clearance_20260727/h2_engineering_scene_clearance_report.json` sha256 `6fb99a356ee8da46`
- `engineering_h2_pipe_rack_gpu_fire_obstacle_report`: `docs/codex_audit/evidence/engineering_h2_pipe_rack_gpu_fire_obstacle_20260727/pipe_rack_gpu_fire_obstacle_report.json` sha256 `f8d2a16e319e9bb1`
- `engineering_h2_reacting_mpi_cuda_smoke_report`: `docs/codex_audit/evidence/engineering_h2_reacting_mpi_cuda_smoke_20260727/reacting_mpi_cuda_smoke_report.json` sha256 `57f95b413ab8bc08`
- `engineering_h2_pipe_rack_direct_reacting_cuda_report`: `docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_cuda_2000step_20260727/pipe_rack_direct_reacting_cuda_report.json` sha256 `12b98e8c794016be`
- `engineering_h2_pipe_rack_direct_reacting_mpi_cuda_report`: `docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_mpi_cuda_2000step_20260727/pipe_rack_direct_reacting_mpi_cuda_report.json` sha256 `a0c6df5513382e75`
- `engineering_h2_pipe_rack_direct_reacting_largegrid_cuda_report`: `docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_largegrid_cuda_20260727/pipe_rack_direct_reacting_cuda_report.json` sha256 `92dc50c8ca6c1c6a`
- `engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_report`: `docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_largegrid_mpi_cuda_20260727/pipe_rack_direct_reacting_mpi_cuda_report.json` sha256 `5721a79c006f1c0e`
- `engineering_h2_pipe_rack_reacting_mpi_cuda_restart_report`: `docs/codex_audit/evidence/engineering_h2_pipe_rack_direct_reacting_mpi_cuda_restart_20260727/pipe_rack_reacting_mpi_cuda_restart_report.json` sha256 `1d9172b102f948a0`
- `engineering_h2_fire_consequence_traceability_report`: `docs/codex_audit/evidence/engineering_h2_fire_consequence_traceability_20260727/fire_consequence_traceability_report.json` sha256 `b525a70304dc9108`
