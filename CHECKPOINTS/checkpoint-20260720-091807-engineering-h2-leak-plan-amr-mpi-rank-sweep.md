# Checkpoint: engineering H2 leak plan-AMR MPI rank sweep

Date: 2026-07-20

## Context

User priority is engineering production readiness first. The previous H2 open-domain dynamic plan-AMR MPI overlay proved the maintained baseline-vs-AMR chain could run on 2 MPI ranks, but it did not prove that AMR hazard metrics remain stable when rank count changes.

## Changes

- Added `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_rank_sweep.sh`.
- The wrapper runs the maintained H2 open-domain plan-AMR MPI gate for ranks 2 and 4 with `max_step=80`, `plot_int=20`, `min_plotfiles=5`, and `amr.max_grid_size/amr.max_grid_size_x/y/z=8` so distributed output has enough FABs for rank-sweep validation.
- It writes `rank_sweep_cases.tsv` and `rank_sweep_summary.csv`, validates each baseline/AMR MPI log, scans subcase logs for failure markers, and enforces identical AMR hazard metrics across ranks within `1e-10`.
- Fixed the rank-sweep summary CSV writer after the first full run exposed a missing `baseline_cloud_volume` field in the field list; reuse-mode rerun then passed from the already-computed successful subcases.

## Evidence

Evidence root: `/tmp/codex_h2_leak_open_domain_plan_amr_mpi_rank_sweep_20260720`.

Target gate result:

```text
h2_leak_open_domain_plan_amr_mpi_rank_sweep PASS cases=2 ranks=2,4 summary=/tmp/codex_h2_leak_open_domain_plan_amr_mpi_rank_sweep_20260720/rank_sweep_summary.csv log_files=28 max_cloud_rel_vs_ref=0.00000000e+00 max_peak_rel_vs_ref=0.00000000e+00
[codex-smoke] PASS h2_leak open-domain plan-AMR MPI rank sweep ...
```

Both rank cases reported matching AMR comparison metrics:

```text
amr_finest_level=1
amr_finest_fabs=36
regrid_count=39
cloud_rel_diff=1.32530122e-01
peak_rel_diff=5.27292147e-02
centroid_abs_diff=1.79225400e-04
downstream_abs_diff=8.39265200e-03
```

MPI validation covered both baseline and AMR logs for ranks 2 and 4, with `final_time=0.08`, `finalized=1`, and the known `mpi_thread_support_level_0` warning classification.

## Verification

- `bash -n tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_rank_sweep.sh tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi.sh`
- Log scan over `/tmp/codex_h2_leak_open_domain_plan_amr_mpi_rank_sweep_20260720`: `log_files=28`, `failure_marker_hits=0`
- `python3 tools/check_machine_local_paths.py --strict`: `machine_local_paths PASS scanned_files=952`
- `ctest --test-dir build-codex-smoke --output-on-failure`: `100% tests passed, 0 tests failed out of 22`

## Remaining risk

This is still a smoke-grid 2/4-rank consistency gate. It does not prove production-size MPI scaling, scheduler/affinity behavior, hybrid OpenMP safety, long-time stability, real CAD/large-layout AMR load balance, or reference-data accuracy.
