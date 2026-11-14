# Checkpoint: Engineering H2 production evidence verifier

Date UTC: 2026-07-20 07:08:04

## What changed

- Added `tools/verify_engineering_h2_production_evidence.sh`, a one-command read-only verifier for current engineering H2 production evidence.
- The verifier checks the durable 16-case release pack, H2 acceptance matrix, production scorecard, scheduler-run report, ignition/fire consequence reports, all maintained production-scale/production-mesh scout reports, strict machine-local path audit, and `build-codex-smoke` CTest.
- First run exposed a real evidence consistency issue: the release pack stored an old hash for `plan-amr-mpi-reduced-long` after the long-open-boundary threshold propagation fix.
- Regenerated `docs/codex_audit/evidence/engineering_h2_production_full_20260720/release_pack` from the preserved campaign summary under `/tmp/codex_engineering_h2_campaign_full_20260720`, without launching new CFD cases.
- Refreshed `engineering_h2_acceptance_matrix` and `engineering_production_scorecard` so their referenced evidence hashes match the rebuilt pack.
- Added sanitized verification evidence under `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/`.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` with the new verification command and evidence path.

## Verification

- `bash -n tools/verify_engineering_h2_production_evidence.sh`: PASS.
- `tools/verify_engineering_h2_production_evidence.sh`: PASS.
- `python3 tools/check_machine_local_paths.py --strict`: PASS, scanned files = 967.
- CTest via verifier: 22/22 PASS in `build-codex-smoke`.

## Current engineering status

- Scorecard remains `NOT_PRODUCTION_READY`.
- Engineering functional coverage remains `90.8%`.
- Engineering production credibility remains `70.5%`.
- H2 acceptance matrix remains `PARTIAL-PRODUCTION`, with 6/7 pass-like rows.
- The only matrix `NOT_READY` row is still `scheduler_managed_campaign` because SLURM controller access is unavailable and no scheduler-managed CFD allocation has completed.

## Next best work

- Continue toward production credibility by either clearing the scheduler-managed campaign blocker when SLURM responds, or adding stronger non-scheduler production evidence: larger MPI/rank scaling, longer production-mesh runs, real-CAD/tank-farm geometry campaigns, calibrated fire/consequence validation, and reference-data agreement.
