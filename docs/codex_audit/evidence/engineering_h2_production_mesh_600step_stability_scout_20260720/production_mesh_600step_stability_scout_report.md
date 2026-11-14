# H2 Production-Mesh 600-Step Stability Scout Report

Status: `PASS-STABILITY`

## Summary

- Ranks: `4`
- Max step: `600`
- Base grid: `[64, 32, 32]` = `65536` cells
- AMR equivalent fine grid: `[128, 64, 64]` = `524288` cells
- AMR finest level: `1`
- AMR final cloud volume: `9.56344604e-02`
- AMR final peak X: `2.36445291e-01`
- AMR cloud relative difference: `3.15976518e-02`
- AMR peak relative difference: `3.40034177e-02`
- Mean cell-count ratio: `1.97647135e+00`
- Advance-seconds ratio: `2.26482395e+00`

## Limitations

- This is a production-scale scout, not a final production-size campaign.
- It packages compact logs/summaries/inputs only, not full AMReX plotfile directories.
- It does not prove external reference-data agreement, real CAD geometry, scheduler allocation, or overnight stability.

## Packaged Files

- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/engineering_case_report.json` sha256 `5d0f0732cd7127d3`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/engineering_case_report.md` sha256 `47faf3570ae94dec`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/reduced_long_summary.csv` sha256 `df8a665f82958357`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/plan_amr_compare_summary.csv` sha256 `44ec460305662791`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/amr_overhead_summary.csv` sha256 `a01f44a068101266`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/baseline/validation.log` sha256 `88ad87488aa53cc4`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/baseline/profile_validation.log` sha256 `d647c935d5698c07`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/baseline/hazard_summary.log` sha256 `d2b32331241d5c05`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/baseline/hazard_planes.log` sha256 `199891c5166bc330`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/baseline/hazard_timeseries.log` sha256 `ba2e65a141c5efeb`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/baseline/mpi_validation.log` sha256 `a10c9e136e67b14e`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/baseline/run/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `cea42800aaa06b5e`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/amr/validation.log` sha256 `1da3411dfac5a064`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/amr/profile_validation.log` sha256 `7995ceef9ce2fc03`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/amr/hazard_summary.log` sha256 `2c6dc42566be60b8`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/amr/hazard_planes.log` sha256 `5e72f2010ba853d8`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/amr/hazard_timeseries.log` sha256 `b839598ea0ddcc76`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/amr/mpi_validation.log` sha256 `a10c9e136e67b14e`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_600step_stability_scout_20260720/files/amr/run/input.codex_open_domain_plan_amr_level1_smoke` sha256 `9804f132135b9bfa`
