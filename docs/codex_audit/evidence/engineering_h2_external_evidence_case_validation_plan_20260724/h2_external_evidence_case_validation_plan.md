# Engineering H2 External Evidence Case Validation Plan

Status: `PASS-H2-EXTERNAL-EVIDENCE-CASE-VALIDATION-PLAN`

## Summary

- `worksheet_row_count`: `14`
- `worksheet_valid_artifact_row_count`: `0`
- `worksheet_missing_or_invalid_artifact_row_count`: `14`
- `worksheet_ready_for_external_evidence_acceptance`: `False`
- `domain_count`: `3`
- `case_validation_campaign_count`: `4`
- `ready_case_validation_campaign_count`: `0`
- `integrated_replay_ready`: `False`
- `acceptance_contract_metric_count`: `44`

## Domain Readiness

- `external_plume_shape_reference`: valid `0/4`, ready `False`
- `fire_consequence_calibration`: valid `0/4`, ready `False`
- `real_cad_cleanup`: valid `0/6`, ready `False`

## Case Validation Campaigns

- `real_cad_large_layout_leak_dispersion`: ready `False`
  commands: `python3 tools/write_engineering_h2_real_cad_intake_preflight_report.py; python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py; bash tools/rebuild_engineering_h2_evidence_chain.sh`
  acceptance contract metrics: `10`
- `sbepv5_d27_external_plume_validation`: ready `False`
  commands: `python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py; python3 tools/write_engineering_h2_sbepv5_external_dataset_report.py; python3 tools/write_engineering_h2_reference_agreement_report.py --external-plume-dataset-json <generated_external_plume_dataset_json>; python3 tools/write_engineering_h2_external_plume_benchmark_readiness.py; bash tools/rebuild_engineering_h2_evidence_chain.sh`
  acceptance contract metrics: `13`
- `calibrated_fire_consequence_validation`: ready `False`
  commands: `python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py; python3 tools/write_engineering_h2_fire_calibration_package_report.py; python3 tools/write_engineering_h2_fire_calibration_dataset_report.py; python3 tools/write_engineering_h2_fire_consequence_metrics_report.py --calibration-dataset-json <generated_fire_calibration_dataset_json>; bash tools/rebuild_engineering_h2_evidence_chain.sh`
  acceptance contract metrics: `11`
- `integrated_engineering_production_replay`: ready `False`
  commands: `python3 tools/write_engineering_h2_external_artifact_drop_validator.py; python3 tools/write_engineering_h2_external_artifact_controlled_copy_report.py --apply --confirm-controlled-copy H2_EXTERNAL_ARTIFACTS_READY; bash tools/rebuild_engineering_h2_evidence_chain.sh; bash tools/verify_engineering_h2_production_evidence.sh`
  acceptance contract metrics: `10`

## Limitations

- This plan converts accepted external evidence into explicit validation campaigns; it does not launch long CFD runs.
- No validation campaign may clear production blockers until its commands run on accepted controlled evidence and the full verifier passes.
