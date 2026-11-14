# Checkpoint 20260718-134751 - Engineering H2 leak pressure multihole tank blowdown

## Priority
- User priority remains engineering production scenarios first: large-scale tank/pipeline leakage, fire, and detonation-risk workflows.
- Academic validation remains lower priority, ordered gas-phase first and gas-liquid/two-phase later.
- Static droplet / CSF surface-tension work remains intentionally deferred.

## Gap addressed
- The code already had pressure-driven multi-hole source support, but shared-tank depletion for pressure-driven multi-hole blowdown did not have a dedicated smoke gate.
- A regression risk was found in `tools/codex_smoke_engineering_h2_leak_tank_blowdown.sh`: its parser did not accept the newer `compressibility_factor=` field in tank-blowdown logs.

## Changes
- Added `examples/engineering/h2_leak_3d/input.codex_pressure_multihole_tank_blowdown_smoke`.
  - Three leak holes share one tank blowdown state.
  - Per-hole diameters are 0.002, 0.003, and 0.004 m.
  - Initial tank pressure is 5.0e5 Pa, ambient pressure is 101325 Pa, tank volume is 0.005 m^3.
- Added `tools/codex_smoke_engineering_h2_leak_pressure_multihole_tank_blowdown.sh`.
  - Verifies shared tank pressure decreases.
  - Verifies interval-averaged mdot decreases during blowdown.
  - Verifies first pressure drop equals injected mass converted through `Z * R * T / V`.
  - Verifies per-hole pressure-orifice mdot, fractions, assigned mdot, and H2 source row consistency.
  - Verifies final history mass matches cumulative injected mass.
- Fixed `tools/codex_smoke_engineering_h2_leak_tank_blowdown.sh` so its log parser accepts optional `compressibility_factor=`.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` with the new smoke and evidence.

## Validation evidence
- Syntax check passed:
  - `bash -n tools/codex_smoke_engineering_h2_leak_pressure_multihole_tank_blowdown.sh tools/codex_smoke_engineering_h2_leak_tank_blowdown.sh`
- New shared-tank pressure-driven multi-hole smoke passed:
  - Log directory: `/tmp/codex_h2_leak_pressure_multihole_tank_20260718`
  - `h2_leak_plume_history_validation PASS`
  - `massN=2.62140628e-04`
  - `injectedN=2.62140493e-04`
  - `mass_ratioN=1.00000051e+00`
  - Wrapper check: `first_avg_mdot=5.60766898e-03`, `start_mdot=5.61542439e-03`, `pressure_drop=6.48640293e+04`.
- Default tank-blowdown regression passed after parser fix:
  - Log directory: `/tmp/codex_h2_leak_tank_blowdown_post_pressure_multihole_tank_20260718`
  - Wrapper check: `pressure_drop=2.11027122e+04`, `injected=8.52841643e-05`, `mass_ratioN=1.00000000e+00`.
- Unit/smoke regression passed:
  - `ctest --test-dir build-codex-smoke -R leak_source_smoke --output-on-failure`
  - `100% tests passed`.
- Log hygiene passed:
  - No `Unused ParmParse Variables`, `RuntimeWarning`, or `FAIL` found in the new smoke logs.

## Current engineering readiness estimate
- Engineering track estimate after this checkpoint: about 75%.
- This closes the previously identified shared-tank pressure-driven multi-hole blowdown smoke gap.
- The estimate remains below production-grade because the current model is still a lumped-tank engineering source model rather than a full production leakage/fire/detonation workflow.

## Remaining production gaps
- Real-gas EOS as a function of pressure and temperature, instead of fixed/configured compressibility factor.
- Joule-Thomson / thermal cooldown and wall heat-transfer effects for blowdown.
- Distributed pipe network, valves, linepack, rupture timing, and boundary-condition integration.
- Sonic jet near-field resolution and grid/time-step guidance for engineering-scale runs.
- Fire / ignition / thermal-radiation coupling and scenario acceptance criteria.
- Production-scale hazard campaign matrix with reproducible meshes, input decks, expected ranges, and runtime/performance evidence.

## Next recommended slice
- Add a production-oriented blowdown campaign smoke that exercises time-varying tank pressure against a scenario-style acceptance envelope, then begin the distributed pipe/linepack abstraction.
