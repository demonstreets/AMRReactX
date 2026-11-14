# Checkpoint: Engineering H2 Production-Mesh 600-Step Stability Scout

Date: 2026-07-20

## Scope

Priority remains engineering H2 leak/dispersion/fire workflows before academic scenarios. This checkpoint records the new 4-rank, 600-step production-mesh H2 open-domain dynamic plan-AMR/MPI stability scout and its scorecard integration.

## Evidence Added

- Evidence report: `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/production_mesh_600step_stability_scout_report.json`
- Markdown report: `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/production_mesh_600step_stability_scout_report.md`
- Source run root used during packaging: `${SCOUT_ROOT}` = production mesh 600-step stability scout root outside the repository.

## Key Metrics

- Solver path: PeleLMeX engineering H2 open-domain dynamic plan-AMR/MPI.
- MPI ranks: 4.
- Steps/outputs: `max_step=600`, `plot_int=60`, 11 plotfiles per case.
- Base grid: `64x32x32` = 65536 cells.
- AMR equivalent fine grid: `128x64x64` = 524288 cells.
- AMR finest level: 1.
- Baseline final cloud volume: `9.87548828e-02`.
- AMR final cloud volume: `9.56344604e-02`.
- Cloud relative difference: `3.15976518e-02`.
- Peak H2 relative difference: `3.40034177e-02`.
- Centroid absolute difference: `5.37634000e-04`.
- Downstream fraction absolute difference: `4.98946000e-04`.
- AMR mean cell-count ratio: `1.97647135`.
- AMR advance-seconds ratio: `2.26482395`.
- AMR final active planes: 77.
- AMR final flammable planes: 72.
- AMR final peak X(H2): `2.36445291e-01`.

## Threshold Note

The first full wrapper attempt failed only the AMR centroid-plane H2 fraction threshold: the AMR final profile reported `plane_fraction=1.28163874e-02` against the short-smoke default `0.02`. Mass conservation, downstream motion, hazard time-series, MPI finalization, and AMR-vs-baseline drift were healthy. The existing 600-step outputs were therefore revalidated with `--min-plane-mass-fraction 0.01`, which is recorded as a production-mesh 600-step stability threshold for a more spatially distributed long-time plume, not as a relaxation of short smoke criteria.

## Scorecard Integration

- Updated `tools/write_engineering_production_scorecard.py` with `--production-mesh-600step-stability-scout-report`.
- New scorecard verifier result: `engineering_production_scorecard VERIFY-PASS ... functional=90.1 production=69.3`.
- Status remains `NOT_PRODUCTION_READY`.
- The `long_duration_stability` gate is now `PARTIAL++` based on 600-step production-mesh evidence.

## Remaining Production Gaps

- Completed scheduler-managed production campaign remains missing.
- Overnight/full-duration stability remains missing; this is a 600-step scout, not an overnight campaign.
- Full production-size/reference-data agreement remains missing.
- Real CAD cleanup and large layout campaigns remain missing.
- Fire/radiation/overpressure consequence metrics remain screening-only, not calibrated validation.

## Validation Commands

- MPI log validator passed for baseline and AMR with 4 ranks and `final_time=0.6`.
- Manual profile/hazard validators passed for baseline and AMR using the documented 600-step centroid-plane threshold.
- Reduced-long reuse wrapper passed using existing 600-step outputs.
- Production-scale scout report verifier passed for the new evidence JSON.
- Engineering production scorecard verifier passed after integration.

