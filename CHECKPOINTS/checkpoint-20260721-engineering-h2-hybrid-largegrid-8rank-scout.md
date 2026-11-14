# Checkpoint: Engineering H2 Hybrid Large-Grid 8-Rank Scout

Date: 2026-07-21

## What changed

- Ran a real H2 open-domain AMR hybrid MPI+OpenMP large-grid CFD scout.
- Packaged the run with `tools/write_engineering_h2_hybrid_cfd_scout_report.py`.
- Added the large-grid scout to the engineering production scorecard.
- Added the large-grid scout to the one-command engineering H2 production evidence verifier and schema 5 verification report.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md`.

## Evidence

- Large-grid scout report: `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/hybrid_largegrid_8rank_120step_scout_report.json`, `PASS-HYBRID-CFD-SCOUT`.
- Parallelism: 8 MPI ranks x 2 OpenMP threads.
- Mesh: base grid `96x48x48` (`221184` cells), AMR-equivalent fine grid `192x96x96` (`1769472` cells).
- Runtime: `max_step=120`, 5 baseline plotfiles, 5 AMR plotfiles, AMR finest level 1, 36 fine FABs, `regrid_count=59`.
- AMR-vs-baseline drift: `cloud_rel_diff=1.59761211e-02`, `peak_rel_diff=1.55533247e-03`, `advance_seconds_ratio=1.72411476`.
- Scorecard: `engineering_production_scorecard VERIFY-PASS`, `status=NOT_PRODUCTION_READY`, `functional=93.3`, `production=73.3`.
- Full archive: `tools/run_engineering_h2_production_evidence_verification_archive.sh` PASS, path audit PASS, MPI link shim PASS, CTest `22/22 PASS`, verification report schema 5 PASS.

## Interpretation

This strengthens large-grid interactive hybrid AMR evidence for the engineering H2 leak/dispersion chain. It does not clear the scheduler-managed production blocker, overnight/full-duration stability blocker, real-CAD blocker, external reference-data blocker, or calibrated fire-consequence blocker.
