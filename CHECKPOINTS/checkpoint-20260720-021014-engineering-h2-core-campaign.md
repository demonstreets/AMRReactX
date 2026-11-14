# Checkpoint: engineering H2 core campaign execution

Date: 2026-07-20 UTC

## Context

User priority remains engineering production readiness first. Source-physics, geometry, and AMR/MPI staged suites have already executed through `tools/run_engineering_h2_campaign.py`. This pass exercises the core dispersion suite for open-domain hazard outputs, release-rate response, crosswind response, and low-wind/source-retention response.

## Campaign

Command:

```text
python3 tools/run_engineering_h2_campaign.py --suite h2-core --campaign engineering-h2-core-staged --output-root /tmp/codex_engineering_h2_campaign_core_20260720 --case-timeout-s 1800
```

Result:

```text
engineering_h2_campaign PASS suite=h2-core cases=4 json=/tmp/codex_engineering_h2_campaign_core_20260720/campaign_run_summary.json md=/tmp/codex_engineering_h2_campaign_core_20260720/campaign_run_summary.md
```

JSON spot-check:

```text
PASS h2-core 4
open-domain duration=26.24 validation.log:18d8c1090358,profile_validation.log:9119638794bb,hazard_summary.log:94563482b9fc,hazard_planes.csv:bd719f3055c8,hazard_timeseries.csv:3ca5aee1813f
release-rate duration=52.21 release_rate_summary.csv:f515e8b91db9
crosswind duration=52.90 crosswind_summary.csv:8c0f14deaa03
low-wind duration=52.11 low_wind_summary.csv:cc7801d5dfff
bad_cases []
markers []
md_exists True
```

Trend spot-checks:

```text
release-rate: low_release cloud=1.75781250e-02 peak=8.42193316e-02; high_release cloud=2.53906250e-02 peak=2.32350305e-01
crosswind: baseline lateral_y_shift=0.00000000e+00; crosswind lateral_y_shift=3.20681320e-02
low-wind: baseline downstream_fraction=8.49997579e-01 centroid_shift=1.01245408e-01; low_wind downstream_fraction=6.15805511e-01 centroid_shift=2.65765289e-02
```

## Verification

Commands run after campaign execution:

```text
python3 -m py_compile tools/run_engineering_h2_campaign.py tools/write_engineering_campaign_manifest.py tools/write_engineering_h2_case_report.py
python3 tools/check_machine_local_paths.py --strict
ctest --test-dir build-codex-smoke --output-on-failure
```

Verification output summary:

```text
machine_local_paths PASS scanned_files=956
100% tests passed, 0 tests failed out of 22
```

## Docs Updated

- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` now records completed core dispersion, source-physics, geometry, and AMR/MPI staged campaigns through the campaign runner.
- `docs/codex_audit/SMOKE_MATRIX.md` now records the h2-core staged campaign evidence and keeps the full production-campaign limitation explicit.

## Remaining Risk

This proves a staged core dispersion campaign through the production runner. It does not complete the full 16-case engineering production campaign, production-size hazardous releases, long-time plume-shape reference validation, broader boundary-condition/calm-wind/ABL validation, scheduler/affinity policy, overnight stability, fire heat-release metrics, or reference-data accuracy.
