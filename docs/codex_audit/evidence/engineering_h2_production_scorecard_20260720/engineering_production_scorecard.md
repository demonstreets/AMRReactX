# Engineering Production Scorecard

Status: `NOT_PRODUCTION_READY`

## Scores

- Engineering functional coverage: `93.4%`
- Engineering production credibility: `73.5%`

## Gates

| Gate | Status | Functional pts | Production pts | Main gaps |
| --- | --- | ---: | ---: | --- |
| `reproducible_release_evidence` | `PASS-SMOKE` | 10.0/10.0 | 9.0/10.0 | smoke-scale pack, no full plotfile archive |
| `h2_leak_source_physics_chain` | `PASS-SMOKE+` | 15.2/16.0 | 9.6/12.0 | isothermal/lumped/steady approximations remain for several source models |
| `h2_dispersion_and_hazard_outputs` | `PASS-SMOKE+` | 13.3/14.0 | 9.0/12.0 | Gaussian-profile smoke only; no experimental or field reference agreement |
| `obstacle_geometry_and_stl_pipeline` | `PASS-SMOKE` | 11.0/12.0 | 6.8/10.0 | synthetic STL/tank-farm smoke only; real CAD cleanup and large layouts remain open |
| `engineering_amr_mpi_efficiency` | `PASS-SMOKE++++++` | 13.7/14.0 | 12.3/14.0 | 4-rank/1200-step, 8-rank/600-step, 16-rank short production-mesh, 8x2 large-grid hybrid, and 4/8/16 short MPI scaling scouts exist; scheduler-managed runs, production-size scaling curves, and overnight/full-duration campaigns remain open |
| `ignition_fire_consequence_chain` | `PARTIAL++` | 8.8/10.0 | 7.4/12.0 | screening radiation/overpressure metrics exist, but flame speed, calibrated radiation, calibrated overpressure, and validated fire metrics remain missing |
| `runtime_affinity_and_scheduler_handoff` | `PARTIAL++++++` | 7.3/8.0 | 6.0/10.0 | interactive MPI+OpenMP affinity preflight plus short, 4x2 production-mesh, 8x2 production-mesh, 4x2 600-step, and 8x2 600-step production-mesh hybrid CFD scouts exist; scheduler campaign has not produced PASS run outputs |
| `long_duration_stability` | `PARTIAL+++` | 7.0/8.0 | 8.4/12.0 | 1200-step production-mesh MPI+AMR scout exists; overnight/full-duration stability campaigns still missing |
| `production_scale_and_reference_accuracy` | `PARTIAL++++` | 7.0/8.0 | 5.0/8.0 | H2 LEL/UEL and ALOHA LOC threshold agreement exists, but external plume-shape datasets, full production-size campaigns, and acceptance tolerances remain missing |

## Blocking Gaps

- `scheduler_controller_unavailable_or_job_not_accepted`
- `campaign_evidence_is_production_mesh_scout_not_full_duration`
- `stability_evidence_is_production_mesh_1200step_scout_with_full_duration_candidate_not_executed`
- `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`
- `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`
- `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`
- `bfs_kepsilon_reference_validation_failed`

## Evidence Files

- `campaign_manifest`: `docs/codex_audit/evidence/engineering_h2_production_full_20260720/campaign_manifest.json` sha256 `97dfe6b8ef872b5e`
- `release_pack`: `docs/codex_audit/evidence/engineering_h2_production_full_20260720/release_pack/evidence_pack_manifest.json` sha256 `9fd154e5c1b20365`
- `runtime_affinity_manifest`: `docs/codex_audit/evidence/engineering_runtime_affinity_20260720/runtime_affinity_manifest.json` sha256 `8baa9ff21cf2694e`
- `hybrid_runtime_affinity_manifest`: `docs/codex_audit/evidence/engineering_runtime_affinity_hybrid_20260720/runtime_affinity_manifest.json` sha256 `c3707d1611d611a5`
- `scheduler_run_report`: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json` sha256 `f213229920476ff1`
- `ignition_consequence_report`: `docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/ignition_consequence_report.json` sha256 `3f1eb940bc75c59e`
- `fire_consequence_metrics_report`: `docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.json` sha256 `59ffddc75e1b5745`
- `production_scale_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/production_scale_scout_report.json` sha256 `378ef270a2e8ca67`
- `long_stability_scout_report`: `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/long_stability_scout_report.json` sha256 `27fb942118a0302e`
- `production_mesh_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_scout_20260720/production_mesh_scout_report.json` sha256 `ea806a6dd56bb0ed`
- `production_mesh_8rank_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_scout_20260720/production_mesh_8rank_scout_report.json` sha256 `6b4c05d1d48a0205`
- `production_mesh_16rank_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/production_mesh_16rank_scout_report.json` sha256 `976464cb31a86f6c`
- `production_mesh_8rank_600step_stability_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_600step_stability_scout_20260720/production_mesh_8rank_600step_stability_scout_report.json` sha256 `76cf3ad46f4f9720`
- `production_mesh_600step_stability_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/production_mesh_600step_stability_scout_report.json` sha256 `11e1114eeebb8ab4`
- `production_mesh_1200step_stability_scout_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/production_mesh_1200step_stability_scout_report.json` sha256 `1d0f9891d1ef7700`
- `engineering_h2_production_mesh_campaign_report`: `docs/codex_audit/evidence/engineering_h2_production_mesh_campaign_20260722/production_mesh_campaign_report.json` sha256 `a9b9e0d0bd32c83d`
- `engineering_h2_full_duration_candidate_report`: `docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/full_duration_candidate_report.json` sha256 `b7f93d9a83b17300`
- `engineering_h2_acceptance_matrix`: `docs/codex_audit/evidence/engineering_h2_acceptance_matrix_20260720/engineering_h2_acceptance_matrix.json` sha256 `85ed63e3d3cb4edd`
- `engineering_h2_mpi_scaling_report`: `docs/codex_audit/evidence/engineering_h2_mpi_scaling_20260720/mpi_scaling_report.json` sha256 `e175591c7b4ee68a`
- `engineering_h2_hybrid_cfd_scout_report`: `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/hybrid_cfd_scout_report.json` sha256 `faef5650a6bbc49b`
- `engineering_h2_hybrid_production_mesh_scout_report`: `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/hybrid_production_mesh_scout_report.json` sha256 `a1904e6a386548aa`
- `engineering_h2_hybrid_production_mesh_8rank_scout_report`: `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/hybrid_production_mesh_8rank_scout_report.json` sha256 `6f782b257dade094`
- `engineering_h2_hybrid_production_mesh_600step_stability_scout_report`: `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/hybrid_production_mesh_600step_stability_scout_report.json` sha256 `47a64264ae2a4220`
- `engineering_h2_hybrid_largegrid_8rank_120step_scout_report`: `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/hybrid_largegrid_8rank_120step_scout_report.json` sha256 `c542c808e81dc86f`
- `engineering_h2_reference_agreement_report`: `docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/h2_reference_agreement_report.json` sha256 `aabbc8cb145dbbea`
- `engineering_bfs_kepsilon_reference_report`: `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.json` sha256 `bf056f5d12b64d42`
