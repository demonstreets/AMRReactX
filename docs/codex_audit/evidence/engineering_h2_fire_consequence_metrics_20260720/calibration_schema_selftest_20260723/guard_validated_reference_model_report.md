# H2 Fire Consequence Screening Metrics

Status: `PASS-SCREENING`
Scope: `engineering_screening_not_calibrated`
Consequence model tier: `screening_metrics`
Radiation model calibrated: `False`
Overpressure model calibrated: `False`
Flame geometry model: `False`
Validated against fire experiment: `False`
Validated against blast experiment: `False`
Clears calibrated fire consequence blocker: `False`

## Summary

- Flammable-cloud H2 mass: `2.23883994e-04 kg`
- Flammable-cloud volume: `2.46582031e-02 m^3`
- Inferred source heat release: `2.40030061e+05 W`
- Flammable-cloud energy: `2.68660793e+04 J`
- TNT-equivalent screening mass: `1.92634412e-04 kg`
- Max screening radiation flux: `2.86514780e+03 W/m^2`
- Max screening overpressure: `2.44388282e-01 kPa`

## Radiation

| Distance m | Source-limited W/m2 | Cloud-average W/m2 |
| ---: | ---: | ---: |
| 1 | 2.86514780e+03 | 3.20690199e+02 |
| 3 | 3.18349756e+02 | 3.56322443e+01 |
| 5 | 1.14605912e+02 | 1.28276080e+01 |
| 10 | 2.86514780e+01 | 3.20690199e+00 |
| 20 | 7.16286951e+00 | 8.01725497e-01 |

## Overpressure

| Distance m | Scaled distance | Screening peak kPa |
| ---: | ---: | ---: |
| 1 | 1.73149819e+01 | 2.44388282e-01 |
| 3 | 5.19449458e+01 | 1.12771635e-02 |
| 5 | 8.65749097e+01 | 2.54902238e-03 |
| 10 | 1.73149819e+02 | 3.29756388e-04 |
| 20 | 3.46299639e+02 | 4.19366793e-05 |

## External Calibration Agreement

- Source type: `validated_reference_model`
- Metric count: `2`
- All metrics passed: `True`
- Clears calibrated fire consequence blocker: `False`

| Metric | Family | Simulation | Reference | Relative error | Passed |
| --- | --- | ---: | ---: | ---: | --- |
| `guard_max_radiation_flux` | `radiation` | 2.86514780e+03 | 2.86514780e+03 | 0.00000000e+00 | `True` |
| `guard_max_overpressure` | `overpressure` | 2.44388282e-01 | 2.44388282e-01 | 0.00000000e+00 | `True` |

## Limitations

- Screening-only consequence metrics derived from smoke/scout CFD evidence.
- Radiation uses an isotropic point-source fraction and does not model flame geometry, soot, view factors, terrain, or shielding.
- Overpressure uses a TNT-equivalent screening metric and is not a calibrated deflagration or congestion model.
- This report does not replace site-specific safety engineering, regulatory compliance, or validated consequence tools.
