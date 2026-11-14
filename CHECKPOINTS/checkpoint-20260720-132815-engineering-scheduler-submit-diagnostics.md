# Checkpoint: Engineering Scheduler Submit Diagnostics

Date: 2026-07-20

## Scope

This checkpoint continues the engineering-production priority by tightening the scheduler handoff evidence. It does not clear the scheduler production blocker because the SLURM controller is not currently accepting jobs.

## Changes

- Added `tools/submit_engineering_scheduler_job.py`, a sanitized `sbatch --parsable` submit-attempt reporter.
- Updated `tools/verify_engineering_scheduler_run.py` to ingest `scheduler_submit_attempt.json` and report whether the scheduler accepted a job.
- Added a read-only `--verify-json` mode to `tools/verify_engineering_scheduler_run.py` so evidence validation no longer rewrites timestamps and invalidates scorecard hashes.
- Updated `tools/write_engineering_scheduler_campaign_manifest.py` to include `scontrol ping`, list the submit diagnostic command, and fix a concatenated limitation string.
- Refreshed `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_campaign_manifest.json` and `scheduler_run_report.json`.
- Updated engineering audit docs to record the scheduler controller failure explicitly.

## Evidence

- Submit attempt: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_submit_attempt.json`
- Submit status: `CONTROLLER_UNAVAILABLE`
- Submit return code: `1`
- Submit job id: empty
- Captured scheduler detail: `sbatch could not contact the SLURM controller`
- Manifest status: `READY_WITH_WARNINGS`
- Manifest warnings: `sinfo_timed_out`, `squeue_user_timed_out`, `scontrol_ping_returncode_1`, `sbatch_test_only_timed_out`
- Scheduler run report status: `NOT_READY`
- Scheduler run report now includes `scheduler_submit_job_accepted=FAIL` with controller-unavailable detail.

## Scorecard Impact

- Engineering score remains `functional=90.1`, `production=69.3`.
- Status remains `NOT_PRODUCTION_READY`.
- The scheduler blocker remains valid. This pass converts an ambiguous missing-output condition into a clear external scheduler-control-plane blocker.

## Validation

- `python3 -m py_compile tools/write_engineering_scheduler_campaign_manifest.py tools/verify_engineering_scheduler_run.py tools/submit_engineering_scheduler_job.py tools/write_engineering_production_scorecard.py`
- `python3 tools/write_engineering_scheduler_campaign_manifest.py --verify-json docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_campaign_manifest.json`
- `python3 tools/verify_engineering_scheduler_run.py --verify-json docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json`
- `python3 tools/write_engineering_production_scorecard.py --verify-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json`

