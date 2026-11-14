# Engineering Liquefied Release Thermal Plausibility

Status: `PASS-ENGINEERING-LIQUEFIED-RELEASE-THERMAL-PLAUSIBILITY`

## Summary

- Thermal plausibility ready: True
- Species: C3H8, CH4
- Max gas mass relative error: 0.0654634
- Total gas-source latent load J: 2.69864e+06
- Production phase-change claim allowed: False

## Cases

### lng_ch4_screening_release

- Fluid/species: LNG_CH4 / CH4
- Vaporized fraction: 0.141275
- Flash fraction from superheat: 0.0912745
- External pool-assisted fraction: 0.05
- Gas mass integral kg: 3.04643
- Gas-source latent load J: 1.55368e+06

### lpg_c3h8_screening_release

- Fluid/species: LPG_C3H8 / C3H8
- Vaporized fraction: 0.20809
- Flash fraction from superheat: 0.12809
- External pool-assisted fraction: 0.08
- Gas mass integral kg: 3.21618
- Gas-source latent load J: 1.14496e+06

## Limitations

- This report audits the thermal plausibility of generated gas-source schedules only.
- It does not validate internal tank rupture mechanics, flashing multiphase discharge, liquid-pool spread, boiling heat transfer, or ground heat transfer.
- For production liquefied-gas phase-change claims, replace the screening source with measured, process-safety, or high-fidelity external-source data and add validation evidence.
