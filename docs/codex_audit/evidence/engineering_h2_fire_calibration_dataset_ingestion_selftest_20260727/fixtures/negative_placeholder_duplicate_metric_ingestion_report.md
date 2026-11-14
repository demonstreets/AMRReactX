# Engineering H2 Fire Calibration Dataset Ingestion

Status: `NOT_READY-H2-FIRE-CALIBRATION-DATASET-INGESTION`
Clears fire-consequence blocker: `False`
Dataset root: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_selftest_20260727/fixtures/negative_placeholder_duplicate_metric`

## Current Inputs

- `metadata_available`: `False`
- `metadata_file_present`: `True`
- `metadata_strict_schema_and_alignment_ready`: `False`
- `metadata_alignment_missing_or_false`: `[]`
- `radiation_metrics_available`: `False`
- `radiation_metrics_file_present`: `True`
- `overpressure_metrics_available`: `False`
- `overpressure_metrics_file_present`: `True`

## Blocking Gaps

- `fire_calibration_metadata_contains_synthetic_or_selftest_marker`
- `fire_calibration_metadata_contains_placeholder_marker`
- `radiation_calibration_contains_placeholder_marker`
- `overpressure_calibration_duplicate_metric_id:op_far`

## Required Dataset Files

- `calibration_metadata_json`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_selftest_20260727/fixtures/negative_placeholder_duplicate_metric/calibration_metadata.json`
- `radiation_metrics_csv`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_selftest_20260727/fixtures/negative_placeholder_duplicate_metric/radiation_metrics.csv`
- `overpressure_metrics_csv`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_selftest_20260727/fixtures/negative_placeholder_duplicate_metric/overpressure_metrics.csv`

## Limitations

- This report validates availability and schema of external fire/blast calibration data.
- It does not calibrate the model or clear the fire-consequence blocker.
- The fire consequence metrics report must still pass with --calibration-dataset-json before production credit is claimed.
