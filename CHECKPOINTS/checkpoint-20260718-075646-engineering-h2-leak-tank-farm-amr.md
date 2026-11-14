# Checkpoint: engineering H2 leak tank-farm AMR comparison

Date: 2026-07-18 UTC

## Status

Engineering priority remains active. This slice advances the H2 leak workflow from open-domain AMR to a compact three-cylinder EB tank-farm AMR-vs-uniform smoke with maintained hazard diagnostics.

Estimated engineering production-readiness progress: about 85%. The code is still not production-ready for full industrial consequence modeling because real CAD tank farms, overhead/scaling, long-time stability, validated ABL/terrain, and reference-data campaigns remain open.

## Changes

- Added `tools/codex_smoke_engineering_h2_leak_tank_farm_amr_compare.sh`.
- Extended H2 post-processing validators to honor EB `volFrac` when computing mass, cloud volume, plane, and time-series diagnostics.
- Kept invalid/nonfinite fluid-cell guards; solid/covered EB cells are excluded through `volFrac` rather than treated as fluid evidence.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` with the new evidence and remaining limits.

## Primary Evidence

- `/tmp/codex_h2_leak_tank_farm_amr_compare_20260718_volfrac/tank_farm_amr_compare_summary.csv`
- PASS metrics: `amr_finest_level=1`, `amr_finest_fabs=12`, `cloud_rel_diff=1.78378378e-01`, `peak_rel_diff=5.29877227e-02`, `centroid_abs_diff=9.75198000e-05`, `downstream_abs_diff=5.69016300e-03`.
- AMR H2 history/profile/hazard checks passed with `mass_ratioN=1.00000142e+00`, `cloud_volume=2.25830078e-02`, `active_planes=7`, `flammable_planes=3`.
- Text-log scan over 12 `.log` files found 0 matches for `FAIL`, `Traceback`, `Unused ParmParse`, `RuntimeWarning`, `nan`, `abort`, or standalone `error`.

## Regression Evidence

- `python3 -m py_compile tools/validate_h2_leak_hazard_summary.py tools/validate_h2_leak_hazard_planes.py tools/validate_h2_leak_hazard_timeseries.py tools/validate_h2_leak_plume_history.py tools/validate_h2_leak_plume_profile.py`
- `bash -n tools/codex_smoke_engineering_h2_leak_tank_farm_amr_compare.sh`
- `python3 tools/test_amrex_reader_multibox.py`: PASS.
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=946`.
- `ctest --test-dir build-codex-smoke --output-on-failure`: 22/22 PASS.

## Remaining Engineering Gaps

- Real CAD/large-layout tank-farm AMR campaigns and CAD quality classification.
- AMR refinement efficiency, overhead, dynamic tagging, and production-size MPI scaling.
- Long-time stability and larger hazardous-release campaigns.
- Validated ABL/calm-wind/terrain/boundary-condition benchmarks.
- Fire/heat-release consequence metrics and reference-data validation.
