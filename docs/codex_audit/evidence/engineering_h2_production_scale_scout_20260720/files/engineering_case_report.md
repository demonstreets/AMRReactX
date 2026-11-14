# Engineering H2 Case Report: h2-open-domain-plan-amr-mpi-reduced-long

Status: `PASS`
Generated UTC: `2026-07-20T03:37:36+00:00`
Evidence root: `${SCOUT_ROOT}`

## Run Summary

- MPI ranks: `4`
- Steps: `120` with plot interval `20`
- Plotfiles: baseline `7`, AMR `7`
- Final time: `1.200000000000e-01`
- Baseline FABs: `[(0, 12)]`
- AMR FABs: `[(0, 12), (1, 12)]`

## Hazard Metrics

- Baseline final cloud volume: `2.77777778e-02`
- AMR final cloud volume: `2.53906250e-02`
- Baseline final peak X: `1.76935021e-01`
- AMR final peak X: `1.86082715e-01`
- AMR final flammable planes: `6`
- Cloud relative difference: `8.59375007e-02`
- Peak relative difference: `4.91592892e-02`
- Centroid absolute difference: `6.91329000e-04`
- Downstream absolute difference: `4.28493900e-03`

## AMR Overhead

- Mean cell ratio: `1.54197531e+00`
- Advance seconds ratio: `1.59525717e+00`
- Final plotfile bytes ratio: `1.75073988e+00`

## Evidence Hashes

- `${SCOUT_ROOT}/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `62eb3e9327909cc22d2cf8cae0611ecce22a5dd61301f4bd075edcfdba7f1668`
- `${SCOUT_ROOT}/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256 `b5876710de5b3e7eff81b42ef6b0067ac0a083c2d90c6b0a67d405817e7e3b55`
- `${SCOUT_ROOT}/plan_amr_compare_summary.csv` sha256 `cbfe6c83443ba5129b90473a05a15ec1839ee0e5ede5431587cdaf43417787df`
- `${SCOUT_ROOT}/amr_overhead_summary.csv` sha256 `01165ab0fc99ff4e8bfaf55100ed3c59fe0f6279716e5e1fed61d35771e35f20`
- `${SCOUT_ROOT}/reduced_long_summary.csv` sha256 `63996e6ed38a5af292600ae133578f6227324e56888a01e2165993674688f32e`

## Limitations

- Reduced-long smoke evidence, not production completion.
- Does not prove overnight stability, production-size MPI scaling, scheduler/affinity behavior, real CAD/large-layout tank-farm AMR load balance, fire heat-release validation, or experimental/reference-data accuracy.
