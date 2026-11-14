# Engineering H2 Hybrid MPI/OpenMP CFD Scout

Status: `PASS-HYBRID-CFD-SCOUT`
Generated UTC: `2026-07-20T08:24:07+00:00`
Parallel mode: `4 MPI x 2 OMP`
Max step / plot interval: `40` / `20`
AMR finest level / fabs: `1` / `4`
Regrid count: `19`
Cloud rel diff: `4.46428599e-02`
Peak-X rel diff: `4.55934286e-02`
Centroid abs diff: `1.20702100e-04`
Downstream abs diff: `8.84127700e-03`
Advance seconds ratio: `1.57272302e+00`

## Evidence
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/plan_amr_compare_summary.csv` sha256=`0bfa803756d89bb4453c1db528b182175b5b0d5125606699268db06074cc8f0f`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/amr_overhead_summary.csv` sha256=`789d3fe6c8cf39ae29f973f84889c004a106bfd92e9edf0cf87b8b4d9302c315`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256=`5bdfb41260776df0a9886b597316b02040c100dba30e8fef182a3babc77d7e6c`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256=`1d7f3aac28876991556fbce8909a5d62f14aa7f199bdbc039414b1604426ff5e`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/baseline/validation.log` sha256=`7b917f0432b322864936d9479146493ef350247faff8784bccfaa942eefb5d89`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/baseline/profile_validation.log` sha256=`f226fb74a536ee9e41064e10f0739661b71f80ba5265bc8468dda6fb0526e086`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/baseline/hazard_summary.log` sha256=`8ad72913f0fb2b4d5a454b1aee74835b445a3bbf2d7eb73b1989594e444febfc`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/baseline/hazard_planes.log` sha256=`d8825adb97233678615bd7e0bf4cb8522cca5abcf93b15a7dde28269c6d59adb`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/baseline/hazard_planes.csv` sha256=`8a02f2a928aa039f8ceb31976f51b0864b895a79ea3edc59469d07e292ae63e6`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/baseline/hazard_timeseries.log` sha256=`ad56f80bdee525119b93cd35381e2c37080d697619c2aa79e4fe6daca59f091a`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/baseline/hazard_timeseries.csv` sha256=`8279e628b35eab58b84d132580964ae7bbd08247f8a4f740ee9e4b57ce35a4b4`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/baseline/hybrid_validation.log` sha256=`3ac00e6f0475db9d740d235b83d38044c875268e3b8f8889a06219183e36a727`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/baseline/run/input.codex_open_domain_plan_amr_baseline_smoke` sha256=`5bdfb41260776df0a9886b597316b02040c100dba30e8fef182a3babc77d7e6c`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/amr/validation.log` sha256=`d6d6cddb54e41214c2386d1f0cc3ff4e369bb93853aa4003732a7ca0102b5d3f`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/amr/profile_validation.log` sha256=`ae6bdc549690676dcf7590800f6817a04649d1030c46019306d838ca64f0dccd`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/amr/hazard_summary.log` sha256=`65885523263916355df5e28fbb0cdb2a1f3d486d72b20e2e9c4b884af4e84b36`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/amr/hazard_planes.log` sha256=`ab8bdf47d3013ce2f2cf77e8a3737ff9747005b52c8011ce701c194d2cdc1482`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/amr/hazard_planes.csv` sha256=`f2880fdcd5905aaeb53e5e3bcf19a257a1fe424b6ab8e3ba94a114195789c2ad`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/amr/hazard_timeseries.log` sha256=`910266511203df502bee9b862a720253f587d77402f2dfd767e3587b4bf0c24c`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/amr/hazard_timeseries.csv` sha256=`3d712d92e7c1d6e1f222e58d6d02c962b49f9b45a215def444e04d53d67fb1e0`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/amr/hybrid_validation.log` sha256=`3ac00e6f0475db9d740d235b83d38044c875268e3b8f8889a06219183e36a727`
- `docs/codex_audit/evidence/engineering_h2_hybrid_cfd_scout_20260720/files/amr/run/input.codex_open_domain_plan_amr_level1_smoke` sha256=`1d7f3aac28876991556fbce8909a5d62f14aa7f199bdbc039414b1604426ff5e`

## Limitations
- This is a short 40-step interactive hybrid MPI/OpenMP CFD scout, not a scheduler-managed production campaign.
- The scout verifies the real PeleLMeX hybrid executable, AMR Level_1 creation, H2 hazard post-processing, and bounded AMR-vs-baseline drift.
- It does not prove long-duration hybrid scaling, production-size geometry, queue integration, calibrated fire consequences, or reference-data agreement.
- The MPI implementation reports thread support level 0; this run does not request MPI calls from multiple OpenMP threads, so the warning is tracked but accepted for this scout.
