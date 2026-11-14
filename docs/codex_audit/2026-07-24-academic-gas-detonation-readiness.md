# 2026-07-24 Academic Gas Detonation Readiness Gate

Scope: master-plan ACD-02 and ACD-03, after the engineering H2 production
chain was prioritized and the remaining production blockers were narrowed to
external reference data, real CAD cleanup, and calibrated fire metrics.

Changes:

- Added `tools/write_academic_gas_detonation_readiness_report.py`.
- Added a maintained evidence root:
  `docs/codex_audit/evidence/academic_gas_detonation_readiness_20260724/`.
- Integrated the readiness report into
  `tools/verify_engineering_h2_production_evidence.sh`.
- Updated the production evidence verification report to schema 13 so it records
  academic gas readiness status without changing engineering production scores.
- Updated master-plan traceability so ACD-02 and ACD-03 cite the new readiness
  gate while remaining `PARTIAL`.

Current intent:

- Prove that the maintained gas-phase numerical foundation is visible in the
  verification chain: WENO, PeleC WENO integration, Sod shock tube, isentropic
  vortex, H2 ignition evidence, and academic detonation tooling.
- Optionally archive a short 2D detonation-wave validation log when
  `tools/codex_smoke_academic_detonation_wave.sh` is run.
- Keep ACD-02 and ACD-03 honest: the gate does not clear either requirement
  until Cantera mechanism comparison, 0D ignition-delay reference curves,
  reference-quality 2D/3D detonation validation, and detonation-front AMR
  validation exist.

What this does not prove:

- It does not prove production-ready large-scale H2 storage/pipeline leakage.
- It does not clear real-CAD, external plume-shape, or calibrated fire blockers.
- It does not prove full academic 2D/3D detonation validation unless the
  missing reference-quality artifacts are added later.
