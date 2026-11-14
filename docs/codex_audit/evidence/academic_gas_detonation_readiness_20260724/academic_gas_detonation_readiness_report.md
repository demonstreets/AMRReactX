# Academic Gas Detonation and Chemistry Readiness

Status: `PASS-ACADEMIC-GAS-DETONATION-READINESS`
Scope: `master-plan ACD-02/ACD-03 gas-phase chemistry and gas detonation readiness`

## Summary

- `ignition_status`: `PASS-SMOKE`
- `ctest_foundation_tests_present`: `['isentropic_vortex_smoke', 'pelec_weno_smoke', 'sod_shock_tube_smoke', 'weno5_smoke']`
- `ctest_foundation_tests_missing`: `[]`
- `foundation_ready`: `True`
- `short_2d_detonation_wave_validation_passed`: `True`
- `cantera_mechanism_comparison_available`: `True`
- `compiled_pelephysics_rate_kernel_equivalence_available`: `True`
- `zero_d_reference_curve_available`: `True`
- `two_d_reference_validation_available`: `True`
- `three_d_reference_validation_available`: `True`
- `detonation_front_amr_validation_available`: `True`
- `detonation_subreport_evidence_hash_counts`: `{'two_d': 10, 'three_d': 10, 'detonation_front_amr': 7}`
- `academic_gas_detonation_ready`: `True`
- `clears_acd_02`: `True`
- `clears_acd_03`: `True`
- `missing_or_partial_quality_gate_count`: `0`

## Quality Gates

| Gate | Status | Evidence | Gap |
| --- | --- | --- | --- |
| `ctest_list_present` | `PASS` | docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724/ctest_list.log | none |
| `weno_foundation_ctests_present` | `PASS` | weno5_smoke; pelec_weno_smoke | none |
| `compressible_baseline_ctests_present` | `PASS` | sod_shock_tube_smoke; isentropic_vortex_smoke | none |
| `ignition_consequence_evidence_present` | `PASS` | docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/ignition_consequence_report.json | none |
| `academic_detonation_tooling_present` | `PASS` | tools/codex_smoke_academic_detonation_wave.sh; tools/validate_detonation_wave.py; tools/codex_smoke_academic_sod_plotfile.sh; tools/validate_sod_plotfile.py; tools/codex_smoke_academic_pelec_isentropic_vortex.sh; tools/validate_pelec_isentropic_vortex.py | none |
| `short_2d_detonation_wave_validation` | `PASS` | docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724/detonation_wave_validation.log | none |
| `cantera_mechanism_comparison` | `PASS` | docs/codex_audit/evidence/academic_gas_cantera_mechanism_comparison_20260728/cantera_mechanism_comparison_report.json | none |
| `compiled_pelephysics_rate_kernel_equivalence` | `PASS` | docs/codex_audit/evidence/academic_gas_pelephysics_rate_kernel_equivalence_20260728/pelephysics_rate_kernel_equivalence_report.json | none |
| `zero_d_ignition_delay_reference_curve` | `PASS` | docs/codex_audit/evidence/academic_gas_cantera_ignition_reference_20260724/cantera_ignition_reference_report.json | none |
| `two_d_detonation_reference_validation` | `PASS` | docs/codex_audit/evidence/academic_gas_2d_detonation_reference_20260728/academic_gas_2d_detonation_reference_report.json | none |
| `three_d_detonation_reference_validation` | `PASS` | docs/codex_audit/evidence/academic_gas_3d_detonation_reference_20260728/academic_gas_3d_detonation_reference_report.json | none |
| `detonation_front_amr_validation` | `PASS` | docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/academic_gas_detonation_front_amr_validation_report.json | none |
| `detonation_subreport_evidence_hashes_verified` | `PASS` | two_d=10; three_d=10; detonation_front_amr=7 | none |

## Next Required Artifacts


## Evidence Files

- `ctest_list_log`: `docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724/ctest_list.log` sha256 `8c42b8707145526a`
- `ignition_consequence_report`: `docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/ignition_consequence_report.json` sha256 `3f1eb940bc75c59e`
- `cantera_ignition_reference_report`: `docs/codex_audit/evidence/academic_gas_cantera_ignition_reference_20260724/cantera_ignition_reference_report.json` sha256 `d97b6bf16226b426`
- `cantera_mechanism_comparison_report`: `docs/codex_audit/evidence/academic_gas_cantera_mechanism_comparison_20260728/cantera_mechanism_comparison_report.json` sha256 `e83a2e2aeeed3aaf`
- `pelephysics_rate_kernel_equivalence_report`: `docs/codex_audit/evidence/academic_gas_pelephysics_rate_kernel_equivalence_20260728/pelephysics_rate_kernel_equivalence_report.json` sha256 `5d1e56a6c32e5ba3`
- `two_d_detonation_reference_report`: `docs/codex_audit/evidence/academic_gas_2d_detonation_reference_20260728/academic_gas_2d_detonation_reference_report.json` sha256 `1b0d80ac7b404cf5`
- `three_d_detonation_reference_report`: `docs/codex_audit/evidence/academic_gas_3d_detonation_reference_20260728/academic_gas_3d_detonation_reference_report.json` sha256 `8720a61710c2a35b`
- `detonation_front_amr_validation_report`: `docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728/academic_gas_detonation_front_amr_validation_report.json` sha256 `baa219db77104759`
- `academic_detonation_wave_script`: `tools/codex_smoke_academic_detonation_wave.sh` sha256 `37cbb04928f71fec`
- `academic_detonation_wave_validator`: `tools/validate_detonation_wave.py` sha256 `ca5b631a2f1ed301`
- `academic_sod_plotfile_script`: `tools/codex_smoke_academic_sod_plotfile.sh` sha256 `fccf671e59329da6`
- `academic_sod_plotfile_validator`: `tools/validate_sod_plotfile.py` sha256 `121794311dd81aee`
- `academic_isentropic_vortex_script`: `tools/codex_smoke_academic_pelec_isentropic_vortex.sh` sha256 `ce2c76dae2902c8f`
- `academic_isentropic_vortex_validator`: `tools/validate_pelec_isentropic_vortex.py` sha256 `5c7478ebe3003808`
- `detonation_wave_validation_log`: `docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724/detonation_wave_validation.log` sha256 `cd3b7b608b8b3fa2`

## Limitations

- This report clears maintained in-repository ACD-02/ACD-03 readiness gates when all quality gates pass.
- Short smoke-scale detonation evidence, when present, is not a substitute for reference-quality 2D/3D detonation validation.
- The compiled rate-kernel evidence samples the CPU LiDryer C++ mechanism kernel; GPU bitwise source-rate equivalence remains a deeper certification task.
- The 2D detonation reference evidence is solver self-consistency/grid evidence; external literature agreement remains a deeper certification task.
- The 3D detonation reference evidence is a thin-slab ZND-style gate; external literature agreement remains a deeper certification task.
- The detonation-front AMR evidence is an in-repository validation gate; external literature agreement remains a deeper certification task.
