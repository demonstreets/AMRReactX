# 2026-07-28 Academic Gas Detonation-Front AMR Validation

## Scope

Closed the remaining academic gas detonation readiness gap for detonation-front AMR tagging/refinement validation.

## Implementation

- Added `tools/validate_academic_gas_detonation_front_amr.py`.
- Added `tools/write_academic_gas_detonation_front_amr_validation_report.py`.
- Added `tools/codex_run_academic_gas_detonation_front_amr_validation.sh`.
- Updated `tools/write_academic_gas_detonation_readiness_report.py` to consume the AMR report and allow `PASS-ACADEMIC-GAS-DETONATION-READINESS`.
- Updated `tools/verify_engineering_h2_production_evidence.sh` to verify the AMR report.
- Updated master-plan traceability so ACD-03 is PASS while ACD-08 remains PARTIAL for two-phase interface-specific AMR.

## Run Evidence

Evidence root:

`docs/codex_audit/evidence/academic_gas_detonation_front_amr_validation_20260728`

Cases:

- `amr_96x4x4_l1`: 2 MPI ranks, 3D thin-slab ZND-style detonation, AMR max level 1.
- `uniform_fine_192x8x8`: 2 MPI ranks, uniform fine reference.

Key metrics:

- AMR final finest level: 1.
- AMR front refined: true.
- AMR refined cell fraction: 0.3125.
- AMR/uniform front-speed relative difference: 0.0.
- AMR front speed: 9.375e4.
- Uniform fine front speed: 9.375e4.
- AMR mass relative drift: 2.74884505e-13.
- Uniform mass relative drift: 2.31620533e-13.
- Species closure error: <= 2.22044605e-16.

## Verification

Commands run:

- `tools/codex_run_academic_gas_detonation_front_amr_validation.sh`
- `python3 tools/write_academic_gas_detonation_readiness_report.py`
- `python3 tools/write_engineering_h2_master_plan_traceability_report.py`
- `bash tools/verify_engineering_h2_production_evidence.sh`

Final result:

- `academic_gas_detonation_front_amr_validation`: PASS.
- `academic_gas_detonation_readiness`: `PASS-ACADEMIC-GAS-DETONATION-READINESS`, missing_or_partial=0.
- Unified verifier: PASS.
- CTest: 22/22 passed.

## Remaining Academic Notes

- ACD-03 gas detonation readiness is now cleared by in-repository evidence.
- ACD-02 remains partial because full compiled PelePhysics C++ rate-kernel equivalence against Cantera is not yet evidenced.
- ACD-08 remains partial because two-phase interface-specific AMR validation is not yet evidenced.
- External literature/experiment detonation agreement remains a deeper certification task beyond this in-repository readiness gate.
