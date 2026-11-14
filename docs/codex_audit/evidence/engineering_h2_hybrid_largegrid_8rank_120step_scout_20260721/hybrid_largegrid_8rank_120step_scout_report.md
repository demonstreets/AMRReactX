# Engineering H2 Hybrid MPI/OpenMP CFD Scout

Status: `PASS-HYBRID-CFD-SCOUT`
Generated UTC: `2026-07-21T05:40:36+00:00`
Parallel mode: `8 MPI x 2 OMP`
Max step / plot interval: `120` / `30`
AMR finest level / fabs: `1` / `36`
Regrid count: `59`
Cloud rel diff: `1.59761211e-02`
Peak-X rel diff: `1.55533247e-03`
Centroid abs diff: `8.55490000e-05`
Downstream abs diff: `3.23786000e-04`
Advance seconds ratio: `1.72411476e+00`

## Evidence
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/plan_amr_compare_summary.csv` sha256=`94373f806a244b830da0a931c27a19d1439c726f646b969cbd1b8a48cd7c3308`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/amr_overhead_summary.csv` sha256=`74bfb3ab5d5b3b201b718f524e2b911e779ccad13d07e29282ec2e3af10d1d6d`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256=`a28f6c921b30e9586cae69a0f2186e67df957ea43326eb43635f0405925661f7`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256=`ee842f1a3f2d7dcaf97ec5824bd58a33a2f6a6c5511d82f45cd6f83c6b95964c`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/baseline/validation.log` sha256=`c913366ff31ddbc526f1f73e280182df6d0c8487858adb9d45fef6be62596a1b`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/baseline/profile_validation.log` sha256=`879a16e23a72b1f7b77d12b2793ca8bc257f221922f02554ea8808c2bcf220e9`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/baseline/hazard_summary.log` sha256=`d621d3c4b4e3d717bea852691257a7c2e8bb31ed862f4ae25c352a3971d6e831`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/baseline/hazard_planes.log` sha256=`c264709cbb35739543f40d14ec10a2d27218b6cc57fd3758f636c79b2dc4eb3d`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/baseline/hazard_planes.csv` sha256=`125c6adfe951614f0bd6b9245b7c5bfeecbf8b5ae0bc99765c445754dfa34e8b`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/baseline/hazard_timeseries.log` sha256=`e36e6c219fe6a78784f6a02dedca980f9d469e34598dba4893c9ecd3b926b349`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/baseline/hazard_timeseries.csv` sha256=`8f8c21d93d198ab3d96371f90bfdf40956e8a80f5d611eb180319998cf22c5d6`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/baseline/hybrid_validation.log` sha256=`1c4014f64dc5098e9fe8dcf8a2ac8fabe49da4e09679661fce3f15f3b1aeb554`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/baseline/run/input.codex_open_domain_plan_amr_baseline_smoke` sha256=`a28f6c921b30e9586cae69a0f2186e67df957ea43326eb43635f0405925661f7`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/amr/validation.log` sha256=`e160e91ef8fbc0b07cc2a01f6787cc33574f4e0a0a1b451d8ed241f5f9da1cc9`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/amr/profile_validation.log` sha256=`6383e1adf1637208530102907723d925a80137f7ab868dd50df7c2810465fbae`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/amr/hazard_summary.log` sha256=`c81ea94011469dcec608a36e7ad667416cb1d44242a0cd31ca2ec9e3962f5c67`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/amr/hazard_planes.log` sha256=`5da700f5d97dbb8354c5675325c710cb1450a06b57a9a09c8420aef8d9a9abeb`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/amr/hazard_planes.csv` sha256=`deac01f1db143c2955128ee5df6f83294f57e9345b03c1db22130704241e781b`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/amr/hazard_timeseries.log` sha256=`1db6623d36b571e61b190dc8ff087be6f5885aad9534903d258215553d4b646c`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/amr/hazard_timeseries.csv` sha256=`6d3dd829fe3cbd44fd54452d2384e73d9b8f280cd5622511ecf845e3eaa18e83`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/amr/hybrid_validation.log` sha256=`1c4014f64dc5098e9fe8dcf8a2ac8fabe49da4e09679661fce3f15f3b1aeb554`
- `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/files/amr/run/input.codex_open_domain_plan_amr_level1_smoke` sha256=`ee842f1a3f2d7dcaf97ec5824bd58a33a2f6a6c5511d82f45cd6f83c6b95964c`

## Limitations
- This is a production-mesh interactive hybrid MPI/OpenMP CFD scout, not a scheduler-managed full production campaign.
- The scout verifies the real PeleLMeX hybrid executable, AMR Level_1 creation, H2 hazard post-processing, and bounded AMR-vs-baseline drift.
- It does not prove long-duration hybrid scaling, production-size geometry, queue integration, calibrated fire consequences, or reference-data agreement.
- The MPI implementation reports thread support level 0; this run does not request MPI calls from multiple OpenMP threads, so the warning is tracked but accepted for this scout.
