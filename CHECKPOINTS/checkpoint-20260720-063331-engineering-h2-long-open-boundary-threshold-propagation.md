# Checkpoint: engineering H2 long open-boundary threshold propagation

Date: 2026-07-20

## Summary

Fixed a reproducibility issue in the H2 open-domain plan-AMR long-run wrappers. The 1200-step production-mesh MPI+AMR solver run was physically and numerically valid, but the first automatic chain could fail because short-smoke mass-retention thresholds were hard-coded in the profile wrapper and not consistently propagated from the reduced-long wrapper.

## Changes

- `tools/codex_smoke_engineering_h2_leak_plume_profile.sh` now preserves caller-provided history/profile final mass-ratio thresholds instead of hard-coding `0.80/1.20`.
- `tools/validate_h2_leak_hazard_timeseries.py` now supports `--max-mass-drop-ratio` for explicit long-run open-boundary mass-drop tolerance while preserving the strict default `1.0e-6`.
- `tools/codex_smoke_engineering_h2_leak_flammable_cloud.sh` passes the configurable time-series mass-drop ratio into the validator.
- `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_compare.sh` propagates plan-AMR mass-growth, max-drop, final-retention, profile-retention, and plane-mass thresholds into downstream validators.
- `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh` maps `CODEX_H2_LEAK_PLAN_AMR_MPI_LONG_*` threshold knobs to the downstream `CODEX_H2_LEAK_PLAN_AMR_*` knobs.

## Evidence

- 1200-step reduced-long reuse verification: PASS with 4 MPI ranks, `max_step=1200`, 11/11 plotfiles, `cloud_rel_diff=2.99314337e-02`, `peak_rel_diff=3.58285346e-02`.
- Baseline and AMR hazard time-series rechecks PASS with `--require-monotone-mass --max-mass-drop-ratio 0.002` on the 1200-step production-mesh scout outputs.
- Refreshed 1200-step evidence report: `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/production_mesh_1200step_stability_scout_report.json`.
- Refreshed scorecard: `engineering_functional_coverage_percent=90.6`, `engineering_production_credibility_percent=70.0`, `status=NOT_PRODUCTION_READY`.

## Validation

- `python3 -m py_compile tools/validate_h2_leak_plume_history.py tools/validate_h2_leak_hazard_timeseries.py tools/write_engineering_production_scorecard.py tools/write_engineering_h2_production_scale_scout_report.py`: PASS
- `bash -n` on the H2 plume/open-domain/plan-AMR shell wrappers: PASS
- `python3 tools/write_engineering_h2_production_scale_scout_report.py --verify-json ...1200step...json`: PASS
- `python3 tools/write_engineering_production_scorecard.py --verify-json ...scorecard.json`: PASS, `functional=90.6`, `production=70.0`
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=965`
- `ctest --test-dir build-codex-smoke --output-on-failure`: PASS, `22/22`
