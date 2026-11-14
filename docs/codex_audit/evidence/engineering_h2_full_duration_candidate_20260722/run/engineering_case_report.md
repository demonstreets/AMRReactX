# Engineering H2 Case Report: h2-open-domain-plan-amr-mpi-reduced-long

Status: `PASS`
Generated UTC: `2026-07-22T07:33:13+00:00`
Evidence root: `/home/cj/my-pele/docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/run`

## Run Summary

- MPI ranks: `8`
- Steps: `7200` with plot interval `240`
- Plotfiles: baseline `31`, AMR `31`
- Final time: `7.200000000000e+00`
- Baseline FABs: `[(0, 16)]`
- AMR FABs: `[(0, 16), (1, 86)]`

## Hazard Metrics

- Baseline final cloud volume: `9.66796875e-02`
- AMR final cloud volume: `1.15722656e-01`
- Baseline final peak X: `2.00222909e-01`
- AMR final peak X: `2.28180342e-01`
- AMR final flammable planes: `42`
- Cloud relative difference: `1.64556960e-01`
- Peak relative difference: `1.22523407e-01`
- Centroid absolute difference: `1.97077500e-03`
- Downstream absolute difference: `1.35478700e-03`

## AMR Overhead

- Mean cell ratio: `3.90905599e+00`
- Advance seconds ratio: `4.74059718e+00`
- Final plotfile bytes ratio: `4.04785200e+00`

## Evidence Hashes

- `/home/cj/my-pele/docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/run/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `391dfb8dea834090d29481ecee78736f8e069d6b37d6f77bd09ab57e9adfa94a`
- `/home/cj/my-pele/docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/run/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256 `7edf822d9062eb2348544bce58116ac070e1cfebe768bf9e6a6d84b180d17499`
- `/home/cj/my-pele/docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/run/plan_amr_compare_summary.csv` sha256 `0aee9c7da4fab55917e6ab1d55845ee688f8dd8c38085f5ea2567a9e5bcab485`
- `/home/cj/my-pele/docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/run/amr_overhead_summary.csv` sha256 `2c0182da8d2dcc3a0ba0acf3a78d76ca3bca3176242801bb9e6f12585147aee4`
- `/home/cj/my-pele/docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/run/reduced_long_summary.csv` sha256 `96d54a0c0f796f2434b76763b0fbfba1c4110e333676af55c1c058dae3a52d73`

## Limitations

- Reduced-long smoke evidence, not production completion.
- Does not prove overnight stability, production-size MPI scaling, scheduler/affinity behavior, real CAD/large-layout tank-farm AMR load balance, fire heat-release validation, or experimental/reference-data accuracy.
