# Checkpoint: engineering H2 leak compact tank-farm EB union smoke

Date: 2026-07-17 16:59:40 CST
Scope: engineering-first gas-phase H2 leak dispersion path for storage-yard/tank-farm scenarios.

## Intent

Move the H2 engineering leak workflow beyond a single obstacle by adding a compact three-cylinder tank-farm EB smoke. This is not a full industrial geometry campaign yet, but it proves the maintained H2 leak case can build and run a union of multiple EB cylinders while preserving the existing flammable-cloud diagnostics and the previous single-cylinder gate.

## Code changes in this slice

- `examples/engineering/h2_leak_3d/pelelmex_prob.H`
  - Added `obstacle_count` to `MyProbParm` while preserving the existing single-cylinder defaults.
- `examples/engineering/h2_leak_3d/pelelmex_prob.cpp`
  - Added `prob.obstacle_count` support.
  - Added explicit support for one to three EB cylinders.
  - Uses `amrex::EB2::makeUnion(cyl0,cyl1)` or `makeUnion(cyl0,cyl1,cyl2)` for multi-cylinder geometry.
  - Preserves the old single-cylinder log string so `tools/codex_smoke_engineering_h2_leak_obstacle_cylinder.sh` remains compatible.
  - Aborts early if `prob.obstacle_count` is outside `[1,3]`.
- `examples/engineering/h2_leak_3d/input.codex_tank_farm_smoke`
  - New compact three-cylinder vertical tank-farm input derived from the obstacle-cylinder H2 leak smoke.
- `tools/codex_smoke_engineering_h2_leak_tank_farm.sh`
  - New engineering smoke wrapper for the three-cylinder case.
  - Reuses the flammable-cloud workflow and adds checks for `UserDefined EB cylinders: count=3`, the third obstacle report, EB covered-cell mask initialization, no unused ParmParse variables, no text-log RuntimeWarnings, mass agreement, nonzero flammable cloud, hazard planes, and plotfile count.
- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
  - Updated current verdict, gate matrix, evidence table, and next-slice guidance.
- `docs/codex_audit/SMOKE_MATRIX.md`
  - Added tank-farm wrapper and evidence summary to the H2 engineering smoke matrix.

## Verification

Primary tank-farm command:

```bash
CODEX_H2_LEAK_TANK_FARM_LOG_DIR=/tmp/codex_h2_leak_tank_farm_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_tank_farm.sh
```

Primary result:

```text
h2_leak_tank_farm PASS output=/tmp/codex_h2_leak_tank_farm_20260717/tank_farm_summary.csv mass_ratio=1.00148922e+00 cloud_volume=2.14843750e-02 active_planes=5 flammable_planes=2 max_X=1.82368348e-01
```

Key tank-farm metrics:

- `obstacle_count = 3`
- `mass_ratio = 1.00148922e+00`
- `h2_mass = 2.40357412e-04`
- `centroid_shift = 1.15570293e-01`
- `downstream_fraction = 8.71965595e-01`
- `cloud_volume = 2.14843750e-02`
- `cloud_species_mass = 2.05991468e-04`
- `total_species_mass = 2.40357412e-04`
- `max_X = 1.82368348e-01`
- `active_planes = 5`
- `flammable_planes = 2`
- `plotfiles = 7`

EB evidence in `/tmp/codex_h2_leak_tank_farm_20260717/run.log`:

```text
H2 leak UserDefined EB cylinders: count=3, height=1, direction=2, has_fluid_inside=0
  obstacle2: radius=0.1, center=(1.2,0.68,0.5)
Resetting fine-covered cells mask
```

Single-cylinder regression command:

```bash
CODEX_H2_LEAK_OBSTACLE_LOG_DIR=/tmp/codex_h2_leak_obstacle_cylinder_post_tankfarm_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_obstacle_cylinder.sh
```

Single-cylinder regression result:

```text
h2_leak_obstacle_cylinder PASS output=/tmp/codex_h2_leak_obstacle_cylinder_post_tankfarm_20260717/obstacle_summary.csv mass_ratio=1.00002925e+00 cloud_volume=2.14843750e-02 active_planes=5 flammable_planes=2 max_X=1.81587588e-01
```

Text-log warning check:

```text
PASS_NO_WARNINGS_TEXT
```

Auxiliary checks:

```bash
bash -n tools/codex_smoke_engineering_h2_leak_tank_farm.sh tools/codex_smoke_engineering_h2_leak_obstacle_cylinder.sh tools/codex_smoke_engineering_h2_leak_flammable_cloud.sh
python3 tools/check_machine_local_paths.py --strict
SUNDIALS_DIR=/home/cj/my-pele/external/PelePhysics/ThirdParty/INSTALL/gnu bash tools/codex_preflight_environment.sh
```

Results:

```text
bash -n: PASS (empty log)
machine_local_paths PASS scanned_files=923
preflight SUMMARY PASS warnings=3
```

The three preflight warnings are the existing optional CUDA SUNDIALS library warnings and are not new to this slice.

## Evidence files

- `/tmp/codex_h2_leak_tank_farm_20260717/run.log`
- `/tmp/codex_h2_leak_tank_farm_20260717/tank_farm_summary.csv`
- `/tmp/codex_h2_leak_tank_farm_20260717/validation.log`
- `/tmp/codex_h2_leak_tank_farm_20260717/profile_validation.log`
- `/tmp/codex_h2_leak_tank_farm_20260717/hazard_summary.log`
- `/tmp/codex_h2_leak_tank_farm_20260717/hazard_planes.csv`
- `/tmp/codex_h2_leak_tank_farm_20260717/hazard_timeseries.csv`
- `/tmp/codex_h2_leak_obstacle_cylinder_post_tankfarm_20260717/obstacle_summary.csv`
- `/tmp/codex_h2_tankfarm_bashn_20260717.log`
- `/tmp/codex_h2_tankfarm_path_audit_20260717.log`
- `/tmp/codex_h2_tankfarm_preflight_20260717.log`

## Current verdict

This is a meaningful engineering step: H2 leak dispersion now has a maintained gas-phase path covering open-domain sensitivity, single EB obstacle, and compact three-cylinder tank-farm EB union smoke.

Still not production-grade for real storage-yard consequence analysis:

- The tank-farm case is compact and coarse.
- Geometry is still analytic cylinders, not imported STL/CAD.
- There is no multi-layout obstacle campaign yet.
- There is no long-time production-scale plume/fire stability campaign.
- There is no external experimental/FLACS-style reference validation.
- Orifice/tank-pressure source modeling remains synthetic spherical-source based.
- Crosswind, low-wind, terrain, wall-function, radiation, pool fire, and suppression gates remain open.

## Git/worktree note

The repository remains heavily dirty/untracked from the long-running audit. This checkpoint documents only the current compact tank-farm EB union slice and its regression evidence.
