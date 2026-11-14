# Engineering H2 Case Report: h2-open-domain-plan-amr-mpi-reduced-long

Status: `PASS`
Generated UTC: `2026-07-20T04:26:04+00:00`
Evidence root: `${SCOUT_ROOT}`

## Run Summary

- MPI ranks: `8`
- Steps: `120` with plot interval `30`
- Plotfiles: baseline `5`, AMR `5`
- Final time: `1.200000000000e-01`
- Baseline FABs: `[(0, 16)]`
- AMR FABs: `[(0, 16), (1, 12)]`

## Hazard Metrics

- Baseline final cloud volume: `2.56347656e-02`
- AMR final cloud volume: `2.46582031e-02`
- Baseline final peak X: `1.81306773e-01`
- AMR final peak X: `1.89474519e-01`
- AMR final flammable planes: `10`
- Cloud relative difference: `3.80952381e-02`
- Peak relative difference: `4.31073584e-02`
- Centroid absolute difference: `3.15499000e-04`
- Downstream absolute difference: `2.60922300e-03`

## AMR Overhead

- Mean cell ratio: `1.41002604e+00`
- Advance seconds ratio: `1.83771921e+00`
- Final plotfile bytes ratio: `1.57063332e+00`

## Evidence Hashes

- `${SCOUT_ROOT}/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `a14f93c6fab8e0b0a06b0958bb79916467ecffda886692e2dc2863cd97f6a78c`
- `${SCOUT_ROOT}/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256 `39dd112b920ee39386f73dda2e165382d256c1eceb86f591941143fac85fdbbe`
- `${SCOUT_ROOT}/plan_amr_compare_summary.csv` sha256 `d9216fb8ad6e55ed6bc74d317c3a45686ce7e4792b267a0d6079c6ef2d78a2c2`
- `${SCOUT_ROOT}/amr_overhead_summary.csv` sha256 `1082976825e7e94a0cf4e8a525e6080ee9bfc2dde3617c818ba55521f5d9f1b0`
- `${SCOUT_ROOT}/reduced_long_summary.csv` sha256 `1777efc523b22e4ed5b5227a6b9b7859fdd983351932518103a46fe298ae4ad6`

## Limitations

- Reduced-long smoke evidence, not production completion.
- Does not prove overnight stability, production-size MPI scaling, scheduler/affinity behavior, real CAD/large-layout tank-farm AMR load balance, fire heat-release validation, or experimental/reference-data accuracy.
