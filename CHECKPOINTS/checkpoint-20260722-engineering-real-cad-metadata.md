# Checkpoint: Engineering Real-CAD Metadata

Date: 2026-07-22

## Scope

Made geometry/CAD evidence scope machine-readable so synthetic tank-farm and
STL regression evidence is not mistaken for a real-CAD cleanup campaign.

## Change

- Updated `tools/write_engineering_campaign_manifest.py`.
  - Adds `geometry_evidence_tier`, `synthetic_tank_farm_evidence`,
    `synthetic_stl_pipeline_evidence`, `real_cad_cleanup_campaign`,
    `real_cad_large_layout_campaign`, `real_cad_geometry_count`, and
    `clears_real_cad_cleanup_blocker`.
- Updated `tools/write_engineering_production_scorecard.py`.
  - Replaces the static `real_cad_cleanup_campaign_missing` blocker with a
    manifest-derived blocker.
  - Current blocker is
    `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`.

## Current Geometry Evidence Classification

- Campaign manifest:
  `docs/codex_audit/evidence/engineering_h2_production_full_20260720/campaign_manifest.json`
- `geometry_evidence_tier`: `synthetic_obstacle_regression`
- `synthetic_tank_farm_evidence`: `True`
- `synthetic_stl_pipeline_evidence`: `True`
- `real_cad_cleanup_campaign`: `False`
- `real_cad_large_layout_campaign`: `False`
- `real_cad_geometry_count`: `0`
- `clears_real_cad_cleanup_blocker`: `False`

## Verification

- `python3 -m py_compile tools/write_engineering_campaign_manifest.py tools/write_engineering_production_scorecard.py`
- `python3 tools/write_engineering_campaign_manifest.py --campaign engineering-h2-production-full-20260720 --campaign-run-summary /tmp/codex_engineering_h2_campaign_full_20260720/campaign_run_summary.json --output-json docs/codex_audit/evidence/engineering_h2_production_full_20260720/campaign_manifest.json --output-md docs/codex_audit/evidence/engineering_h2_production_full_20260720/campaign_manifest.md`
- `python3 tools/write_engineering_production_scorecard.py --output-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json --output-md docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.md`
- `python3 tools/write_engineering_h2_production_evidence_verification_report.py --no-require-ctest`
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
- `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`
- `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`
- `bfs_kepsilon_reference_validation_failed`
- `calibrated_fire_radiation_overpressure_metrics_missing`
