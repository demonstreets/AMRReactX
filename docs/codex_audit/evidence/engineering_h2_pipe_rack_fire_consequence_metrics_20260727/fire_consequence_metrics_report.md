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

- Flammable-cloud H2 mass: `2.02496001e-04 kg`
- Flammable-cloud volume: `2.09796873e-02 m^3`
- Inferred source heat release: `2.40000452e+05 W`
- Flammable-cloud energy: `2.42995201e+04 J`
- TNT-equivalent screening mass: `1.74231741e-04 kg`
- Max screening radiation flux: `2.86479437e+03 W/m^2`
- Max screening overpressure: `2.23386703e-01 kPa`

## Radiation

| Distance m | Source-limited W/m2 | Cloud-average W/m2 |
| ---: | ---: | ---: |
| 1 | 2.86479437e+03 | 2.90054156e+02 |
| 3 | 3.18310486e+02 | 3.22282395e+01 |
| 5 | 1.14591775e+02 | 1.16021662e+01 |
| 10 | 2.86479437e+01 | 2.90054156e+00 |
| 20 | 7.16198593e+00 | 7.25135389e-01 |

## Overpressure

| Distance m | Scaled distance | Screening peak kPa |
| ---: | ---: | ---: |
| 1 | 1.79043094e+01 | 2.23386703e-01 |
| 3 | 5.37129283e+01 | 1.02378516e-02 |
| 5 | 8.95215471e+01 | 2.31071031e-03 |
| 10 | 1.79043094e+02 | 2.98592593e-04 |
| 20 | 3.58086188e+02 | 3.79519765e-05 |

## Limitations

- Screening-only consequence metrics derived from smoke/scout CFD evidence.
- Radiation uses an isotropic point-source fraction and does not model flame geometry, soot, view factors, terrain, or shielding.
- Overpressure uses a TNT-equivalent screening metric and is not a calibrated deflagration or congestion model.
- This report does not replace site-specific safety engineering, regulatory compliance, or validated consequence tools.
