# Engineering H2 Leak Low-Wind Checkpoint

Date: 2026-07-18

## Scope

This checkpoint advances the engineering-priority H2 leak workflow with a low ambient-wind open-domain response gate. The new gate compares the maintained open-domain baseline against a weak-wind case while preserving the fixed source jet speed, so it verifies ambient-advection sensitivity rather than changing the injected momentum source together with the wind.

## Code Changes

- Added `tools/codex_smoke_engineering_h2_leak_open_domain_low_wind.sh`.
- The script derives temporary inputs from `examples/engineering/h2_leak_3d/input.codex_open_domain_flammable_smoke` and modifies only `prob.wind_u`.
- Baseline case: `wind_u=2.0`, `prob.leak_vel_x=2.0`.
- Low-wind case: `wind_u=0.5`, `prob.leak_vel_x=2.0`.
- The acceptance checks require:
  - mass/profile/hazard summary/plane/time-series chain PASS for both cases;
  - reduced low-wind advection/source-region retention relative to baseline;
  - finite downstream hazard resolution;
  - nonzero bounded flammable cloud in both cases;
  - adequate outlet margin so the weak-wind smoke cloud is not clipped.

## Evidence

- `CODEX_H2_LEAK_LOW_WIND_LOG_DIR=/tmp/codex_h2_leak_open_domain_low_wind_20260718 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_open_domain_low_wind.sh` PASS.
- Summary CSV: `/tmp/codex_h2_leak_open_domain_low_wind_20260718/low_wind_summary.csv`.
- PASS metrics:
  - `baseline_shift=1.01245408e-01`
  - `low_shift=2.65765289e-02`
  - `baseline_downstream=8.49997579e-01`
  - `low_downstream=6.15805511e-01`
  - `baseline_cloud=2.14843750e-02`
  - `low_cloud=1.75781250e-02`
  - `low_margin=1.47342347e+00`
- Low-wind profile log reports `mass_ratio=1.00000000e+00`, `centroid=(5.26576529e-01,5.00000000e-01,5.00000000e-01)`, `centroid_shift=2.65765289e-02`, and `downstream_fraction=6.15805511e-01`.
- Low-wind hazard summary reports `cloud_cells=72`, `cloud_volume=1.75781250e-02`, `cloud_species_mass=1.89691468e-04`, and `total_species_mass=2.00000000e-04`.
- Log hygiene grep over baseline/low_wind logs found no `Unused ParmParse Variables`, `RuntimeWarning`, `nan`, `inf`, or `FAIL` matches.
- `bash -n tools/codex_smoke_engineering_h2_leak_open_domain_low_wind.sh` PASS.
- `python3 tools/check_machine_local_paths.py --strict` PASS with `scanned_files=942`.
- `ctest --test-dir build-codex-smoke --output-on-failure` PASS: `22/22` tests.

## Documentation Updated

- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` now lists the low ambient-wind/source-region-retention gate in the engineering readiness verdict, gas-dispersion gate table, hazard-output gate table, and evidence table.
- `docs/codex_audit/SMOKE_MATRIX.md` now lists the new wrapper and its PASS evidence.
- Remaining low-wind language was narrowed to calm-wind/ABL/inlet/terrain sensitivity, since this checkpoint covers only a two-point uniform weak-wind smoke.

## Production Readiness Impact

Engineering scenario readiness moves from about 79% to about 80% for the currently prioritized gas-release/fire/detonation-risk workflow. The new slice closes one important gap: weak ambient wind no longer relies only on a streamwise sensitivity case that changed wind and source velocity together.

## Residual Risks

- Still smoke-scale, not production-scale mesh/domain/time horizon.
- Still uniform wind, not calm wind, atmospheric boundary layer, terrain-following inflow, transient meteorology, or obstacle-interaction validation under weak wind.
- Still lacks full reference-quality plume validation against experimental/literature data.
- Still lacks production CAD/STL cleanup workflows, bad-mesh quality reporting, larger multi-layout tank-farm campaigns, and long-time stability evidence.
- Fire/thermal-radiation/heat-release production reporting remains incomplete.
