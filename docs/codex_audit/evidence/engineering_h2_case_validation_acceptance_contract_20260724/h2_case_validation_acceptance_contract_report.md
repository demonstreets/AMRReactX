# Engineering H2 Case Validation Acceptance Contract

Status: `PASS-H2-CASE-VALIDATION-ACCEPTANCE-CONTRACT`

## Summary

- `campaign_count`: `4`
- `acceptance_contract_metric_count`: `44`
- `quantitative_metric_count`: `14`
- `failed_contract_campaign_count`: `0`
- `source_report_count`: `13`
- `negative_missing_threshold_refused`: `True`

## Campaign Contracts

- `real_cad_large_layout_leak_dispersion`: `PASS`, metrics `10`, quantitative `4`
- `sbepv5_d27_external_plume_validation`: `PASS`, metrics `13`, quantitative `4`
- `calibrated_fire_consequence_validation`: `PASS`, metrics `11`, quantitative `2`
- `integrated_engineering_production_replay`: `PASS`, metrics `10`, quantitative `4`

## Quality Gates

- `all_campaigns_have_acceptance_contracts`: `PASS`
- `contract_metric_count_is_production_sized`: `PASS`
- `contract_sources_cover_domain_and_final_reports`: `PASS`
- `negative_selftest_refuses_missing_threshold`: `PASS`
- `contract_report_does_not_clear_blockers`: `PASS`

## Limitations

- This report audits structured acceptance contracts only; it does not execute CFD validation campaigns.
- Production credit still requires accepted external data, campaign execution, metric comparison, and the full verifier passing.
