# 2026-07-24 Academic Gas Cantera Ignition Reference

Scope: master-plan ACD-02, after the academic gas detonation readiness gate
identified that no maintained multi-condition 0D Cantera ignition-delay
reference curve was attached.

Changes:

- Added `tools/write_academic_gas_cantera_ignition_reference_report.py`.
- Added a maintained evidence root:
  `docs/codex_audit/evidence/academic_gas_cantera_ignition_reference_20260724/`.
- Integrated the Cantera reference report into
  `tools/verify_engineering_h2_production_evidence.sh`.
- Updated `tools/write_academic_gas_detonation_readiness_report.py` so the
  `zero_d_ignition_delay_reference_curve` gate becomes `PASS` only when the
  Cantera reference report verifies.
- Updated master-plan traceability wording for ACD-02 so the remaining gap is
  mechanism/species/rate equivalence against PelePhysics, not the absence of a
  0D reference curve.

Current intent:

- Generate a constant-volume H2/O2/N2 Cantera reference curve using
  `h2o2.yaml` over multiple initial temperatures.
- Verify the curve has at least three cases, positive ignition delays, strong
  temperature rise, an OH peak, and monotonic delay decrease with increasing
  initial temperature.
- Preserve a CSV with a sha256 recorded in the JSON report.

What this does not prove:

- It does not prove Pele/PelePhysics generated LiDryer mechanism equivalence to
  Cantera.
- It does not prove multidimensional detonation speed, cell size, or AMR
  front-tracking accuracy.
- It does not change engineering H2 production readiness scores.
