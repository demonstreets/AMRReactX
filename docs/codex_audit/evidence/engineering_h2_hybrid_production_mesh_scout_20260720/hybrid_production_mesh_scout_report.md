# Engineering H2 Hybrid MPI/OpenMP CFD Scout

Status: `PASS-HYBRID-CFD-SCOUT`
Generated UTC: `2026-07-20T08:24:08+00:00`
Parallel mode: `4 MPI x 2 OMP`
Max step / plot interval: `120` / `30`
AMR finest level / fabs: `1` / `12`
Regrid count: `59`
Cloud rel diff: `3.80952381e-02`
Peak-X rel diff: `4.31073584e-02`
Centroid abs diff: `3.15499000e-04`
Downstream abs diff: `2.60922300e-03`
Advance seconds ratio: `1.61148722e+00`

## Evidence
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/plan_amr_compare_summary.csv` sha256=`966214b3b791d4000149e75ae09097f59788da465ece6ce51851d355bfc89da3`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/amr_overhead_summary.csv` sha256=`2ad5e2fe8fac636099bb69d49cca64894a583565ad53bfff0e1d3cf6117135dd`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256=`2421edb9d9a8a7269a6836334c51e647fdec67d389f55d4a50799fe7954a29e7`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256=`39dd112b920ee39386f73dda2e165382d256c1eceb86f591941143fac85fdbbe`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/baseline/validation.log` sha256=`ef867f55b627f64364e1598fb75e57f180fafdc1ebcc24ae06a6f312dc0d11fc`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/baseline/profile_validation.log` sha256=`d7c024969bd1c394a168fd5f8cdfcdbd699ecc17dcf4e1df607c489071ad89e7`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/baseline/hazard_summary.log` sha256=`1f50cd57ada309553144c59d1a3596f55214f62a11a49c61b38ba76365e84073`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/baseline/hazard_planes.log` sha256=`d81c70ce6380e4397d653c76dc0cac8341d27ef7bdb278e30510bc35b9b5e306`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/baseline/hazard_planes.csv` sha256=`00d609c5568068e39a651197f3facb637630b22f0f3c66ba1d0755f1f7c1b5f3`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/baseline/hazard_timeseries.log` sha256=`2b4d12529fe64a83953be48a5c70a011f0f16d4acf014e93b1584e7c772df882`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/baseline/hazard_timeseries.csv` sha256=`f17666c241bd1be85a7612c10edc98f2e10769fe8573aa0bf08ad2a70b9c06d8`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/baseline/hybrid_validation.log` sha256=`32f51d0ceff3d71e5e49b678a8166c9b84aa824f7081e50a75f70966af0766fe`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/baseline/run/input.codex_open_domain_plan_amr_baseline_smoke` sha256=`2421edb9d9a8a7269a6836334c51e647fdec67d389f55d4a50799fe7954a29e7`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/amr/validation.log` sha256=`34e8ebdbdafffb880a7d6bdfa6ac7451886792da6e8bac587b6db3125e5181bd`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/amr/profile_validation.log` sha256=`fc5c6d9cb6be078b5bf3a6f409249fab4baa3c40ea9be8c510740f43ae4b617b`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/amr/hazard_summary.log` sha256=`7115f180c02f83bd7446ab8c7ddf2f87c82e5f150852af8935e47881a29d73fd`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/amr/hazard_planes.log` sha256=`f0b32effe73265d00b947ee41c40eab588307302439f7e8e71934545d23b5cb0`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/amr/hazard_planes.csv` sha256=`91d31e4c329d9ee0c6c10ba5c044427eb91582b0d9509930d83bce43031235a6`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/amr/hazard_timeseries.log` sha256=`0ebfd31cc7c1f8ecd3bdd706e3ebfb2bec95d5cc6ee28a97c1fb4657579be1b5`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/amr/hazard_timeseries.csv` sha256=`c57f99194f8b2b66dd146885a5a7542d7f35128e1ffc4589afa874fc05540fa3`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/amr/hybrid_validation.log` sha256=`32f51d0ceff3d71e5e49b678a8166c9b84aa824f7081e50a75f70966af0766fe`
- `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_scout_20260720/files/amr/run/input.codex_open_domain_plan_amr_level1_smoke` sha256=`39dd112b920ee39386f73dda2e165382d256c1eceb86f591941143fac85fdbbe`

## Limitations
- This is a production-mesh interactive hybrid MPI/OpenMP CFD scout, not a scheduler-managed full production campaign.
- The scout verifies the real PeleLMeX hybrid executable, AMR Level_1 creation, H2 hazard post-processing, and bounded AMR-vs-baseline drift.
- It does not prove long-duration hybrid scaling, production-size geometry, queue integration, calibrated fire consequences, or reference-data agreement.
- The MPI implementation reports thread support level 0; this run does not request MPI calls from multiple OpenMP threads, so the warning is tracked but accepted for this scout.
