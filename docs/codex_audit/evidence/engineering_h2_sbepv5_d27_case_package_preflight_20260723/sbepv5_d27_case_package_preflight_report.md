# HySafe SBEPV5 D27 Case Package Preflight

Status: `PASS-SBEPV5-D27-CASE-PACKAGE-PREFLIGHT`
Reference source resolution ready: `True`
Case runnable: `False`
Production validation ready: `False`

## Input Checks

- `scout` n_cell: `[60, 10, 45]`
- `scout` max cell size m: `0.02`
- `scout` nozzle cells: `0.6`
- `reference` n_cell: `[240, 40, 180]`
- `reference` max cell size m: `0.005`
- `reference` nozzle cells: `2.4`

## Remaining Runtime Gaps

- `dataset_metadata_json_missing_or_not_passed`
- `exact_sensor_coordinates_missing_or_not_passed`
- `exact_baffle_geometry_missing_or_not_passed`
- `experimental_timeseries_missing_or_not_passed`

## Limitations

- This preflight checks package self-consistency and source-region resolution of the scaffold.
- It does not run PeleLMeX and does not clear the external reference-data blocker.
- production_validation_ready remains false until the exact dataset is ingested and a 120 s case-matched run is completed.
