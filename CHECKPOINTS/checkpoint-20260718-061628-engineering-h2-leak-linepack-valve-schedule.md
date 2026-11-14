# Checkpoint: engineering H2 leak linepack valve schedule

Date: 2026-07-18

## Goal slice

Raise the engineering H2 leak workflow toward production readiness by adding a maintained delayed/ramped valve or rupture schedule for single-hole pressure-orifice, tank-blowdown, and linepack-blowdown paths, with regression evidence that the default always-open behavior is unchanged.

## Changes

- Added `Leak::ValveSchedule` helpers in `src/engineering/leak_source/leak_source.H`:
  - validity checks for nonnegative open/ramp times and fractions in `[0,1]`
  - time-dependent fraction interpolation
  - single-hole orifice area scaling
  - scheduled lumped tank/linepack substep integration
- Wired PeleLMeX H2 leak parameters in `examples/engineering/h2_leak_3d`:
  - `prob.leak_valve_open_time`
  - `prob.leak_valve_ramp_time`
  - `prob.leak_valve_initial_fraction`
  - `prob.leak_valve_final_fraction`
  - aliases `prob.leak_rupture_time` and `prob.leak_rupture_ramp_time`
- Added runtime validation and log fields for valve schedule fractions at interval start/mid/end.
- Added `input.codex_linepack_valve_schedule_smoke` and `tools/codex_smoke_engineering_h2_leak_linepack_valve_schedule.sh`.
- Extended `test/unit/test_leak_source.cpp` with valve schedule validity/fraction checks and scheduled linepack interval checks.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md`.

## Verification

- `bash -n tools/codex_smoke_engineering_h2_leak_linepack_valve_schedule.sh`: PASS
- `cmake --build build-codex-smoke --target test_leak_source_smoke -j 4`: PASS
- `ctest --test-dir build-codex-smoke -R leak_source_smoke --output-on-failure`: PASS
- `CODEX_H2_LEAK_LINEPACK_VALVE_LOG_DIR=/tmp/codex_h2_leak_linepack_valve_schedule_20260718_rerun RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_linepack_valve_schedule.sh`: PASS
  - `intervals=50`
  - `closed_intervals=5`
  - `ramp_intervals=20`
  - `first_positive_fraction=2.50000000e-02`
  - `injected=1.72889628e-04`
  - `mass_ratioN=1.00000110e+00`
- Always-open linepack regression:
  - `/tmp/codex_h2_leak_linepack_blowdown_post_valve_20260718/validation.log`
  - `mass_ratioN=1.00000178e+00`
- Tank-blowdown regression:
  - `/tmp/codex_h2_leak_tank_blowdown_post_valve_20260718/validation.log`
  - `mass_ratioN=1.00000000e+00`
- Pipe-loss regression:
  - `/tmp/codex_h2_leak_pipe_loss_post_valve_20260718/validation.log`
  - `mass_ratioN=1.00000000e+00`
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=938`
- `git diff --check -- ...`: PASS

## Residual risks

- The new schedule is a single-hole lumped valve/rupture abstraction. It does not model distributed pressure waves, network branching, rupture-front propagation, complex valve topology, or control logic.
- The linepack/tank blowdown remains isothermal and uses a constant user-specified compressibility factor, not full `Z(P,T)` or thermal cooldown.
- Smoke grids remain coarse and short; production use still needs long-time, larger-domain, MPI, obstacle/fire, and reference-validation campaigns.

## Engineering readiness estimate

Engineering production-readiness estimate moves from about 76% to about 77%.

This is a real engineering capability increment because delayed/ramped releases are now runnable, logged, and regression-tested. It is still not production-grade overall because the remaining gaps are system-level validation and high-fidelity physics rather than just missing parameters.
