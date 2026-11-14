# Current Parallel Capability Matrix

- Status: `PASS-CURRENT-PARALLEL-CAPABILITY-MATRIX`
- Generated: `2026-08-20T10:11:37.811980+00:00`
- CPU/MPI ready for all current scenarios: `True`
- Single GPU ready for all current scenarios: `True`
- Multi-GPU MPI+CUDA ready for all current scenarios: `True`
- Strict master-plan complete: `False`
- Open strict blockers: `3`

| Scenario | CPU/MPI | Single GPU | Multi-GPU MPI+CUDA | Limitation |
|---|---:|---:|---:|---|
| engineering_h2_leak_diffusion_fire | True | True | True | Current engineering production credibility excludes strict external plume-shape agreement, real CAD cleanup, and calibrated radiation/overpressure closure until controlled artifacts are supplied. |
| engineering_multifuel_lng_lpg_surrogate_sources | True | True | True | This is evidence for gas-phase configurable-source and screening vaporization workflows; it does not claim CFD-internal flashing discharge, liquid pool spread, boiling, or pool evaporation. |
| academic_gas_detonation | True | True | True | The gate demonstrates current runtime capability and stability, not final publication-grade grid convergence for every mechanism/domain variant. |
| academic_gas_liquid_twophase_detonation | True | True | True | The 1000-step MPI+CUDA gate is a reduced-resolution stability proof for reacting spray coupling; final quantitative two-phase detonation validation still needs case-specific grid convergence and external comparison. |

## Open Strict Blockers

- `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`
- `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`
- `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`
