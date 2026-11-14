# Engineering H2 Plume Observation Extraction

Status: `PASS-H2-PLUME-OBSERVATION`
Run directory: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/campaign_run/cases/plan-amr-mpi-reduced-long/amr/run`
Sensor basis: `guard_boundary_requires_nearest_not_production_evidence`
Sensor sampling: `nearest`

## Summary

- `time_start`: `0.0`
- `time_end`: `0.20000000000000015`
- `max_cloud_volume`: `0.0382080078125`
- `max_peak_X`: `0.22629682198090545`
- `max_flammable_x`: `0.984375`
- `max_flammable_z`: `0.640625`
- `extent_rows`: `11`
- `sensor_rows`: `11`
- `plume_extents_available`: `True`
- `sensor_timeseries_available`: `True`
- `all_sensors_inside_domain`: `True`
- `max_sensor_sample_distance`: `0.05412658773652741`
- `max_nearest_cell_distance`: `0.05412658773652741`
- `case_matched_external_benchmark`: `False`

## Outputs

- `plume_extents_csv`: `docs/codex_audit/evidence/engineering_h2_plume_observation_20260723/sensor_sampling_compat_20260723/boundary_nearest_extents.csv`
- `sensor_timeseries_csv`: `docs/codex_audit/evidence/engineering_h2_plume_observation_20260723/sensor_sampling_compat_20260723/boundary_nearest_sensors.csv`

## Limitations

- This report proves extraction capability for plume extents and point-probe time series.
- It does not by itself prove agreement with an external field-test, wind-tunnel, or literature-digitized benchmark.
