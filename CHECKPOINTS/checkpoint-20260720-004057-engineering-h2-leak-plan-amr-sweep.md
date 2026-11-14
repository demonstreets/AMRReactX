# Engineering H2 Leak Plan-AMR Sweep Checkpoint

Timestamp UTC: 20260720-004057

## Scope

Priority remains engineering production readiness first, with H2 open-domain/tank-farm leak and fire/detonation support ahead of academic-only gas/two-phase work.

This checkpoint records the first maintained dynamic open-domain H2 plan-AMR threshold sweep. It builds on the previous single-threshold dynamic AMR comparison by checking two H2 species-gradient thresholds and enforcing cost/error trend evidence.

## Changes

- Parameterized `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_compare.sh` for shorter reusable sweep runs: max step, plot interval, minimum plotfile count, minimum mass-growth ratio, and AMR grid sizes are now overrideable.
- Added `tools/codex_smoke_engineering_h2_leak_open_domain_plan_amr_sweep.sh` to run thresholds `1.0e-2` and `4.0e-2`, aggregate AMR, plume, hazard, and overhead metrics, and require bounded hazard deltas plus meaningful overhead response.
- Fixed H2 wrapper reuse by making `CODEX_H2_LEAK_HISTORY_MIN_PLOTFILES` and `CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO` override-safe through the open-domain and plume-profile wrappers.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` with the sweep evidence and remaining gaps.

## Evidence

PASS root: `/tmp/codex_h2_leak_open_domain_plan_amr_sweep_20260720_massfix`

Summary CSV: `/tmp/codex_h2_leak_open_domain_plan_amr_sweep_20260720_massfix/plan_amr_sweep_summary.csv`

Final gate:

`h2_leak_open_domain_plan_amr_sweep PASS output=/tmp/codex_h2_leak_open_domain_plan_amr_sweep_20260720_massfix/plan_amr_sweep_summary.csv thresholds=2 mean_ncells_ratio_min=1.40312500e+00 mean_ncells_ratio_max=1.76289063e+00 mean_ncells_ratio_spread=3.59765630e-01 max_cloud_rel_diff=1.32530122e-01 max_peak_rel_diff=5.68331993e-02`

Threshold trend:

- `amr.plan_species_gradient=1.0e-2`: `amr_finest_fabs=15`, `mean_ncells_ratio=1.76289063e+00`, `advance_seconds_ratio=2.54658458e+00`, `cloud_rel_diff=1.32530122e-01`, `peak_rel_diff=5.68331993e-02`.
- `amr.plan_species_gradient=4.0e-2`: `amr_finest_fabs=2`, `mean_ncells_ratio=1.40312500e+00`, `advance_seconds_ratio=1.63213195e+00`, `cloud_rel_diff=1.16564416e-01`, `peak_rel_diff=4.43360862e-02`.

## Verification

- PASS root log scan: 26 logs, zero failure markers.
- `python3 -m py_compile tools/amrex_reader.py tools/validate_h2_leak_plume_history.py tools/summarize_h2_leak_amr_overhead.py tools/test_amrex_reader_multibox.py tools/validate_h2_leak_hazard_timeseries.py` passed.
- `python3 tools/test_amrex_reader_multibox.py` passed.
- `python3 tools/check_machine_local_paths.py --strict` passed.
- `ctest --test-dir build-codex-smoke --output-on-failure` passed 22/22.

## Remaining Engineering Gaps

- Broader calibrated AMR threshold/efficiency/convergence sweeps across release rates, winds, domain sizes, tank-farm layouts, and multi-box partitions.
- Production MPI scaling and longer wall-clock stability for H2 leak, fire, and detonation workflows.
- Real CAD / large-layout tank-farm dynamic AMR campaigns.
- Reference-data validation for plume shape, flammable cloud envelope, ignition/fire response, and detonation metrics.
- More complete distributed-pipe-network, real-gas thermal cooldown, valve transient, and fire radiation/heat-release coupling evidence.
