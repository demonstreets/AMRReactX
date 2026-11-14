# Engineering H2 Case Report: h2-open-domain-plan-amr-mpi-reduced-long

Status: `PASS`
Generated UTC: `2026-07-20T03:59:25+00:00`
Evidence root: `${SCOUT_ROOT}`

## Run Summary

- MPI ranks: `4`
- Steps: `300` with plot interval `30`
- Plotfiles: baseline `11`, AMR `11`
- Final time: `3.000000000000e-01`
- Baseline FABs: `[(0, 12)]`
- AMR FABs: `[(0, 12), (1, 16)]`

## Hazard Metrics

- Baseline final cloud volume: `5.46875000e-02`
- AMR final cloud volume: `5.13237847e-02`
- Baseline final peak X: `2.35477060e-01`
- AMR final peak X: `2.22321843e-01`
- AMR final flammable planes: `24`
- Cloud relative difference: `6.15079369e-02`
- Peak relative difference: `5.58662360e-02`
- Centroid absolute difference: `1.00087900e-03`
- Downstream absolute difference: `1.72400100e-03`

## AMR Overhead

- Mean cell ratio: `1.76123457e+00`
- Advance seconds ratio: `1.74300080e+00`
- Final plotfile bytes ratio: `2.08412954e+00`

## Evidence Hashes

- `${SCOUT_ROOT}/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `788f422756a2415ce8749e28ea34caf4573c9965498c23075c3adfa3a95927d2`
- `${SCOUT_ROOT}/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256 `7ca660c467e740dc2369b6081d2f55d409bffd95eab369fef158754cad484039`
- `${SCOUT_ROOT}/plan_amr_compare_summary.csv` sha256 `5ce6f77cd275ca9614488c3068c6d3d4c8d5831fa0a6ac71a7dbfb16ac9c0af7`
- `${SCOUT_ROOT}/amr_overhead_summary.csv` sha256 `ccdb2d14eb8ff004b17e7ef057a2931eabb583c0a2cec699cec9bc9bc7ba0188`
- `${SCOUT_ROOT}/reduced_long_summary.csv` sha256 `d20a7d749879fdda93ced718e90a81f927ccb3e58e81a85a64fdfb513b3f6ec4`

## Limitations

- Reduced-long smoke evidence, not production completion.
- Does not prove overnight stability, production-size MPI scaling, scheduler/affinity behavior, real CAD/large-layout tank-farm AMR load balance, fire heat-release validation, or experimental/reference-data accuracy.
