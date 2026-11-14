# HySafe SBEPV5 D27 Dataset Ingestion Readiness

Status: `NOT_READY-SBEPV5-D27-DATASET-INGESTION`
Clears reference-data blocker: `False`
Dataset root: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_selftest_20260724/fixtures/negative_placeholder_duplicate_sensor`

## Current Inputs

- `dataset_metadata_available`: `False`
- `exact_sensor_coordinates_available`: `False`
- `exact_baffle_geometry_available`: `True`
- `experimental_timeseries_available`: `True`

## Blocking Gaps

- `dataset_metadata_synthetic_or_selftest_marker_present`
- `dataset_metadata_placeholder_or_template_marker_present`
- `sensor_coordinates_duplicate_sensor_id_1`
- `sensor_coordinates_placeholder_or_template_marker_present`
- `sensor_coordinates_missing_sensor_ids:2`

## Required Dataset Files

- `dataset_metadata_json`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_selftest_20260724/fixtures/negative_placeholder_duplicate_sensor/dataset_metadata.json`
- `sensor_coordinates_csv`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_selftest_20260724/fixtures/negative_placeholder_duplicate_sensor/sensor_coordinates.csv`
- `baffle_geometry_csv`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_selftest_20260724/fixtures/negative_placeholder_duplicate_sensor/baffle_geometry.csv`
- `experimental_timeseries_csv`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_selftest_20260724/fixtures/negative_placeholder_duplicate_sensor/experimental_timeseries.csv`

## Schema Requirements

- `content_quality_gate_level`: `strict-v1-placeholder-free-and-non-synthetic`
- `accepted_sensor_id_formats`: `['1', '01', 'Gas01']`
- `sensor_coordinates_csv_columns`: `['sensor_id', 'x_m', 'y_m', 'z_m', 'reliability', 'source_basis', 'digitization_uncertainty_m']`
- `baffle_geometry_csv_columns`: `['baffle_id', 'x_min_m', 'x_max_m', 'y_min_m', 'y_max_m', 'z_min_m', 'z_max_m', 'source_basis', 'digitization_uncertainty_m']`
- `experimental_timeseries_csv_columns`: `['time_s', 'Gas01_vol_percent', 'Gas02_vol_percent', 'Gas03_vol_percent', 'Gas04_vol_percent', 'Gas05_vol_percent', 'Gas06_vol_percent', 'Gas07_vol_percent', 'Gas08_vol_percent', 'Gas09_vol_percent', 'Gas10_vol_percent', 'Gas11_vol_percent', 'Gas12_vol_percent']`

## Limitations

- This report validates the external dataset ingestion package before reference-agreement scoring.
- It cannot clear the production reference-data blocker by itself.
- The official reference-agreement report must still be regenerated with a passing external plume dataset JSON.
