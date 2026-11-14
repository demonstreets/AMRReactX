# Checkpoint: Engineering H2 Leak Binary STL Smoke

Date: 2026-07-17

## Goal Slice

Extend the engineering H2 leak STL/CAD path from ASCII-only solver evidence to an actual binary STL solver run. This matters for production use because CAD/meshing tools commonly export binary STL, and the maintained H2 leak workflow must prove that AMReX EB2 can load the binary asset, not merely that repository-level parsers can inspect it.

## Code And Input Changes

- `examples/engineering/h2_leak_3d/cube_obstacle_binary.stl`
  - New binary STL cube generated from the maintained ASCII `cube_obstacle.stl` geometry.
  - Contains 12 triangles and 36 vertices; file size is 684 bytes (`84 + 12*50`).
- `examples/engineering/h2_leak_3d/input.codex_stl_binary_obstacle_smoke`
  - New H2 leak input matching the ASCII STL smoke but using `prob.obstacle_stl_file = cube_obstacle_binary.stl`.
- `tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh`
  - Parameterized summary parsing to use the actual `CODEX_H2_LEAK_PROFILE_INPUT` basename, so the same validation chain can support ASCII, binary, and future STL inputs.
- `tools/codex_smoke_engineering_h2_leak_stl_binary_obstacle.sh`
  - New binary STL wrapper that runs the existing STL obstacle chain and additionally requires `stl_format=binary`, `stl_vertices=36`, expected scaled bounds, and a binary `buildFromSTL QA` log line.
- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
  - Updated EB/geometry readiness evidence for ASCII/binary STL H2 leak smokes.
- `docs/codex_audit/SMOKE_MATRIX.md`
  - Added binary STL wrapper and evidence to the H2 engineering smoke matrix.

## Verification Evidence

Binary STL H2 leak smoke:

```bash
CODEX_H2_LEAK_STL_BINARY_LOG_DIR=/tmp/codex_h2_leak_stl_binary_obstacle_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_stl_binary_obstacle.sh
```

Result:

```text
h2_leak_stl_binary_obstacle PASS output=/tmp/codex_h2_leak_stl_binary_obstacle_20260717/stl_obstacle_summary.csv mass_ratio=1.00108533e+00 cloud_volume=2.14843750e-02 active_planes=5 flammable_planes=2 max_X=1.80968056e-01
```

Binary STL QA evidence:

```text
buildFromSTL QA: file=cube_obstacle_binary.stl, format=binary, vertices=36, raw_bounds=([-1,-1,-1],[1,1,1]), scaled_bounds=([0.9,0.4,0.4],[1.1,0.6,0.6])
```

Summary row:

```text
case=input.codex_stl_binary_obstacle_smoke
stl_file=cube_obstacle_binary.stl
stl_format=binary
stl_vertices=36
scaled_bounds_lo=0.9,0.4,0.4
scaled_bounds_hi=1.1,0.6,0.6
mass_ratio=1.00108533e+00
cloud_volume=2.14843750e-02
active_planes=5
flammable_planes=2
plotfiles=7
```

ASCII STL regression after parameterizing the wrapper:

```bash
CODEX_H2_LEAK_STL_LOG_DIR=/tmp/codex_h2_leak_stl_ascii_post_binary_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh
```

Result:

```text
h2_leak_stl_obstacle PASS output=/tmp/codex_h2_leak_stl_ascii_post_binary_20260717/stl_obstacle_summary.csv mass_ratio=1.00108533e+00 cloud_volume=2.14843750e-02 active_planes=5 flammable_planes=2 max_X=1.80968056e-01
```

STL geometry guard regression:

```bash
CODEX_H2_LEAK_STL_GUARD_LOG_DIR=/tmp/codex_h2_leak_stl_geometry_guard_post_binary_20260717 RUN_TIMEOUT=120 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_stl_geometry_guard.sh
```

Result:

```text
[codex-smoke] PASS h2_leak STL geometry guard log_dir=/tmp/codex_h2_leak_stl_geometry_guard_post_binary_20260717 rc=1
```

Tank-farm regression:

```bash
CODEX_H2_LEAK_TANK_FARM_LOG_DIR=/tmp/codex_h2_leak_tank_farm_post_binary_stl_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_tank_farm.sh
```

Result:

```text
h2_leak_tank_farm PASS output=/tmp/codex_h2_leak_tank_farm_post_binary_stl_20260717/tank_farm_summary.csv mass_ratio=1.00148922e+00 cloud_volume=2.14843750e-02 active_planes=5 flammable_planes=2 max_X=1.82368348e-01
```

Static checks:

```text
bash -n tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh tools/codex_smoke_engineering_h2_leak_stl_binary_obstacle.sh tools/codex_smoke_engineering_h2_leak_stl_geometry_guard.sh tools/codex_smoke_engineering_h2_leak_tank_farm.sh -> zero-byte log at /tmp/codex_h2_stl_binary_bashn_20260717.log
machine_local_paths PASS scanned_files=926
preflight SUMMARY PASS warnings=3
PASS_NO_WARNINGS_TEXT for unused ParmParse variables and RuntimeWarning scan across binary, ASCII, guard, and tank-farm run directories
```

## Remaining Risk

This proves that the maintained H2 leak workflow can run both ASCII and binary STL assets through AMReX EB2 with QA bounds reporting. It is still a tiny cube on a coarse single-box mesh. It does not yet prove messy CAD cleanup, multiple independent STL assets, bad normals, nonmanifold/degenerate triangles, wall/turbulence fidelity, fire coupling, long-time stability, multi-box plotfile reading, or production-scale dispersion accuracy.

## Recommended Next Slice

Continue engineering-first work with a multi-obstacle STL/CAD layout: at least two independently positioned imported STL obstacles or a stronger tank-farm-like geometry, plus geometry QA checks, source-pressure/orifice variants, and longer reduced stability runs.
