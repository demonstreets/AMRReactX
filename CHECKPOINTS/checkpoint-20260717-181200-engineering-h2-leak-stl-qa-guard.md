# Checkpoint: Engineering H2 Leak STL QA And Geometry Guard

Date: 2026-07-17

## Goal Slice

Advance the engineering H2 leak STL/CAD path from a single positive STL smoke to a more production-diagnostic geometry path. The code now performs pre-build STL checks before handing geometry to AMReX EB2, reports STL format/vertex count/raw and scaled bounds, and has an expected-fail guard for an STL placed outside the computational domain.

## Code Changes

- `src/geometry/eb2_factory.cpp`
  - Added ASCII and binary STL bounds scanning before `amrex::EB2::IndexSpaceSTL` construction.
  - Rejects missing/empty STL files, malformed/truncated STL data, non-finite vertices, non-positive `stl_scale`, non-finite `stl_center`, negative `ngrow`, and scaled STL bounds that do not intersect the AMReX domain.
  - Logs `buildFromSTL QA` with `format`, `vertices`, `raw_bounds`, and `scaled_bounds`.
- `tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh`
  - Now requires `buildFromSTL QA` in the run log and writes `stl_format`, `stl_vertices`, `scaled_bounds_lo`, and `scaled_bounds_hi` to `stl_obstacle_summary.csv`.
- `tools/codex_smoke_engineering_h2_leak_stl_geometry_guard.sh`
  - New expected-fail guard. It shifts the STL cube outside the domain and requires the run to abort with explicit scaled bounds and domain bounds.
- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
  - Updated EB/geometry status and STL evidence row with QA and guard evidence.
- `docs/codex_audit/SMOKE_MATRIX.md`
  - Added the STL geometry guard to the H2 leak smoke matrix and remaining-gap narrative.

## Verification Evidence

Positive STL obstacle smoke:

```bash
CODEX_H2_LEAK_STL_LOG_DIR=/tmp/codex_h2_leak_stl_qa_clean_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh
```

Result:

```text
h2_leak_stl_obstacle PASS output=/tmp/codex_h2_leak_stl_qa_clean_20260717/stl_obstacle_summary.csv mass_ratio=1.00108533e+00 cloud_volume=2.14843750e-02 active_planes=5 flammable_planes=2 max_X=1.80968056e-01
```

QA log evidence:

```text
buildFromSTL QA: file=cube_obstacle.stl, format=ascii, vertices=36, raw_bounds=([-1,-1,-1],[1,1,1]), scaled_bounds=([0.9,0.4,0.4],[1.1,0.6,0.6])
buildFromSTL: built AMReX EB2 IndexSpace from cube_obstacle.stl
```

Summary CSV fields now include:

```text
stl_format=ascii
stl_vertices=36
scaled_bounds_lo=0.9,0.4,0.4
scaled_bounds_hi=1.1,0.6,0.6
```

Expected-fail STL geometry guard:

```bash
CODEX_H2_LEAK_STL_GUARD_LOG_DIR=/tmp/codex_h2_leak_stl_geometry_guard_20260717 RUN_TIMEOUT=120 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_stl_geometry_guard.sh
```

Result:

```text
[codex-smoke] PASS h2_leak STL geometry guard log_dir=/tmp/codex_h2_leak_stl_geometry_guard_20260717 rc=1
```

Guard diagnostic:

```text
amrex::Abort::0::buildFromSTL: scaled STL bounds do not intersect the computational domain: bounds=[(8.9,0.4,0.4),(9.1,0.6,0.6)] domain=[(0,0,0),(2,1,1)] !!!
```

Tank-farm regression:

```bash
CODEX_H2_LEAK_TANK_FARM_LOG_DIR=/tmp/codex_h2_leak_tank_farm_post_stl_qa_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_tank_farm.sh
```

Result:

```text
h2_leak_tank_farm PASS output=/tmp/codex_h2_leak_tank_farm_post_stl_qa_20260717/tank_farm_summary.csv mass_ratio=1.00148922e+00 cloud_volume=2.14843750e-02 active_planes=5 flammable_planes=2 max_X=1.82368348e-01
```

Static checks:

```text
bash -n ... PASS, zero-byte log at /tmp/codex_h2_stl_qa_final_bashn_20260717.log
machine_local_paths PASS scanned_files=924
preflight SUMMARY PASS warnings=3
PASS_NO_WARNINGS_TEXT for unused ParmParse variables and RuntimeWarning scan
```

## Remaining Risk

This is still smoke-scale geometry coverage. It improves diagnosability for STL import and catches one serious operator error, but it does not yet prove real CAD cleanup, binary STL coverage in the H2 run, bad-normal sensitivity, multi-STL industrial layouts, wall/turbulence fidelity, fire coupling, long-time stability, or production-scale dispersion accuracy.

## Recommended Next Slice

Continue engineering-first work by adding a broader industrial geometry campaign: binary STL guard, multiple imported obstacles/tank layouts, source-pressure/orifice variants, longer reduced runs, and eventually fire/heat-release outputs with documented reference comparisons.
