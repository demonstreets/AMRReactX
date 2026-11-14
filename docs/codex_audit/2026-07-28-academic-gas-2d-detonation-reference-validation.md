# 2026-07-28 Academic Gas 2D Detonation Reference Validation

## Result

- Added and ran the 2D academic gas detonation reference-validation gate.
- Evidence status: `PASS-ACADEMIC-GAS-2D-DETONATION-REFERENCE`.
- Three 2D resolutions were run to the same physical stop time: `64x32`, `96x48`, and `128x64`.
- The medium and fine cases matched the measured front speed; the coarse case stayed within the configured engineering tolerance.

## Evidence

- `docs/codex_audit/evidence/academic_gas_2d_detonation_reference_20260728/academic_gas_2d_detonation_reference_report.json`
- `docs/codex_audit/evidence/academic_gas_2d_detonation_reference_20260728/academic_gas_2d_detonation_reference_report.md`
- `docs/codex_audit/evidence/academic_gas_2d_detonation_reference_20260728/case_manifest.json`

## Readiness Impact

- The academic gas detonation readiness gate now treats the 2D reference-validation gap as closed.
- Remaining academic gas blocking gaps are:
  - 3D detonation reference validation.
  - Detonation-front AMR validation.

## Scope Boundary

This closes the maintained 2D in-repository validation gate. It does not claim full production certification for all academic detonation cases, and it does not replace future 3D validation, AMR-front validation, or external literature/experimental benchmark comparison.
