# H2 Fire Plotfile Sensor Sampling Negative Selftest

- Status: `PASS-H2-FIRE-PLOTFILE-SENSOR-SAMPLING-NEGATIVE-SELFTEST`
- Positive linear case passed: `True`
- Negative cases refused: `8/8`
- Strict fire calibration blocker cleared: `False`

## Negative Cases

- `duplicate_sensor_id`: returncode=`2`, passed=`True`
- `missing_x_column`: returncode=`2`, passed=`True`
- `nan_coordinate`: returncode=`2`, passed=`True`
- `outside_domain_x`: returncode=`2`, passed=`True`
- `empty_sensor_csv`: returncode=`2`, passed=`True`
- `missing_variable`: returncode=`2`, passed=`True`
- `invalid_sampling_mode`: returncode=`2`, passed=`True`
- `no_plotfile`: returncode=`2`, passed=`True`

## Evidence

- `plotfile_sensor_extractor`: `tools/codex_extract_plotfile_sensor_timeseries.py`
- `positive_linear_sensors`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/positive_linear_sensors.csv`
- `positive_linear_log`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/positive_linear.log`
- `positive_linear_json`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/positive_linear.json`
- `duplicate_sensor_id_log`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/duplicate_sensor_id.log`
- `missing_x_column_log`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/missing_x_column.log`
- `nan_coordinate_log`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/nan_coordinate.log`
- `outside_domain_x_log`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/outside_domain_x.log`
- `empty_sensor_csv_log`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/empty_sensor_csv.log`
- `missing_variable_log`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/missing_variable.log`
- `invalid_sampling_mode_log`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/invalid_sampling_mode.log`
- `no_plotfile_log`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_negative_selftest_20260807/no_plotfile.log`
