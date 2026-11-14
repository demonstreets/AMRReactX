# Engineering H2 Fire Calibration Dataset Builder

Status: `NOT_READY-H2-FIRE-CALIBRATION-DATASET`
Calibration dataset written: `False`
Clears fire-consequence blocker: `False`

## Current Inputs

- `fire_screening_report_passed`: `True`
- `dataset_ingestion_passed`: `False`
- `distance_summary_keys_available`: `True`

## Blocking Gaps

- `fire_calibration_dataset_ingestion_not_passed`
- `fire_calibration_metadata_case_alignment_release_or_cloud_mass_not_true`
- `fire_calibration_metadata_case_alignment_ignition_or_burn_basis_not_true`
- `fire_calibration_metadata_case_alignment_boundary_conditions_not_true`

## Limitations

- This builder writes the calibration dataset JSON consumed by the fire consequence report.
- It does not clear the fire-consequence blocker by itself.
- Production credit requires the official fire consequence report to pass with --calibration-dataset-json.
