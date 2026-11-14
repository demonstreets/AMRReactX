# Checkpoint: Engineering H2 Full-Duration Candidate Preflight

Date: 2026-07-22

## Scope

- Added `tools/write_engineering_h2_full_duration_candidate_report.py`.
- Updated `tools/write_engineering_production_scorecard.py`.
- Updated `tools/verify_engineering_h2_production_evidence.sh`.

## Evidence Added

- `docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/full_duration_candidate_report.json`
- `docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/full_duration_candidate_report.md`

## Candidate Target

- Wrapper: `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh`
- Ranks: `8`
- Jobs: `8`
- Max step: `7200`
- Plot interval: `240`
- Expected plotfiles per case: `31`
- Expected simulation time: `7.2 s`
- Run timeout: `43200 s`

## Result

- Full-duration candidate report status: `NOT_READY-FULL-DURATION-CANDIDATE`
- Blocking gap: `insufficient_free_disk_for_full_duration_candidate`
- Free disk observed: `10.212028503417969 GB`
- Minimum required free disk: `20.0 GB`

The candidate report is intentionally not an execution claim. It records the launch contract and proves that the current server state should not start the full-duration candidate until disk space is cleared or a larger evidence/output location is configured.

## Scorecard Impact

The stability blocker is now more actionable:

- Old blocker: `stability_evidence_is_production_mesh_1200step_stability_scout_not_overnight_or_full_duration`
- New blocker: `stability_full_duration_candidate_blocked_by_insufficient_disk`

Scores remain unchanged:

- Functional coverage: `93.4`
- Production credibility: `73.5`
- Status: `NOT_PRODUCTION_READY`

## Verification

- `python3 -m py_compile tools/write_engineering_h2_full_duration_candidate_report.py tools/write_engineering_production_scorecard.py`
- `python3 tools/write_engineering_h2_full_duration_candidate_report.py`
- `python3 tools/write_engineering_h2_full_duration_candidate_report.py --verify-json docs/codex_audit/evidence/engineering_h2_full_duration_candidate_20260722/full_duration_candidate_report.json`
- `bash tools/run_engineering_h2_production_evidence_verification_archive.sh`
- `python3 tools/write_engineering_production_scorecard.py --verify-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`
- `python3 tools/write_engineering_h2_production_evidence_verification_report.py --verify-json docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json`

Full archive verification passed:

- CTest: `22/22` passed
- Path audit: `machine_local_paths PASS scanned_files=980`
- Production evidence verification report: `PASS`, score `93.4/73.5`
