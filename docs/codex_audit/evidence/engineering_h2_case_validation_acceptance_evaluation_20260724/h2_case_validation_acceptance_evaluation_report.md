# Engineering H2 Case Validation Acceptance Evaluation

Status: `NOT_READY-H2-CASE-VALIDATION-ACCEPTANCE-EVALUATION`

## Summary

- `campaign_count`: `4`
- `ready_campaign_count`: `0`
- `acceptance_metric_count`: `44`
- `passed_metric_count`: `0`
- `failed_metric_count`: `41`
- `deferred_metric_count`: `3`
- `ready_for_production_credit`: `False`
- `comparator_selftest_case_count`: `10`
- `comparator_selftest_passed`: `True`

## Campaigns

- `real_cad_large_layout_leak_dispersion`: ready `False`, pass/fail/deferred `0/9/1`
- `sbepv5_d27_external_plume_validation`: ready `False`, pass/fail/deferred `0/13/0`
- `calibrated_fire_consequence_validation`: ready `False`, pass/fail/deferred `0/11/0`
- `integrated_engineering_production_replay`: ready `False`, pass/fail/deferred `0/8/2`

## Quality Gates

- `acceptance_contract_attached`: `PASS`
- `all_contract_metrics_evaluated_or_deferred`: `PASS`
- `current_state_retains_unmet_real_data_metrics`: `PASS`
- `final_verifier_metrics_are_deferred_to_avoid_hash_cycle`: `PASS`
- `comparator_selftest_passed`: `PASS`
- `evaluation_does_not_clear_blockers`: `PASS`

## Limitations

- This report evaluates acceptance contracts against the current evidence JSON files; it does not run CFD campaigns.
- Final production-verifier metrics are intentionally deferred here to avoid a circular evidence hash dependency.
- Production credit still requires accepted external data, campaign execution, zero failed metrics, and the final verifier passing.
