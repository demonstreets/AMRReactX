# Checkpoint: engineering H2 leak configurable obstacle-cylinder smoke

Date: 2026-07-17 16:47:54 CST
Scope: engineering-first H2 leak path toward tank/pipeline/storage-yard use cases.

## Intent

Add the first production-relevant obstacle/EB gate to the H2 leak workflow. The previous open-domain gates covered flammable-cloud formation, wind sensitivity, release-rate sensitivity, source-radius/source-volume sensitivity, and outlet/domain-length margin. This checkpoint adds a configurable cylinder obstacle using PeleLMeX EB2 UserDefined geometry and verifies that the leak diagnostics still pass with EB covered cells present.

## Code changes in this slice

- `examples/engineering/h2_leak_3d/pelelmex_prob.H`
  - Added obstacle parameters to `MyProbParm`: radius, height, center, direction, and `obstacle_has_fluid_inside`.
- `examples/engineering/h2_leak_3d/pelelmex_prob.cpp`
  - `readProbParm()` now reads the obstacle parameters.
  - `EBUserDefined()` now builds a configurable `amrex::EB2::CylinderIF` and prints the selected geometry.
- `examples/engineering/h2_leak_3d/input.codex_obstacle_cylinder_smoke`
  - New reduced 3D obstacle leak input with `eb2.geom_type = UserDefined`.
- `tools/codex_smoke_engineering_h2_leak_obstacle_cylinder.sh`
  - New smoke wrapper around the flammable-cloud workflow.
  - Checks EB startup, covered-cell reset, no unused ParmParse warnings, mass closure, nonzero flammable cloud, active hazard planes, and plotfile count.
- `tools/validate_h2_leak_hazard_summary.py`
  - Fixed species mole-fraction calculation to avoid NumPy divide warnings on EB/covered cells.
- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
  - Updated H2 leak engineering readiness and evidence matrix.
- `docs/codex_audit/SMOKE_MATRIX.md`
  - Added the obstacle-cylinder H2 leak smoke gate.

## Verification

Primary command:

```bash
CODEX_H2_LEAK_OBSTACLE_LOG_DIR=/tmp/codex_h2_leak_obstacle_cylinder_20260717 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_obstacle_cylinder.sh
```

Primary result:

```text
h2_leak_obstacle_cylinder PASS output=/tmp/codex_h2_leak_obstacle_cylinder_20260717/obstacle_summary.csv mass_ratio=1.00002925e+00 cloud_volume=2.14843750e-02 active_planes=5 flammable_planes=2 max_X=1.81587588e-01
```

Key physics/diagnostic metrics from the same run:

- `mass_ratioN = 1.00002925e+00`
- `downstream_fraction = 8.72903144e-01`
- `upstream_fraction = 1.27096856e-01`
- `centroid_shift = 1.17282809e-01`
- `cloud_volume = 2.14843750e-02`
- `cloud_species_mass = 2.08802414e-04`
- `total_species_mass = 2.40007019e-04`
- `max_X = 1.81587588e-01`
- `active_planes = 5`
- `flammable_planes = 2`
- `plotfiles = 7`

EB evidence in `/tmp/codex_h2_leak_obstacle_cylinder_20260717/run.log`:

```text
H2 leak UserDefined EB cylinder: radius=0.1, height=1, direction=2, center=(1,0.5,0.5), has_fluid_inside=0
Resetting fine-covered cells mask
```

Warning checks:

- No `Unused ParmParse Variables` in the obstacle run logs.
- No `RuntimeWarning` in hazard summary/plane/timeseries rechecks after the EB covered-cell validator fix.

Auxiliary checks:

```bash
bash -n tools/codex_smoke_engineering_h2_leak_obstacle_cylinder.sh tools/codex_smoke_engineering_h2_leak_flammable_cloud.sh tools/codex_smoke_engineering_h2_leak_open_domain_length.sh
python3 tools/check_machine_local_paths.py --strict
SUNDIALS_DIR=/home/cj/my-pele/external/PelePhysics/ThirdParty/INSTALL/gnu bash tools/codex_preflight_environment.sh
```

Results:

```text
bash -n: PASS
machine_local_paths PASS scanned_files=922
preflight SUMMARY PASS warnings=3
```

The three preflight warnings are the existing optional CUDA SUNDIALS warnings and are not new to this slice.

## Evidence files

- `/tmp/codex_h2_leak_obstacle_cylinder_20260717/run.log`
- `/tmp/codex_h2_leak_obstacle_cylinder_20260717/obstacle_summary.csv`
- `/tmp/codex_h2_obstacle_hazard_summary_recheck_20260717.log`
- `/tmp/codex_h2_obstacle_hazard_planes_recheck_20260717.log`
- `/tmp/codex_h2_obstacle_hazard_timeseries_recheck_20260717.log`
- `/tmp/codex_h2_obstacle_path_audit_20260717.log`
- `/tmp/codex_h2_obstacle_preflight_20260717.log`
- `/tmp/codex_h2_obstacle_bashn_20260717.log`

## Current verdict

This is a useful engineering milestone but not a production-grade storage-yard/tank-farm model yet.

What is now covered:

- Gas-phase H2 leak reduced 3D workflow.
- Flammable-cloud metrics and time-series CSV diagnostics.
- Open-domain sensitivity gates for wind, release rate, source radius/source volume, and outlet/domain length.
- First EB obstacle-cylinder case with mass closure and hazard-plane checks.

Remaining production gaps:

- Multi-obstacle/tank-farm layouts are not yet validated.
- Imported STL/CAD geometry is not yet coupled into the H2 leak workflow.
- Long-duration plume/fire cases at production scale are still missing.
- Orifice/tank-pressure source modeling needs stronger engineering parameterization.
- Broader boundary-condition coverage is still needed: crosswind, low-wind, terrain/wall/inlet variants.
- Fire coupling, radiation, pool fire, and water/foam suppression are not yet production gates.
- Quantitative validation against external experiments/FLACS-style references is not complete.

## Git/worktree note

The repository remains heavily dirty/untracked from the ongoing audit and prior generated work. This checkpoint documents only the current obstacle-cylinder H2 leak slice and does not imply unrelated modified files are reviewed or production-ready.
