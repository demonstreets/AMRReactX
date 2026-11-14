# Engineering H2 Case Validation Failure Attribution

Status: `PASS-H2-CASE-VALIDATION-FAILURE-ATTRIBUTION`

## Summary

- `evaluation_status`: `NOT_READY-H2-CASE-VALIDATION-ACCEPTANCE-EVALUATION`
- `evaluation_acceptance_metric_count`: `44`
- `failed_metric_count`: `41`
- `deferred_metric_count`: `3`
- `attributed_problem_metric_count`: `44`
- `unattributed_problem_metric_count`: `0`
- `action_group_count`: `5`
- `external_artifact_row_count`: `14`
- `missing_or_invalid_artifact_row_count`: `14`

## Action Groups

- `external_plume_shape_reference`: metrics `11`, failed `11`, deferred `0`, artifacts `4`
- `final_verifier_deferred`: metrics `3`, failed `0`, deferred `3`, artifacts `14`
- `fire_consequence_calibration`: metrics `9`, failed `9`, deferred `0`, artifacts `4`
- `real_cad_cleanup`: metrics `7`, failed `7`, deferred `0`, artifacts `6`
- `real_cad_cleanup+external_plume_shape_reference+fire_consequence_calibration`: metrics `14`, failed `14`, deferred `0`, artifacts `14`

## Quality Gates

- `evaluation_attached`: `PASS`
- `failed_and_deferred_metrics_match_evaluation`: `PASS`
- `all_problem_metrics_are_attributed`: `PASS`
- `current_not_ready_state_has_actionable_artifacts`: `PASS`
- `failure_attribution_does_not_clear_blockers`: `PASS`

## Limitations

- This report attributes failed or deferred acceptance metrics to operator actions; it does not supply external data or run CFD campaigns.
- Production credit still requires all attributed artifacts to pass the strict intake gates, campaign execution, and final verifier pass.
