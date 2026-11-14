# 2026-07-23 BFS/k-epsilon Boundary Fix and Verification

## Scope

Engineering production-readiness blocker: `bfs_kepsilon_reference_validation_failed`.

This note records the current corrective action on the PeleLMeX
`examples/engineering/backward_facing_step` and `examples/engineering/bfs_kepsilon`
problem boundary fills.

## Fix

- Restricted domain inlet state filling to the x-low face only:
  `idir == 0 && sgn == 1`.
- This prevents y-low wall ghost cells from receiving inlet velocity,
  density, temperature, enthalpy, and species state.
- The change was applied to:
  - `examples/engineering/backward_facing_step/pelelmex_prob.H`
  - `examples/engineering/bfs_kepsilon/pelelmex_prob.H`

## Build Environment Repair

The default MPI build initially failed because OpenMPI runtime packages were
present but OpenMPI development headers/libraries were missing.

- Installed `libopenmpi-dev`.
- Rebuilt `examples/engineering/backward_facing_step` from a clean build
  directory with the default OpenMPI toolchain.
- New verification executable:
  `examples/engineering/backward_facing_step/codex_bfs_openmpi2d.gnu.MPI.ex`.

## Verification Evidence

4-rank refined BFS/k-epsilon, 208 x 56, CFL 0.05, dt_shrink 0.001:

- Previous behavior: 4-rank run aborted at step 0 with NaNs.
- New short run:
  `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/boundaryfix_clean_openmpi_208x56_lowcfl_4rank_200step`
  completed 200 steps with no NaNs.
- New longer run:
  `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/boundaryfix_clean_openmpi_208x56_lowcfl_4rank_5000step`
  completed 5000 steps with no NaNs; final time `0.08871921372`.

The refreshed BFS validator still reports `FAIL`:

- `X_R/H = 2.6602768365911147`
- recirculation length `2.4606299212598426 H`
- required reference: `X_R/H = 6.26 +/- 10%`, minimum recirculation length `3 H`

Therefore the NaN/stability defect is fixed, but the BFS physical reference
validation blocker remains open.

## Refreshed Gates

- `bfs_kepsilon_reference_report.json`: `NOT_READY-BFS-KEPSILON-REFERENCE`
- `engineering_production_scorecard.json`: `NOT_PRODUCTION_READY`,
  functional `94.1`, production credibility `76.0`
- `production_evidence_verification_report.json`: `PASS`, score `94.1/76.0`
- CTest: `22/22` passed

Remaining production scorecard blockers:

- `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`
- `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`
- `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`
- `bfs_kepsilon_reference_validation_failed`

## Follow-up: k/epsilon Aux Initialization

The true `examples/engineering/backward_facing_step` case enabled
`peleLM.les_model = kepsilon` but did not declare or initialize the auxiliary
`k` and `epsilon` fields.  The case now declares:

- `peleLM.aux_vars = k epsilon`
- `peleLM.k.advect = 1`
- `peleLM.k.Schmidt = 1.0`
- `peleLM.epsilon.advect = 1`
- `peleLM.epsilon.Schmidt = 1.3`

The problem initialization and auxiliary boundary fill now seed inlet
turbulence from configurable `peleLM.ke_inlet_TI` and `peleLM.ke_inlet_L`.

Verification executable:
`examples/engineering/backward_facing_step/codex_bfs_tunable2d.gnu.MPI.ex`.

Best 4-rank 208 x 56 aux-initialized baseline before wall-function filtering:

- evidence:
  `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/tunable_sensitivity_4rank_5000_20260723/baseline_TI005_L1H/plt04014`
- `X_R/H = 3.38`
- recirculation length `3.28 H`
- verdict: `FAIL`

The 4-case inlet turbulence sensitivity matrix was stable on 4 MPI ranks:

| Case | TI | L [m] | X_R/H | Recirculation [H] | Verdict |
| --- | ---: | ---: | ---: | ---: | --- |
| baseline_TI005_L1H | 0.05 | 0.0381 | 3.38 | 3.28 | FAIL |
| lowTI001_L1H | 0.01 | 0.0381 | 3.36 | 3.28 | FAIL |
| lowTI0005_L1H | 0.005 | 0.0381 | 3.34 | 3.12 | FAIL |
| TI001_L4H | 0.01 | 0.1524 | 3.36 | 3.28 | FAIL |

This rules out simple inlet turbulence intensity/length-scale tuning as a
sufficient path to the Driver & Seegmiller reattachment target.

## Follow-up: k/epsilon Wall-Function Boundary Filtering

The current PeleLMeX k-epsilon wall-function implementation applied
`applyKEWallFunctions()` to every non-periodic domain side.  That incorrectly
overrode `k` and `epsilon` in inlet, outlet, and slip-wall boundary cell layers.

The implementation now filters by physical boundary type and applies the
domain wall function only to:

- `BoundaryCondition::BCNoSlipWallAdiab`
- `BoundaryCondition::BCNoSlipWallIsotherm`

Changed file:

- `external/PeleLMeX/Source/PeleLMeX_Diffusion.cpp`

Verification executable:
`examples/engineering/backward_facing_step/codex_bfs_wallbc2d.gnu.MPI.ex`.

4-rank refined BFS/k-epsilon, 208 x 56, CFL 0.05, dt_shrink 0.001:

- evidence:
  `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/wallbc_filter_4rank_20260723/plt03900`
- return code: `0`
- final time: `0.5`
- `X_R/H = 3.51`
- recirculation length `3.28 H`
- verdict: `FAIL`

The wall-function filtering fix is a real correctness repair and moves the
reattachment metric in the right direction (`3.38 -> 3.51`), but it is not
sufficient to satisfy the reference gate (`6.26 +/- 10%`). The remaining BFS
gap is likely in the wall/EB treatment fidelity, inlet boundary-layer realism,
or the reference validation method for this coarse wall-function mesh.

## Follow-up: Wall-Function-Off Control

A control run with the same filtered-wall-function executable but
`peleLM.ke_wall_functions=0` was executed to test whether the current wall
function model itself was shortening reattachment.

4-rank refined BFS/k-epsilon, 208 x 56, CFL 0.05, dt_shrink 0.001:

- evidence:
  `docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/wallfunc_off_4rank_20260723/plt04552`
- return code: `0`
- final time: `0.5`
- `X_R/H = 2.64`
- recirculation length `2.46 H`
- verdict: `FAIL`

Turning wall functions off worsened both metrics relative to the filtered
wall-function case (`X_R/H = 3.51`, recirculation `3.28 H`). This indicates
the wall-function path is necessary on the current coarse wall mesh; the next
repair should focus on EB wall treatment, near-wall/step-face consistency, and
more realistic inlet boundary-layer development rather than disabling wall
functions.
