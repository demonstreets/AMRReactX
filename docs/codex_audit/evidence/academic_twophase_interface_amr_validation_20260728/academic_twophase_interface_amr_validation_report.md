# Academic Two-Phase Interface AMR Validation

Status: `PASS-ACADEMIC-TWOPHASE-INTERFACE-AMR-VALIDATION`
Scope: `Rayleigh-Taylor VOF interface-specific AMR tagging/refinement, conservation, boundedness, and uniform-fine consistency gate`

## Summary

- `case_count`: `2`
- `amr_case`: `amr_64x128_l1`
- `uniform_reference_case`: `uniform_fine_128x256`
- `interface_refined_fraction`: `1.0`
- `min_interface_refined_fraction`: `0.55`
- `amr_refined_cell_fraction`: `0.5`
- `max_refined_cell_fraction_limit`: `0.9`
- `refined_cell_savings_fraction_vs_full_level1_uniform`: `0.5`
- `amr_uniform_growth_rate_rel_diff`: `0.1944027065372531`
- `amr_uniform_growth_ratio_rel_diff`: `0.03468452754397695`
- `max_growth_rate_rel_diff_limit`: `0.55`
- `min_growth_ratio`: `1.0253621`
- `min_growth_ratio_limit`: `1.02`
- `max_mass_rel`: `1.4803e-16`
- `max_vof_mass_rel`: `2.22045e-16`
- `mass_rtol`: `2e-05`
- `clears_acd_08_two_phase_interface_amr_gap`: `True`

## Cases

| Case | Role | AMR | n_cell | Growth ratio | Growth rate | Interface refined | Refined fraction |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `amr_64x128_l1` | `amr_interface` | `True` | `[64, 128, 1]` | `1.0609263` | `6.7403544` | `1.0` | `0.5` |
| `uniform_fine_128x256` | `uniform_fine_reference` | `False` | `[128, 256, 1]` | `1.0253621` | `5.6432846` | `` | `` |

## Quality Gates

| Gate | Status | Evidence | Gap |
| --- | --- | --- | --- |
| `amr_refined_level_created` | `PASS` | /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/runs/interface_amr_amr_64x128_l1.log | none |
| `two_phase_interface_refined` | `PASS` | /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/runs/interface_amr_amr_64x128_l1.log | none |
| `amr_refinement_efficiency` | `PASS` | /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/runs/interface_amr_amr_64x128_l1.log | none |
| `vof_mass_conservation` | `PASS` | /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/runs/conservation_amr_64x128_l1.log; /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/runs/conservation_uniform_fine_128x256.log | none |
| `alpha_boundedness` | `PASS` | /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/runs/conservation_amr_64x128_l1.log; /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/runs/conservation_uniform_fine_128x256.log | none |
| `amr_uniform_growth_consistency` | `PASS` | /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/runs/growth_amr_64x128_l1.log; /home/cj/my-pele/docs/codex_audit/evidence/academic_twophase_interface_amr_validation_20260728/runs/growth_uniform_fine_128x256.log | none |

## Limitations

- This validates two-phase interface AMR on the maintained Rayleigh-Taylor case.
- The maintained gate includes a buffered AMR run that advances beyond the step-3000 regrid; unbuffered exploratory AMR runs remain a known coarse-fine-boundary instability mode.
- It is not a gas-liquid detonation, spray-combustion, or external literature benchmark.
