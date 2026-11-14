# Checkpoint: engineering SLURM scheduler campaign manifest

Timestamp: 2026-07-20 03:00:46 UTC
Scope: engineering production-readiness, scheduler-managed H2 production-scout campaign preparation.

## Context

The engineering H2 smoke-scale campaign and runtime-affinity preflight already existed. The remaining production-readiness gap was a scheduler-managed campaign path: reproducible SLURM script generation, explicit MPI/OpenMP resource policy, runtime-affinity capture inside the scheduled job, and campaign summary capture inside durable evidence directories.

## Added tool

- `tools/write_engineering_scheduler_campaign_manifest.py`

The tool generates a scheduler campaign manifest, Markdown summary, and a relative-path SLURM submission script. The generated script sets `OMP_NUM_THREADS`, `OMP_PROC_BIND`, `OMP_PLACES`, H2 reduced-long ranks/steps/plot cadence, runs `tools/write_engineering_runtime_affinity_manifest.py`, then runs `tools/run_engineering_h2_campaign.py --suite h2-production-scout`. The tool also verifies existing manifests with `--verify-json` and checks that stored evidence does not contain machine-local path or credential markers.

## Evidence generated

Command:

```bash
python3 tools/write_engineering_scheduler_campaign_manifest.py   --evidence-dir engineering_scheduler_h2_20260720   --suite h2-production-scout   --campaign engineering-h2-production-scheduler-readiness   --ranks 4   --threads 1   --jobs 4   --max-step 200   --plot-int 20   --min-plotfiles 11   --time-limit 02:00:00   --probe-timeout-s 5   --sbatch-test-only
```

Result:

```text
engineering_scheduler_campaign_manifest PASS status=READY_WITH_WARNINGS suite=h2-production-scout ranks=4 threads=1 warnings=3 json=docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_campaign_manifest.json md=docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_campaign_manifest.md script=docs/codex_audit/evidence/engineering_scheduler_h2_20260720/run_engineering_h2_slurm.sh
```

Verification:

```text
engineering_scheduler_campaign_manifest VERIFY-PASS suite=h2-production-scout ranks=4 threads=1 json=docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_campaign_manifest.json
```

Spot-check summary:

```text
status READY_WITH_WARNINGS
warnings sinfo_timed_out,squeue_user_timed_out,sbatch_test_only_timed_out
script_sha edb18123f942823f
sbatch_test_only True True None
sbatch_version True False 0
sinfo True True None
squeue_user True True None
```

## Interpretation

This closes the first reproducible scheduler packaging gap: a SLURM-ready production-scout campaign script now exists and is hash-verified by a manifest. It does not close batch execution itself. The current SLURM client can report its version, but queue/partition/test-only control-plane probes timed out in the configured 5-second window.

## Docs updated

- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
- `docs/codex_audit/SMOKE_MATRIX.md`

The docs now state that scheduler-ready packaging exists while completed scheduler-managed allocation/run evidence remains open.

## Remaining limitations

- No SLURM job was submitted in this checkpoint.
- No scheduler allocation ID, queued/running/completed state, or scheduled CFD log exists yet.
- The generated script still needs to be run with `sbatch` once the SLURM control plane responds reliably.
- This does not prove production-size scaling, overnight stability, hybrid threaded-MPI safety, or reference-data agreement.

## Final verification

- Python compile passed for `tools/write_engineering_scheduler_campaign_manifest.py`, `tools/write_engineering_runtime_affinity_manifest.py`, and `tools/run_engineering_h2_campaign.py`.
- Manifest `--verify-json` passed for `docs/codex_audit/evidence/engineering_scheduler_h2_20260720/scheduler_campaign_manifest.json`.
- Documentation grep confirmed the scheduler evidence is referenced by the production-readiness report, smoke matrix, and this checkpoint.
- `python3 tools/check_machine_local_paths.py --strict` passed with `machine_local_paths PASS scanned_files=959`.
- `bash -n docs/codex_audit/evidence/engineering_scheduler_h2_20260720/run_engineering_h2_slurm.sh` passed.
- `ctest --test-dir build-codex-smoke --output-on-failure` passed 22/22 tests.
