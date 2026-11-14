# Checkpoint: Engineering H2 Hybrid Production-Mesh 8-Rank Scout

Date: 2026-07-21

## What changed

- Completed a real PeleLMeX H2 open-domain production-mesh AMR scout with MPI+OpenMP hybrid execution: 8 MPI ranks x 2 OpenMP threads.
- Generated and verified `docs/codex_audit/evidence/engineering_h2_hybrid_production_mesh_8rank_scout_20260720/hybrid_production_mesh_8rank_scout_report.json`.
- Integrated that report into `tools/write_engineering_production_scorecard.py`, `tools/verify_engineering_h2_production_evidence.sh`, and `tools/write_engineering_h2_production_evidence_verification_report.py`.
- Refreshed the engineering production scorecard and the production evidence verification archive.

## Evidence

- Case root: `/tmp/codex_h2_leak_open_domain_plan_amr_hybrid_prodmesh_8rank_20260720`.
- Report status: `PASS-HYBRID-CFD-SCOUT`.
- Parallel mode: 8 MPI ranks x 2 OpenMP threads.
- Mesh: base `64x32x32`, AMR-equivalent fine `128x64x64`.
- Runtime span: `max_step=120`, 5 baseline plotfiles and 5 AMR plotfiles.
- AMR: finest level `1`, fine FABs `12`, `regrid_count=59`.
- Conservation/profile checks: final H2 mass ratio `1.00012525`, downstream fraction `0.882114607`.
- AMR-vs-baseline drift: `cloud_rel_diff=3.80952381e-02`, `peak_rel_diff=4.31073584e-02`.
- AMR overhead: `advance_seconds_ratio=2.00980894`.
- Fast archive verification: `tools/run_engineering_h2_production_evidence_verification_archive.sh` with `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE` passed.

## Scorecard

- `engineering_functional_coverage_percent=92.7`.
- `engineering_production_credibility_percent=72.5`.
- Overall status remains `NOT_PRODUCTION_READY`.

## Remaining blockers

- Scheduler-managed SLURM campaign evidence is still `NOT_READY`.
- Overnight/full-duration production campaigns are still missing.
- External reference-data agreement, real-CAD cleanup campaigns, and calibrated fire/radiation/overpressure metrics remain open.
- MPI reports thread support level 0 in the hybrid CFD logs; accepted for these gates because the workflow does not call MPI from multiple OpenMP threads, but it remains a production portability risk to track.
