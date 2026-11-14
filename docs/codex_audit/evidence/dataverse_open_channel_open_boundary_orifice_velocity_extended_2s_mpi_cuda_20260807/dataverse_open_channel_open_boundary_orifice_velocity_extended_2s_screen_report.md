# DataverseNO Open-Channel Open-Boundary Orifice 2s MPI+CUDA Screen

- Status: `PASS-DATAVERSE-OPEN-CHANNEL-OPEN-BOUNDARY-ORIFICE-EXTENDED-2S-MPI-CUDA`
- Time end: `2.0` s
- MPI ranks: `2`
- CUDA initialized: `True`
- Plotfiles: `21`
- Sensor rows: `609`
- Retained mass ratio: `0.797244198`
- Max Y(H2): `0.0178122135`
- Downstream fraction: `0.998907675`
- Clears strict external plume blocker: `False`

## Limitations

- This is a 2s MPI+CUDA stability and agreement-screen window, not a production-duration match to the external plume-shape record.
- Open/open boundaries allow H2 to leave the domain; mass_ratio_final is retained in-domain mass divided by injected mass.
- This evidence strengthens the external-reference path but does not clear the strict external plume-shape blocker.

## Evidence

- `run_log`: `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_mpi_cuda_20260807/run.log`
- `validation_open_boundary_2s_log`: `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_mpi_cuda_20260807/validation_open_boundary_2s.log`
- `plume_observation_report`: `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_mpi_cuda_20260807/h2_plume_observation_report.json`
- `agreement_attempt_status`: `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_mpi_cuda_20260807/agreement_attempt_status.json`
- `input_deck`: `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_mpi_cuda_20260807/input.dataverse_open_channel_h2_scout_3d`
- `dataverse_sensor_solver_coords`: `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_mpi_cuda_20260807/sensors.dataverse_open_channel_solver_coords.json`
- `status_txt`: `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_mpi_cuda_20260807/status.txt`
- `run_status`: `docs/codex_audit/evidence/dataverse_open_channel_open_boundary_orifice_velocity_extended_2s_mpi_cuda_20260807/run.status`
