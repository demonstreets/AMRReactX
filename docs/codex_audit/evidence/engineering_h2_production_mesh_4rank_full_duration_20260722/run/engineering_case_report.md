# Engineering H2 Case Report: h2-open-domain-plan-amr-mpi-reduced-long

Status: `PASS`
Generated UTC: `2026-07-23T02:05:54+00:00`
Evidence root: `/home/cj/my-pele/docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/run`

## Run Summary

- MPI ranks: `4`
- Steps: `7200` with plot interval `240`
- Plotfiles: baseline `31`, AMR `31`
- Final time: `7.200000000000e+00`
- Baseline FABs: `[(0, 16)]`
- AMR FABs: `[(0, 16), (1, 28)]`

## Hazard Metrics

- Baseline final cloud volume: `1.15478516e-01`
- AMR final cloud volume: `1.12243652e-01`
- Baseline final peak X: `2.28263526e-01`
- AMR final peak X: `2.36439019e-01`
- AMR final flammable planes: `83`
- Cloud relative difference: `2.80126911e-02`
- Peak relative difference: `3.45775965e-02`
- Centroid absolute difference: `4.64821000e-04`
- Downstream absolute difference: `3.95459000e-04`

## AMR Overhead

- Mean cell ratio: `2.62805664e+00`
- Advance seconds ratio: `2.90979970e+00`
- Final plotfile bytes ratio: `2.68761142e+00`

## Evidence Hashes

- `/home/cj/my-pele/docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/run/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `afd8984bfaf6b83c264512954e4c07003d92bb1d8da06a231366520d36078064`
- `/home/cj/my-pele/docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/run/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256 `c0dfd077ec39fc20991da9a9c072772011cb9d13feb72e0f7ccee8e70d43b695`
- `/home/cj/my-pele/docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/run/plan_amr_compare_summary.csv` sha256 `fda9209b146e533b1e25f5c1613bcc061dfe2e574f95611d393ee78a685964e8`
- `/home/cj/my-pele/docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/run/amr_overhead_summary.csv` sha256 `98b881918c680ba61d69a2c8e27f70c412ac7930c02a2e2f2f9903f5a5a96853`
- `/home/cj/my-pele/docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/run/reduced_long_summary.csv` sha256 `619d48dc1dddebd52a49d7387e21b31d8f80c858461d42031c5f99552ec1d7ee`

## Limitations

- Reduced-long smoke evidence, not production completion.
- Does not prove overnight stability, production-size MPI scaling, scheduler/affinity behavior, real CAD/large-layout tank-farm AMR load balance, fire heat-release validation, or experimental/reference-data accuracy.
