# Engineering H2 Case Report: h2-open-domain-plan-amr-mpi-reduced-long

Status: `PASS`
Generated UTC: `2026-07-20T06:31:09+00:00`
Evidence root: `${SCOUT_ROOT}`

## Run Summary

- MPI ranks: `4`
- Steps: `1200` with plot interval `120`
- Plotfiles: baseline `11`, AMR `11`
- Final time: `1.200000000000e+00`
- Baseline FABs: `[(0, 16)]`
- AMR FABs: `[(0, 16), (1, 28)]`

## Hazard Metrics

- Baseline final cloud volume: `1.15722656e-01`
- AMR final cloud volume: `1.12258911e-01`
- Baseline final peak X: `2.28267974e-01`
- AMR final peak X: `2.36446481e-01`
- AMR final flammable planes: `83`
- Cloud relative difference: `2.99314337e-02`
- Peak relative difference: `3.58285346e-02`
- Centroid absolute difference: `4.40686000e-04`
- Downstream absolute difference: `3.92451000e-04`

## AMR Overhead

- Mean cell ratio: `2.33083984e+00`
- Advance seconds ratio: `2.53215280e+00`
- Final plotfile bytes ratio: `2.68761107e+00`

## Evidence Hashes

- `${SCOUT_ROOT}/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `edd2ccffae5d683562ca239d4e0304114f325be84ef00252217d4d3f9c82ff8d`
- `${SCOUT_ROOT}/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256 `e22071d91f21c9668f96f02521af36fb148ac338e845add2de89a9534457115d`
- `${SCOUT_ROOT}/plan_amr_compare_summary.csv` sha256 `42287a923d1d0edf08155dff281759fe7fb0cf3bdf97769d54a094593ac56ee1`
- `${SCOUT_ROOT}/amr_overhead_summary.csv` sha256 `edc92ee01a517d0cf2c9107f56d3e65df31af3db004b584dcfa1f091184ab2bd`
- `${SCOUT_ROOT}/reduced_long_summary.csv` sha256 `ce51e33238d767182818da29133c6544ef81ac39385d4f6a69678ef5360ccb8e`

## Limitations

- Reduced-long smoke evidence, not production completion.
- Does not prove overnight stability, production-size MPI scaling, scheduler/affinity behavior, real CAD/large-layout tank-farm AMR load balance, fire heat-release validation, or experimental/reference-data accuracy.
