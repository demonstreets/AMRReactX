# Engineering H2 Case Report: h2-open-domain-plan-amr-mpi-reduced-long

Status: `PASS`
Generated UTC: `2026-07-20T02:30:02+00:00`
Evidence root: `/tmp/codex_engineering_h2_campaign_full_20260720/cases/plan-amr-mpi-reduced-long`

## Run Summary

- MPI ranks: `4`
- Steps: `200` with plot interval `20`
- Plotfiles: baseline `11`, AMR `11`
- Final time: `2.000000000000e-01`
- Baseline FABs: `[(0, 16)]`
- AMR FABs: `[(0, 16), (1, 47)]`

## Hazard Metrics

- Baseline final cloud volume: `3.32031250e-02`
- AMR final cloud volume: `3.82080078e-02`
- Baseline final peak X: `1.97328208e-01`
- AMR final peak X: `2.26296822e-01`
- AMR final flammable planes: `10`
- Cloud relative difference: `1.30990415e-01`
- Peak relative difference: `1.28011581e-01`
- Centroid absolute difference: `1.68538700e-03`
- Downstream absolute difference: `4.83289200e-03`

## AMR Overhead

- Mean cell ratio: `1.97898438e+00`
- Advance seconds ratio: `2.62897371e+00`
- Final plotfile bytes ratio: `2.44258847e+00`

## Evidence Hashes

- `/tmp/codex_engineering_h2_campaign_full_20260720/cases/plan-amr-mpi-reduced-long/inputs/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `678527f737e9ec5a7440ce6853374c043e5efd7b65a623f608b0d7fea310184a`
- `/tmp/codex_engineering_h2_campaign_full_20260720/cases/plan-amr-mpi-reduced-long/inputs/input.codex_open_domain_plan_amr_level1_smoke` sha256 `d9a43810797785a06293f02f1fe4b33250bafd433cc6d6e29b8cabe0e6dc6222`
- `/tmp/codex_engineering_h2_campaign_full_20260720/cases/plan-amr-mpi-reduced-long/plan_amr_compare_summary.csv` sha256 `74eb1d931a448ccadab595805038c840fd3285a78c823b70e07617851d85e076`
- `/tmp/codex_engineering_h2_campaign_full_20260720/cases/plan-amr-mpi-reduced-long/amr_overhead_summary.csv` sha256 `0c5e9fd53626961a907279c751fcd356de024a1690d5cf0134a75abba711e4ae`
- `/tmp/codex_engineering_h2_campaign_full_20260720/cases/plan-amr-mpi-reduced-long/reduced_long_summary.csv` sha256 `4166ac92139e9683120f60923b389823ec747eb74e625ebad87bcc7cf38c1cac`

## Limitations

- Reduced-long smoke evidence, not production completion.
- Does not prove overnight stability, production-size MPI scaling, scheduler/affinity behavior, real CAD/large-layout tank-farm AMR load balance, fire heat-release validation, or experimental/reference-data accuracy.
