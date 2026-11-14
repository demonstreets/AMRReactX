# Engineering H2 Fire Calibration Dataset Ingestion

Status: `PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION`
Clears fire-consequence blocker: `False`
Dataset root: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_selftest_20260727/fixtures/positive_literature_digitized`

## Current Inputs

- `metadata_available`: `True`
- `metadata_file_present`: `True`
- `metadata_strict_schema_and_alignment_ready`: `True`
- `metadata_alignment_missing_or_false`: `[]`
- `radiation_metrics_available`: `True`
- `radiation_metrics_file_present`: `True`
- `overpressure_metrics_available`: `True`
- `overpressure_metrics_file_present`: `True`

## Blocking Gaps


## Required Dataset Files

- `calibration_metadata_json`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_selftest_20260727/fixtures/positive_literature_digitized/calibration_metadata.json`
- `radiation_metrics_csv`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_selftest_20260727/fixtures/positive_literature_digitized/radiation_metrics.csv`
- `overpressure_metrics_csv`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_selftest_20260727/fixtures/positive_literature_digitized/overpressure_metrics.csv`

## Limitations

- This report validates availability and schema of external fire/blast calibration data.
- It does not calibrate the model or clear the fire-consequence blocker.
- The fire consequence metrics report must still pass with --calibration-dataset-json before production credit is claimed.
