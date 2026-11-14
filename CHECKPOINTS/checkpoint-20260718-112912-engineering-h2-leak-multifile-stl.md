# Checkpoint: engineering H2 leak multi-file STL support

Date: 2026-07-18
Scope: engineering-priority H2 leak/tank-farm geometry path.

## What changed

- Added true multi-file STL support through `prob.obstacle_stl_files` in `examples/engineering/h2_leak_3d/pelelmex_prob.cpp`.
- Added `pele::buildFromSTLFiles(...)` in `src/geometry/eb2_factory.cpp/.H`. Multi-file inputs are read as ASCII or binary STL, validated for finite/nondegenerate triangles during merge, written as a merged binary STL, and then passed through the existing AMReX EB2 STL path.
- Preserved existing `prob.obstacle_stl_file` single-file behavior.
- Added two single-cube binary STL assets, `input.codex_stl_multifile_obstacle_smoke`, and `tools/codex_smoke_engineering_h2_leak_stl_multifile_obstacle.sh`.
- Generalized `tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh` so one wrapper handles single-file and multi-file STL smoke inputs and records `stl_source_files` in the summary CSV.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` so multi-file STL is no longer listed as missing.

## Verification evidence

- Multi-file STL smoke passed: `/tmp/codex_h2_leak_stl_multifile_obstacle_20260718/stl_obstacle_summary.csv`.
  - `stl_source_files=multi_cube_obstacle_a_binary.stl;multi_cube_obstacle_b_binary.stl`
  - `stl_file=codex_merged_two_cube_obstacles.stl`
  - `stl_format=binary`, `stl_vertices=72`
  - `scaled_bounds_lo=0.8999999762,0.2800000012,0.400000006`
  - `scaled_bounds_hi=1.379999995,0.7200000286,0.6000000238`
  - `mass_ratio=1.00049213e+00`, `cloud_volume=2.14843750e-02`, `max_X=1.80950384e-01`, `active_planes=5`, `flammable_planes=2`
- Multi-file run log confirmed `H2 leak UserDefined EB STL files: count=2`, `buildFromSTLFiles: merging 2 STL files into codex_merged_two_cube_obstacles.stl`, both source filenames, and `buildFromSTL QA: file=codex_merged_two_cube_obstacles.stl, format=binary, vertices=72`.
- Single-file binary STL regression passed: `/tmp/codex_h2_leak_stl_binary_post_multifile_20260718/stl_obstacle_summary.csv`.
- Single-file composite/two-body STL regression passed: `/tmp/codex_h2_leak_stl_composite_post_multifile_20260718/stl_obstacle_summary.csv`.
- Expected-fail outside-domain STL guard passed: `/tmp/codex_h2_leak_stl_geometry_guard_post_multifile_20260718/run.log`.
- Tank-farm EB union regression passed: `/tmp/codex_h2_leak_tank_farm_post_multifile_stl_20260718/tank_farm_summary.csv`.
- Script syntax check passed with empty `/tmp/codex_h2_stl_multifile_bashn_20260718.log`.
- Machine-local path audit passed: `/tmp/codex_h2_stl_multifile_path_audit_20260718.log` reports `machine_local_paths PASS scanned_files=928`.
- Environment preflight passed: `/tmp/codex_h2_stl_multifile_preflight_20260718.log` reports `preflight SUMMARY PASS warnings=3`; the warnings are optional SUNDIALS CUDA library warnings.
- New run logs contain no `Unused ParmParse Variables` or `RuntimeWarning` markers.

## Current engineering readiness impact

This closes the previous immediate imported-geometry gap for synthetic multi-body STL layouts: single ASCII STL, single binary STL, composite/two-body binary STL, and true multi-file STL inputs now all have maintained H2 leak smoke evidence. The code is still not production-grade for industrial leakage/fire studies because the evidence remains smoke-scale and synthetic.

## Remaining risks

- Real CAD/STL cleanup and geometry quality reports are still missing.
- Per-file STL transforms/scale/center are not implemented; the current multi-file path uses one shared transform after merge.
- The multi-file merge path rejects degenerate triangles, but single-file STL still relies mostly on AMReX STL handling plus bounds QA.
- Nonmanifold meshes, wrong normals, tiny slivers, self-intersections, and unit-system mistakes need stronger guards.
- Wall/turbulence validation, terrain/inlet sensitivity, fire/heat-release coupling, long-time stability, MPI/GPU scaling, and production-size hazard campaigns remain open.

## Recommended next slice

Prioritize one of these engineering-production items next:

1. Real CAD quality gate: STL quality report, bad-mesh guards, optional per-file transforms, and a dirty/invalid STL expected-fail suite.
2. Source physics: tank pressure/orifice/choked-flow leak model with mass-flow regression and open-domain plume/hazard response.
3. Boundary realism: crosswind/low-wind/open-terrain variants plus longer reduced stability runs.
