# H2 Fire Plotfile Sensor Sampling Contract

- Status: `PASS-H2-FIRE-PLOTFILE-SENSOR-SAMPLING-CONTRACT`
- Plotfiles: `2`
- Sensors: `4`
- Rows: `8`
- Variables: `['avg_pressure', 'temp', 'Y(H2)']`
- Sampling mode: `linear`
- Linear interpolation used: `True`
- Pressure sensor time-series path ready: `True`
- Uses synthetic sensor coordinates: `True`
- Uses non-cell-center sensor coordinates: `True`
- EXP002 pressure agreement ready: `False`
- Strict fire calibration blocker cleared: `False`

## Claim Boundary

- This proves a reusable plotfile sensor-sampling output path.
- It proves linear interpolation for non-cell-center synthetic sensor coordinates.
- It uses synthetic in-domain sensor locations, not EXP002 sensor coordinates.
- It samples avg_pressure as a pressure proxy and does not claim calibrated overpressure agreement.
- It does not address calibrated radiation agreement.

## Evidence

- `plotfile_sensor_extractor`: `tools/codex_extract_plotfile_sensor_timeseries.py`
- `sensor_csv`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_contract_20260807/synthetic_pressure_sensor_locations.csv`
- `timeseries_csv`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_contract_20260807/synthetic_pressure_sensor_timeseries.csv`
- `extractor_json`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_contract_20260807/plotfile_sensor_timeseries_extraction_report.json`
- `extractor_log`: `docs/codex_audit/evidence/h2_fire_plotfile_sensor_sampling_contract_20260807/extractor.log`
- `plt00000_header`: `examples/engineering/h2_leak_3d/plt00000/Header`
- `plt00001_header`: `examples/engineering/h2_leak_3d/plt00001/Header`
