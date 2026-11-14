# Checkpoint: engineering hybrid runtime-affinity preflight

Timestamp: 2026-07-20 07:37:59 UTC

## Scope

Continued the engineering-priority production-readiness track by closing a runtime evidence gap for MPI+OpenMP launch/binding policy. This work does not claim production H2 CFD hybrid scaling; it records and verifies an interactive hybrid preflight.

## Changes completed

- Generated a warning-free hybrid runtime-affinity manifest with `4` MPI ranks and `2` OpenMP threads per rank.
- Used explicit binding policy: `OMP_PROC_BIND=spread`, `OMP_PLACES=cores`, `OMP_NUM_THREADS=2`.
- Evidence written to `docs/codex_audit/evidence/engineering_runtime_affinity_hybrid_20260720/runtime_affinity_manifest.json` and `.md`.
- Updated `tools/write_engineering_production_scorecard.py` to treat hybrid runtime-affinity as a separate evidence input instead of overwriting the existing 4x1 scheduler handoff affinity manifest.
- Updated `tools/verify_engineering_h2_production_evidence.sh` to directly verify both runtime-affinity manifests.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` so human-facing status matches the scorecard.
- Refreshed `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json`, `.md`, and sanitized `verification.log`.

## Current scorecard

- Status: `NOT_PRODUCTION_READY`.
- Engineering functional coverage: `91.8`.
- Engineering production credibility: `71.5`.
- Runtime/scheduler gate: `PARTIAL+`.
- Hybrid runtime-affinity summary: `status=PASS`, `ranks=4`, `threads_per_rank=2`, `warnings=[]`.
- Scheduler status remains `NOT_READY`.

## Verification

- `python3 tools/write_engineering_runtime_affinity_manifest.py --verify-json docs/codex_audit/evidence/engineering_runtime_affinity_hybrid_20260720/runtime_affinity_manifest.json`: `VERIFY-PASS ranks=4 threads=2 warnings=0`.
- `python3 -m py_compile tools/write_engineering_production_scorecard.py`: PASS.
- `bash -n tools/verify_engineering_h2_production_evidence.sh`: PASS.
- `tools/verify_engineering_h2_production_evidence.sh`: PASS.
- `python3 tools/check_machine_local_paths.py --strict`: `machine_local_paths PASS scanned_files=968`.
- `build-codex-smoke` CTest inside the unified verifier: `22/22 PASS`.

## Remaining blockers

- Completed scheduler-managed engineering campaign is still missing because the current SLURM evidence remains `NOT_READY` / controller unavailable.
- Production-size H2 CFD campaign is not yet executed.
- Overnight/full-duration stability is not yet executed.
- Real CAD/industrial layout cleanup and regression cases remain open.
- External reference-data agreement for dispersion/detonation/fire remains open.
- Calibrated fire/radiation/overpressure validation remains open.
- Production H2 CFD hybrid performance/scaling remains open; this checkpoint only proves the interactive launch/binding preflight.

## Suggested next engineering move

If the scheduler remains unavailable, the next high-value local step is a larger non-scheduler H2 production-size surrogate or a short PeleLMeX H2 CFD hybrid smoke/scout that reuses the existing production-mesh workflow with explicit OpenMP binding. If the scheduler responds, rerun the prepared SLURM production-scout campaign first.
