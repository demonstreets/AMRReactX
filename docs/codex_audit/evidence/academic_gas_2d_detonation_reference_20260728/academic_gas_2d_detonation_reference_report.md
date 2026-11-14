# Academic Gas 2D Detonation Reference Validation

Status: `PASS-ACADEMIC-GAS-2D-DETONATION-REFERENCE`
Scope: `multi-resolution PeleC detonation_2D wave-speed, conservation, species-closure, and chemistry-product validation`

## Summary

- `case_count`: `3`
- `resolutions`: `[[64, 32, 1], [96, 48, 1], [128, 64, 1]]`
- `front_speeds_m_per_s`: `[2893518.52, 3472222.22, 3472222.22]`
- `speed_rel_spread`: `0.1764705871590312`
- `medium_fine_speed_rel_diff`: `0.0`
- `max_speed_rel_spread_limit`: `0.35`
- `max_medium_fine_speed_rel_diff_limit`: `0.25`
- `max_mass_rel`: `2.78862926e-16`
- `max_species_closure_rel`: `9.42117686e-05`
- `min_front_shift_cells`: `5.0`
- `clears_two_d_detonation_reference_validation_gap`: `True`
- `clears_external_literature_detonation_benchmark`: `False`
- `clears_three_d_detonation_reference_validation_gap`: `False`
- `clears_detonation_front_amr_validation_gap`: `False`

## Cases

| Case | n_cell | front speed | speed shift cells | mass rel | species closure |
| --- | --- | --- | --- | --- | --- |
| `coarse_64x32` | `[64, 32, 1]` | `2.89351852e+06` | `5.000` | `2.789e-16` | `9.404e-05` |
| `medium_96x48` | `[96, 48, 1]` | `3.47222222e+06` | `9.000` | `0.000e+00` | `9.421e-05` |
| `fine_128x64` | `[128, 64, 1]` | `3.47222222e+06` | `12.000` | `0.000e+00` | `9.300e-05` |

## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `multi_resolution_2d_runs` | `PASS` | none |
| `plotfile_physics_validation` | `PASS` | none |
| `front_speed_grid_consistency` | `PASS` | none |
| `mass_and_species_closure` | `PASS` | none |
| `external_literature_reference` | `PARTIAL` | This is a self-consistency and conservation reference gate; no external experimental or literature detonation benchmark is attached. |

## Limitations

- This clears the maintained 2D detonation readiness gate using multi-resolution solver evidence.
- It does not by itself clear 3D detonation validation or detonation-front AMR validation.
- External literature/experimental detonation agreement remains a deeper academic-certification task.
