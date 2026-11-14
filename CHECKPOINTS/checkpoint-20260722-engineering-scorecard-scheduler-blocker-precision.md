# Checkpoint: Engineering Scorecard Scheduler Blocker Precision

Date: 2026-07-22

## Scope

Refined the engineering production scorecard so the scheduler production
blocker reflects the current scheduler evidence instead of using a static,
ambiguous run-summary label.

## Change

- Updated `tools/write_engineering_production_scorecard.py`.
- Added `check_by_name()` and `scheduler_blocking_gap()`.
- The scorecard now emits `scheduler_controller_unavailable_or_job_not_accepted`
  when `scheduler_submit_job_accepted` fails because the SLURM controller is
  unavailable.
- If the scheduler report reaches `PASS`, this blocker is omitted
  automatically.

## Evidence

- `python3 -m py_compile tools/write_engineering_production_scorecard.py`
- `python3 tools/write_engineering_production_scorecard.py --output-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json --output-md docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.md`
- `python3 tools/write_engineering_h2_production_evidence_verification_report.py --no-require-ctest`
- `python3 tools/write_engineering_bfs_kepsilon_reference_report.py --verify-json docs/codex_audit/evidence/engineering_bfs_kepsilon_reference_20260721/bfs_kepsilon_reference_report.json`
- `python3 tools/write_engineering_production_scorecard.py --verify-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`
- `python3 tools/write_engineering_h2_production_evidence_verification_report.py --verify-json docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json`
- `python3 tools/check_machine_local_paths.py`

## Result

- BFS/k-epsilon evidence: `VERIFY-PASS`, status `NOT_READY-BFS-KEPSILON-REFERENCE`.
- Engineering scorecard: `VERIFY-PASS`, status `NOT_PRODUCTION_READY`,
  functional `93.4`, production `73.5`.
- H2 production evidence report: `VERIFY-PASS`, status `PASS`, score
  `93.4/73.5`, CTest evidence `22`.
- Machine-local path audit: `PASS`, scanned files `977`.

## Current Blocking Gaps

- `scheduler_controller_unavailable_or_job_not_accepted`
- `production_size_mesh_campaign_missing`
- `overnight_or_full_duration_stability_missing`
- `reference_data_agreement_missing`
- `bfs_kepsilon_reference_validation_failed`
- `real_cad_cleanup_campaign_missing`
- `calibrated_fire_radiation_overpressure_metrics_missing`
