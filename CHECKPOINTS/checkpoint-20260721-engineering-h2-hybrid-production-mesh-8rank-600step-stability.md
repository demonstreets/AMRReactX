# Checkpoint: Engineering H2 Hybrid Production-Mesh 8x2 600-Step Stability Scout

Date: 2026-07-21

## What changed

- Added the real 8 MPI rank x 2 OpenMP thread H2 production-mesh 600-step PeleLMeX hybrid CFD scout evidence to the maintained engineering scorecard and production evidence verifier.
- Added `tools/prepare_mpi_link_shims.sh` and wired the MPI history path to source it when `CODEX_H2_LEAK_HISTORY_USE_MPI=TRUE`, fixing a non-interactive relink blocker caused by missing unversioned OpenMPI development symlinks on this server.
- Refreshed `docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json` and `.md`.

## Evidence

- Report: `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_600step_stability_scout_20260721/hybrid_production_mesh_8rank_600step_stability_scout_report.json`
- Status: `PASS-HYBRID-CFD-SCOUT`
- Parallel mode: 8 MPI ranks x 2 OpenMP threads
- Steps: `max_step=600`
- Mesh: base `64x32x32`, AMR-equivalent `128x64x64`
- Plotfiles: 11 baseline and 11 AMR
- AMR: finest level 1, 28 fine FABs, `regrid_count=299`
- Drift/overhead: `cloud_rel_diff=3.15976518e-02`, `peak_rel_diff=3.40034177e-02`, `mean_ncells_ratio=1.97647135`, `advance_seconds_ratio=2.20802169`
- Scorecard after integration: `status=NOT_PRODUCTION_READY`, `functional=92.8`, `production=72.7`

## Remaining blockers

- Scheduler-managed production campaign remains `NOT_READY` because SLURM controller probes/submission are not currently accepting jobs.
- Full production-size/overnight campaign evidence is still missing.
- Real CAD cleanup, external reference-data agreement, and calibrated fire/radiation/overpressure validation remain open.
- MPI reports thread support level 0; current hybrid runs avoid MPI calls from multiple OpenMP threads, so this is tracked but not cleared as a production deployment risk.
