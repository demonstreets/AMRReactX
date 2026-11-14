# DataverseNO Open-Channel H2 Agreement Contract

- Status: `PASS-DATAVERSE-OPEN-CHANNEL-H2-AGREEMENT-CONTRACT`
- Mode: `selftest_reference_identity`
- Selected case: `23_FFI_P101_T00031.zip` / `test-08-1`
- Agreement sensors: `29`
- LFL sensors: `25`
- Peak checks: `29/29`
- NRMSE checks: `29/29`
- Arrival checks passed: `29`
- Ready for CFD/reference scoring: `True`
- Production agreement completed: `False`
- Clears external plume blocker: `False`

## Simulation Input Contract

- Required columns: `['time', 'sensor_id', 'X(H2)']`
- Method: `linear interpolation of simulation X(H2) onto reference sensor times`

## Limitations

- Default mode is a reference-identity selftest that proves the scorer contract and thresholds only.
- The strict external plume blocker remains open until a real CFD sensor-sampling CSV is supplied and scored in production mode.
- Exact Dataverse obstacle/component geometry bounds are still needed before full geometry mesh parity can be claimed.
