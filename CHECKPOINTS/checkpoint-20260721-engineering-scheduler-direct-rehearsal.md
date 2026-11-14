# Checkpoint: Engineering Scheduler Direct Rehearsal

Date: 2026-07-21

## What changed

- Exercised the scheduler script body outside SLURM to separate script/campaign correctness from SLURM controller availability.
- Added `tools/sanitize_engineering_scheduler_evidence.py` to sanitize machine-local paths from scheduler evidence directories.
- Patched `tools/verify_engineering_scheduler_run.py` so `--allow-incomplete` produces `NOT_READY` for known incomplete scheduler evidence instead of escalating expected controller-unavailable evidence to `FAIL`.
- Patched `tools/write_engineering_scheduler_campaign_manifest.py` to include the sanitizer in generated SLURM scripts and to resolve relative output paths against the repo root.

## Evidence

- Runtime affinity rehearsal: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/runtime_affinity_manifest.json`, `PASS`, 4 ranks x 1 thread.
- Campaign rehearsal: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/campaign_run_summary.json`, `PASS`, suite `h2-production-scout`, case `plan-amr-mpi-reduced-long`.
- Scheduler run report: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json`, `NOT_READY`, 35 checks, only `scheduler_submit_job_accepted` remains failing because SLURM reports `CONTROLLER_UNAVAILABLE`.
- Sanitizer pass: 37 files scanned; current evidence already sanitized after regeneration.
- Full engineering evidence archive passed with scorecard `92.8/72.7`, path audit PASS, and CTest `22/22 PASS`.

## Interpretation

This does not clear the scheduler-managed production blocker. It proves that the generated SLURM script body, runtime-affinity capture, campaign runner, evidence packaging, hash verification, log scanning, and path sanitization all work when invoked directly. The remaining scheduler blocker is now narrowed to external SLURM job acceptance/controller availability.
