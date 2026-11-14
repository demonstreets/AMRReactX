# H2 Fire EXP002 Pressure CFD Proxy

- Status: `PASS-H2-FIRE-EXP002-PRESSURE-CFD-PROXY`
- avg_pressure extracted: `True`
- Plotfiles per run: `13`
- CPU/GPU peak-pressure proxy relative diff: `5.89654836e-04`
- Case-aligned EXP002 pressure agreement: `False`
- Strict fire blocker cleared: `False`

## Run Proxies

| Run | Peak plotfile | Peak time s | Peak abs pressure proxy Pa | Final abs pressure proxy Pa |
| --- | --- | ---: | ---: | ---: |
| `single_cuda` | `plt00030` | 3.00000000e-07 | 8.52271434e+10 | 3.58984116e+08 |
| `cpu_mpi` | `plt00030` | 3.00000000e-07 | 8.51768888e+10 | 3.81000505e+08 |

## Limitations

- avg_pressure is a pressure-like solver field and may be signed; it is not a direct experimental overpressure sensor.
- No EXP002 sensor positions or arrival-time waveforms are mapped in this report.
- The delayed-ignition smoke window is not the full EXP002 release and ignition timeline.
