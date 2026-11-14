# H2 Fire MDPI Radiation Screening Comparison

- Status: `QUANTIFIED-H2-FIRE-MDPI-RADIATION-SCREENING-NOT-PASSING`
- Screening comparison executed: `True`
- MDPI radiation metrics: `4`
- Screening pass/fail: `0/4`
- Strict fire blocker cleared: `False`

## Comparison

| Metric | Distance m | Reference W/m2 | Screening W/m2 | Relative error | Passed |
| --- | ---: | ---: | ---: | ---: | --- |
| `mdpi_jet_fire_1p5mm_0p6mpa_0p23m` | 0.23 | 1.36050000e+03 | 5.41615842e+04 | 3.88100582e+01 | `False` |
| `mdpi_jet_fire_1p5mm_0p6mpa_0p50m` | 0.5 | 4.12100000e+02 | 1.14605912e+04 | 2.68102189e+01 | `False` |
| `mdpi_jet_fire_max_1p2mm_0p23m` | 0.23 | 9.52800000e+02 | 5.41615842e+04 | 5.58446517e+01 | `False` |
| `mdpi_jet_fire_max_2p0mm_0p23m` | 0.23 | 3.37810000e+03 | 5.41615842e+04 | 1.50331500e+01 | `False` |

## Limitations

- This uses a screening point-source flux, not a resolved flame radiation model.
- The current engineering H2 scenario is not case-aligned to each MDPI nozzle diameter and pressure.
- This report quantifies the current gap and intentionally does not clear strict fire calibration credit.
