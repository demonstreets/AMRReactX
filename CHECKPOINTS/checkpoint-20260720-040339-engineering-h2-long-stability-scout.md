# Engineering H2 Long-Stability Scout Checkpoint

UTC: 2026-07-20T04:03:39+00:00

## Result

- Added long-run plan-AMR validation thresholds for source-side retention and centroid-plane mass fraction without changing short plume-history/profile defaults.
- Ran 4-rank H2 open-domain dynamic plan-AMR/MPI long-stability scout at `max_step=300`, `plot_int=30`, `n_cell=48 24 24`.
- Baseline and AMR plume-history, profile, flammable-cloud planes/time-series, plan-AMR drift, AMR overhead, and MPI log validators all passed.
- Packaged evidence at `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/long_stability_scout_report.json` with status `PASS-STABILITY`.
- Updated engineering production scorecard to `functional=88.0%`, `production=65.9%`, status `NOT_PRODUCTION_READY`.

## Key Metrics

- Baseline final cloud volume: `5.46875000e-02`
- AMR final cloud volume: `5.13237847e-02`
- AMR finest level/fabs: `1` / `16`
- Cloud relative difference: `6.15079369e-02`
- Peak relative difference: `5.58662360e-02`
- Mean cell-count ratio: `1.76123457e+00`
- Advance-seconds ratio: `1.74300080e+00`
- MPI validation: `ranks=4`, `final_time=0.3`, `finalized=1`

## Remaining Blockers

- Scheduler-run outputs are still not PASS because current SLURM probes time out.
- Full production-size mesh campaigns, overnight/full-duration stability, reference-data agreement, real-CAD cleanup campaigns, and calibrated fire/radiation/overpressure metrics remain open.
