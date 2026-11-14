# Self-built Large H2 Engineering Acceptance Run

- Status: PASS-H2-LARGE-ENGINEERING-ACCEPTANCE
- Source root: `/tmp/codex_h2_engineering_acceptance_20260727_8rank_96x48x48_120step_v2`
- MPI ranks: 8
- Base grid: [96, 48, 48] (221184 cells)
- AMR equivalent fine grid: [192, 96, 96] (1769472 cells)
- Max step / plot interval: 120 / 30
- AMR finest level / regrid count: 1 / 59
- Mass ratios baseline/AMR: 1.00000000e+00 / 1.00001907e+00
- Cloud relative diff / peak relative diff: 2.81250000e-01 / 1.82438001e-01
- AMR advance overhead ratio: 1.15410241e+00

The run passed the engineering stability gate: parallel finalization, AMR level creation, regridding, plotfile integrity, finite metrics, positive H2 cloud/hazard metrics, and no failure/NaN/Inf log markers.
