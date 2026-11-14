# Academic Gas Detonation-Front AMR Validation

Status: `PASS-ACADEMIC-GAS-DETONATION-FRONT-AMR-VALIDATION`
Scope: `3D PeleC ZND-style detonation AMR tagging, front refinement, conservation, and uniform-fine consistency gate`

## Summary

- `case_count`: `2`
- `amr_case`: `amr_96x4x4_l1`
- `uniform_fine_reference_case`: `uniform_fine_192x8x8`
- `amr_front_speed_m_per_s`: `93750.0`
- `uniform_fine_front_speed_m_per_s`: `93750.0`
- `amr_uniform_speed_rel_diff`: `0.0`
- `max_amr_uniform_speed_rel_diff_limit`: `0.3`
- `amr_refined_cell_fraction`: `0.3125`
- `max_refined_cell_fraction_limit`: `0.85`
- `refined_cell_savings_fraction_vs_full_level1_uniform`: `0.6875`
- `max_mass_rel`: `2.74884505e-13`
- `max_species_closure_rel`: `2.22044605e-16`
- `min_front_shift_cells`: `9.0`
- `clears_detonation_front_amr_validation_gap`: `True`
- `clears_external_literature_detonation_benchmark`: `False`

## Cases

| Case | Role | AMR | n_cell | Front speed | Finest level | Refined fraction | Mass rel |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `amr_96x4x4_l1` | `amr_front` | `True` | `[96, 4, 4]` | `9.37500000e+04` | `1` | `3.12500000e-01` | `2.74884505e-13` |
| `uniform_fine_192x8x8` | `uniform_fine_reference` | `False` | `[192, 8, 8]` | `9.37500000e+04` | `0` | `0.00000000e+00` | `2.31620533e-13` |

## Quality Gates

| Gate | Status | Evidence | Gap |
| --- | --- | --- | --- |
| `amr_refined_level_created` | `PASS` | docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/runs/amr_96x4x4_l1/validation.log | none |
| `detonation_front_refined` | `PASS` | docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/runs/amr_96x4x4_l1/validation.log | none |
| `amr_refinement_efficiency` | `PASS` | docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/runs/amr_96x4x4_l1/validation.log | none |
| `amr_uniform_front_speed_consistency` | `PASS` | docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/case_manifest.json | none |
| `mass_and_species_closure` | `PASS` | docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/runs/amr_96x4x4_l1/validation.log; docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/runs/uniform_fine_192x8x8/validation.log | none |
| `external_literature_reference` | `PARTIAL` | none | This is an in-repository AMR gate; no external literature detonation AMR benchmark is attached. |

## Evidence Files

- `case_manifest`: `docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/case_manifest.json` sha256 `b1b94b3f1190f66c`
- `amr_96x4x4_l1_input`: `docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/runs/amr_96x4x4_l1/inputs` sha256 `489a4c594f651b02`
- `amr_96x4x4_l1_run_log`: `docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/runs/amr_96x4x4_l1/run.log` sha256 `b8bbac74c99f2c95`
- `amr_96x4x4_l1_validation_log`: `docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/runs/amr_96x4x4_l1/validation.log` sha256 `a82662c372658f13`
- `uniform_fine_192x8x8_input`: `docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/runs/uniform_fine_192x8x8/inputs` sha256 `600e1b18d810c63a`
- `uniform_fine_192x8x8_run_log`: `docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/runs/uniform_fine_192x8x8/run.log` sha256 `0f71000d5b71166b`
- `uniform_fine_192x8x8_validation_log`: `docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/runs/uniform_fine_192x8x8/validation.log` sha256 `b4b91c21e4c3092b`

## Limitations

- This clears the maintained detonation-front AMR readiness gate using solver-generated 3D evidence.
- The AMR comparison is against an in-repository uniform-fine reference, not an external experiment.
- The case is a thin 3D ZND-style slab and does not represent full cellular detonation morphology.
