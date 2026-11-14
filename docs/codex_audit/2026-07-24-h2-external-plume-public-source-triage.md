# 2026-07-24 H2 External Plume Public Source Triage

Scope: engineering H2 production blocker
`reference_agreement_is_threshold_only_not_external_plume_shape_dataset`.

Changes:

- Added `tools/write_engineering_h2_external_plume_public_source_triage_report.py`.
- Added maintained evidence root:
  `docs/codex_audit/evidence/engineering_h2_external_plume_public_source_triage_20260724/`.
- Integrated the triage report into
  `tools/write_engineering_h2_external_plume_benchmark_readiness.py`.
- Integrated the triage report into
  `tools/verify_engineering_h2_production_evidence.sh`.
- Updated `tools/write_engineering_h2_production_evidence_verification_report.py`
  to schema 14 so the production evidence pack hashes the public-source triage
  report.

Current intent:

- Freeze the public source registry for HySafe SBEPV5 / GexCon D27.
- Record the public facts that are strong enough for case scaffolding:
  vessel size, D27 release settings, sensor count/reliability, baffle count, and
  reported existence of a 120 s Excel concentration dataset.
- Record the exact missing production artifacts: `sensor_coordinates.csv`,
  `baffle_geometry.csv`, `experimental_timeseries.csv`, and
  `dataset_metadata.json`.

What this does not prove:

- It does not ingest the original Excel data or digitized concentration curves.
- It does not provide exact Gas01..Gas12 coordinates or exact baffle bounds.
- It does not clear the external plume reference-data blocker.
