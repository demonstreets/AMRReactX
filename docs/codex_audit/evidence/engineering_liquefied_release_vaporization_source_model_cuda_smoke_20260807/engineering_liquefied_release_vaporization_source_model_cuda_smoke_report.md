# Engineering Liquefied Release Source Model CUDA Smoke

- Status: `PASS-ENGINEERING-LIQUEFIED-RELEASE-VAPORIZATION-SOURCE-MODEL-CUDA-SMOKE`
- CUDA smoke ready: `True`
- LNG CH4 generated input CUDA smoke passed: `True`
- LPG C3H8 generated input CUDA smoke passed: `True`
- CFD solves liquid phase change: `False`

## Cases

- `lng_ch4`: species `CH4`, schedule lines `7`, mdot range `0.5907484347`-`0.5907484605`
- `lpg_c3h8`: species `C3H8`, schedule lines `7`, mdot range `0.61944134`-`0.6194413426`

## Limitations

- This is a short CUDA smoke test of generated gas-source inputs, not a production-duration liquid-release validation.
- It confirms PeleLMeX can read and advance the generated CH4/LNG-surrogate and C3H8/LPG-surrogate fixed-mass-flow schedules with STL obstacles on CUDA.
- It does not implement internal flashing discharge, liquid-pool spread, or pool evaporation physics.
