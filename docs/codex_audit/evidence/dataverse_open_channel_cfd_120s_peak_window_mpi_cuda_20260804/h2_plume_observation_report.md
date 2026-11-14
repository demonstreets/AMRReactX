# Engineering H2 Plume Observation Extraction

Status: `PASS-H2-PLUME-OBSERVATION`
Run directory: `/home/cj/my-pele/docs/codex_audit/evidence/dataverse_open_channel_cfd_120s_peak_window_mpi_cuda_20260804/run`
Sensor basis: `DataverseNO open-channel H2 sensors transformed for the h2_leak_3d x-downstream solver convention`
Sensor sampling: `nearest`

## Summary

- `time_start`: `0.0`
- `time_end`: `119.99999999999326`
- `max_cloud_volume`: `3.9617500000000017`
- `max_peak_X`: `0.997278812613899`
- `max_flammable_x`: `5.624999999999999`
- `max_flammable_z`: `0.775`
- `extent_rows`: `13`
- `sensor_rows`: `377`
- `plume_extents_available`: `True`
- `sensor_timeseries_available`: `True`
- `all_sensors_inside_domain`: `True`
- `max_sensor_sample_distance`: `0.043301270189221946`
- `max_nearest_cell_distance`: `0.043301270189221946`
- `case_matched_external_benchmark`: `True`

## Outputs

- `plume_extents_csv`: `/home/cj/my-pele/docs/codex_audit/evidence/dataverse_open_channel_cfd_120s_peak_window_mpi_cuda_20260804/plume_extents.csv`
- `sensor_timeseries_csv`: `/home/cj/my-pele/docs/codex_audit/evidence/dataverse_open_channel_cfd_120s_peak_window_mpi_cuda_20260804/sensor_timeseries.csv`

## Limitations

- This report proves extraction capability for plume extents and point-probe time series.
- It does not by itself prove agreement with an external field-test, wind-tunnel, or literature-digitized benchmark.
