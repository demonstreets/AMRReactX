# DataverseNO Open-Channel H2 Time-Series Index

- Status: `PASS-DATAVERSE-OPEN-CHANNEL-H2-TIMESERIES-INDEX`
- ZIP cases: `22`
- Strong plume candidates: `22`
- Flow meter counts: `{'mass flow meter 1 [g/s]': 16, 'mass flow meter 2 [g/s]': 6}`
- Sensor column counts seen: `[29]`
- Max H2 peak vol percent: `30.827625806451614`
- Ready for case selection: `True`
- Clears external plume blocker: `False`

## Recommended Validation Candidates

| File | Peak H2 vol % | Peak Sensor | LFL Sensors | Duration s | Flow Columns |
| --- | --- | --- | --- | --- | --- |
| `23_FFI_P101_T00031.zip` | `30.8276` | `20` | `25` | `378.5` | `mass flow meter 1 [g/s]` |
| `23_FFI_P101_T00011.zip` | `27.6906` | `20` | `26` | `306.08` | `mass flow meter 1 [g/s]` |
| `23_FFI_P101_T00007.zip` | `18.2866` | `20` | `24` | `271.16` | `mass flow meter 1 [g/s]` |
| `23_FFI_P101_T00042.zip` | `17.7676` | `20` | `25` | `498.08` | `mass flow meter 1 [g/s]` |
| `23_FFI_P101_T00044.zip` | `17.2236` | `20` | `22` | `487.9` | `mass flow meter 1 [g/s]` |
| `23_FFI_P101_T00008.zip` | `15.9181` | `20` | `24` | `263.47` | `mass flow meter 1 [g/s]` |
| `23_FFI_P101_T00009.zip` | `15.6196` | `22` | `24` | `264.81` | `mass flow meter 1 [g/s]` |
| `23_FFI_P101_T00030.zip` | `15.3361` | `20` | `23` | `395.12` | `mass flow meter 1 [g/s]` |

## Limitations

- This report indexes reference time-series signals and validation candidates.
- It does not provide sensor coordinates or channel/obstacle geometry mapping.
- It does not run CFD/reference agreement scoring and therefore does not clear the external plume blocker.
