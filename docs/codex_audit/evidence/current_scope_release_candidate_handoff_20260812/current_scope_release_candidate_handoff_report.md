# Current-Scope Release Candidate Handoff

- Status: `PASS-CURRENT-SCOPE-RELEASE-CANDIDATE-HANDOFF`
- Handoff ready: `True`
- Current user-priority ready: `True`
- Engineering progress estimate: `90-92`
- Overall progress estimate: `90-92`
- Scenarios ready: `4/4`
- CPU/MPI: `True`
- Single GPU: `True`
- MPI+CUDA: `True`
- Multifuel/liquefied answer ready: `True`
- Gas species: `C3H8, CH4, H2`
- Liquefied screening fluids: `LNG_CH4, LPG_C3H8`
- Internal liquid phase-change CFD ready: `False`
- Goal complete: `False`
- Strict master-plan complete: `False`
- Open strict blockers: `3`

## Handoff Paths

- `operator_runbook`: `docs/codex_audit/current_scope_operator_runbook.md`
- `readme`: `README.md`
- `final_readiness_report`: `docs/codex_audit/evidence/master_plan_final_readiness_20260731/master_plan_final_readiness_report.json`
- `completion_audit_report`: `docs/codex_audit/evidence/master_plan_completion_audit_20260803/master_plan_completion_audit_report.json`
- `scenario_matrix_report`: `docs/codex_audit/evidence/current_scenario_readiness_matrix_20260805/current_scenario_readiness_matrix_report.json`
- `parallel_matrix_report`: `docs/codex_audit/evidence/current_parallel_capability_matrix_20260803/current_parallel_capability_matrix_report.json`
- `multifuel_liquefied_answer_report`: `docs/codex_audit/evidence/engineering_multifuel_liquefied_user_answer_20260811/engineering_multifuel_liquefied_user_answer_report.json`

## Remaining Strict Work

- `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`: external plume-shape/time-series agreement data and passing CFD comparison
- `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`: real CAD artifact intake, cleanup, boundary tagging, and mesh parity evidence
- `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`: calibrated radiation and overpressure evidence, not only screening proxies
