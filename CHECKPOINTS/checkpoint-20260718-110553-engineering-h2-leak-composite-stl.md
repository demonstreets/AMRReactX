# Checkpoint: engineering H2 leak composite STL obstacle

Date: 2026-07-18 11:05 local server time
Scope: engineering-first H2 leak dispersion path, STL EB obstacle import robustness
Status: incremental progress; overall project remains NOT PRODUCTION READY

## What changed

- Added `examples/engineering/h2_leak_3d/composite_two_cube_obstacles_binary.stl`.
  - Binary STL containing two independent cube bodies.
  - 24 triangles, 72 vertices.
  - Expected bounds with scale 1 and zero center shift: lo `(0.9,0.28,0.4)`, hi `(1.38,0.72,0.6)`.
- Added `examples/engineering/h2_leak_3d/input.codex_stl_composite_obstacle_smoke`.
  - Uses `prob.obstacle_geometry = stl`.
  - Uses the composite/two-body binary STL asset.
  - Keeps legacy `prob.obstacle_xc/yc/zc` placeholders because existing problem setup still queries them before the STL branch.
- Added `tools/codex_smoke_engineering_h2_leak_stl_composite_obstacle.sh`.
  - Reuses the generic STL H2 leak wrapper.
  - Requires `CODEX_H2_LEAK_HISTORY_EXTRA_FILES=composite_two_cube_obstacles_binary.stl`.
  - Checks summary fields for `stl_file`, `stl_format=binary`, `stl_vertices=72`, STL scaled bounds, nonzero flammable cloud, and `buildFromSTL QA` log output.
- Updated audit evidence:
  - `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
  - `docs/codex_audit/SMOKE_MATRIX.md`

## Verification evidence

- Syntax checks:
  - `bash -n tools/codex_smoke_engineering_h2_leak_stl_composite_obstacle.sh tools/codex_smoke_engineering_h2_leak_stl_binary_obstacle.sh tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh tools/codex_smoke_engineering_h2_leak_stl_geometry_guard.sh tools/codex_smoke_engineering_h2_leak_tank_farm.sh`
  - Evidence: `/tmp/codex_h2_stl_composite_bashn_20260717.log`, size 0 bytes.
- Composite/two-body STL smoke:
  - Command: `CODEX_H2_LEAK_STL_COMPOSITE_LOG_DIR=/tmp/codex_h2_leak_stl_composite_obstacle_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_stl_composite_obstacle.sh`
  - Evidence: `/tmp/codex_h2_leak_stl_composite_obstacle_20260717/stl_obstacle_summary.csv`
  - Result: PASS.
  - Metrics: `stl_file=composite_two_cube_obstacles_binary.stl`, `stl_format=binary`, `stl_vertices=72`, `scaled_bounds_lo=0.8999999762,0.2800000012,0.400000006`, `scaled_bounds_hi=1.379999995,0.7200000286,0.6000000238`, `mass_ratio=1.00049213e+00`, `cloud_volume=2.14843750e-02`, `max_X=1.80950384e-01`, `active_planes=5`, `flammable_planes=2`.
  - Log QA: `buildFromSTL QA: file=composite_two_cube_obstacles_binary.stl, format=binary, vertices=72`.
- Binary single-STL regression after composite:
  - Command: `CODEX_H2_LEAK_STL_BINARY_LOG_DIR=/tmp/codex_h2_leak_stl_binary_post_composite_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_stl_binary_obstacle.sh`
  - Evidence: `/tmp/codex_h2_leak_stl_binary_post_composite_20260717/stl_obstacle_summary.csv`
  - Result: PASS.
  - Metrics: `stl_format=binary`, `stl_vertices=36`, `mass_ratio=1.00108533e+00`, `cloud_volume=2.14843750e-02`, `max_X=1.80968056e-01`, `active_planes=5`, `flammable_planes=2`.
- STL outside-domain geometry guard after composite:
  - Command: `CODEX_H2_LEAK_STL_GUARD_LOG_DIR=/tmp/codex_h2_leak_stl_geometry_guard_post_composite_20260717 RUN_TIMEOUT=120 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_stl_geometry_guard.sh`
  - Evidence: `/tmp/codex_h2_leak_stl_geometry_guard_post_composite_20260717/run.log`
  - Result: PASS expected failure with return code 1 and explicit STL/domain bounds diagnostics.
- Tank-farm EB union regression after composite:
  - Command: `CODEX_H2_LEAK_TANK_FARM_LOG_DIR=/tmp/codex_h2_leak_tank_farm_post_composite_stl_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_tank_farm.sh`
  - Evidence: `/tmp/codex_h2_leak_tank_farm_post_composite_stl_20260717/tank_farm_summary.csv`
  - Result: PASS.
  - Metrics: `obstacle_count=3`, `mass_ratio=1.00148922e+00`, `cloud_volume=2.14843750e-02`, `max_X=1.82368348e-01`, `active_planes=5`, `flammable_planes=2`.
- Path/preflight/log hygiene:
  - `python3 tools/check_machine_local_paths.py --strict` PASS, `scanned_files=927`; evidence `/tmp/codex_h2_stl_composite_path_audit_20260717.log`.
  - `SUNDIALS_DIR=/home/cj/my-pele/external/PelePhysics/ThirdParty/INSTALL/gnu bash tools/codex_preflight_environment.sh` PASS with 3 optional SUNDIALS CUDA-library warnings; evidence `/tmp/codex_h2_stl_composite_preflight_20260717.log`.
  - Grep over composite/binary/guard/tank-farm logs found no `Unused ParmParse Variables` or `RuntimeWarning`.

## Remaining risks

- This is still smoke-scale, coarse single-box evidence; it is not production-scale dispersion validation.
- Composite STL support here means multiple independent bodies in one STL file. It does not yet prove multi-file STL union support.
- Real CAD cleanup remains open: nonmanifold facets, degenerate triangles, inverted/wrong normals, tiny sliver triangles, disconnected junk components, and unit/scale mistakes need stronger QA and acceptance tests.
- Engineering production still lacks tank-pressure/orifice discharge models, wall/turbulence validation, crosswind/calm-wind campaigns, fire/heat-release consequence metrics, long-duration stability, and reference/experimental validation.

## Recommended next slice

Highest value next: turn STL geometry import into a more production-like CAD gate. Add either multi-file STL union support or a real-CAD-quality QA harness that rejects degenerate/nonfinite/nonmanifold/wrong-scale layouts before AMReX EB build, then run the H2 flammable-cloud chain plus tank-farm regression.
