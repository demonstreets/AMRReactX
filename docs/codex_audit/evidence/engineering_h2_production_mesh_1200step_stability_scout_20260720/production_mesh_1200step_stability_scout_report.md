# H2-Production-Mesh-1200-Step-Stability-Scout-Report

Status: `PASS-STABILITY`
Evidence tier: `engineering_cfd_scout`
Stability duration class: `production_mesh_1200step_stability_scout`
Production campaign: `False`
Production-size mesh campaign: `False`
Overnight campaign: `False`
Full-duration campaign: `False`
Full plotfile archive: `False`

## Summary

- Ranks: `4`
- Max step: `1200`
- Base grid: `[64, 32, 32]` = `65536` cells
- AMR equivalent fine grid: `[128, 64, 64]` = `524288` cells
- AMR finest level: `1`
- AMR final cloud volume: `1.12258911e-01`
- AMR final peak X: `2.36446481e-01`
- AMR cloud relative difference: `2.99314337e-02`
- AMR peak relative difference: `3.58285346e-02`
- Mean cell-count ratio: `2.33083984e+00`
- Advance-seconds ratio: `2.53215280e+00`

## Limitations

- This is a production-scale scout, not a final production-size campaign.
- It packages compact logs/summaries/inputs only, not full AMReX plotfile directories.
- It does not prove external reference-data agreement, real CAD geometry, scheduler allocation, or overnight stability.

## Packaged Files

- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/engineering_case_report.json` sha256 `88d42c3baeb1efe3`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/engineering_case_report.md` sha256 `b14766005e7447ef`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/reduced_long_summary.csv` sha256 `e626eeb8497ba290`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/plan_amr_compare_summary.csv` sha256 `bd1aab7534478479`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/amr_overhead_summary.csv` sha256 `998bc1e81f36eea3`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/baseline/validation.log` sha256 `3df8f03e48ec8233`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/baseline/profile_validation.log` sha256 `214ff5b2121c8812`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/baseline/hazard_summary.log` sha256 `1cbb44ee07527468`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/baseline/hazard_planes.log` sha256 `3b86335404a6b00e`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/baseline/hazard_timeseries.log` sha256 `58b296f01a6b189d`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/baseline/mpi_validation.log` sha256 `8e5855f98f41891a`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/baseline/run/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `edd2ccffae5d6835`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/amr/validation.log` sha256 `5b23154f143e6cac`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/amr/profile_validation.log` sha256 `26e1516b18e675f7`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/amr/hazard_summary.log` sha256 `7bf2543f963a9519`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/amr/hazard_planes.log` sha256 `55a325c4bcfe2c4f`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/amr/hazard_timeseries.log` sha256 `cdce8ee5dc782db9`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/amr/mpi_validation.log` sha256 `8e5855f98f41891a`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/files/amr/run/input.codex_open_domain_plan_amr_level1_smoke` sha256 `e22071d91f21c966`
