# Checkpoint: Engineering Campaign Scale Metadata

Date: 2026-07-22

## Scope

Made engineering H2 campaign evidence scale machine-readable so the 16-case
regression campaign cannot be mistaken for a production-size campaign.

## Change

- Updated `tools/run_engineering_h2_campaign.py`.
  - Adds `evidence_tier`, `campaign_scale`, `production_campaign`,
    `production_size_mesh_campaign`, and `full_duration_campaign` to new runner
    summaries.
- Updated `tools/write_engineering_campaign_manifest.py`.
  - Propagates those fields into campaign manifests.
  - Defaults older runner summaries to `workflow_regression` /
    `engineering_regression_smoke`.
- Updated `tools/write_engineering_production_scorecard.py`.
  - Replaces the static `production_size_mesh_campaign_missing` blocker with a
    manifest-derived blocker.
  - Current blocker is
    `campaign_evidence_is_smoke_regression_not_production_size`.

## Current Evidence Classification

- Campaign manifest:
  `docs/codex_audit/evidence/engineering_h2_production_full_20260720/campaign_manifest.json`
- `evidence_tier`: `workflow_regression`
- `campaign_scale`: `engineering_regression_smoke`
- `production_campaign`: `False`
- `production_size_mesh_campaign`: `False`
- `full_duration_campaign`: `False`

## Verification

- `python3 -m py_compile tools/run_engineering_h2_campaign.py tools/write_engineering_campaign_manifest.py tools/write_engineering_production_scorecard.py`
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
- `overnight_or_full_duration_stability_missing`
- `reference_data_agreement_missing`
- `bfs_kepsilon_reference_validation_failed`
- `real_cad_cleanup_campaign_missing`
- `calibrated_fire_radiation_overpressure_metrics_missing`
