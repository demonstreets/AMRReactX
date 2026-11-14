# Engineering Scheduler Campaign Manifest: engineering-h2-production-scheduler-readiness

Status: `READY_WITH_WARNINGS`
Suite: `h2-production-scout`
Generated UTC: `2026-07-22T03:53:21+00:00`
Scheduler: `slurm`
Script: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/run_engineering_h2_slurm.sh`
Script SHA-256: `08d0dd4392fe6ba8d2dd4b4216974ae31d964371d53a42b8664d086a634ea0af`

## Requested Resources

- nodes: `1`
- ranks: `4`
- threads_per_rank: `1`
- jobs: `4`
- max_step: `200`
- plot_int: `20`
- min_plotfiles: `11`
- time_limit: `02:00:00`
- partition: ``
- account: ``
- omp_proc_bind: `close`
- omp_places: `cores`
- run_timeout_s: `2400`
- case_timeout_s: `4200`

## Scheduler Probes

- sbatch_version: `available`, returncode=`0`
- sinfo: `timeout`, returncode=`None`
- squeue_user: `timeout`, returncode=`None`
- scontrol_ping: `available`, returncode=`1`
- sbatch_test_only: `timeout`, returncode=`None`

## Execution Plan

- Plan tier: `scheduler_managed_production_scout_candidate`
- Run mode: `slurm_batch`
- evidence_root: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720`
- campaign_run_root: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/campaign_run`
- runtime_affinity_manifest: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/runtime_affinity_manifest.json`
- campaign_run_summary: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/campaign_run_summary.json`
- scheduler_run_report: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json`
- sanitized_slurm_stdout_glob: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/slurm-*.out`

### Closure Criteria

- scheduler_submit_attempt.status == SUBMITTED
- runtime_affinity_manifest.status == PASS
- campaign_run_summary.status == PASS
- verify_engineering_scheduler_run.py status == PASS
- scheduler logs contain no failure markers, nonfinite tokens, private markers, or unsanitized machine-local paths

## Commands

- `bash docs/codex_audit/evidence/engineering_scheduler_h2_20260720/run_engineering_h2_slurm.sh`
- `sbatch docs/codex_audit/evidence/engineering_scheduler_h2_20260720/run_engineering_h2_slurm.sh`
- `python3 tools/submit_engineering_scheduler_job.py docs/codex_audit/evidence/engineering_scheduler_h2_20260720/run_engineering_h2_slurm.sh --output-json docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_submit_attempt.json --output-md docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_submit_attempt.md --allow-non-submitted`
- `python3 tools/write_engineering_scheduler_campaign_manifest.py --verify-json docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_campaign_manifest.json`

## Warnings

- sinfo_timed_out
- squeue_user_timed_out
- scontrol_ping_returncode_1
- sbatch_test_only_timed_out

## Limitations

- This manifest prepares a scheduler-managed engineering H2 campaign but does not submit a job by itself.
- A PASS manifest proves reproducible scheduler script generation, client probing, resource capture, optional sbatch test-only probing, script hash verification, and automatic scheduler-run report generation after successful or failed scheduled execution.
- Production readiness still requires a completed scheduler-managed run with runtime-affinity evidence, campaign summary, sanitized logs, and long-duration stability metrics.
