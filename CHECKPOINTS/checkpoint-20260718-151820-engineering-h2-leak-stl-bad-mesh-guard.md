# Engineering H2 Leak STL Bad-Mesh Guard Checkpoint

Date: 2026-07-18

## Scope

This checkpoint strengthens the engineering-priority H2 leak STL/CAD ingestion path. The single-file AMReX STL path now performs the same triangle-level preflight used by the multi-file merge path, so degenerate STL triangles are rejected with an explicit `buildFromSTL` diagnostic before AMReX EB2 construction and before plotfile output.

## Code Changes

- Updated `src/geometry/eb2_factory.cpp`:
  - `STLBounds` now records `triangles` as well as vertices and format.
  - `readSTLBounds()` now calls `readSTLTriangles()` so single-file STL input is checked for non-finite and degenerate triangles before `amrex::EB2::IndexSpaceSTL` construction.
  - The `buildFromSTL QA` log now reports `triangles=...` for machine-readable CAD/STL QA evidence.
- Added `tools/codex_smoke_engineering_h2_leak_stl_bad_mesh_guard.sh`:
  - builds the H2 leak EB executable;
  - creates a deliberately degenerate ASCII STL triangle;
  - rewrites the maintained STL obstacle input to use that file;
  - verifies the run fails clearly and does not write a plotfile.

## Evidence

- `CODEX_H2_LEAK_STL_BAD_MESH_LOG_DIR=/tmp/codex_h2_leak_stl_bad_mesh_guard_20260718 RUN_TIMEOUT=120 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_stl_bad_mesh_guard.sh` PASS.
- Bad-mesh log: `/tmp/codex_h2_leak_stl_bad_mesh_guard_20260718/run.log`.
- The bad-mesh log contains the explicit diagnostic `buildFromSTL: encountered degenerate STL triangle in 'codex_degenerate_triangle.stl'` and contains no `Writing plotfile` marker.
- Normal STL regression: `CODEX_H2_LEAK_STL_LOG_DIR=/tmp/codex_h2_leak_stl_obstacle_post_bad_mesh_20260718 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh` PASS.
- Normal STL summary: `/tmp/codex_h2_leak_stl_obstacle_post_bad_mesh_20260718/stl_obstacle_summary.csv` with `mass_ratio=1.00108533e+00`, `cloud_volume=2.14843750e-02`, `active_planes=5`, `flammable_planes=2`, and `max_X=1.80968056e-01`.
- Normal STL run log reports `triangles=12` in the `buildFromSTL QA` line.
- Log hygiene grep over bad-mesh and normal STL logs found no hidden `Unused ParmParse Variables`, `RuntimeWarning`, `nan`, `inf`, or wrapper `FAIL` markers.
- `bash -n tools/codex_smoke_engineering_h2_leak_stl_bad_mesh_guard.sh` PASS.
- `python3 tools/check_machine_local_paths.py --strict` PASS with `scanned_files=943`.
- `ctest --test-dir build-codex-smoke --output-on-failure` PASS: `22/22` tests.

## Documentation Updated

- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` now lists the degenerate-triangle STL bad-mesh guard in the engineering readiness verdict, EB/geometry row, STL evidence row, and next-slice residual-risk wording.
- `docs/codex_audit/SMOKE_MATRIX.md` now lists the new bad-mesh guard wrapper, triangle-count QA, the expected-fail evidence, and the post-change normal STL regression evidence.

## Production Readiness Impact

Engineering scenario readiness moves from about 80% to about 81% for the prioritized gas-release/fire/detonation-risk workflow. This closes a concrete CAD/STL reliability gap: malformed degenerate triangles are now caught before AMReX EB2 construction in the maintained single-file STL path.

## Residual Risks

- Still smoke-scale synthetic cube STL geometry, not real plant CAD.
- Still lacks broader bad-mesh classification for nonmanifold surfaces, wrong normals, self-intersections, tiny sliver triangles, duplicate facets, and unit/scale mistakes.
- Still lacks per-file STL transforms/scale/center for multi-body industrial layouts.
- Still lacks production-size multi-layout tank-farm/STL/CAD dispersion campaigns and long-time stability evidence.
- Fire/thermal-radiation/heat-release production reporting remains incomplete.
