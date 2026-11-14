# Checkpoint: engineering scheduler-run verifier

Timestamp: 2026-07-20 03:10:22 UTC
Scope: engineering production-readiness, scheduler-run completion evidence.

## Context

The engineering H2 production-scout SLURM manifest and submission script existed, but the script only prepared a scheduler-ready campaign path. The missing piece was a completion verifier that can decide whether a scheduler-run evidence directory is actually ready to support production-readiness claims.

## Added tool

- `tools/verify_engineering_scheduler_run.py`

The verifier checks the scheduler campaign manifest, generated SLURM script hash, runtime-affinity manifest, campaign run summary, case PASS statuses, required-output hashes, missing outputs, log failure markers, nonfinite log tokens, and machine-local/private markers. It writes JSON and Markdown reports.

## Generator integration

`tools/write_engineering_scheduler_campaign_manifest.py` now generates a SLURM script with an `EXIT` trap. On successful scheduled execution, the trap runs `tools/verify_engineering_scheduler_run.py` in strict mode. On failed or interrupted execution, it runs the verifier with `--allow-incomplete` so a diagnostic report is still written while the original failure code is preserved.

Generated script:

- `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/run_engineering_h2_slurm.sh`
- Script SHA-256 prefix: `740d40af58d21972`

## Evidence generated

Scheduler manifest generation:

```text
engineering_scheduler_campaign_manifest PASS status=READY_WITH_WARNINGS suite=h2-production-scout ranks=4 threads=1 warnings=3
```

Manifest verification:

```text
engineering_scheduler_campaign_manifest VERIFY-PASS suite=h2-production-scout ranks=4 threads=1 json=docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_campaign_manifest.json
```

Current scheduler-run report with incomplete scheduled outputs allowed:

```text
engineering_scheduler_run_report NOT_READY checks=17 json=docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json md=docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.md
```

Strict-mode behavior:

```text
engineering_scheduler_run_report FAIL checks=17 json=docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.json md=docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_run_report.md
strict_rc=1
```

The strict-mode non-PASS checks are exactly:

```text
runtime_affinity_manifest_exists:MISSING
campaign_run_summary_exists:MISSING
```

The report was restored to `NOT_READY` with `--allow-incomplete` after the strict-mode negative test.

## Interpretation

This adds a fail-closed scheduler evidence gate. The package can no longer be mistaken for completed scheduler-run proof until the scheduled runtime-affinity manifest and campaign summary exist. This still does not prove a completed SLURM allocation or production CFD campaign because the SLURM job has not been accepted/run yet.

## Docs updated

- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
- `docs/codex_audit/SMOKE_MATRIX.md`

The docs now record the scheduler-run verifier, the updated script hash, and the current `NOT_READY` report.

## Remaining limitations

- SLURM control-plane probes still time out, so no batch job was submitted.
- Scheduled-run runtime-affinity and campaign summary outputs are missing by design in the current evidence directory.
- Production-size scaling, overnight stability, hybrid threaded-MPI safety, fire consequence validation, and reference-data agreement remain outside this checkpoint.

## Final verification

- Python compile passed for `tools/write_engineering_scheduler_campaign_manifest.py`, `tools/verify_engineering_scheduler_run.py`, `tools/write_engineering_runtime_affinity_manifest.py`, and `tools/run_engineering_h2_campaign.py`.
- Scheduler campaign manifest `--verify-json` passed.
- Scheduler-run verifier with `--allow-incomplete` wrote `NOT_READY` with 17 checks.
- Current non-PASS checks remain exactly `runtime_affinity_manifest_exists:MISSING` and `campaign_run_summary_exists:MISSING`, which are expected until the SLURM job is accepted and run.
- Generated SLURM script passed `bash -n`.
- Documentation grep confirmed production-readiness report, smoke matrix, and this checkpoint reference the verifier, `NOT_READY` report, updated script SHA-256 prefix, and missing scheduled-run outputs.
- `python3 tools/check_machine_local_paths.py --strict` passed with `machine_local_paths PASS scanned_files=960`.
- `ctest --test-dir build-codex-smoke --output-on-failure` passed 22/22 tests.
