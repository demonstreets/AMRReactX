# Current Scenario Readiness Matrix

- Status: `PASS-CURRENT-SCENARIO-READINESS-MATRIX`
- Overall current-priority progress estimate: `90-92`
- Current user-priority ready: `True`
- Strict master-plan complete: `False`
- Deferred strict blockers: `3`

| Scenario | Progress | CPU/MPI | Single GPU | Multi-GPU MPI+CUDA | Current-use answer |
|---|---:|---:|---:|---:|---|
| Engineering H2 leak / dispersion / ignition / fire | `90-92` | `True` | `True` | `True` | `yes_current_priority_scope` |
| Engineering multi-fuel gas sources / gasified LNG-LPG surrogate workflows | `90-92` | `True` | `True` | `True` | `yes_current_priority_scope` |
| Academic gas-phase detonation | `85-90` | `True` | `True` | `True` | `yes_current_priority_scope` |
| Academic gas-liquid / two-phase detonation | `92-94` | `True` | `True` | `True` | `yes_current_priority_scope` |

## Limits
- `engineering_h2_leak_diffusion_fire`: Current engineering production credibility excludes strict external plume-shape agreement, real CAD cleanup, and calibrated radiation/overpressure closure until controlled artifacts are supplied.
- `engineering_multifuel_lng_lpg_surrogate_sources`: This is evidence for gas-phase configurable-source and screening vaporization workflows; it does not claim CFD-internal flashing discharge, liquid pool spread, boiling, or pool evaporation.
- `academic_gas_detonation`: The gate demonstrates current runtime capability and stability, not final publication-grade grid convergence for every mechanism/domain variant.
- `academic_gas_liquid_twophase_detonation`: The 1000-step MPI+CUDA gate is a reduced-resolution stability proof for reacting spray coupling; final quantitative two-phase detonation validation still needs case-specific grid convergence and external comparison.

## Deferred Strict Blockers
- `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`
- `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`
- `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`
