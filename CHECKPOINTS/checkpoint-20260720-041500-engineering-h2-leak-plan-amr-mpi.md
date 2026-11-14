# Checkpoint: engineering H2 leak dynamic plan-AMR MPI overlay

Date: 2026-07-20

## Scope

Advanced the engineering-production priority by proving the maintained H2 open-domain leak workflow can combine dynamic plan-AMR with MPI execution and distributed plot output. This closes the first AMR+MPI overlay smoke gap while keeping larger-rank scaling and long-time stability open.

## Code Changes

- Added `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi.sh`.
- The wrapper reuses `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_compare.sh`, exports `CODEX_H2_LEAK_HISTORY_USE_MPI=TRUE`, validates baseline and AMR MPI logs, and checks final plotfile FAB counts across levels.

## Evidence

- Target gate: `CODEX_H2_LEAK_PLAN_AMR_MPI_LOG_DIR=/tmp/codex_h2_leak_open_domain_plan_amr_mpi_20260720 RUN_TIMEOUT=900 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi.sh`
- PASS root: `/tmp/codex_h2_leak_open_domain_plan_amr_mpi_20260720`
- AMR comparison PASS: `amr_finest_level=1`, `amr_finest_fabs=16`, `regrid_count=49`, `cloud_rel_diff=7.85340319e-02`, `peak_rel_diff=4.21517687e-02`, `centroid_abs_diff=3.27653000e-04`, `downstream_abs_diff=5.61330700e-03`.
- Overhead PASS: `mean_ncells_ratio=1.68921875e+00`, `advance_seconds_ratio=2.20741323e+00`, `final_plotfile_bytes_ratio=2.11334374e+00`.
- MPI overlay validation PASS: `baseline_finest_level=0`, `baseline_fabs=[(0, 2)]`, `amr_finest_level=1`, `amr_fabs=[(0, 2), (1, 16)]`.
- Both baseline and AMR MPI logs PASS with `solver=pelelmex`, `mode=mpi`, `ranks=2`, `final_time=0.1`, and `warning=mpi_thread_support_level_0`.

## Verification

- PASS-root scan: 14 log files, zero `FAIL`/`ERROR`/`Traceback`/`Abort`/`Backtrace`/`Unused ParmParse Variables` markers.
- `bash -n tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi.sh tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_compare.sh tools/codex_smoke_engineering_h2_leak_plume_history.sh`
- `python3 tools/check_machine_local_paths.py --strict`: `machine_local_paths PASS scanned_files=951`.
- `ctest --test-dir build-codex-smoke --output-on-failure`: 22/22 passed.

## Remaining Risk

This is a 2-rank coarse AMR+MPI overlay smoke, not a scaling or long-stability result. Production readiness still needs larger rank counts, scheduler/affinity and MPI thread-support policy, AMR load-balance studies, real CAD/tank-farm production meshes, fire/heat-release validation, and longer engineering campaigns.
