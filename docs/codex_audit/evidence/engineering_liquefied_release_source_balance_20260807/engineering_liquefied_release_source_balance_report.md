# Engineering Liquefied-Release Source Balance Report

- Status: `PASS-ENGINEERING-LIQUEFIED-RELEASE-SOURCE-BALANCE`
- Case count: `2`
- Species: `C3H8, CH4`
- Total gas mass integral kg: `6.262612621214`
- Max inventory mass relative error: `0.06546339683315126`
- Mapping schedule matches CSV: `True`
- Generated input matches mapping: `True`
- CUDA smoke: `PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE`
- Internal liquid phase-change CFD: `False`
- Pool spread evaporation CFD: `False`
- Flashing discharge CFD: `False`
- Production phase-change claim allowed: `False`
- Overclaim guard active: `True`

## Cases

### lng_ch4_screening_release

- Species: `CH4`
- Points: `9`
- Time span s: `0.0 .. 8.0`
- Gas mass integral kg: `3.0464336073549996`
- Expected gas mass kg: `3.259833373065967`
- Inventory relative error: `0.06546339683315126`
- Jet speed max m/s: `42.8333665947`

### lpg_c3h8_screening_release

- Species: `C3H8`
- Points: `9`
- Time span s: `0.0 .. 8.0`
- Gas mass integral kg: `3.2161790138590005`
- Expected gas mass kg: `3.436995494792542`
- Inventory relative error: `0.06424695093959386`
- Jet speed max m/s: `17.2034944549`
