# Checkpoint: Engineering Fire Consequence Calibration Metadata

Date: 2026-07-22

## Scope

Made fire/radiation/overpressure consequence evidence scope machine-readable so
screening metrics are not mistaken for calibrated consequence models.

## Change

- Updated `tools/write_engineering_h2_fire_consequence_metrics_report.py`.
  - Adds `consequence_model_tier`, `radiation_model_calibrated`,
    `overpressure_model_calibrated`, `flame_geometry_model`,
    `validated_against_fire_experiment`,
    `validated_against_blast_experiment`, and
    `clears_calibrated_fire_consequence_blocker`.
- Updated `tools/write_engineering_production_scorecard.py`.
  - Replaces the static
    `calibrated_fire_radiation_overpressure_metrics_missing` blocker with a
    fire-report-derived blocker.
  - Current blocker is
    `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`.

## Current Fire Consequence Evidence Classification

- Report:
  `docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.json`
- `consequence_model_tier`: `screening_metrics`
- `radiation_model_calibrated`: `False`
- `overpressure_model_calibrated`: `False`
- `flame_geometry_model`: `False`
- `validated_against_fire_experiment`: `False`
- `validated_against_blast_experiment`: `False`
- `clears_calibrated_fire_consequence_blocker`: `False`

## Verification

- `python3 -m py_compile tools/write_engineering_h2_fire_consequence_metrics_report.py tools/write_engineering_production_scorecard.py`
- `python3 tools/write_engineering_h2_fire_consequence_metrics_report.py --output-json docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.json --output-md docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.md`
- Refreshed `engineering_h2_acceptance_matrix`.
- Refreshed `engineering_production_scorecard`.
- Refreshed `engineering_h2_production_evidence_verification_report`.
- `bash tools/run_engineering_h2_production_evidence_verification_archive.sh`

## Result

- Fire consequence metrics: `PASS-SCREENING`.
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
- `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`
- `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`
- `bfs_kepsilon_reference_validation_failed`
