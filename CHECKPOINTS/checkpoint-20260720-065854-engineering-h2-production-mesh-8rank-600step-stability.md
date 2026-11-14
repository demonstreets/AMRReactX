# Checkpoint: engineering H2 production-mesh 8-rank 600-step stability scout

Date: 2026-07-20

## Summary

Completed and packaged an 8-rank MPI H2 open-domain dynamic plan-AMR production-mesh 600-step stability scout. This bridges the previous 8-rank short production-mesh scout and the 4-rank long production-mesh stability evidence.

## Run Evidence

- Scout root token: `${SCOUT_ROOT}` = `codex_h2_leak_production_mesh_8rank_600step_stability_scout_20260720`
- MPI ranks: `8`
- Max step: `600`
- Plot interval: `60`
- Plotfiles: baseline `11`, AMR `11`
- Base grid: `64x32x32` = `65536` cells
- AMR equivalent fine grid: `128x64x64` = `524288` cells
- AMR finest level: `1`
- Cloud relative difference: `3.15976518e-02`
- Peak-X relative difference: `3.40034177e-02`
- Mean Ncells ratio: `1.97647135`
- Advance-seconds ratio: `2.38748687`

## Packaged Evidence

- `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_600step_stability_scout_20260720/production_mesh_8rank_600step_stability_scout_report.json`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_8rank_600step_stability_scout_20260720/production_mesh_8rank_600step_stability_scout_report.md`

## Scorecard / Matrix Update

- Updated `tools/write_engineering_h2_acceptance_matrix.py` to include the 8-rank/600-step stability report as first-class evidence for the production-mesh AMR/MPI stability row.
- Updated `tools/write_engineering_production_scorecard.py` to include the report as hashed evidence and use it in the AMR/MPI efficiency gate.
- Latest scorecard: `engineering_functional_coverage_percent=90.8`, `engineering_production_credibility_percent=70.5`, `status=NOT_PRODUCTION_READY`.
- Acceptance matrix remains `PARTIAL-PRODUCTION` with `pass_like_rows=6` and `scheduler_managed_campaign` as the only not-ready row.

## Validation

- `python3 -m py_compile tools/write_engineering_h2_acceptance_matrix.py tools/write_engineering_production_scorecard.py tools/write_engineering_h2_production_scale_scout_report.py tools/validate_h2_leak_hazard_timeseries.py`: PASS
- `python3 tools/write_engineering_h2_production_scale_scout_report.py --verify-json ...8rank_600step...json`: PASS
- `python3 tools/write_engineering_h2_acceptance_matrix.py --verify-json ...engineering_h2_acceptance_matrix.json`: PASS
- `python3 tools/write_engineering_production_scorecard.py --verify-json ...engineering_production_scorecard.json`: PASS, `functional=90.8`, `production=70.5`
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=966`
- `ctest --test-dir build-codex-smoke --output-on-failure`: PASS, `22/22`
