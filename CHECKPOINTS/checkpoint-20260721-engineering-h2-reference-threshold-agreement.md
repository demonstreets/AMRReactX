# Checkpoint: Engineering H2 Reference Threshold Agreement

Date: 2026-07-21

## What changed

- Added `tools/write_engineering_h2_reference_agreement_report.py`.
- Generated a maintained H2 reference-threshold agreement report from the 8x2 large-grid hybrid AMR scout.
- Integrated the report into the engineering production scorecard.
- Integrated the report into the one-command engineering H2 production evidence verifier and schema 6 verification report.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md`.

## Evidence

- Reference agreement report: `docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/h2_reference_agreement_report.json`, `PASS-REFERENCE-THRESHOLD-AGREEMENT`.
- Public engineering thresholds recorded in the report:
  - H2 LEL `0.04` and UEL `0.75` volume fraction from NOAA CAMEO.
  - ALOHA-style LOCs `0.024` and `0.004` volume fraction from NOAA ORR defaults of 60% and 10% of LEL.
  - NIST flammable-limit definition as fuel volume percent in air.
- Large-grid AMR evidence consumed: `docs/codex_audit/evidence/engineering_h2_hybrid_largegrid_8rank_120step_scout_20260721/hybrid_largegrid_8rank_120step_scout_report.json`.
- AMR hazard result: peak H2 volume fraction `0.186431079`, LEL cloud volume `2.53408927e-02`, final flammable planes `14`.
- AMR-vs-baseline drift: `cloud_rel_diff=1.59761211e-02`, `peak_rel_diff=1.55533247e-03`.
- Scorecard: `engineering_production_scorecard VERIFY-PASS`, `status=NOT_PRODUCTION_READY`, `functional=93.4`, `production=73.5`.

## Interpretation

This improves engineering interpretation of H2 hazard outputs against published threshold definitions. It does not clear the external reference-data blocker: field-test data, wind-tunnel data, literature plume profiles, or ALOHA spatial plume cross-comparisons are still required for production validation.
