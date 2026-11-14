# Checkpoint: Engineering Stability Duration Metadata

Date: 2026-07-22

## Scope

Made production-mesh stability evidence duration class machine-readable so a
1200-step scout cannot be mistaken for an overnight or full-duration production
campaign.

## Change

- Updated `tools/write_engineering_h2_production_scale_scout_report.py`.
  - Adds `evidence_tier`, `stability_duration_class`,
    `production_campaign`, `production_size_mesh_campaign`,
    `overnight_campaign`, `full_duration_campaign`, and
    `full_plotfile_archive`.
  - Verifies boolean metadata when present.
- Updated `tools/write_engineering_production_scorecard.py`.
  - Replaces the static `overnight_or_full_duration_stability_missing`
    blocker with a report-derived blocker.
  - Current blocker is
    `stability_evidence_is_production_mesh_1200step_stability_scout_not_overnight_or_full_duration`.

## Current 1200-Step Stability Evidence Classification

- Report:
  `docs/codex_audit/evidence/engineering_h2_production_mesh_1200step_stability_scout_20260720/production_mesh_1200step_stability_scout_report.json`
- `evidence_tier`: `engineering_cfd_scout`
- `stability_duration_class`: `production_mesh_1200step_stability_scout`
- `production_campaign`: `False`
- `production_size_mesh_campaign`: `False`
- `overnight_campaign`: `False`
- `full_duration_campaign`: `False`
- `full_plotfile_archive`: `False`

## Verification

- `python3 -m py_compile tools/write_engineering_h2_production_scale_scout_report.py tools/write_engineering_production_scorecard.py`
- Repacked existing 1200-step stability evidence with the new metadata.
- Refreshed `engineering_h2_acceptance_matrix`.
- Refreshed `engineering_production_scorecard`.
- Refreshed `engineering_h2_production_evidence_verification_report`.
- `bash tools/run_engineering_h2_production_evidence_verification_archive.sh`

## Result

- Engineering production scorecard: `NOT_PRODUCTION_READY`, functional `93.4`,
  production `73.5`.
- Production evidence archive: `PASS`.
- CTest archive evidence: `22/22 PASS`.
- Machine-local path audit: `PASS`, scanned files `977`.

## Current Blocking Gaps

- `scheduler_controller_unavailable_or_job_not_accepted`
- `campaign_evidence_is_smoke_regression_not_production_size`
- `stability_evidence_is_production_mesh_1200step_stability_scout_not_overnight_or_full_duration`
- `reference_data_agreement_missing`
- `bfs_kepsilon_reference_validation_failed`
- `real_cad_cleanup_campaign_missing`
- `calibrated_fire_radiation_overpressure_metrics_missing`
