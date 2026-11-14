# 2026-07-23 BFS EB Wall and Inlet Profile Audit

## Scope

Continued work on the engineering production blocker:

```text
bfs_kepsilon_reference_validation_failed
```

The previous best 4-rank refined BFS result reached `X_R/H = 3.51`, below the
Driver and Seegmiller reference gate of `6.26 +/- 10%`.

## Code Changes

### PeleLMeX k-epsilon EB wall treatment

`external/PeleLMeX/Source/PeleLMeX_Diffusion.cpp` now applies the k-epsilon wall
function to EB single-valued cut cells in addition to physical no-slip domain
boundaries. The EB branch uses the EB boundary normal and boundary center to
compute local tangential velocity and wall distance, then sets the near-wall
`k` and `epsilon` auxiliary values.

This is intentionally guarded by `AMREX_USE_EB`, `m_ke_wall_functions`, the
`kepsilon` model selection, and `m_nAux >= 2`.

### BFS inlet profile control

`examples/engineering/backward_facing_step/pelelmex_prob.H` and `.cpp` now
support optional inlet profile parameters:

```text
prob.inlet_profile = 0|1
prob.inlet_channel_ylo
prob.inlet_channel_yhi
prob.inlet_power_law_exp
```

The default remains the previous uniform inlet. `prob.inlet_profile=1` applies
a symmetric turbulent channel power-law profile and initializes inlet
turbulence from the local inlet speed.

## Verification Runs

All runs below used 4 MPI ranks, 208 x 56 cells, `max_level=0`, and the patched
BFS executable.

### EB wall-function cut-cell probe

Directory:

```text
docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/ebwall_cutcell_4rank_1000_20260723
```

Result:

```text
RUN_RC 0
X_R/H = 3.52
recirculation = 3.28H
VERDICT = FAIL
```

The EB wall-function path is stable but does not by itself move the reference
metric enough.

### Top wall no-slip probe

Directory:

```text
docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/ebwall_topnoslip_4rank_1000_20260723
```

Result:

```text
X_R/H = 3.51
recirculation = 3.28H
VERDICT = FAIL
```

Changing the top boundary from slip to no-slip alone does not explain the
short reattachment length.

### Inlet profile probe

Directory:

```text
docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/profile_ebwall_topnoslip_4rank_1000_20260723
```

Result:

```text
X_R/H = 4.42
recirculation = 4.27H
VERDICT = FAIL
```

The inlet profile is a real sensitivity lever and improves the reference
metric, but not enough for the production gate.

### Inlet profile sensitivity

Directory:

```text
docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/profile_sweep_4rank_1000_20260723
```

Results:

```text
exp=0.2:    X_R/H = 4.49, recirculation = 4.27H, FAIL
exp=1/3:    X_R/H = 4.16, recirculation = 3.77H, FAIL
lower-wall: MLMG failed near step 916, rejected
```

The best stable short probe was `inlet_power_law_exp=0.2`.

### Long reference probe

Directory:

```text
docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/profile_exp020_ebwall_topnoslip_4rank_5000_20260723
```

Result:

```text
RUN_RC 0
final time = 0.5
latest plotfile = plt04309
X_R/H = 4.41
recirculation = 4.27H
VERDICT = FAIL
```

The official BFS report was refreshed to this current best plotfile:

```text
docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.json
```

Current official status remains:

```text
NOT_READY-BFS-KEPSILON-REFERENCE
```

## Current Interpretation

The BFS blocker is narrowed but not cleared. Evidence now indicates:

- EB k-epsilon wall treatment compiles and remains stable.
- Top-wall no-slip alone is not the missing physics.
- A more realistic inlet profile improves reattachment from about `3.51H` to
  `4.41H`.
- The remaining gap likely requires a stronger turbulence-model/near-wall
  correction, improved EB wall shear coupling into the momentum solve, a better
  validated inlet boundary-layer specification, or a refined-wall mesh strategy.

No production score should be upgraded from this work yet.
