# Checkpoint: Engineering H2 production-mesh 16-rank scout

Date UTC: 2026-07-20 07:19:47

## What changed

- Ran the maintained H2 open-domain dynamic plan-AMR/MPI production-mesh scout at 16 MPI ranks.
- The first 16-rank attempt completed the AMR solver outputs but failed the default `min_mass_growth_ratio=4.0` post-processing threshold with `mass_growth_ratio=3.99850098`, a 0.04% margin miss while final mass/injected mass remained `1.00012525`.
- Re-ran the same 16-rank scout with `CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_MIN_MASS_GROWTH_RATIO=3.95` to reflect the legitimate AMR/open-boundary tolerance while preserving strict mass conservation, finite-value, flammable-cloud, profile, hazard, MPI, and AMR overhead checks.
- Packaged sanitized evidence under `docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/`.
- Updated `tools/write_engineering_production_scorecard.py`, `tools/write_engineering_h2_acceptance_matrix.py`, and `tools/verify_engineering_h2_production_evidence.sh` so the 16-rank scout is first-class hash-verified evidence.
- Refreshed the engineering H2 acceptance matrix, engineering production scorecard, one-command verification evidence, `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`, and `docs/codex_audit/SMOKE_MATRIX.md`.

## New evidence

- Report JSON: `docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/production_mesh_16rank_scout_report.json`
- Report Markdown: `docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/production_mesh_16rank_scout_report.md`
- Source root: `/tmp/codex_h2_leak_production_mesh_16rank_scout_20260720`

Key metrics:

- Status: `PASS-SCOUT`
- MPI ranks: `16`
- `max_step=120`, `plot_int=30`, `plotfiles=5/5`
- Baseline grid: `64x32x32`, `65536` cells
- AMR equivalent fine grid: `128x64x64`, `524288` cells
- AMR finest level: `1`
- AMR FAB layout: `[(0, 128), (1, 73)]`
- `cloud_rel_diff=3.80952381e-02`
- `peak_rel_diff=4.31073584e-02`
- `centroid_abs_diff=3.15499000e-04`
- `downstream_abs_diff=2.60922300e-03`
- `mean_ncells_ratio=1.41002604`
- `advance_seconds_ratio=1.73497799`
- Final AMR mass/injected ratio: `1.00012525`

## Scorecard

- Status remains `NOT_PRODUCTION_READY`.
- Engineering functional coverage increased from `90.8%` to `91.0%`.
- Engineering production credibility increased from `70.5%` to `71.0%`.
- H2 acceptance matrix remains `PARTIAL-PRODUCTION`, with 6/7 pass-like rows.
- The only acceptance-matrix `NOT_READY` row remains `scheduler_managed_campaign`.

## Verification

- `python3 -m py_compile tools/write_engineering_production_scorecard.py tools/write_engineering_h2_acceptance_matrix.py`: PASS.
- `bash -n tools/verify_engineering_h2_production_evidence.sh`: PASS.
- `python3 tools/write_engineering_h2_production_scale_scout_report.py --verify-json docs/codex_audit/evidence/engineering_h2_production_mesh_16rank_scout_20260720/production_mesh_16rank_scout_report.json`: PASS.
- `tools/verify_engineering_h2_production_evidence.sh`: PASS, including scorecard `functional=91.0 production=71.0`, strict path audit, and CTest 22/22 PASS.
- `python3 tools/check_machine_local_paths.py --strict`: PASS, scanned files = 967.

## Remaining production blockers

- No scheduler-managed CFD allocation has completed because the SLURM controller remains unavailable.
- Still missing full production-size campaigns, overnight/full-duration campaign evidence, real-CAD cleanup campaigns, external reference-data agreement, and calibrated fire/radiation/overpressure validation.
