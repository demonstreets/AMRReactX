# Engineering Liquefied Release Vaporization Source Model

- Status: `PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL`
- LNG CH4 screening release source ready: `True`
- LPG C3H8 screening release source ready: `True`
- Outputs external vaporization CSV: `True`
- Outputs PeleLMeX fixed-mass-flow schedule input: `True`
- CFD solves liquid phase change: `False`
- CFD solves flashing discharge: `False`
- CFD solves pool spread evaporation: `False`
- Claim level: `screening_external_gas_source_generator_not_internal_liquid_solver`

## Cases

- `lng_ch4_screening_release`: species `CH4`, max gas mdot `0.590748` kg/s, vaporized fraction `0.141275`
- `lpg_c3h8_screening_release`: species `C3H8`, max gas mdot `0.619441` kg/s, vaporized fraction `0.20809`

## Limitations

- This evidence adds a reproducible engineering source generator upstream of the existing gas-source bridge.
- It does not implement internal tank rupture mechanics, flashing two-phase discharge, liquid-pool spread, boiling, or ground heat-transfer closure inside PeleLMeX.
- For production consequence work, replace the screening schedule with measured data or a validated process-safety release model when available.
