# 2026-07-28 Academic Gas 3D Detonation Reference Validation

## Result

- Added and ran the maintained 3D academic gas detonation reference-validation gate.
- Evidence status: `PASS-ACADEMIC-GAS-3D-DETONATION-REFERENCE`.
- Three 3D thin-slab ZND-style resolutions were run with CPU/MPI:
  - `96x4x4`
  - `128x4x4`
  - `160x4x4`

## Evidence

- `docs/codex_audit/evidence/academic_gas_3d_detonation_reference_20260728/academic_gas_3d_detonation_reference_report.json`
- `docs/codex_audit/evidence/academic_gas_3d_detonation_reference_20260728/academic_gas_3d_detonation_reference_report.md`
- `docs/codex_audit/evidence/academic_gas_3d_detonation_reference_20260728/case_manifest.json`
- `tools/validate_academic_gas_3d_znd.py`
- `tools/codex_run_academic_gas_3d_detonation_reference.sh`

## Readiness Impact

- The academic gas detonation readiness gate now treats the 3D detonation reference-validation gap as closed.
- The remaining academic gas blocking gap is detonation-front AMR tagging/refinement efficiency validation.

## Scope Boundary

This is a maintained 3D ZND-style thin-slab solver reference gate. It proves stable 3D execution, wave motion, chemistry/species evolution, total-mass conservation, and mass-fraction closure for the in-repository gas detonation path. It does not claim external literature agreement, fully 3D cellular detonation certification, or detonation-front AMR validation.
