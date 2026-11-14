# Checkpoint: Engineering H2 Production Mesh Campaign Report

Date: 2026-07-22

## Scope

- Added `tools/write_engineering_h2_production_mesh_campaign_report.py`.
- Updated `tools/write_engineering_production_scorecard.py`.
- Updated `tools/verify_engineering_h2_production_evidence.sh`.

## Evidence Added

- `docs/codex_audit/evidence/engineering_h2_production_mesh_campaign_20260722/production_mesh_campaign_report.json`
- `docs/codex_audit/evidence/engineering_h2_production_mesh_campaign_20260722/production_mesh_campaign_report.md`

The new report aggregates six existing production-mesh scout/stability reports:

- 4-rank 120-step production-mesh scout
- 8-rank 120-step production-mesh scout
- 16-rank 120-step production-mesh scout
- 4-rank 600-step production-mesh stability scout
- 8-rank 600-step production-mesh stability scout
- 4-rank 1200-step production-mesh stability scout

## Result

- Production mesh campaign report status: `PASS-PRODUCTION-MESH-CAMPAIGN-SCOUT`
- Cases passing: `6/6`
- Ranks covered: `4, 8, 16`
- Max step: `1200`
- Max base cells: `65536`
- Max AMR-equivalent fine cells: `524288`
- Max cloud relative difference: `0.0380952381`
- Max peak relative difference: `0.0431073584`

## Scorecard Impact

The campaign-scale blocker is now more accurate:

- Old blocker: `campaign_evidence_is_smoke_regression_not_production_size`
- New blocker: `campaign_evidence_is_production_mesh_scout_not_full_duration`

The score is intentionally unchanged:

- Functional coverage: `93.4`
- Production credibility: `73.5`
- Status: `NOT_PRODUCTION_READY`

The blocker remains because the new report proves production-mesh scout coverage, not full-duration production acceptance.

## Verification

- `python3 -m py_compile tools/write_engineering_h2_production_mesh_campaign_report.py tools/write_engineering_production_scorecard.py`
- `python3 tools/write_engineering_h2_production_mesh_campaign_report.py`
- `python3 tools/write_engineering_h2_production_mesh_campaign_report.py --verify-json docs/codex_audit/evidence/engineering_h2_production_mesh_campaign_20260722/production_mesh_campaign_report.json`
- `bash tools/run_engineering_h2_production_evidence_verification_archive.sh`

Full archive verification passed:

- CTest: `22/22` passed
- Path audit: `machine_local_paths PASS scanned_files=979`
- Production evidence verification report: `PASS`, score `93.4/73.5`
