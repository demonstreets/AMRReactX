# Engineering H2 Fire Calibration Dataset Ingestion

Status: `NOT_READY-H2-FIRE-CALIBRATION-DATASET-INGESTION`
Clears fire-consequence blocker: `False`
Dataset root: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset`

## Current Inputs

- `metadata_available`: `False`
- `metadata_file_present`: `True`
- `metadata_strict_schema_and_alignment_ready`: `False`
- `metadata_alignment_missing_or_false`: `['release_or_cloud_mass', 'ignition_or_burn_basis', 'boundary_conditions']`
- `radiation_metrics_available`: `True`
- `radiation_metrics_file_present`: `True`
- `overpressure_metrics_available`: `True`
- `overpressure_metrics_file_present`: `True`

## Blocking Gaps

- `fire_calibration_metadata_case_alignment_release_or_cloud_mass_not_true`
- `fire_calibration_metadata_case_alignment_ignition_or_burn_basis_not_true`
- `fire_calibration_metadata_case_alignment_boundary_conditions_not_true`

## Required Dataset Files

- `calibration_metadata_json`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata.json`
- `radiation_metrics_csv`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics.csv`
- `overpressure_metrics_csv`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics.csv`

## Limitations

- This report validates availability and schema of external fire/blast calibration data.
- It does not calibrate the model or clear the fire-consequence blocker.
- The fire consequence metrics report must still pass with --calibration-dataset-json before production credit is claimed.
