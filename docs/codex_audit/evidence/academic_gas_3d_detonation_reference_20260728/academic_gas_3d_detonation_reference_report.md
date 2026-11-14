# Academic Gas 3D Detonation Reference Validation

Status: `PASS-ACADEMIC-GAS-3D-DETONATION-REFERENCE`
Scope: `multi-resolution 3D PeleC ZND-style detonation slab wave-motion, conservation, species-closure, and chemistry-product validation`

## Summary

- `case_count`: `3`
- `resolutions`: `[[96, 4, 4], [128, 4, 4], [160, 4, 4]]`
- `front_speeds_m_per_s`: `[83333.3333, 93750.0, 87500.0]`
- `speed_rel_spread`: `0.11811023661330523`
- `medium_fine_speed_rel_diff`: `0.07142857142857142`
- `max_speed_rel_spread_limit`: `0.35`
- `max_medium_fine_speed_rel_diff_limit`: `0.25`
- `max_mass_rel`: `1.13014782e-12`
- `max_species_closure_rel`: `2.22044605e-16`
- `min_front_shift_cells`: `4.0`
- `clears_three_d_detonation_reference_validation_gap`: `True`
- `clears_detonation_front_amr_validation_gap`: `False`
- `clears_external_literature_detonation_benchmark`: `False`

## Cases

| Case | n_cell | front speed | shift cells | mass rel | species closure |
| --- | --- | --- | --- | --- | --- |
| `coarse_96x4x4` | `[96, 4, 4]` | `8.33333333e+04` | `4.000` | `1.130e-12` | `2.220e-16` |
| `medium_128x4x4` | `[128, 4, 4]` | `9.37500000e+04` | `6.000` | `6.962e-13` | `2.220e-16` |
| `fine_160x4x4` | `[160, 4, 4]` | `8.75000000e+04` | `7.000` | `4.177e-13` | `2.220e-16` |

## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `multi_resolution_3d_runs` | `PASS` | none |
| `plotfile_physics_validation` | `PASS` | none |
| `front_speed_grid_consistency` | `PASS` | none |
| `mass_and_species_closure` | `PASS` | none |
| `detonation_front_amr_validation` | `PARTIAL` | This gate uses uniform 3D grids; AMR front tagging/refinement efficiency is validated separately. |
| `external_literature_reference` | `PARTIAL` | This is an in-repository ZND-style reference gate; no external literature detonation benchmark is attached. |

## Limitations

- This clears the maintained 3D detonation readiness gate using multi-resolution solver evidence.
- The case is a thin 3D ZND-style slab, not a fully 3D cellular detonation benchmark.
- It does not by itself clear detonation-front AMR validation or external literature agreement.
