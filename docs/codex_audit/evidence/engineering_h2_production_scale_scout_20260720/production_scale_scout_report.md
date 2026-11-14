# H2 Production-Scale Scout Report

Status: `PASS-SCOUT`

## Summary

- Ranks: `4`
- Max step: `120`
- Base grid: `[48, 24, 24]` = `27648` cells
- AMR equivalent fine grid: `[96, 48, 48]` = `221184` cells
- AMR finest level: `1`
- AMR final cloud volume: `2.53906250e-02`
- AMR final peak X: `1.86082715e-01`
- AMR cloud relative difference: `8.59375007e-02`
- AMR peak relative difference: `4.91592892e-02`
- Mean cell-count ratio: `1.54197531e+00`
- Advance-seconds ratio: `1.59525717e+00`

## Limitations

- This is a production-scale scout, not a final production-size campaign.
- It packages compact logs/summaries/inputs only, not full AMReX plotfile directories.
- It does not prove external reference-data agreement, real CAD geometry, scheduler allocation, or overnight stability.

## Packaged Files

- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/engineering_case_report.json` sha256 `870d6038a5340867`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/engineering_case_report.md` sha256 `d5a0fe8460818286`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/reduced_long_summary.csv` sha256 `ce760f6154e673b7`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/plan_amr_compare_summary.csv` sha256 `aacf5746f4493f79`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/amr_overhead_summary.csv` sha256 `59eecd8ef9577c59`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/baseline/validation.log` sha256 `67309cdc05c65797`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/baseline/profile_validation.log` sha256 `f2e0c3477161ecac`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/baseline/hazard_summary.log` sha256 `8d5f27f29710aaac`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/baseline/hazard_planes.log` sha256 `2e66fc8a3f1b8c4d`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/baseline/hazard_timeseries.log` sha256 `476a3bf263cc1efa`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/baseline/mpi_validation.log` sha256 `d054b6f4b4a0769a`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/baseline/run/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `62eb3e9327909cc2`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/amr/validation.log` sha256 `bd63b63bb506b2b4`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/amr/profile_validation.log` sha256 `db3974dc4312441c`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/amr/hazard_summary.log` sha256 `448273f32a951bb6`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/amr/hazard_planes.log` sha256 `47eb75ae897f9fe0`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/amr/hazard_timeseries.log` sha256 `16181bbeee37a414`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/amr/mpi_validation.log` sha256 `d054b6f4b4a0769a`
- `docs/codex_audit/evidence/engineering_h2_production_scale_scout_20260720/files/amr/run/input.codex_open_domain_plan_amr_level1_smoke` sha256 `b5876710de5b3e7e`
