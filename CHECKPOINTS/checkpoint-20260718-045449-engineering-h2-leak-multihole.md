# Checkpoint: engineering H2 leak multi-hole source layout

UTC: 20260718-045449

## User priority

Engineering scenarios remain the first priority and should move toward production-grade evidence before broader academic expansion. Academic work is secondary, with gas-phase validation ahead of gas-liquid/two-phase work. Static-droplet/CSF work is low priority for now.

## Implemented in this slice

- Added fixed-rate multi-hole source layout support to `examples/engineering/h2_leak_3d`.
- Added `prob.leak_count` / `prob.leak_source_count` with up to four configured `leak0..leak3` center/radius/fraction records.
- Preserved legacy `prob.leak_xc`, `prob.leak_yc`, `prob.leak_zc`, `prob.leak_radius` behavior by mapping it into `leak0` defaults.
- Normalized nonnegative per-source fractions to the total effective source `mdot` and computed/logged each source active volume and volumetric source strength.
- Added `input.codex_multihole_smoke` and `tools/codex_smoke_engineering_h2_leak_multihole.sh`.
- Updated engineering readiness and smoke matrix documentation with the new gate and the remaining production limitations.

## Validation evidence

- Multi-hole smoke: `/tmp/codex_h2_leak_multihole_20260718/validation.log`, PASS with `massN=5.00000000e-10`, `injectedN=5.00000000e-10`, `mass_ratioN=1.00000000e+00`, centroid `(4.81255000e-01,2.31250001e-01,2.50000000e-01)`, downstream/upstream `3.87526765e-01/6.12473235e-01`; wrapper reported `h2_leak_multihole PASS leak_count=3 mdot_sum=1.00000000e-05 mass_ratioN=1.00000000e+00`.
- Fixed-rate regression: `/tmp/codex_h2_leak_plume_history_post_multihole_20260718/validation.log`, PASS with `mass_ratioN=1.00000000e+00`.
- Pressure-orifice regression: `/tmp/codex_h2_leak_pressure_orifice_post_multihole_20260718/validation.log`, PASS; wrapper reported `mdot=1.74271791e-03 expected=1.74271791e-03 rel=2.353e-10 mass_ratioN=1.00000000e+00`.
- Tank-blowdown regression: `/tmp/codex_h2_leak_tank_blowdown_post_multihole_20260718/validation.log`, PASS; wrapper reported `intervals=50 pressure_drop=2.11027122e+04 mdot_drop=7.20811300e-05 injected=8.52841643e-05 mass_ratioN=1.00000000e+00`.
- Pipe-loss regression: `/tmp/codex_h2_leak_pipe_loss_post_multihole_20260718/validation.log`, PASS; wrapper reported `mdot=1.32564063e-03 no_loss_mdot=1.74271791e-03 reduction=7.60674246e-01 effective_pressure=3.80337123e+05 supply_pressure=5.00000000e+05 line_loss_total=4.40000000e+01 mass_ratioN=1.00000000e+00`.
- `cmake --build build-codex-smoke --target test_leak_source_smoke -j 4`, PASS.
- `./build-codex-smoke/test_leak_source_smoke`, PASS.
- `ctest --test-dir build-codex-smoke -R leak_source_smoke --output-on-failure`, PASS.
- `bash -n` on H2 leak smoke wrappers, PASS.
- `python3 -m py_compile` on H2 leak validators, PASS.
- `python3 tools/check_machine_local_paths.py --strict`, PASS with `scanned_files=932`.
- `SUNDIALS_DIR=/home/cj/my-pele/external/PelePhysics/ThirdParty/INSTALL/gnu bash tools/codex_preflight_environment.sh`, PASS with 3 known optional CUDA SUNDIALS warnings.
- Targeted `git diff --check` for this slice, PASS.
- Grep of new H2 smoke logs found no `Unused ParmParse Variables` or `RuntimeWarning` markers.

## Residual production risks

- Multi-hole support is currently fixed-rate source layout splitting; per-hole tank pressure/orifice/timing, rupture propagation, transient valve behavior, distributed pipe-network waves, and linepack remain unvalidated.
- Leak models are still idealized and lack real-gas compressibility, thermal cooldown, sonic jet resolution, and production-scale long transients.
- Hazard/consequence evidence remains smoke-scale; production use still needs larger campaigns, boundary-condition sensitivity, reference data, and industrial CAD/tank-farm layouts.
- Gas-liquid CSF/static-droplet evidence remains intentionally low priority under the current user priority.

## Recommended next slice

Continue engineering-first hardening with one of: real-gas/thermal-cooldown leak source model, distributed pipe-network/linepack approximation, per-hole transient variants, CAD/STL quality guards, or longer reduced tank-farm/open-domain hazard campaigns. Academic gas-phase validation should follow after the engineering path is stronger; gas-liquid two-phase should remain later.
