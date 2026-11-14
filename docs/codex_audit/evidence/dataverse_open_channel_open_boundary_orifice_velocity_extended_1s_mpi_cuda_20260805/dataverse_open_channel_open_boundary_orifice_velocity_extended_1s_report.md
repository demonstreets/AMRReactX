# DataverseNO Open-Channel H2 CFD Scout

- Status: `PASS-DATAVERSE-OPEN-CHANNEL-H2-CFD-SCOUT-MPI-CUDA`
- MPI ranks: `2`
- CUDA initialized: `True`
- Plotfiles: `11`
- Sensors: `29`
- Sensor rows: `319`
- Final mass ratio: `1.0`
- Max Y(H2): `0.0177280151`
- Agreement attempt: `failed_expected_for_short_scout`
- Ready for longer Dataverse CFD campaign: `True`
- Clears external plume blocker: `False`

## Limitations

- This is a short MPI+CUDA CFD scout with Dataverse channel dimensions and transformed sensor coordinates.
- It proves run stability and sensor sampling, not long-duration agreement with the 378.5 s experimental record.
- Exact internal obstacle/component bounds are still not encoded, so full geometry parity is not claimed.
