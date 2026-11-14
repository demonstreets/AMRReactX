# Engineering H2 Hybrid MPI/OpenMP CFD Scout

Status: `PASS-HYBRID-CFD-SCOUT`
Generated UTC: `2026-07-21T00:24:39+00:00`
Parallel mode: `8 MPI x 2 OMP`
Max step / plot interval: `120` / `30`
AMR finest level / fabs: `1` / `12`
Regrid count: `59`
Cloud rel diff: `3.80952381e-02`
Peak-X rel diff: `4.31073584e-02`
Centroid abs diff: `3.15499000e-04`
Downstream abs diff: `2.60922300e-03`
Advance seconds ratio: `2.00980894e+00`

## Evidence
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/plan_amr_compare_summary.csv` sha256=`0b8b6e2a3e7b0987e36d6bf3e395677300cfc09405e8abfa797c81fc1ca95a55`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/amr_overhead_summary.csv` sha256=`b0a02abb4815c17194dbad3590efdc52f891597190f09f47c3ac377bd0860a66`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256=`2421edb9d9a8a7269a6836334c51e647fdec67d389f55d4a50799fe7954a29e7`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256=`39dd112b920ee39386f73dda2e165382d256c1eceb86f591941143fac85fdbbe`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/baseline/validation.log` sha256=`185b1c9af51b7c209a4733ac81ab444e61936914e32aa3cd45d29c0f47b2377c`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/baseline/profile_validation.log` sha256=`d7c024969bd1c394a168fd5f8cdfcdbd699ecc17dcf4e1df607c489071ad89e7`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/baseline/hazard_summary.log` sha256=`1f50cd57ada309553144c59d1a3596f55214f62a11a49c61b38ba76365e84073`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/baseline/hazard_planes.log` sha256=`d81c70ce6380e4397d653c76dc0cac8341d27ef7bdb278e30510bc35b9b5e306`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/baseline/hazard_planes.csv` sha256=`b72fd4b8c604105e040009a6af5292c07f56b837fc9bce5b89b2359681c8e685`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/baseline/hazard_timeseries.log` sha256=`2b4d12529fe64a83953be48a5c70a011f0f16d4acf014e93b1584e7c772df882`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/baseline/hazard_timeseries.csv` sha256=`f17666c241bd1be85a7612c10edc98f2e10769fe8573aa0bf08ad2a70b9c06d8`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/baseline/hybrid_validation.log` sha256=`1c4014f64dc5098e9fe8dcf8a2ac8fabe49da4e09679661fce3f15f3b1aeb554`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/baseline/run/input.codex_open_domain_plan_amr_baseline_smoke` sha256=`2421edb9d9a8a7269a6836334c51e647fdec67d389f55d4a50799fe7954a29e7`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/amr/validation.log` sha256=`34e8ebdbdafffb880a7d6bdfa6ac7451886792da6e8bac587b6db3125e5181bd`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/amr/profile_validation.log` sha256=`fc5c6d9cb6be078b5bf3a6f409249fab4baa3c40ea9be8c510740f43ae4b617b`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/amr/hazard_summary.log` sha256=`7115f180c02f83bd7446ab8c7ddf2f87c82e5f150852af8935e47881a29d73fd`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/amr/hazard_planes.log` sha256=`f0b32effe73265d00b947ee41c40eab588307302439f7e8e71934545d23b5cb0`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/amr/hazard_planes.csv` sha256=`79178ce94ad9d11eb86b4f40051847d13a3d1cd24a416990ea47a2469f083cbd`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/amr/hazard_timeseries.log` sha256=`0ebfd31cc7c1f8ecd3bdd706e3ebfb2bec95d5cc6ee28a97c1fb4657579be1b5`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/amr/hazard_timeseries.csv` sha256=`c57f99194f8b2b66dd146885a5a7542d7f35128e1ffc4589afa874fc05540fa3`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/amr/hybrid_validation.log` sha256=`1c4014f64dc5098e9fe8dcf8a2ac8fabe49da4e09679661fce3f15f3b1aeb554`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/files/amr/run/input.codex_open_domain_plan_amr_level1_smoke` sha256=`39dd112b920ee39386f73dda2e165382d256c1eceb86f591941143fac85fdbbe`

## Limitations
- This is a production-mesh interactive hybrid MPI/OpenMP CFD scout, not a scheduler-managed full production campaign.
- The scout verifies the real PeleLMeX hybrid executable, AMR Level_1 creation, H2 hazard post-processing, and bounded AMR-vs-baseline drift.
- It does not prove long-duration hybrid scaling, production-size geometry, queue integration, calibrated fire consequences, or reference-data agreement.
- The MPI implementation reports thread support level 0; this run does not request MPI calls from multiple OpenMP threads, so the warning is tracked but accepted for this scout.
