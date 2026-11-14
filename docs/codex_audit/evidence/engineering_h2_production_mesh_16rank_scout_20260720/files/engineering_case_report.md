# Engineering H2 Case Report: h2-open-domain-plan-amr-mpi-reduced-long

Status: `PASS`
Generated UTC: `2026-07-20T07:14:18+00:00`
Evidence root: `${SCOUT_ROOT}`

## Run Summary

- MPI ranks: `16`
- Steps: `120` with plot interval `30`
- Plotfiles: baseline `5`, AMR `5`
- Final time: `1.200000000000e-01`
- Baseline FABs: `[(0, 128)]`
- AMR FABs: `[(0, 128), (1, 73)]`

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
- Advance seconds ratio: `1.73497799e+00`
- Final plotfile bytes ratio: `1.57040264e+00`

## Evidence Hashes

- `${SCOUT_ROOT}/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `757b26e02fb84a597b363e72774740b3714837db2d0a19f2e8e64643b5ce2d04`
- `${SCOUT_ROOT}/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256 `33db36746f0d82750e0a85bb2dca6629dec2d6fc21f4287499b013cd65b6e5b1`
- `${SCOUT_ROOT}/plan_amr_compare_summary.csv` sha256 `8fd36ea731fc7f12a3181394aa0b0d364a19daf8ddf22dc61b6ab38bafd27789`
- `${SCOUT_ROOT}/amr_overhead_summary.csv` sha256 `b81f41243e562035367db27988a1c972fe15dbe64debf6fa2817a649882ee67a`
- `${SCOUT_ROOT}/reduced_long_summary.csv` sha256 `94beac3d7669c2829c4d000e8f733a145e164553c0d86fb0a5de3dec2d3c2a67`

## Limitations

- Reduced-long smoke evidence, not production completion.
- Does not prove overnight stability, production-size MPI scaling, scheduler/affinity behavior, real CAD/large-layout tank-farm AMR load balance, fire heat-release validation, or experimental/reference-data accuracy.
