# Engineering H2 production-scale scout checkpoint

Date: 2026-07-20

## Scope

This checkpoint adds the first larger-grid H2 open-domain plan-AMR/MPI production-scale scout. It is stronger than the existing smoke-scale campaign but is not claimed as final production-size validation.

## Changes

- Parameterized `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_compare.sh` with:
  - `CODEX_H2_LEAK_PLAN_AMR_N_CELL`
  - `CODEX_H2_LEAK_PLAN_AMR_PROB_HI`
- Added `tools/write_engineering_h2_production_scale_scout_report.py` to package and verify compact project-local scout evidence.
- Generated project-local evidence at `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/`.
- Updated the engineering production scorecard, readiness audit, and smoke matrix.

## Run Evidence

Source run root: `${SCOUT_ROOT}` after sanitization.

Command class: H2 open-domain plan-AMR/MPI reduced-long wrapper with 4 ranks, 120 steps, base grid `48x24x24`, and Level-1 AMR.

Key PASS lines:

- Baseline plume/history PASS: `nplot=7`, `timeN=0.12`, `mass_ratioN=1.00000000e+00`, `grid_shapes=[(48, 24, 24)]`, `downstream_fraction=8.77095989e-01`.
- AMR plume/history PASS: `nplot=7`, `timeN=0.12`, `mass_ratioN=1.00000036e+00`, `grid_shapes=[(48, 24, 24), (96, 48, 48)]`, `downstream_fraction=8.81380928e-01`.
- AMR compare PASS: `amr_finest_level=1`, `amr_finest_fabs=12`, `regrid_count=59`, `cloud_rel_diff=8.59375007e-02`, `peak_rel_diff=4.91592892e-02`.
- AMR overhead PASS: `mean_ncells_ratio=1.54197531e+00`, `advance_seconds_ratio=1.59525717e+00`, `final_plotfile_bytes_ratio=1.75073988e+00`.
- MPI validation PASS for baseline and AMR: `ranks=4`, `final_time=0.12`, `finalized=1`.
- Scout report PASS/VERIFY-PASS: base cells `27648`, AMR equivalent fine cells `221184`.

## Scorecard Impact

- Engineering functional coverage moved from `85.0%` to `86.6%`.
- Engineering production credibility moved from `62.6%` to `64.2%`.
- Status remains `NOT_PRODUCTION_READY` because scheduler outputs, full production-size campaigns, overnight stability, reference-data agreement, real-CAD cleanup, and calibrated fire metrics remain open.
