# HySafe SBEPV5 D27 Case Package Scaffold

Status: `PASS-SBEPV5-D27-CASE-PACKAGE-SCAFFOLD`
Case runnable: `False`
Clears reference-data blocker: `False`
Package root: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package`

## Package Files

- `scout_input`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/inputs.sbepv5_d27_scout`
- `reference_input`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/inputs.sbepv5_d27_reference`
- `sensor_template`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/sensors_template.csv`
- `baffle_template`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/baffle_geometry_template.csv`
- `metadata_template`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/dataset_metadata_template.json`
- `experimental_timeseries_template`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/experimental_timeseries_template.csv`
- `readme`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/README.md`

## Runnable Blocking Gaps

- `dataset_metadata_json_missing_or_not_passed`
- `exact_sensor_coordinates_missing_or_not_passed`
- `exact_baffle_geometry_missing_or_not_passed`
- `experimental_timeseries_missing_or_not_passed`

## Limitations

- This report proves the SBEPV5 case package scaffold exists.
- It does not prove that the case has been run or validated against external data.
- case_runnable remains false until exact geometry, sensors, metadata, and experimental time series pass ingestion.
