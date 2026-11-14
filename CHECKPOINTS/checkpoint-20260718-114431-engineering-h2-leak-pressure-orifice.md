# Checkpoint: engineering H2 leak pressure-orifice source

Date: 2026-07-18
Scope: engineering-priority H2 leak source physics for tank/pipe leakage workflows.

## What changed

- Added `PressureOrificeLeakModel` helpers in `src/engineering/leak_source/leak_source.H` for ideal-gas compressible orifice mass flow, choked/unchoked detection, positive area selection, and exit velocity.
- Added optional `prob.leak_model = pressure_orifice` to `examples/engineering/h2_leak_3d` while preserving `fixed_mass_flow` as the default.
- Added H2 leak input parameters for tank pressure, ambient pressure, orifice diameter/area, discharge coefficient, gamma, gas constant, and optional orifice-velocity use.
- Updated the H2 source application log to print the effective mass flow rate and source model, so validation can audit the injected mass reference.
- Updated `validate_h2_leak_plume.py`, `validate_h2_leak_plume_history.py`, and `validate_h2_leak_plume_profile.py` to use `H2 leak effective mass flow rate=` from the run log when present, falling back to `prob.leak_rate` for older/fixed-rate logs.
- Added `examples/engineering/h2_leak_3d/input.codex_pressure_orifice_smoke` and `tools/codex_smoke_engineering_h2_leak_pressure_orifice.sh`.
- Extended `test/unit/test_leak_source.cpp` to cover pressure-orifice positivity, pressure monotonicity, area scaling, unchoked/choked branch behavior, and zero pressure-drop behavior.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` with pressure-orifice evidence and remaining limitations.

## Verification evidence

- Pressure-orifice engineering smoke passed: `/tmp/codex_h2_leak_pressure_orifice_20260718/validation.log`.
  - `timeN=0.05`
  - `massN=8.71358957e-05`
  - `injectedN=8.71358957e-05`
  - `mass_ratioN=1.00000000e+00`
  - `mass_growth_ratio=5.00000000e+00`
  - `downstream_fraction=7.16734740e-01`
  - `upstream_fraction=2.83265260e-01`
- Pressure-orifice wrapper independently recomputed the input formula and reported:
  - `h2_leak_pressure_orifice PASS mdot=1.74271791e-03 expected=1.74271791e-03 rel=2.353e-10 mass_ratioN=1.00000000e+00`
- Legacy fixed-rate plume-history regression passed after validator changes: `/tmp/codex_h2_leak_plume_history_post_pressure_orifice_20260718/validation.log`.
  - `massN=5.00000000e-10`
  - `injectedN=5.00000000e-10`
  - `mass_ratioN=1.00000000e+00`
- Header/unit regression passed: `/tmp/codex_pressure_orifice_ctest_leak_source_20260718.log` reports `100% tests passed` for `leak_source_smoke`.
- Direct build/run of `test_leak_source_smoke` passed after rebuilding the target; build log: `/tmp/codex_pressure_orifice_leak_source_build_20260718.log`.
- Script syntax and validator bytecode checks passed with empty logs:
  - `/tmp/codex_pressure_orifice_bashn_20260718.log`
  - `/tmp/codex_pressure_orifice_pycompile_20260718.log`
- Machine-local path audit passed: `/tmp/codex_pressure_orifice_path_audit_20260718.log` reports `machine_local_paths PASS scanned_files=929`.
- Environment preflight passed: `/tmp/codex_pressure_orifice_preflight_20260718.log` reports `preflight SUMMARY PASS warnings=3`; warnings are optional SUNDIALS CUDA library warnings.
- `git diff --check` produced no output for the touched source/docs files: `/tmp/codex_pressure_orifice_diff_check_20260718.log`.
- New pressure-orifice and fixed-rate regression logs contain no `Unused ParmParse Variables` or `RuntimeWarning` markers.

## Current engineering readiness impact

This is the first maintained engineering source model beyond a prescribed fixed mass-flow rate. It makes the H2 leak workflow more relevant to storage-vessel and pipe-leak studies because the solver can now derive source strength from pressure, orifice size, gas constants, and discharge coefficient, with mass conservation checked against the effective injected mass.

## Remaining risks

- The model is a constant-reservoir ideal-gas orifice smoke, not a full transient tank blowdown model.
- No tank inventory depletion, thermal cooldown, real-gas EOS, multi-hole release, pipe-network loss, valve schedule, or rupture-growth model yet.
- Sonic jet resolution and near-field source-shape sensitivity are not validated.
- Fire/heat-release coupling, obstacle/CAD campaigns, turbulence/wall validation, long-time stability, MPI/GPU scaling, and production-size hazard reporting remain open.

## Recommended next slice

Next best engineering-production step: add transient tank depletion / pipe-network source physics on top of the new pressure-orifice kernel, with a mass-budget history validator that integrates time-varying `mdot(t)`. If geometry risk is more urgent, switch to real CAD/STL quality reporting and bad-mesh guards.
