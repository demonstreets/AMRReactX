# Checkpoint: engineering H2 leak plan-AMR MPI reduced-long stability

Date: 2026-07-20

## Context

User priority is engineering production readiness first. The H2 open-domain plan-AMR MPI chain already had 2-rank overlay evidence and a 2/4-rank consistency sweep, but the audit still listed long engineering stability campaigns as missing.

## Changes

- Added `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh`.
- The wrapper runs the maintained baseline-vs-plan-AMR MPI overlay with 4 MPI ranks, `max_step=200`, `plot_int=20`, `min_plotfiles=11`, and `amr.max_grid_size/amr.max_grid_size_x/y/z=8`.
- It validates final MPI logs, final plotfile FAB layouts, hazard time-series step/time monotonicity, finite nonnegative history metrics, sustained final flammable-cloud metrics, bounded AMR-vs-baseline hazard drift, and log failure markers.
- Fixed the reduced-long CSV summary writer after the first full successful run exposed a missing `final_step` field in the field list; reuse-mode rerun then passed from the already-computed successful subcases.

## Evidence

Evidence root: `/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720`.

Target gate result:

```text
h2_leak_open_domain_plan_amr_mpi_reduced_long PASS root=/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720 ranks=4 max_step=200 plotfiles=11/11 baseline_final_cloud=3.32031250e-02 amr_final_cloud=3.82080078e-02 amr_finest_level=1 amr_fabs=[(0, 16), (1, 47)] cloud_rel_diff=1.30990415e-01 peak_rel_diff=1.28011581e-01 log_files=14
[codex-smoke] PASS h2_leak open-domain plan-AMR MPI reduced-long root=/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720 summary=/tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720/reduced_long_summary.csv
```

Key metrics:

```text
ranks=4
max_step=200
plotfiles=11/11
final_time=0.2
baseline_fabs=[(0, 16)]
amr_fabs=[(0, 16), (1, 47)]
amr_regrid_count=99
amr_mass_ratioN=1.00000048e+00
baseline_final_cloud=3.32031250e-02
amr_final_cloud=3.82080078e-02
amr_final_flammable_planes=10
cloud_rel_diff=1.30990415e-01
peak_rel_diff=1.28011581e-01
centroid_abs_diff=1.68538700e-03
downstream_abs_diff=4.83289200e-03
mean_ncells_ratio=1.97898438e+00
advance_seconds_ratio=2.67246063e+00
final_plotfile_bytes_ratio=2.44258847e+00
```

## Verification

- `bash -n tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_mpi_reduced_long.sh`
- Target gate full run completed solver/profile/hazard/MPI checks; reuse-mode final summary PASS after the CSV writer fix
- `python3 tools/check_machine_local_paths.py --strict`: `machine_local_paths PASS scanned_files=953`
- `ctest --test-dir build-codex-smoke --output-on-failure`: `100% tests passed, 0 tests failed out of 22`

## Remaining risk

This is reduced-long smoke evidence, not production completion. It does not prove overnight stability, production-size MPI scaling, scheduler/affinity behavior, hybrid OpenMP safety, real CAD/large-layout tank-farm AMR load balance, fire heat-release validation, or experimental/reference-data accuracy.
