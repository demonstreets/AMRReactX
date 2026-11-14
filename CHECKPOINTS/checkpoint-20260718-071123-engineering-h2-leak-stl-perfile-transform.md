# Checkpoint: engineering H2 leak STL per-file transforms

Date: 2026-07-18 UTC

## Slice completed

Engineering priority slice for industrial H2 leak / tank-farm geometry workflows: optional per-file STL scale/center transforms for multi-body CAD layouts.

## Code changes

- `src/geometry/eb2_factory.H`
  - Added `pele::buildFromSTLFilesWithTransforms(...)` declaration.
- `src/geometry/eb2_factory.cpp`
  - Extended the internal binary STL merger to apply one scale/center transform per source STL before writing the merged asset.
  - Added finite/positive scale and finite center validation.
  - Preserved legacy `buildFromSTLFiles(...)` behavior for shared global STL transform inputs.
  - Added log markers for transformed multi-file STL merges.
- `examples/engineering/h2_leak_3d/pelelmex_prob.cpp`
  - Added optional `prob.obstacle_stl_scales`, `prob.obstacle_stl_xcs`, `prob.obstacle_stl_ycs`, and `prob.obstacle_stl_zcs` arrays.
  - Requires all four arrays to match `prob.obstacle_stl_files` count when any per-file transform array is present.
  - Keeps old single/global STL transform path unchanged when the new arrays are absent.
- `tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh`
  - Accepts both legacy `buildFromSTLFiles` and new `buildFromSTLFilesWithTransforms` merge log markers.
  - Records raw and scaled STL bounds in `stl_obstacle_summary.csv`.
- `tools/codex_smoke_engineering_h2_leak_stl_perfile_transform.sh`
  - New maintained smoke that places two copies of `cube_obstacle_binary.stl` at different scales/centers and validates merged STL bounds plus H2 plume/hazard metrics.
- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md`
  - Updated evidence matrix and residual limitations.

## Evidence

- New per-file transform gate:
  - Command: `CODEX_H2_LEAK_STL_PERFILE_LOG_DIR=/tmp/codex_h2_leak_stl_perfile_transform_20260718 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_stl_perfile_transform.sh`
  - PASS summary: `/tmp/codex_h2_leak_stl_perfile_transform_20260718/stl_obstacle_summary.csv`
  - Key values: `stl_vertices=72`, `raw_bounds_lo=0.8500000238,0.3000000119,0.400000006`, `raw_bounds_hi=1.379999995,0.7300000191,0.6000000238`, matching scaled bounds, `mass_ratio=1.00166748e+00`, `cloud_volume=2.19726562e-02`, `active_planes=5`, `flammable_planes=2`.
- Legacy multi-file regression:
  - Command: `CODEX_H2_LEAK_STL_MULTIFILE_LOG_DIR=/tmp/codex_h2_leak_stl_multifile_post_perfile_20260718 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_stl_multifile_obstacle.sh`
  - PASS summary: `/tmp/codex_h2_leak_stl_multifile_post_perfile_20260718/stl_obstacle_summary.csv`
- Global light checks:
  - `python3 tools/check_machine_local_paths.py --strict` PASS, `scanned_files=944`.
  - `ctest --test-dir build-codex-smoke --output-on-failure` PASS, 22/22 tests.
  - PASS run logs checked for `Unused ParmParse Variables`, `RuntimeWarning`, `nan`, `inf`, and `FAIL`; no unexpected matches.

## Current engineering readiness estimate

Approximately 82% for the engineering-priority track.

This bump is intentionally small because the new evidence is still smoke-scale, but it removes a real industrial-CAD workflow gap: multi-body STL layouts can now carry per-body scale/center transforms instead of forcing one global transform for all source files.

## Remaining engineering risks

- Still lacks reference-quality validation for large-scale tank/pipeline dispersion, fire, and detonation consequences.
- Real-gas support remains configurable-Z smoke coverage, not full EOS/thermal cooldown/two-phase flashing.
- Pipe/valve/network dynamics remain lumped/steady or scheduled smoke coverage, not distributed pressure-wave validation.
- STL/CAD coverage still uses synthetic cube assets; broader real-CAD cleanup, nonmanifold/wrong-normal quality classification, and larger multi-layout campaigns remain open.
- Long-time stability, production mesh/MPI/AMR campaigns, terrain/ABL/inlet sensitivity, and fire/ignition coupling remain open.
