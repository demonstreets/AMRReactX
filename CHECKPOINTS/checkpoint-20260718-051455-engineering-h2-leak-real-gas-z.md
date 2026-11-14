# Checkpoint: engineering H2 leak real-gas compressibility Z

UTC: 20260718-051455

## User priority

- Engineering production scenarios are the first priority.
- Academic validation comes after engineering hardening, ordered gas-phase first and gas-liquid/two-phase later.
- Static droplet and CSF/two-phase surface-tension work remains low priority for now.

## Implemented in this slice

- Added configurable pressure-orifice compressibility factor `Z` to `PressureOrificeLeakModel` with positivity validation.
- Updated pressure-orifice mass flow, exit velocity, pipe-loss line density, and tank-blowdown pressure/mass helpers to use the configured `Z` while preserving ideal-gas default `Z=1` behavior.
- Exposed `prob.leak_compressibility_factor` plus aliases `prob.leak_Z` and `prob.leak_real_gas_Z` in the PeleLMeX engineering H2 leak problem.
- Added `examples/engineering/h2_leak_3d/input.codex_real_gas_orifice_smoke`.
- Added `tools/codex_smoke_engineering_h2_leak_real_gas_orifice.sh` to verify logged `Z`, mdot scaling, and plume mass accounting.
- Added unit tests for ideal compatibility, `1/sqrt(Z)` mdot scaling, `sqrt(Z)` velocity scaling, invalid `Z`, and tank pressure/mass round-trip with `Z`.
- Updated engineering readiness and smoke-matrix documentation.

## Validation evidence

- `bash -n tools/codex_smoke_engineering_h2_leak_real_gas_orifice.sh`: PASS.
- `cmake --build build-codex-smoke --target test_leak_source_smoke -j 4`: PASS.
- `./build-codex-smoke/test_leak_source_smoke`: PASS.
- Real-gas pressure-orifice smoke: PASS with `Z=1.44`, `mdot=1.45226493e-03`, `ideal_mdot=1.74271791e-03`, `ratio=8.33333333e-01`, `mass_ratioN=1.00000000e+00`.
- Default pressure-orifice regression after real-gas change: PASS with `mdot=1.74271791e-03`, `mass_ratioN=1.00000000e+00`.
- Default tank-blowdown regression after real-gas change: PASS with `pressure_drop=2.11027122e+04`, `mdot_drop=7.20811300e-05`, `mass_ratioN=1.00000000e+00`.
- Default pipe-loss regression after real-gas change: PASS with `mdot=1.32564063e-03`, `reduction=7.60674246e-01`, `effective_pressure=3.80337123e+05`, `mass_ratioN=1.00000000e+00`.
- Multi-hole fixed-rate regression after real-gas change: PASS with `leak_count=3`, `mdot_sum=1.00000000e-05`, `mass_ratioN=1.00000000e+00`.
- `ctest --test-dir build-codex-smoke -R leak_source_smoke --output-on-failure`: PASS.
- Shell syntax check for real-gas, pressure-orifice, tank-blowdown, pipe-loss, and multi-hole wrappers: PASS.
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=933`.
- `SUNDIALS_DIR=/home/cj/my-pele/external/PelePhysics/ThirdParty/INSTALL/gnu bash tools/codex_preflight_environment.sh`: PASS with the known optional CUDA SUNDIALS warnings only.
- Targeted `git diff --check` for implementation files and updated audit docs: PASS.
- New smoke logs were clean for `Unused ParmParse Variables` and `RuntimeWarning`.

## Residual risks

- The implementation is a constant user-supplied compressibility factor, not a full real-gas EOS/table lookup and not `Z(P,T)`.
- It does not model Joule-Thomson cooling, thermal cooldown, flashing, condensation, or multi-phase release physics.
- Distributed pipe networks, linepack transients, valve dynamics, and per-hole transient multi-hole discharge are still not implemented.
- The smoke cases prove wiring, scaling, and mass accounting on small deterministic meshes; production-scale hazard validation still requires larger 2D/3D campaigns and benchmark comparison.

## Recommended next engineering slice

1. Add full real-gas EOS or tabulated `Z(P,T)`/density support for H2 release, including validation against reference correlations.
2. Add thermal cooldown/Joule-Thomson-aware source temperature behavior.
3. Add distributed pipe/linepack transient network support for storage and pipeline leakage scenarios.
4. Extend multi-hole support from fixed-rate layout checks to pressure-driven per-hole discharge with transient tank coupling.
