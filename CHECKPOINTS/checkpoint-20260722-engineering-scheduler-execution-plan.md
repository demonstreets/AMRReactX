# Checkpoint: Engineering Scheduler Execution Plan Evidence

Date: 2026-07-22

## Scope

- Updated `tools/write_engineering_scheduler_campaign_manifest.py`.
- Updated `tools/verify_engineering_scheduler_run.py`.
- Regenerated scheduler campaign manifest and scheduler run report under:
  - `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/`

## Changes

- Scheduler manifest now includes machine-readable `execution_plan` metadata:
  - `plan_tier = scheduler_managed_production_scout_candidate`
  - `run_mode = slurm_batch`
  - expected output paths for runtime affinity, campaign summary, scheduler run report, and sanitized SLURM stdout
  - rerun/resume guidance
  - closure criteria for treating the scheduled run as accepted/completed evidence

- Scheduler run verifier now checks `execution_plan` presence, tier, run mode, expected outputs, and closure-criteria completeness.
- Scheduler script token checks now use stable unique check names instead of duplicate names for multiple `#SBATCH` directives.

## Result

- Scheduler campaign manifest: `READY_WITH_WARNINGS`
- Scheduler run report: `NOT_READY`
- Scheduler run report checks increased to `44`, including execution-plan checks.
- The production scheduler blocker remains open because `scheduler_submit_job_accepted` is still `FAIL` due to SLURM controller unavailability.
- Engineering production scorecard remains:
  - status: `NOT_PRODUCTION_READY`
  - functional coverage: `93.4`
  - production credibility: `73.5`

## Verification

- `python3 -m py_compile tools/write_engineering_scheduler_campaign_manifest.py tools/verify_engineering_scheduler_run.py`
- `python3 tools/write_engineering_scheduler_campaign_manifest.py --verify-json docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_campaign_manifest.json`
- `python3 tools/verify_engineering_scheduler_run.py --evidence-dir engineering_scheduler_h2_20260720 --allow-incomplete`
- `bash tools/run_engineering_h2_production_evidence_verification_archive.sh`

Full archive verification passed:

- CTest: `22/22` passed
- path audit: `machine_local_paths PASS scanned_files=978`
- production evidence verification report: `PASS`, score `93.4/73.5`

## Next Required External Condition

The scheduler chain is now more reproducible, but it still cannot clear the scheduler production blocker until the SLURM controller accepts and completes the generated job.
