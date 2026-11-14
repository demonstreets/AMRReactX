# H2-Production-Mesh-4Rank-7200-Step-Full-Duration-Report

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
- Max step: `7200`
- Base grid: `[64, 32, 32]` = `65536` cells
- AMR equivalent fine grid: `[128, 64, 64]` = `524288` cells
- AMR finest level: `1`
- AMR final cloud volume: `1.12243652e-01`
- AMR final peak X: `2.36439019e-01`
- AMR cloud relative difference: `2.80126911e-02`
- AMR peak relative difference: `3.45775965e-02`
- Mean cell-count ratio: `2.62805664e+00`
- Advance-seconds ratio: `2.90979970e+00`

## Limitations

- This is a production-scale scout, not a final production-size campaign.
- It packages compact logs/summaries/inputs only, not full AMReX plotfile directories.
- It does not prove external reference-data agreement, real CAD geometry, scheduler allocation, or overnight stability.

## Packaged Files

- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/engineering_case_report.json` sha256 `a37f18bd7f57378c`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/engineering_case_report.md` sha256 `2a18db8f6090b334`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/reduced_long_summary.csv` sha256 `36c0728739ad9c32`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/plan_amr_compare_summary.csv` sha256 `52baa77673545414`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/amr_overhead_summary.csv` sha256 `dc62cea132b88eaa`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/baseline/validation.log` sha256 `aa09a8a8f83d133d`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/baseline/profile_validation.log` sha256 `a29e97734cd6b090`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/baseline/hazard_summary.log` sha256 `7328251d27ed3766`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/baseline/hazard_planes.log` sha256 `d965acb472da1957`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/baseline/hazard_timeseries.log` sha256 `f5c22249c3a020d7`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/baseline/mpi_validation.log` sha256 `d6d2373a75669d48`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/baseline/run/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `afd8984bfaf6b83c`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/amr/validation.log` sha256 `2cdd091dc117d0ed`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/amr/profile_validation.log` sha256 `f85b7873147f9f92`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/amr/hazard_summary.log` sha256 `59496f99e2df6c4f`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/amr/hazard_planes.log` sha256 `44ffecb7a81a9d55`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/amr/hazard_timeseries.log` sha256 `6b8de2c5657c61b1`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/amr/mpi_validation.log` sha256 `d6d2373a75669d48`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_4rank_full_duration_20260722/files/amr/run/input.codex_open_domain_plan_amr_level1_smoke` sha256 `c0dfd077ec39fc20`
