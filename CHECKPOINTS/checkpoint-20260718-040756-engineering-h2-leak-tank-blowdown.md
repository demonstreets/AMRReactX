# Checkpoint: Engineering H2 Leak Tank Blowdown Source

Date: 2026-07-18 04:07:56 UTC

## Scope

Engineering priority slice for the maintained PeleLMeX H2 leak workflow. This slice adds a transient tank-blowdown source mode after the fixed-mass-flow and pressure-orifice modes, with smoke-scale conservation and regression evidence.

## Code Changes

- Added ideal-gas isothermal lumped tank blowdown helpers in `src/engineering/leak_source/leak_source.H`:
  - `TankBlowdownInterval`
  - tank pressure/mass conversion helpers
  - duration-scaled substep integration for elapsed tank depletion
  - interval mass injection and cumulative release reporting
- Added `prob.leak_model = tank_blowdown` support in `examples/engineering/h2_leak_3d/pelelmex_prob.H/.cpp`.
- Added input controls:
  - `prob.leak_tank_volume`
  - `prob.leak_blowdown_substeps`
- Added maintained smoke input `examples/engineering/h2_leak_3d/input.codex_tank_blowdown_smoke`.
- Added wrapper `tools/codex_smoke_engineering_h2_leak_tank_blowdown.sh`.
- Updated H2 leak validators to parse `H2 leak source interval` records and skip PeleLMeX `STEP [-1]` initialization source calls.
- Extended `test/unit/test_leak_source.cpp` with tank-blowdown pressure/mdot decrease and interval mass consistency checks.
- Updated production-readiness and smoke-matrix audit docs.

## Verification

- `cmake --build build-codex-smoke --target test_leak_source_smoke -j 4` PASS.
- `./build-codex-smoke/test_leak_source_smoke` PASS.
- `ctest --test-dir build-codex-smoke -R leak_source_smoke --output-on-failure` PASS.
- Tank-blowdown smoke:
  - Command: `CODEX_H2_LEAK_TANK_BLOWDOWN_LOG_DIR=/tmp/codex_h2_leak_tank_blowdown_20260718b RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_tank_blowdown.sh`
  - `h2_leak_plume_history_validation PASS nplot=6 time0=0 timeN=0.05 mass0=0 mass1=1.73523038e-05 massN=8.52841643e-05 injectedN=8.52841643e-05 mass_ratioN=1.00000000e+00 mass_growth_ratio=4.91486119e+00 max_YH2=5.49869797e-03 centroid=(5.50776016e-01,5.00000000e-01,5.00000000e-01) downstream_fraction=7.18207474e-01 upstream_fraction=2.81792526e-01`
  - Wrapper: `h2_leak_tank_blowdown PASS intervals=50 pressure_drop=2.11027122e+04 mdot_drop=7.20811300e-05 injected=8.52841643e-05 mass_ratioN=1.00000000e+00`
- Pressure-orifice regression:
  - `/tmp/codex_h2_leak_pressure_orifice_post_blowdown_20260718/validation.log` PASS with `massN=8.71358957e-05`, `injectedN=8.71358957e-05`, `mass_ratioN=1.00000000e+00`.
  - Wrapper: `h2_leak_pressure_orifice PASS mdot=1.74271791e-03 expected=1.74271791e-03 rel=2.353e-10 mass_ratioN=1.00000000e+00`.
- Fixed-rate regression:
  - `/tmp/codex_h2_leak_plume_history_post_blowdown_20260718/validation.log` PASS with `timeN=5e-05`, `massN=5.00000000e-10`, `injectedN=5.00000000e-10`, `mass_ratioN=1.00000000e+00`.
- Static hygiene:
  - `bash -n` logs empty for tank-blowdown, pressure-orifice, and plume-history wrappers.
  - `python3 -m py_compile` logs empty for updated H2 validators.
  - `git diff --check` log empty for touched files.
  - `python3 tools/check_machine_local_paths.py --strict` PASS with `scanned_files=930`.
  - `tools/codex_preflight_environment.sh` PASS with three optional SUNDIALS CUDA-library warnings.
  - No `Unused ParmParse Variables` or `RuntimeWarning` markers in the new H2 leak logs.

## Residual Risk

This is still smoke-scale engineering evidence, not production-grade CFD validation. The new tank-blowdown source is an isothermal ideal-gas lumped tank model. It does not yet cover real-gas H2 behavior, thermal cooldown, valve/pipe-network losses, multi-hole releases, two-phase flashing, sonic jet resolution, fire coupling, production-scale mesh/time durations, or experimental/reference validation.

## Recommended Next Slice

Stay on engineering priority: add real-gas/thermal-cooldown/pipe-network or multi-hole discharge variants, or strengthen real CAD/STL quality reporting and bad-mesh guards for tank/pipeline layouts. Academic gas-phase validation remains useful support, but two-phase/static-droplet work should stay lower priority unless the engineering roadmap starts requiring liquid-pool physics.
