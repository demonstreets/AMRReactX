# Checkpoint: engineering H2 leak pressure-driven multi-hole source

## Priority context

- User priority remains engineering production scenarios first: large-scale tank/pipeline leaks, fires, and detonation-risk workflows.
- Academic gas/two-phase validation remains lower priority than engineering leak/fire readiness.
- Static droplet/CSF work remains low priority for now.

## Gap addressed

The maintained H2 leak workflow previously had a fixed-rate multi-hole source layout, but pressure-orifice and tank-blowdown source paths still effectively computed one total source rate and then split by user fractions unless a case author hand-derived the fractions. That is weak for engineering rupture scenarios because different holes should naturally get different mdot from their orifice areas.

## Implementation

- Extended `examples/engineering/h2_leak_3d/pelelmex_prob.H` / `.cpp` with per-source `prob.leakN_orifice_diameter` and `prob.leakN_orifice_area` inputs for up to four leak sources.
- In `prob.leak_model = pressure_orifice` or `tank_blowdown`, explicitly configured per-hole area/diameter now enables `pressure_driven_multihole` mode.
- For pressure-orifice multi-hole cases, each source gets its own pressure-orifice mdot and mdot fraction from the same tank/downstream pressure model.
- For tank-blowdown multi-hole cases, the total equivalent area is available for the lumped tank interval, while per-source assignment is distributed from per-hole pressure mdot at the interval start. This path is implemented but not yet covered by a dedicated smoke.
- Kept legacy fixed-rate multi-hole behavior unchanged when per-source orifice fields are not supplied.
- Updated per-source enthalpy to use each source's actual velocity kinetic-energy contribution in pressure-driven multi-hole mode.
- Added `examples/engineering/h2_leak_3d/input.codex_pressure_multihole_smoke`.
- Added `tools/codex_smoke_engineering_h2_leak_pressure_multihole.sh`.
- Updated `tools/codex_smoke_engineering_h2_leak_multihole.sh` to tolerate the new `pressure_fraction` log field.
- Added a unit-test invariant that parallel pressure-orifice holes sum to the equivalent total area model.

## Verification evidence

- `bash -n tools/codex_smoke_engineering_h2_leak_pressure_multihole.sh tools/codex_smoke_engineering_h2_leak_multihole.sh`: PASS.
- `cmake --build build-codex-smoke --target test_leak_source_smoke -j 4`: PASS.
- `./build-codex-smoke/test_leak_source_smoke`: PASS.
- `ctest --test-dir build-codex-smoke -R leak_source_smoke --output-on-failure`: PASS.
- New pressure-driven multi-hole smoke:
  - Command: `CODEX_H2_LEAK_PRESSURE_MULTIHOLE_LOG_DIR=/tmp/codex_h2_leak_pressure_multihole_20260718 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_pressure_multihole.sh`
  - Validation: `/tmp/codex_h2_leak_pressure_multihole_20260718/validation.log`
  - PASS metrics: `timeN=5e-05`, `massN=2.80771219e-07`, `injectedN=2.80771219e-07`, `mass_ratioN=1.00000000e+00`, centroid `(5.25873093e-01,2.75861530e-01,2.50000000e-01)`.
  - Wrapper: `h2_leak_pressure_multihole PASS leak_count=3 mdot_sum=5.61542439e-03 expected=5.61542439e-03 mass_ratioN=1.00000000e+00`.
- Fixed-rate multi-hole regression:
  - Command: `CODEX_H2_LEAK_MULTIHOLE_LOG_DIR=/tmp/codex_h2_leak_multihole_post_pressure_multihole_20260718 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_multihole.sh`
  - Validation: `/tmp/codex_h2_leak_multihole_post_pressure_multihole_20260718/validation.log` PASS with `massN=5.00000000e-10`, `injectedN=5.00000000e-10`, `mass_ratioN=1.00000000e+00`.
- Pressure-orifice regression:
  - Command: `CODEX_H2_LEAK_PRESSURE_ORIFICE_LOG_DIR=/tmp/codex_h2_leak_pressure_orifice_post_pressure_multihole_20260718 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_pressure_orifice.sh`
  - Validation: `/tmp/codex_h2_leak_pressure_orifice_post_pressure_multihole_20260718/validation.log` PASS with `massN=8.71358957e-05`, `injectedN=8.71358957e-05`, `mass_ratioN=1.00000000e+00`.
  - Wrapper: `h2_leak_pressure_orifice PASS mdot=1.74271791e-03 expected=1.74271791e-03 rel=2.353e-10 mass_ratioN=1.00000000e+00`.
- Log hygiene: no `Unused ParmParse Variables`, `RuntimeWarning`, or `FAIL` in the new pressure multi-hole, fixed multi-hole regression, or pressure-orifice regression log directories.

## Residual risk

- This is still a coarse smoke-grid pressure-orifice source gate, not production-scale rupture validation.
- Shared-tank pressure-driven multi-hole blowdown has implementation support but still needs a dedicated application smoke.
- No distributed pipe-network solver, linepack, valve/rupture timing, real EOS `Z(P,T)`, Joule-Thomson cooldown, sonic jet resolution, ignition/fire coupling, or large-scale hazard campaign has been completed yet.

## Next recommended engineering slice

Add a dedicated shared-tank pressure-driven multi-hole blowdown smoke, then move toward real EOS/thermal cooldown and distributed pipe-network/linepack modeling.
