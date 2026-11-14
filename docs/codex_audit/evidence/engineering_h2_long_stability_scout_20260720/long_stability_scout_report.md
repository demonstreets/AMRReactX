# H2 Long-Stability Scout Report

Status: `PASS-STABILITY`

## Summary

- Ranks: `4`
- Max step: `300`
- Base grid: `[48, 24, 24]` = `27648` cells
- AMR equivalent fine grid: `[96, 48, 48]` = `221184` cells
- AMR finest level: `1`
- AMR final cloud volume: `5.13237847e-02`
- AMR final peak X: `2.22321843e-01`
- AMR cloud relative difference: `6.15079369e-02`
- AMR peak relative difference: `5.58662360e-02`
- Mean cell-count ratio: `1.76123457e+00`
- Advance-seconds ratio: `1.74300080e+00`

## Limitations

- This is a 300-step long-stability scout, not an overnight or full-duration production campaign.
- It packages compact logs/summaries/inputs only, not full AMReX plotfile directories.
- It does not prove external reference-data agreement, real CAD geometry, scheduler allocation, or calibrated fire/radiation metrics.

## Packaged Files

- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/engineering_case_report.json` sha256 `0e9c1d98065dd3e9`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/engineering_case_report.md` sha256 `5e1b09c57a3e289c`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/reduced_long_summary.csv` sha256 `4775d5f15a8e4914`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/plan_amr_compare_summary.csv` sha256 `fa26d02738c3059c`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/amr_overhead_summary.csv` sha256 `f3964c1a0085e0be`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/baseline/validation.log` sha256 `97195bace0aaef6d`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/baseline/profile_validation.log` sha256 `e4443989ec94f2c0`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/baseline/hazard_summary.log` sha256 `1ca2c0263da227c7`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/baseline/hazard_planes.log` sha256 `959d2a528a0dc4c8`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/baseline/hazard_timeseries.log` sha256 `5dcfc071cec36dc1`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/baseline/mpi_validation.log` sha256 `a5e74167da5e9966`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/baseline/run/input.codex_open_domain_plan_amr_baseline_smoke` sha256 `788f422756a2415c`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/amr/validation.log` sha256 `76a40f8abac3f106`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/amr/profile_validation.log` sha256 `72d8837508a83443`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/amr/hazard_summary.log` sha256 `84df559f22493412`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/amr/hazard_planes.log` sha256 `5fddd96147734b22`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/amr/hazard_timeseries.log` sha256 `8f2f1e4d0561a548`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/amr/mpi_validation.log` sha256 `a5e74167da5e9966`
- `docs/codex_audit/evidence/engineering_h2_long_stability_scout_20260720/files/amr/run/input.codex_open_domain_plan_amr_level1_smoke` sha256 `7ca660c467e740dc`
