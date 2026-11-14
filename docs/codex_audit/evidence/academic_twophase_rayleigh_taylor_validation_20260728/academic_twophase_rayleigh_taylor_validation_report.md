# Academic Two-Phase Rayleigh-Taylor Validation

Status: `PASS-ACADEMIC-TWOPHASE-RAYLEIGH-TAYLOR-VALIDATION`
Scope: `multi-resolution VOF two-phase Rayleigh-Taylor instability growth, boundedness, momentum response, and conserved-mass validation`

## Summary

- `case_count`: `3`
- `resolutions`: `[[32, 64, 1], [64, 128, 1], [96, 192, 1]]`
- `mode`: `2`
- `time`: `0.016`
- `growth_rate_spread`: `0.515666`
- `growth_rate_spread_limit`: `0.6`
- `min_growth_ratio`: `1.0855541`
- `min_growth_ratio_limit`: `1.02`
- `max_mass_rel`: `2.63164e-16`
- `max_vof_mass_rel`: `3.94746e-16`
- `mass_rtol`: `2e-05`
- `max_alpha_overshoot`: `0.0`
- `max_alpha_undershoot`: `1.58473e-84`
- `clears_acd_04_two_phase_validation_gap`: `True`
- `clears_acd_08_two_phase_interface_amr_gap`: `False`

## Cases

| Case | n_cell | Growth ratio | Growth rate | Mass rel | VOF mass rel | Alpha range |
| --- | --- | --- | --- | --- | --- | --- |
| `rt_32x64` | `[32, 64, 1]` | `1.1476832` | `8.6090837` | `0.00000000e+00` | `0.00000000e+00` | `-1.58473e-84:1` |
| `rt_64x128` | `[64, 128, 1]` | `1.1095429` | `6.4967595` | `0.00000000e+00` | `0.00000000e+00` | `-1.21106e-144:1` |
| `rt_96x192` | `[96, 192, 1]` | `1.0855541` | `5.1306571` | `2.63164000e-16` | `3.94746000e-16` | `-6.49975e-107:1` |

## Quality Gates

| Gate | Status | Evidence | Gap |
| --- | --- | --- | --- |
| `multi_resolution_rt_runs` | `PASS` | /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/case_manifest.json | none |
| `vof_mass_conservation` | `PASS` | /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/conservation_32x64.log; /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/conservation_64x128.log; /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/conservation_96x192.log | none |
| `alpha_boundedness` | `PASS` | /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/conservation_32x64.log; /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/conservation_64x128.log; /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/conservation_96x192.log | none |
| `rt_growth_trend` | `PASS` | /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/resolution_trend.log | none |
| `two_phase_interface_amr_validation` | `PARTIAL` | none | This gate uses uniform grids; two-phase interface-specific AMR validation is separate. |

## Evidence Files

- `case_manifest`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/case_manifest.json` sha256 `a29bab7f54a397c7`
- `build_log`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/build.log` sha256 `1dd1660b031e30ba`
- `resolution_trend_log`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/resolution_trend.log` sha256 `1961fcd3d0432cfe`
- `rt_32x64_input`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/run_32x64/input.codex_growth_32x64` sha256 `367f3983424a0d7d`
- `rt_32x64_run_log`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/run_32x64.log` sha256 `5830e5ddfa60da35`
- `rt_32x64_conservation_log`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/conservation_32x64.log` sha256 `f5dbc824bbd3393f`
- `rt_32x64_growth_log`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/growth_32x64.log` sha256 `844703750eedfda3`
- `rt_64x128_input`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/run_64x128/input.codex_growth_64x128` sha256 `632a0b59295772dc`
- `rt_64x128_run_log`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/run_64x128.log` sha256 `8bbdb6c6ea4bf31b`
- `rt_64x128_conservation_log`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/conservation_64x128.log` sha256 `7cff28d0415b815d`
- `rt_64x128_growth_log`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/growth_64x128.log` sha256 `d71001417d788a32`
- `rt_96x192_input`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/run_96x192/input.codex_growth_96x192` sha256 `54fb1346ae826dcd`
- `rt_96x192_run_log`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/run_96x192.log` sha256 `5ccb1c0f6f57390c`
- `rt_96x192_conservation_log`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/conservation_96x192.log` sha256 `875c2949f15a945a`
- `rt_96x192_growth_log`: `/home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728/runs/growth_96x192.log` sha256 `f68135729740d9dd`

## Limitations

- This validates VOF two-phase Rayleigh-Taylor behavior on uniform grids.
- It does not validate two-phase interface-specific AMR tagging/refinement.
- It is not a gas-liquid detonation or spray-combustion validation case.
