# Checkpoint: engineering H2 MPI scaling scout evidence

Timestamp: 2026-07-20 07:30:55 UTC

## Scope

Continued the engineering-priority production-readiness track for `/home/cj/my-pele`, focused on H2 tank/pipeline leak dispersion AMR/MPI evidence and audit consistency.

## Changes completed

- Added and verified `tools/write_engineering_h2_mpi_scaling_report.py` to combine the 4-rank, 8-rank, and 16-rank production-mesh scout reports into a hash-checked MPI scaling/consistency report.
- Generated maintained evidence at `docs/codex_audit/evidence/engineering_h2_mpi_scaling_20260720/mpi_scaling_report.json` and `.md`.
- Integrated the MPI scaling report into `tools/write_engineering_production_scorecard.py` and `tools/verify_engineering_h2_production_evidence.sh`.
- Regenerated the engineering production scorecard: `status=NOT_PRODUCTION_READY`, `engineering_functional_coverage_percent=91.1`, `engineering_production_credibility_percent=71.2`.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` so human-facing status matches the machine-readable scorecard and verifier output.

## Key MPI scaling evidence

- Rank series: `[4, 8, 16]`.
- Mesh: baseline `64x32x32` (`65536` cells), AMR-equivalent fine grid `128x64x64` (`524288` cells).
- Status: `PASS-SCALING-SCOUT`.
- Hazard consistency: `cloud_rel_diff_spread=0`, `peak_rel_diff_spread=0`.
- Runtime trend: `baseline_speedup_4_to_16=1.82066093`, `amr_speedup_4_to_16=1.82631363`.
- Max AMR/baseline advance-time ratio across the rank series: `1.83771921`.
- 16-rank AMR finest FAB count: `73`, which is sufficient for the 16-rank scout decomposition check.

## Verification run after documentation sync

- `python3 tools/check_machine_local_paths.py --strict`: `machine_local_paths PASS scanned_files=968`.
- `tools/verify_engineering_h2_production_evidence.sh`: PASS.
- Verified within the unified command:
  - release evidence pack: `VERIFY-PASS`, 16 cases.
  - H2 acceptance matrix: `PARTIAL-PRODUCTION`, pass-like rows `6`, not-ready rows `1`.
  - engineering production scorecard: `NOT_PRODUCTION_READY`, `functional=91.1`, `production=71.2`.
  - scheduler run report: `NOT_READY`, checks `22`.
  - ignition consequence report: `PASS-SMOKE`.
  - fire consequence screening report: `PASS-SCREENING`.
  - MPI scaling report: `VERIFY-PASS`, ranks `[4, 8, 16]`.
  - all maintained production-scale/production-mesh scout reports: `VERIFY-PASS`.
  - strict path audit: PASS.
  - `build-codex-smoke` CTest: `22/22 PASS`.

## Current engineering readiness interpretation

The engineering H2 leak-dispersion chain is now strong at the maintained smoke/scout level and has first 4/8/16 MPI scaling evidence on the production-mesh scout. It is still not production-ready in the strict sense because the remaining blockers are not cosmetic.

## Remaining blockers

- Completed scheduler-managed engineering campaign: still blocked by current SLURM controller availability; existing structured evidence reports `CONTROLLER_UNAVAILABLE`.
- Full production-size large-domain campaign: not yet executed.
- Overnight/full-duration stability: not yet executed.
- Real CAD/industrial layout cleanup and regression cases: not yet completed.
- External reference-data agreement for dispersion/detonation/fire: not yet established.
- Calibrated fire/radiation/overpressure consequence validation: current report remains screening-only.
- Hybrid MPI/OpenMP policy and validation: not yet completed.

## Suggested next engineering move

When continuing, prefer a non-scheduler large-domain surrogate or a scheduler retry depending on cluster state. If SLURM remains unavailable, the highest-value local progress is a larger non-scheduler production-size surrogate with stricter runtime/resource manifesting, followed by hybrid MPI/OpenMP preflight and longer-duration stability evidence.
