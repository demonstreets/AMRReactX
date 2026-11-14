# Checkpoint: Engineering Reference Data Metadata

Date: 2026-07-22

## Scope

Made H2 reference agreement scope machine-readable so threshold agreement is
not mistaken for external plume-shape or field/wind-tunnel validation.

## Change

- Updated `tools/write_engineering_h2_reference_agreement_report.py`.
  - Adds `agreement_tier`, `threshold_reference_agreement`,
    `external_plume_shape_dataset_agreement`,
    `external_consequence_dataset_agreement`,
    `field_or_wind_tunnel_dataset_agreement`, and
    `clears_reference_data_blocker`.
- Updated `tools/write_engineering_production_scorecard.py`.
  - Replaces the static `reference_data_agreement_missing` blocker with a
    reference-report-derived blocker.
  - Current blocker is
    `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`.

## Current Reference Agreement Classification

- Report:
  `docs/codex_audit/evidence/engineering_h2_reference_agreement_20260721/h2_reference_agreement_report.json`
- `agreement_tier`: `reference_threshold_agreement`
- `threshold_reference_agreement`: `True`
- `external_plume_shape_dataset_agreement`: `False`
- `external_consequence_dataset_agreement`: `False`
- `field_or_wind_tunnel_dataset_agreement`: `False`
- `clears_reference_data_blocker`: `False`

## Verification

- `python3 -m py_compile tools/write_engineering_h2_reference_agreement_report.py tools/write_engineering_production_scorecard.py`
- `python3 tools/write_engineering_h2_reference_agreement_report.py`
- `python3 tools/write_engineering_production_scorecard.py --output-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json --output-md docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.md`
- `python3 tools/write_engineering_h2_production_evidence_verification_report.py --no-require-ctest`
- `bash tools/run_engineering_h2_production_evidence_verification_archive.sh`

## Result

- H2 reference agreement: `PASS-REFERENCE-THRESHOLD-AGREEMENT`.
- Engineering production scorecard: `NOT_PRODUCTION_READY`, functional `93.4`,
  production `73.5`.
- Production evidence archive: `PASS`.
- CTest archive evidence: `22/22 PASS`.
- Machine-local path audit: `PASS`, scanned files `977`.

## Current Blocking Gaps

- `scheduler_controller_unavailable_or_job_not_accepted`
- `campaign_evidence_is_smoke_regression_not_production_size`
- `stability_evidence_is_production_mesh_1200step_stability_scout_not_overnight_or_full_duration`
- `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`
- `bfs_kepsilon_reference_validation_failed`
- `real_cad_cleanup_campaign_missing`
- `calibrated_fire_radiation_overpressure_metrics_missing`
