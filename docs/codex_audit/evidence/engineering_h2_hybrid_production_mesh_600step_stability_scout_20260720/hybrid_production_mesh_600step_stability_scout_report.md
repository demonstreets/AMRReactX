# Engineering H2 Hybrid MPI/OpenMP CFD Scout

Status: `PASS-HYBRID-CFD-SCOUT`
Generated UTC: `2026-07-20T08:56:34+00:00`
Parallel mode: `4 MPI x 2 OMP`
Max step / plot interval: `600` / `60`
AMR finest level / fabs: `1` / `28`
Regrid count: `299`
Cloud rel diff: `3.15976518e-02`
Peak-X rel diff: `3.40034177e-02`
Centroid abs diff: `5.37634000e-04`
Downstream abs diff: `4.98946000e-04`
Advance seconds ratio: `2.00754474e+00`

## Evidence
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/plan_amr_compare_summary.csv` sha256=`29dfe6d475baf6df4cdde09401bf3ec72665919475c05c5267386ba4f7e5c70a`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/amr_overhead_summary.csv` sha256=`743bd32e1706df3d54ad4b0a0ef63b8ca91797db5d79f8a5479b6f934bdb0ef0`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256=`305bff86eecd7f2bc4bbdd0622ec56f78d06095bb3c5b2f00ea783014bc496f7`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256=`9804f132135b9bfade506ca777609d79e5116d77f38ac89997a9ad9b3e55e2bf`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/baseline/validation.log` sha256=`32c8730f023b52fe9465f4d5af41856ce6ebe4da84eabd068621432a0e7341e3`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/baseline/profile_validation.log` sha256=`d647c935d5698c075fb4c0c0044413892b8a3a705e61184d7ef1f350920c33b8`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/baseline/hazard_summary.log` sha256=`d2b32331241d5c05a35de5c6d38354c3e36eae4d542558f7f9614c4b418c86c8`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/baseline/hazard_planes.log` sha256=`199891c5166bc330672de152fe137e4415ccd0883d7a88f9bf94c21961e681fa`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/baseline/hazard_planes.csv` sha256=`cd03aff7eecf0b21f450f417a3450e765174569216d8607c51af1ecb29fb4136`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/baseline/hazard_timeseries.log` sha256=`ba2e65a141c5efebdd09d13763f96a4e1edb1b4ed1ae5b538ad6f41727459c42`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/baseline/hazard_timeseries.csv` sha256=`0eb662d740c487da087d8ef9b898e2e268a158a0aa20cbe58569eccb528ecb22`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/baseline/hybrid_validation.log` sha256=`5fb47889fc83fb37dd255d8069516b4e9651f939fe3013c322d273fa45d0294b`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/baseline/run/input.codex_open_domain_plan_amr_baseline_smoke` sha256=`305bff86eecd7f2bc4bbdd0622ec56f78d06095bb3c5b2f00ea783014bc496f7`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/amr/validation.log` sha256=`7f2eb7234d1ef68f1096a50220389de8e296d057f4b5367653085e07ff4bb9b2`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/amr/profile_validation.log` sha256=`7995ceef9ce2fc035cda6fa2faf87811cae9d33418c3dafd4c55af2ed3df2b46`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/amr/hazard_summary.log` sha256=`2c6dc42566be60b82edc809ae3b963e21d7e87438c484f0cd56745e167a42df4`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/amr/hazard_planes.log` sha256=`5e72f2010ba853d86b879a64836c0328bf94a2af33f7214cafe9db5a4f177a13`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/amr/hazard_planes.csv` sha256=`5fd8b3b8186276d3099577073b420312d30a60c21b35bb4d65ce6d5b0a6736f1`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/amr/hazard_timeseries.log` sha256=`b839598ea0ddcc76fef1e844659cf0050c163e8b6df3c49417924d2de061973f`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/amr/hazard_timeseries.csv` sha256=`f5635b59c26cdad33f5a127e128d9478ab01ebac0fb484cc7ce75d557c31edc5`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/amr/hybrid_validation.log` sha256=`5fb47889fc83fb37dd255d8069516b4e9651f939fe3013c322d273fa45d0294b`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_600step_stability_scout_20260720/files/amr/run/input.codex_open_domain_plan_amr_level1_smoke` sha256=`9804f132135b9bfade506ca777609d79e5116d77f38ac89997a9ad9b3e55e2bf`

## Limitations
- This is a production-mesh interactive hybrid MPI/OpenMP CFD scout, not a scheduler-managed full production campaign.
- The scout verifies the real PeleLMeX hybrid executable, AMR Level_1 creation, H2 hazard post-processing, and bounded AMR-vs-baseline drift.
- It does not prove long-duration hybrid scaling, production-size geometry, queue integration, calibrated fire consequences, or reference-data agreement.
- The MPI implementation reports thread support level 0; this run does not request MPI calls from multiple OpenMP threads, so the warning is tracked but accepted for this scout.
