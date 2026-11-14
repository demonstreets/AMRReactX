# Checkpoint 20260718-140013 - Engineering H2 leak lumped linepack blowdown

## Priority
- User priority remains engineering production scenarios first: large-scale tank/pipeline leakage, fire, and detonation-risk workflows.
- Academic validation remains lower priority, ordered gas-phase first and gas-liquid/two-phase later.
- Static droplet / CSF work remains deferred.

## Gap addressed
- The engineering H2 leak path had steady equivalent pipe/valve loss and lumped tank blowdown, but did not yet deplete pipe linepack inventory.
- This pass adds a conservative lumped linepack model. It is intentionally not a distributed 1D wave/network solver, but it verifies that finite pipe gas inventory can decay over time and drive a pressure-orifice source.

## Changes
- Added `Leak::linepack_volume(model, explicit_volume)` in `src/engineering/leak_source/leak_source.H`.
  - Uses explicit volume when provided.
  - Otherwise derives volume from `pi * line_diameter^2 * line_length / 4`.
- Added `prob.leak_model = linepack_blowdown` in `examples/engineering/h2_leak_3d`.
  - New accepted aliases: `linepack_blowdown`, `pipe_blowdown`, `linepack`.
  - New inputs: `prob.leak_linepack_pressure` / `prob.leak_pipe_pressure` and `prob.leak_linepack_volume` / `prob.leak_pipe_volume`.
  - Falls back to `prob.leak_tank_pressure` when `prob.leak_linepack_pressure` is not positive.
  - Uses the same pressure-orifice and equivalent pipe/valve loss formula, then integrates lumped linepack pressure depletion over each source interval.
- Added `examples/engineering/h2_leak_3d/input.codex_linepack_blowdown_smoke`.
  - Uses a derived linepack volume from `D=0.050 m`, `L=20.0 m`, initial line pressure `8.0e5 Pa`, and tank pressure `5.0e5 Pa` to verify the linepack pressure is not accidentally collapsed to tank pressure.
- Added `tools/codex_smoke_engineering_h2_leak_linepack_blowdown.sh`.
  - Runs the maintained H2 plume-history wrapper.
  - Verifies linepack log rows, derived volume, linepack initial pressure, pressure decrease, mdot decrease, first pressure drop, pipe-loss effective pressure, cumulative injected mass, and plotfile species-mass agreement.
- Extended `test/unit/test_leak_source.cpp` for derived/explicit linepack volume and linepack interval pressure drop.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md`.

## Validation evidence
- `ctest --test-dir build-codex-smoke -R leak_source_smoke --output-on-failure`
  - Passed: `100% tests passed`.
- New linepack blowdown smoke:
  - Command: `CODEX_H2_LEAK_LINEPACK_BLOWDOWN_LOG_DIR=/tmp/codex_h2_leak_linepack_blowdown_20260718 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_linepack_blowdown.sh`
  - Plume validation: `massN=2.46620935e-04`, `injectedN=2.46620496e-04`, `mass_ratioN=1.00000178e+00`.
  - Wrapper: `h2_leak_linepack_blowdown PASS intervals=50 volume=3.92699082e-02 first_avg_mdot=4.95603479e-03 start_mdot=4.95651472e-03 pressure_drop=1.56140100e+02 injected=2.46620496e-04 mass_ratioN=1.00000178e+00`.
- Steady pipe-loss regression after linepack change:
  - `/tmp/codex_h2_leak_pipe_loss_post_linepack_20260718/validation.log`
  - `massN=6.62820318e-05`, `injectedN=6.62820318e-05`, `mass_ratioN=1.00000000e+00`.
  - Wrapper: `h2_leak_pipe_loss PASS mdot=1.32564063e-03 no_loss_mdot=1.74271791e-03 reduction=7.60674246e-01 effective_pressure=3.80337123e+05 supply_pressure=5.00000000e+05 line_loss_total=4.40000000e+01 mass_ratioN=1.00000000e+00`.
- Tank-blowdown regression after linepack change:
  - `/tmp/codex_h2_leak_tank_blowdown_post_linepack_20260718/validation.log`
  - `massN=8.52841643e-05`, `injectedN=8.52841643e-05`, `mass_ratioN=1.00000000e+00`.
  - Wrapper: `h2_leak_tank_blowdown PASS intervals=50 pressure_drop=2.11027122e+04 mdot_drop=7.20811300e-05 injected=8.52841643e-05 mass_ratioN=1.00000000e+00`.
- Script syntax:
  - `bash -n tools/codex_smoke_engineering_h2_leak_linepack_blowdown.sh tools/codex_smoke_engineering_h2_leak_pipe_loss.sh tools/codex_smoke_engineering_h2_leak_tank_blowdown.sh`
  - Passed with no output.
- Log hygiene:
  - No `Unused ParmParse Variables`, `RuntimeWarning`, or `FAIL` in the new linepack/pipe-loss/tank-blowdown logs.
- Path and whitespace hygiene:
  - `python3 tools/check_machine_local_paths.py --strict` -> `machine_local_paths PASS scanned_files=937`.
  - `git diff --check` on touched tracked files passed.
  - No trailing whitespace in the new input or wrapper.

## Current engineering readiness estimate
- Engineering track estimate after this checkpoint: about 76%.
- This closes the first lumped linepack-inventory depletion gap, but it is still smoke-scale evidence.

## Remaining production gaps
- Full real-gas EOS `Z(P,T)` and composition-dependent thermodynamics.
- Joule-Thomson / thermal cooldown and wall heat-transfer effects for blowdown and pipeline depressurization.
- Distributed pipe-network pressure waves, valve actuation schedules, network branching, and rupture propagation.
- Sonic jet near-field resolution and grid/time-step guidance.
- Fire / ignition / thermal-radiation coupling and detonation-risk acceptance criteria.
- Production-scale hazard campaign matrix with reproducible meshes, inputs, expected ranges, runtime/performance evidence, and report packaging.

## Next recommended slice
- Add a valve/rupture schedule abstraction for `linepack_blowdown` or a production-style scenario campaign that sweeps linepack pressure/length/diameter and verifies monotonic inventory, cloud, and outlet-margin responses.
