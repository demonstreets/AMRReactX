# Engineering H2 Plume Observation Extraction

Status: `PASS-H2-PLUME-OBSERVATION`
Run directory: `/home/cj/my-pele/docs/codex_audit/evidence/dataverse_open_channel_cfd_agreement_window_mpi_cuda_20260803/run`
Sensor basis: `DataverseNO open-channel H2 sensors transformed for the h2_leak_3d x-downstream solver convention`
Sensor sampling: `nearest`

## Summary

- `time_start`: `0.0`
- `time_end`: `1.9999999999998905`
- `max_cloud_volume`: `0.13000000000000006`
- `max_peak_X`: `0.9996067785182285`
- `max_flammable_x`: `0.9249999999999999`
- `max_flammable_z`: `0.775`
- `extent_rows`: `9`
- `sensor_rows`: `261`
- `plume_extents_available`: `True`
- `sensor_timeseries_available`: `True`
- `all_sensors_inside_domain`: `True`
- `max_sensor_sample_distance`: `0.043301270189221946`
- `max_nearest_cell_distance`: `0.043301270189221946`
- `case_matched_external_benchmark`: `True`

## Outputs

- `plume_extents_csv`: `/home/cj/my-pele/docs/codex_audit/evidence/dataverse_open_channel_cfd_agreement_window_mpi_cuda_20260803/plume_extents.csv`
- `sensor_timeseries_csv`: `/home/cj/my-pele/docs/codex_audit/evidence/dataverse_open_channel_cfd_agreement_window_mpi_cuda_20260803/sensor_timeseries.csv`

## Limitations

- This report proves extraction capability for plume extents and point-probe time series.
- It does not by itself prove agreement with an external field-test, wind-tunnel, or literature-digitized benchmark.
