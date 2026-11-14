# Checkpoint: engineering H2 leak open-domain AMR comparison

Date: 2026-07-18 07:34 UTC

## Scope

Priority remains engineering production readiness. This checkpoint closes the first maintained H2 leak AMR-vs-uniform comparison slice for the open-domain flammable-cloud workflow.

## Changes

- Added `tools/codex_smoke_engineering_h2_leak_open_domain_amr_compare.sh`, deriving a Level 0 baseline and a static Level 1 near-leak AMR case from the maintained open-domain H2 leak input.
- Extended `tools/amrex_reader.py` to read AMR plotfiles by overlaying Level 0..N data onto a finest-resolution composite grid before exposing the usual `fields`, `x/y/z`, `dx`, and `grid` objects to validators.
- Added `finest_level` metadata to the plotfile reader result.
- Updated `tools/validate_h2_leak_plume_history.py` and `tools/validate_h2_leak_plume_profile.py` to de-duplicate repeated AMR source-interval log lines with identical `(step,time,dt,model,mdot,injected)` keys. This prevents multi-level AMR logging from double-counting the physical injected mass.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` with the new evidence and remaining AMR limitations.

## Evidence

- `CODEX_H2_LEAK_AMR_COMPARE_LOG_DIR=/tmp/codex_h2_leak_open_domain_amr_compare_20260718_final RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_open_domain_amr_compare.sh`
  - PASS summary: `/tmp/codex_h2_leak_open_domain_amr_compare_20260718_final/amr_compare_summary.csv`
  - `amr_finest_level=1`
  - `amr_finest_fabs=2`
  - `cloud_rel_diff=7.85340319e-02`
  - `peak_rel_diff=4.90278862e-02`
  - `centroid_abs_diff=3.40203000e-04`
  - `downstream_abs_diff=5.49446000e-03`
- AMR history validation PASS: `mass_ratioN=1.00000276e+00`, `mass_growth_ratio=5.00001294e+00`.
- AMR profile validation PASS: `mass_ratio=1.00000276e+00`, `centroid_shift=1.01585611e-01`, `y_l1=z_l1=1.64800720e-01`.
- AMR hazard summary/planes/timeseries PASS: final cloud volume `2.33154297e-02`, `cloud_species_mass=1.85214929e-04`, `max_X=1.53566370e-01`, active planes `8`, flammable planes `4`.
- Log hygiene grep over the final AMR compare log root found no `FAIL`, `Traceback`, `Unused ParmParse`, `nan`, `abort`, or `error` markers.

## Regression

- `python3 tools/test_amrex_reader_multibox.py` PASS: `amrex_reader_multibox_smoke PASS dims=2,3 gap_guard=1 overlap_guard=1`.
- `python3 tools/check_machine_local_paths.py --strict` PASS: `machine_local_paths PASS scanned_files=945`.
- `ctest --test-dir build-codex-smoke --output-on-failure` PASS: 22/22 tests.

## Remaining Limitations

- This is still a smoke-scale AMR comparison with a static near-leak refinement box, not a production AMR efficiency/overhead study.
- Obstacle/tank-farm AMR, dynamic tagging strategies, long-time AMR stability, production-size MPI, and reference-data dispersion accuracy remain open.
- Engineering readiness estimate after this slice: about 84%. The increase is modest in percent, but the risk reduction is meaningful because AMR post-processing now preserves species mass and hazard metrics instead of silently reading Level 0 only.
