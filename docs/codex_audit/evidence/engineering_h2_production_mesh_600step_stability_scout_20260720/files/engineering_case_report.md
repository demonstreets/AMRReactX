# Engineering H2 Case Report: h2-open-domain-plan-amr-mpi-reduced-long

Status: `PASS`
Generated UTC: `2026-07-20T05:00:33+00:00`
Evidence root: `${SCOUT_ROOT}`

## Run Summary

- MPI ranks: `4`
- Steps: `600` with plot interval `60`
- Plotfiles: baseline `11`, AMR `11`
- Final time: `6.000000000000e-01`
- Baseline FABs: `[(0, 16)]`
- AMR FABs: `[(0, 16), (1, 28)]`

## Hazard Metrics

- Baseline final cloud volume: `9.87548828e-02`
- AMR final cloud volume: `9.56344604e-02`
- Baseline final peak X: `2.28405343e-01`
- AMR final peak X: `2.36445291e-01`
- AMR final flammable planes: `72`
- Cloud relative difference: `3.15976518e-02`
- Peak relative difference: `3.40034177e-02`
- Centroid absolute difference: `5.37634000e-04`
- Downstream absolute difference: `4.98946000e-04`

## AMR Overhead

- Mean cell ratio: `1.97647135e+00`
- Advance seconds ratio: `2.26482395e+00`
- Final plotfile bytes ratio: `2.62522158e+00`

## Evidence Hashes

- `${SCOUT_ROOT}/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `cea42800aaa06b5ed004d2f5c1ebd5d8d5f1d8b559ea1467e946f84ab1f98f8d`
- `${SCOUT_ROOT}/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256 `9804f132135b9bfade506ca777609d79e5116d77f38ac89997a9ad9b3e55e2bf`
- `${SCOUT_ROOT}/plan_amr_compare_summary.csv` sha256 `feab7fd227b994c03d109dc4bb688ad534696018f76e3ee45b76685628db5a8e`
- `${SCOUT_ROOT}/amr_overhead_summary.csv` sha256 `6c6ad64073f63c41d7d4896601e879d02ae51e56a057e2b1572432e1ffca1277`
- `${SCOUT_ROOT}/reduced_long_summary.csv` sha256 `238483dd9ae9346575088792a3c8ff296ac7a9d0723875d55687d29952dca1b6`

## Limitations

- Reduced-long smoke evidence, not production completion.
- Does not prove overnight stability, production-size MPI scaling, scheduler/affinity behavior, real CAD/large-layout tank-farm AMR load balance, fire heat-release validation, or experimental/reference-data accuracy.
