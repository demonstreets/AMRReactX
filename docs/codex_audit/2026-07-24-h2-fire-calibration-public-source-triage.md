# 2026-07-24 H2 Fire Calibration Public Source Triage

Scope: engineering H2 production blocker
`fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`.

Changes:

- Added `tools/write_engineering_h2_fire_calibration_public_source_triage_report.py`.
- Added maintained evidence root:
  `docs/codex_audit/evidence/engineering_h2_fire_calibration_public_source_triage_20260724/`.
- Integrated the triage report into
  `tools/write_engineering_h2_fire_calibration_package_report.py`.
- Integrated the triage report into
  `tools/verify_engineering_h2_production_evidence.sh`.
- Updated `tools/write_engineering_h2_production_evidence_verification_report.py`
  to schema 15 so the production evidence pack hashes the fire-calibration
  public-source triage report.

Current intent:

- Separate public source discovery from actual calibrated agreement.
- Record radiation candidate sources for H2 jet fire heat-flux calibration.
- Record overpressure candidate sources for H2 vented-deflagration calibration.
- Keep the local required artifacts explicit: `calibration_metadata.json`,
  `radiation_metrics.csv`, `overpressure_metrics.csv`, and a calibrated fire
  consequence report.

What this does not prove:

- It does not digitize heat-flux or pressure measurements.
- It does not ingest calibration CSV files.
- It does not clear the fire-consequence production blocker.
