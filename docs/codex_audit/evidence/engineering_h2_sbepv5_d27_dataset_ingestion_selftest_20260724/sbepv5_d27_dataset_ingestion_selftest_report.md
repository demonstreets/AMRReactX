# SBEPV5 D27 Dataset Ingestion Gate Selftest

Status: `PASS-SBEPV5-D27-DATASET-INGESTION-SELFTEST`
Synthetic selftest only: `True`
Does not clear production blockers: `True`

## Summary

- `positive_case_count`: `2`
- `positive_passed_count`: `2`
- `negative_case_count`: `1`
- `negative_refused_count`: `1`
- `numeric_sensor_id_fixture_passed`: `True`
- `gas_sensor_id_fixture_passed`: `True`

## Case Results

- `positive_numeric_sensor_ids`: `PASS-SBEPV5-D27-DATASET-INGESTION`, gaps `0`
- `positive_gas_sensor_ids`: `PASS-SBEPV5-D27-DATASET-INGESTION`, gaps `0`
- `negative_placeholder_duplicate_sensor`: `NOT_READY-SBEPV5-D27-DATASET-INGESTION`, gaps `5`

## Limitations

- This is fixture-only gate evidence and must not be used as external SBEPV5 production data.
- Production credit still requires controlled external sensor, baffle, metadata, and time-series artifacts.
