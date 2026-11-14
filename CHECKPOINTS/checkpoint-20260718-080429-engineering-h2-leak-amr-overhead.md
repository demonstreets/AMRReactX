# Checkpoint: engineering H2 leak AMR overhead accounting

Date: 2026-07-18 UTC

## Status

Engineering priority remains active. This slice adds smoke-level AMR overhead accounting to the maintained H2 leak AMR-vs-uniform workflow, so AMR evidence now records both plume/hazard agreement and bounded static-refinement cost.

Estimated engineering production-readiness progress: about 86%. The program is still not production-ready for full industrial consequence modeling because production scaling, dynamic refinement efficiency, real CAD/large tank farms, long-time stability, ABL/terrain validation, and reference-data campaigns remain open.

## Changes

- Added `tools/summarize_h2_leak_amr_overhead.py`.
- Integrated overhead CSV generation into:
  - `tools/codex_smoke_engineering_h2_leak_open_domain_amr_compare.sh`
  - `tools/codex_smoke_engineering_h2_leak_tank_farm_amr_compare.sh`
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` to reflect smoke-level AMR overhead evidence and remaining scaling/efficiency limits.

## Primary Evidence

- Integrated rerun: `/tmp/codex_h2_leak_open_domain_amr_overhead_20260718/amr_compare_summary.csv`
  - PASS: `amr_finest_level=1`, `amr_finest_fabs=2`, `cloud_rel_diff=7.85340319e-02`, `peak_rel_diff=4.90278862e-02`, `centroid_abs_diff=3.40203000e-04`, `downstream_abs_diff=5.49446000e-03`.
- Integrated overhead CSV: `/tmp/codex_h2_leak_open_domain_amr_overhead_20260718/amr_overhead_summary.csv`
  - PASS: `mean_ncells_ratio=2.00000000e+00`, `advance_seconds_ratio=2.21906710e+00`, `final_plotfile_bytes_ratio=2.00157687e+00`, `amr_finest_level=1`, `amr_finest_fabs=2`.
- Offline tank-farm overhead CSV on prior validated run: `/tmp/codex_h2_leak_tank_farm_amr_compare_20260718_volfrac/amr_overhead_summary.csv`
  - PASS: `mean_ncells_ratio=4.75000000e+00`, `advance_seconds_ratio=5.57653943e+00`, `final_plotfile_bytes_ratio=4.75722149e+00`, `amr_finest_level=1`, `amr_finest_fabs=12`.
- Text-log scan over `/tmp/codex_h2_leak_open_domain_amr_overhead_20260718` found 0 matches across 12 `.log` files for `FAIL`, `Traceback`, `Unused ParmParse`, `RuntimeWarning`, `nan`, `abort`, or standalone `error`.

## Regression Evidence

- `python3 -m py_compile tools/summarize_h2_leak_amr_overhead.py tools/validate_h2_leak_hazard_summary.py tools/validate_h2_leak_hazard_planes.py tools/validate_h2_leak_hazard_timeseries.py tools/validate_h2_leak_plume_history.py tools/validate_h2_leak_plume_profile.py`
- `bash -n tools/codex_smoke_engineering_h2_leak_open_domain_amr_compare.sh`
- `bash -n tools/codex_smoke_engineering_h2_leak_tank_farm_amr_compare.sh`
- `python3 tools/test_amrex_reader_multibox.py`: PASS.
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=947`.
- `ctest --test-dir build-codex-smoke --output-on-failure`: 22/22 PASS.

## Remaining Engineering Gaps

- Dynamic/flow-gradient AMR tagging efficiency and refinement-benefit studies.
- Production-size MPI/GPU scaling and memory-pressure campaigns.
- Real CAD/large-layout tank-farm AMR campaigns.
- Long-time stability and larger hazardous-release runs.
- ABL/calm-wind/terrain/boundary-condition validation, fire/heat-release metrics, and reference-data validation.
