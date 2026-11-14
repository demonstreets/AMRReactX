# Checkpoint: engineering H2 leak STL obstacle smoke

Date: 2026-07-17 17:10:37 CST
Scope: engineering-first gas-phase H2 leak dispersion path for imported geometry support.

## Intent

Advance the H2 engineering leak workflow from analytic cylinder obstacles to an imported STL obstacle coupled through AMReX EB2. This is the first maintained H2 leak smoke where an STL asset is copied into the run directory, loaded by `pele::buildFromSTL()`, and then used in the same flammable-cloud diagnostics as the open-domain, cylinder, and compact tank-farm cases.

## Code changes in this slice

- `examples/engineering/h2_leak_3d/GNUmakefile`
  - Added `src/geometry` include/VPATH support.
  - Added `eb2_factory.cpp` to `CEXE_sources` so the PeleLMeX H2 executable can call `pele::buildFromSTL()`.
- `examples/engineering/h2_leak_3d/pelelmex_prob.cpp`
  - Added `eb2_factory.H` include.
  - Added `prob.obstacle_geometry = stl` branch in `EBUserDefined()`.
  - Added STL parameters: `obstacle_stl_file`, `obstacle_stl_scale`, `obstacle_stl_xc`, `obstacle_stl_yc`, `obstacle_stl_zc`, `obstacle_stl_reverse_normal`, and `obstacle_stl_ngrow`.
  - Kept the existing cylinder/cylinder-union path unchanged for `cylinder`/`cylinders`.
- `tools/codex_smoke_engineering_h2_leak_plume_history.sh`
  - Added optional `CODEX_H2_LEAK_HISTORY_EXTRA_FILES` support to copy extra case assets into the clean run directory.
- `examples/engineering/h2_leak_3d/cube_obstacle.stl`
  - Added a local STL asset derived from AMReX's MarchingCubes cube for reproducible H2 STL smoke input.
- `examples/engineering/h2_leak_3d/input.codex_stl_obstacle_smoke`
  - New H2 leak input using `prob.obstacle_geometry = stl` and `cube_obstacle.stl`.
- `tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh`
  - New wrapper that runs the H2 flammable-cloud chain and verifies STL asset copy, `H2 leak UserDefined EB STL`, `buildFromSTL`, EB covered-cell mask initialization, no unused ParmParse variables, no text-log RuntimeWarnings, mass agreement, active/flammable hazard planes, and machine-readable summary output.
- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
  - Added STL H2 leak evidence and updated next-slice guidance.
- `docs/codex_audit/SMOKE_MATRIX.md`
  - Added the STL H2 leak wrapper and evidence summary to the H2 smoke matrix.

## Verification

Primary STL command:

```bash
CODEX_H2_LEAK_STL_LOG_DIR=/tmp/codex_h2_leak_stl_obstacle_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh
```

Primary result:

```text
h2_leak_stl_obstacle PASS output=/tmp/codex_h2_leak_stl_obstacle_20260717/stl_obstacle_summary.csv mass_ratio=1.00108533e+00 cloud_volume=2.14843750e-02 active_planes=5 flammable_planes=2 max_X=1.80968056e-01
```

Key STL metrics:

- `stl_file = cube_obstacle.stl`
- `stl_scale = 0.10`
- `stl_center = (1.0, 0.5, 0.5)`
- `mass_ratio = 1.00108533e+00`
- `h2_mass = 2.40260479e-04`
- `centroid_shift = 1.19236974e-01`
- `downstream_fraction = 8.73820198e-01`
- `cloud_volume = 2.14843750e-02`
- `cloud_species_mass = 2.09172931e-04`
- `max_X = 1.80968056e-01`
- `active_planes = 5`
- `flammable_planes = 2`
- `plotfiles = 7`

EB/STL evidence in `/tmp/codex_h2_leak_stl_obstacle_20260717/run.log`:

```text
H2 leak UserDefined EB STL: file=cube_obstacle.stl, scale=0.1, center=(1,0.5,0.5), reverse_normal=0, ngrow=4
buildFromSTL: built AMReX EB2 IndexSpace from cube_obstacle.stl
Resetting fine-covered cells mask
```

Cylinder-union regression command:

```bash
CODEX_H2_LEAK_TANK_FARM_LOG_DIR=/tmp/codex_h2_leak_tank_farm_post_stl_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_tank_farm.sh
```

Cylinder-union regression result:

```text
h2_leak_tank_farm PASS output=/tmp/codex_h2_leak_tank_farm_post_stl_20260717/tank_farm_summary.csv mass_ratio=1.00148922e+00 cloud_volume=2.14843750e-02 active_planes=5 flammable_planes=2 max_X=1.82368348e-01
```

Static and environment checks:

```bash
bash -n tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh tools/codex_smoke_engineering_h2_leak_plume_history.sh tools/codex_smoke_engineering_h2_leak_tank_farm.sh
python3 tools/check_machine_local_paths.py --strict
SUNDIALS_DIR=/home/cj/my-pele/external/PelePhysics/ThirdParty/INSTALL/gnu bash tools/codex_preflight_environment.sh
```

Results:

```text
bash -n: PASS (empty log)
machine_local_paths PASS scanned_files=924
preflight SUMMARY PASS warnings=3
PASS_NO_WARNINGS_TEXT
```

The three preflight warnings are the existing optional CUDA SUNDIALS library warnings and are not new to this slice.

## Evidence files

- `/tmp/codex_h2_leak_stl_obstacle_20260717/run.log`
- `/tmp/codex_h2_leak_stl_obstacle_20260717/stl_obstacle_summary.csv`
- `/tmp/codex_h2_leak_stl_obstacle_20260717/validation.log`
- `/tmp/codex_h2_leak_stl_obstacle_20260717/profile_validation.log`
- `/tmp/codex_h2_leak_stl_obstacle_20260717/hazard_summary.log`
- `/tmp/codex_h2_leak_stl_obstacle_20260717/hazard_planes.csv`
- `/tmp/codex_h2_leak_stl_obstacle_20260717/hazard_timeseries.csv`
- `/tmp/codex_h2_leak_tank_farm_post_stl_20260717/tank_farm_summary.csv`
- `/tmp/codex_h2_stl_bashn_20260717.log`
- `/tmp/codex_h2_stl_path_audit_20260717.log`
- `/tmp/codex_h2_stl_preflight_20260717.log`

## Current verdict

This is a material engineering step: the maintained H2 leak path now covers open-domain dispersion sensitivities, analytic cylinder obstacles, compact tank-farm cylinder unions, and a first imported STL obstacle through AMReX EB2.

Still not production-grade for real CAD/tank-yard consequence analysis:

- The STL case is a tiny cube, not a real cleaned CAD geometry.
- Multi-STL layouts and geometry scaling/orientation sweeps are not covered.
- Triangulation robustness, invalid STL handling, and geometry QA reports are not productionized.
- The mesh is coarse and single-box.
- Long-time plume/fire stability, turbulence/wall validation, and external reference comparisons remain open.
- Orifice/tank-pressure source modeling is still synthetic spherical-source based.

## Git/worktree note

The repository remains heavily dirty/untracked from the long-running audit. This checkpoint documents only the current H2 STL obstacle slice and its tank-farm regression evidence.
