# 2026-07-28 Academic Gas PelePhysics Rate-Kernel Equivalence

## Scope

Closed the ACD-02 compiled PelePhysics LiDryer rate-kernel evidence gap for gas-phase chemistry readiness.

## Implementation

- Added `tools/academic_gas_pelephysics_lidryer_kernel_probe.cpp`.
- Added `tools/codex_run_academic_gas_pelephysics_rate_kernel_equivalence.sh`.
- Added `tools/write_academic_gas_pelephysics_rate_kernel_equivalence_report.py`.
- Updated `tools/write_academic_gas_detonation_readiness_report.py` so the compiled rate-kernel equivalence gate clears ACD-02.
- Updated `tools/verify_engineering_h2_production_evidence.sh` to verify the new report.
- Updated master-plan traceability so ACD-02 is PASS.

## Evidence

Evidence root:

`docs/codex_audit/evidence/academic_gas_pelephysics_rate_kernel_equivalence_20260728`

The C++ probe directly compiles PelePhysics `LiDryer/mechanism.H` and `mechanism.cpp`, evaluates 12 lean/stoichiometric/rich H2-air states at 1 atm and 5 atm, and writes:

`pelephysics_lidryer_kernel_probe.csv`

The Python report loads the same PelePhysics `mechanism.yaml` with Cantera and compares:

- density after cgs-to-SI conversion,
- `CKCPBS` mass heat capacity after erg/g/K-to-J/kg/K conversion,
- all species source terms after Cantera kmol/m^3/s-to-mol/cm^3/s conversion,
- mass-fraction consistency from the compiled `CKXTY` path.

Key metrics:

- cases: 12.
- active species-rate comparisons: 60.
- max density relative error: 4.0207758384738836e-16.
- max cp relative error: 2.948307268252305e-15.
- max mass-fraction relative error: 2.776289173751924e-16.
- max active source-term relative error: 2.5923446507006696e-06.

## Verification

Commands run:

- `tools/codex_run_academic_gas_pelephysics_rate_kernel_equivalence.sh`
- `python3 tools/write_academic_gas_detonation_readiness_report.py`
- `python3 tools/write_engineering_h2_master_plan_traceability_report.py`
- `bash tools/verify_engineering_h2_production_evidence.sh`

Final result:

- `academic_gas_pelephysics_rate_kernel_equivalence`: PASS.
- `academic_gas_detonation_readiness`: `PASS-ACADEMIC-GAS-DETONATION-READINESS`.
- ACD-02: PASS in master-plan traceability.
- ACD-03: PASS in master-plan traceability.
- Unified verifier: PASS.
- CTest: 22/22 passed.

## Remaining Academic Notes

- This validates CPU compiled LiDryer rate kernels against Cantera for sampled homogeneous states.
- GPU bitwise chemistry-kernel equivalence remains a deeper certification task.
- External literature/experiment detonation agreement remains beyond this in-repository readiness gate.
- Two-phase/interface AMR and gas-liquid detonation remain later academic-scene work.
