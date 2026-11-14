# Checkpoint: engineering H2 leak open-domain MPI smoke

Date: 2026-07-20

## Scope

Advanced the engineering-production priority by adding a maintained 2-rank MPI gate for the H2 open-domain leak workflow. This targets the ENG-P1 parallel/long-stability gap without claiming production-size scaling.

## Code Changes

- Added `tools/codex_smoke_engineering_h2_leak_open_domain_mpi.sh`.
- Parameterized `tools/codex_smoke_engineering_h2_leak_plume_history.sh` with `CODEX_H2_LEAK_HISTORY_USE_MPI`, `CODEX_H2_LEAK_HISTORY_EBASE`, and MPI rank environment support while preserving the default serial path.

## Evidence

- Target gate: `CODEX_H2_LEAK_OPEN_DOMAIN_MPI_LOG_DIR=/tmp/codex_h2_leak_open_domain_mpi_20260720 RUN_TIMEOUT=420 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_open_domain_mpi.sh`
- PASS root: `/tmp/codex_h2_leak_open_domain_mpi_20260720`
- H2 plume/history/profile/hazard chain PASS: `timeN=0.1`, `mass_ratioN=1.00000000e+00`, `cloud_volume=2.14843750e-02`, `active_planes=4`, `flammable_planes=2`, `final_peak_X=1.61483568e-01`.
- MPI log validation PASS: `parallel_smoke_log_validation PASS solver=pelelmex mode=mpi ranks=2 threads=na final_time=0.1 finalized=1 warning=mpi_thread_support_level_0`.
- Final plotfile distributed-output check PASS: `final_plot=plt00100`, `fab_count=2`.

## Verification

- `bash -n tools/codex_smoke_engineering_h2_leak_plume_history.sh tools/codex_smoke_engineering_h2_leak_open_domain_mpi.sh`
- `python3 -m py_compile tools/validate_parallel_smoke_log.py tools/validate_h2_leak_plume_history.py tools/validate_h2_leak_plume_profile.py tools/validate_h2_leak_hazard_summary.py tools/validate_h2_leak_hazard_planes.py tools/validate_h2_leak_hazard_timeseries.py`
- PASS-root scan: 7 log files, zero `FAIL`/`ERROR`/`Traceback`/`Abort`/`Backtrace`/`Unused ParmParse Variables` markers.
- `python3 tools/check_machine_local_paths.py --strict`: `machine_local_paths PASS scanned_files=950`.
- Serial regression: `CODEX_H2_LEAK_HISTORY_LOG_DIR=/tmp/codex_h2_leak_plume_history_post_mpi_20260720 RUN_TIMEOUT=180 JOBS=4 bash tools/codex_smoke_engineering_h2_leak_plume_history.sh` PASS.
- `ctest --test-dir build-codex-smoke --output-on-failure`: 22/22 passed.

## Remaining Risk

This is a 2-rank coarse smoke, not a scaling result. Production readiness still needs longer engineering MPI runs, larger rank counts, AMR+MPI overlays, scheduler/affinity/thread-support policy, real CAD/tank-farm production meshes, fire/heat-release metrics, and reference-data validation.
