# Checkpoint: engineering H2 leak real-gas Z consistency

UTC: 20260718-052857

## User priority

- Engineering production scenarios remain the first priority.
- Academic validation remains secondary, ordered gas-phase before gas-liquid/two-phase.
- Static droplet/CSF work remains low priority.

## Issue found

During the engineering H2 leak real-gas audit, the constant-`Z` path had two consistency gaps:

- The choked pressure-orifice formula used `Z`, but the unchoked/subcritical mass-flow formula still used the ideal-gas denominator.
- Tank blowdown pressure/mass conversion used `Z` for pressure recovery, but the initial and ambient tank inventories still used the ideal-gas overloads in the interval path.

These bugs were hidden by the earlier choked real-gas orifice smoke and default `Z=1` tank regression.

## Implemented

- Added `Z` to the unchoked pressure-orifice mdot denominator.
- Updated tank blowdown initial and ambient inventory calculations to use the same positive compressibility factor as the pressure update.
- Added unit coverage for subcritical/non-choked `1/sqrt(Z)` mdot scaling and `sqrt(Z)` exit-velocity scaling.
- Added `compressibility_factor` to the tank-blowdown runtime log line.
- Added `examples/engineering/h2_leak_3d/input.codex_real_gas_tank_blowdown_smoke`.
- Added `tools/codex_smoke_engineering_h2_leak_real_gas_tank_blowdown.sh`, which verifies logged `Z`, start-of-step real-gas mdot scaling, real-gas tank pressure drop `dm * ZRT/V`, monotone pressure/mdot depletion, and plotfile/source mass accounting.
- Updated engineering readiness and smoke-matrix documentation.

## Validation evidence

- `cmake --build build-codex-smoke --target test_leak_source_smoke -j 4`: PASS.
- `./build-codex-smoke/test_leak_source_smoke`: PASS.
- `ctest --test-dir build-codex-smoke -R leak_source_smoke --output-on-failure`: PASS.
- `bash -n` for real-gas tank-blowdown, real-gas orifice, tank-blowdown, pressure-orifice, pipe-loss, and multi-hole wrappers: PASS.
- Real-gas tank-blowdown smoke: PASS at `/tmp/codex_h2_leak_real_gas_tank_blowdown_zfix_rerun_20260718`, with `Z=1.44000000e+00`, `mdot=1.45151956e-03`, `ideal_mdot=1.74271791e-03`, `ratio=8.33333333e-01`, `first_pressure_drop=5.17196200e+02`, `mass_ratioN=1.00000000e+00`.
- Real-gas pressure-orifice regression: PASS at `/tmp/codex_h2_leak_real_gas_orifice_zfix_20260718`, with `Z=1.44000000e+00`, `mdot=1.45226493e-03`, `ideal_mdot=1.74271791e-03`, `ratio=8.33333333e-01`, `mass_ratioN=1.00000000e+00`.
- Default tank-blowdown regression: PASS at `/tmp/codex_h2_leak_tank_blowdown_zfix_20260718`, with `pressure_drop=2.11027122e+04`, `mdot_drop=7.20811300e-05`, `injected=8.52841643e-05`, `mass_ratioN=1.00000000e+00`.
- Default pressure-orifice regression: PASS at `/tmp/codex_h2_leak_pressure_orifice_zfix_20260718`, with `mdot=1.74271791e-03`, `expected=1.74271791e-03`, `rel=2.353e-10`, `mass_ratioN=1.00000000e+00`.
- Pipe-loss regression: PASS at `/tmp/codex_h2_leak_pipe_loss_zfix_20260718`, with `mdot=1.32564063e-03`, `no_loss_mdot=1.74271791e-03`, `reduction=7.60674246e-01`, `effective_pressure=3.80337123e+05`, `line_loss_total=4.40000000e+01`, `mass_ratioN=1.00000000e+00`.
- Multi-hole fixed-rate regression: PASS at `/tmp/codex_h2_leak_multihole_zfix_20260718`, with `leak_count=3`, `mdot_sum=1.00000000e-05`, `mass_ratioN=1.00000000e+00`.
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=934`.
- Targeted `git diff --check` for implementation files and audit docs: PASS.
- New smoke logs were clean for `Unused ParmParse Variables` and `RuntimeWarning`.

## Residual risks

- `Z` is still a constant user input, not a full real-gas EOS/table and not `Z(P,T)`.
- Tank blowdown is still isothermal and lumped; no Joule-Thomson cooling, thermal cooldown, linepack, distributed pipe/network dynamics, valve opening transient, or two-phase flashing is modeled.
- The source model is still a small-mesh deterministic smoke, not a validated production-scale high-pressure H2 release campaign.
- Multi-hole pressure-driven tank coupling remains future work; current multi-hole coverage is fixed-rate layout and normalization.

## Recommended next engineering slice

1. Add pressure/temperature-dependent real-gas density or tabulated `Z(P,T)` support with reference-data checks.
2. Add thermal cooldown/Joule-Thomson-aware tank/source temperature behavior.
3. Add distributed linepack/network transient support for storage and pipeline leakage.
4. Add pressure-driven per-hole multi-hole discharge coupled to tank/network state.
