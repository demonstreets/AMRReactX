# Engineering H2 Plume Observation Extraction

Status: `PASS-H2-PLUME-OBSERVATION`
Run directory: `/home/cj/my-pele/docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_mpi_cuda_20260805/run`
Sensor basis: `DataverseNO open-channel H2 sensors transformed for the h2_leak_3d x-downstream solver convention`
Sensor sampling: `nearest`

## Summary

- `time_start`: `0.0`
- `time_end`: `0.9999999999999062`
- `max_cloud_volume`: `0.7497500000000002`
- `max_peak_X`: `0.2052749774993526`
- `max_flammable_x`: `5.0249999999999995`
- `max_flammable_z`: `0.775`
- `extent_rows`: `11`
- `sensor_rows`: `319`
- `plume_extents_available`: `True`
- `sensor_timeseries_available`: `True`
- `all_sensors_inside_domain`: `True`
- `max_sensor_sample_distance`: `0.043301270189221946`
- `max_nearest_cell_distance`: `0.043301270189221946`
- `case_matched_external_benchmark`: `True`

## Outputs

- `plume_extents_csv`: `/home/cj/my-pele/docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_mpi_cuda_20260805/plume_extents.csv`
- `sensor_timeseries_csv`: `/home/cj/my-pele/docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_1s_mpi_cuda_20260805/sensor_timeseries.csv`

## Limitations

- This report proves extraction capability for plume extents and point-probe time series.
- It does not by itself prove agreement with an external field-test, wind-tunnel, or literature-digitized benchmark.
