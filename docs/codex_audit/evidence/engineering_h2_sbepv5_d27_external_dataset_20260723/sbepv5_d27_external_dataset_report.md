# HySafe SBEPV5 D27 External Plume Dataset Builder

Status: `NOT_READY-SBEPV5-D27-EXTERNAL-PLUME-DATASET`
External dataset written: `False`
Clears reference-data blocker: `False`

## Current Inputs

- `dataset_ingestion_passed`: `False`
- `scout_report_passed`: `True`
- `plume_observation_passed`: `True`
- `plume_observation_case_matched_to_sbepv5`: `False`
- `plume_observation_time_end_s`: `0.20000000000000015`

## Blocking Gaps

- `sbepv5_dataset_ingestion_not_passed`
- `dataset_metadata_json_missing`
- `sensor_coordinates_csv_missing`
- `baffle_geometry_csv_missing`
- `experimental_timeseries_csv_missing`
- `plume_observation_not_case_matched_to_sbepv5_d27`
- `plume_observation_time_end_before_sbepv5_120s`

## Outputs

- External dataset JSON: `None`
- Candidate metric count: `0`

## Limitations

- This builder prepares the external plume dataset JSON consumed by the official reference-agreement report.
- The builder report itself does not clear the reference-data blocker.
- External validation is only claimed after the official reference-agreement report passes with the generated dataset JSON.
