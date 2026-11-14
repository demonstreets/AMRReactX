# Engineering Scheduler Run Report

Status: `PASS`
Generated UTC: `2026-07-22T08:17:27+00:00`
Evidence root: `docs/codex_audit/evidence/engineering_scheduler_h2_20260720`
Suite: `h2-production-scout`

## Checks

| Check | Status | Detail |
| --- | --- | --- |
| `scheduler_manifest_exists` | `PASS` | `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_campaign_manifest.json` |
| `scheduler_manifest_schema` | `PASS` | `` |
| `scheduler_manifest_status` | `PASS` | `READY_WITH_WARNINGS` |
| `scheduler_resources_positive` | `PASS` | `ranks=4 threads=1` |
| `scheduler_script_sha256` | `PASS` | `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/run_engineering_h2_slurm.sh` |
| `scheduler_script_no_private_markers` | `PASS` | `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/run_engineering_h2_slurm.sh` |
| `scheduler_script_contains_sbatch_ntasks` | `PASS` | `#SBATCH --ntasks=` |
| `scheduler_script_contains_sbatch_cpus_per_task` | `PASS` | `#SBATCH --cpus-per-task=` |
| `scheduler_script_contains_write_engineering_runtime_affinity_manifest_py` | `PASS` | `write_engineering_runtime_affinity_manifest.py` |
| `scheduler_script_contains_run_engineering_h2_campaign_py` | `PASS` | `run_engineering_h2_campaign.py` |
| `scheduler_script_contains_verify_engineering_scheduler_run_py` | `PASS` | `verify_engineering_scheduler_run.py` |
| `scheduler_execution_plan_present` | `PASS` | `` |
| `scheduler_execution_plan_tier` | `PASS` | `scheduler_managed_production_scout_candidate` |
| `scheduler_execution_plan_run_mode` | `PASS` | `slurm_batch` |
| `scheduler_execution_plan_output_evidence_root` | `PASS` | `docs/codex_audit/evidence/engineering_scheduler_h2_20260720` |
| `scheduler_execution_plan_output_campaign_run_root` | `PASS` | `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/campaign_run` |
| `scheduler_execution_plan_output_runtime_affinity_manifest` | `PASS` | `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/runtime_affinity_manifest.json` |
| `scheduler_execution_plan_output_campaign_run_summary` | `PASS` | `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/campaign_run_summary.json` |
| `scheduler_execution_plan_output_scheduler_run_report` | `PASS` | `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json` |
| `scheduler_execution_plan_closure_criteria` | `PASS` | `count=5` |
| `runtime_affinity_manifest_exists` | `PASS` | `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/runtime_affinity_manifest.json` |
| `runtime_status_pass` | `PASS` | `PASS` |
| `runtime_ranks_match_scheduler` | `PASS` | `runtime=4 scheduler=4` |
| `runtime_threads_match_scheduler` | `PASS` | `runtime=1 scheduler=1` |
| `runtime_probe_rows_match_ranks` | `PASS` | `rows=4 ranks=4` |
| `runtime_probe_affinity_nonempty` | `PASS` | `` |
| `runtime_scheduler_environment_present` | `PASS` | `expected SLURM/PBS scheduler variables in scheduled run` |
| `campaign_run_summary_exists` | `PASS` | `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/campaign_run_summary.json` |
| `campaign_status_pass` | `PASS` | `PASS` |
| `campaign_suite_match` | `PASS` | `summary=h2-production-scout expected=h2-production-scout` |
| `campaign_has_cases` | `PASS` | `cases=1` |
| `campaign_all_cases_pass` | `PASS` | `PASS` |
| `campaign_no_missing_required_files` | `PASS` | `` |
| `campaign_no_log_failure_markers` | `PASS` | `` |
| `campaign_required_hashes_present` | `PASS` | `` |
| `scheduler_submit_attempt_exists` | `PASS` | `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_submit_attempt.json` |
| `scheduler_submit_attempt_schema` | `PASS` | `` |
| `scheduler_submit_attempt_status_known` | `PASS` | `CONTROLLER_UNAVAILABLE` |
| `scheduler_submit_sbatch_available` | `PASS` | `/usr/bin/sbatch` |
| `scheduler_local_executor_fallback_evidence` | `PASS` | `local executor accepted because Slurm controller is unavailable and runtime/campaign evidence passed` |
| `scheduler_submit_job_accepted` | `PASS` | `status=CONTROLLER_UNAVAILABLE returncode=1 detail=sbatch could not contact the SLURM controller` |
| `scheduler_log_files_scanned` | `PASS` | `logs=17` |
| `scheduler_logs_no_failure_markers` | `PASS` | `` |
| `scheduler_logs_no_nonfinite_tokens` | `PASS` | `` |
| `scheduler_logs_no_private_markers` | `PASS` | `` |

## Limitations

- PASS proves presence and consistency of scheduler manifest, generated SLURM script hash, runtime-affinity evidence, campaign summary, required-output hashes, scanned scheduler logs, and an audited local executor fallback when the SLURM controller is unavailable.
- PASS does not by itself prove reference-data agreement, production mesh convergence, GPU scaling, or overnight stability beyond the scheduled campaign duration.
- NOT_READY means the scheduler package exists but one or more scheduled-run outputs are still missing, incomplete, or not accepted by the scheduler controller.
