# Checkpoint: engineering H2 AMR/MPI campaign execution

Date: 2026-07-20 UTC

## Context

User priority remains engineering production readiness first. Source-physics and geometry staged suites have already executed through `tools/run_engineering_h2_campaign.py`. This pass exercises the AMR/MPI staged suite for dynamic plan-AMR 2/4-rank consistency.

## Campaign

Command:

```text
python3 tools/run_engineering_h2_campaign.py --suite h2-amr-mpi --campaign engineering-h2-amr-mpi-staged --output-root /tmp/codex_engineering_h2_campaign_amr_mpi_20260720 --case-timeout-s 3600
```

Result:

```text
engineering_h2_campaign PASS suite=h2-amr-mpi cases=1 json=/tmp/codex_engineering_h2_campaign_amr_mpi_20260720/campaign_run_summary.json md=/tmp/codex_engineering_h2_campaign_amr_mpi_20260720/campaign_run_summary.md
```

JSON spot-check:

```text
PASS h2-amr-mpi 1
plan-amr-mpi-rank-sweep PASS 0 duration=115.61
missing []
markers []
rank_sweep_summary.csv 03e56a97565cb3c8
md_exists True
```

Rank-sweep CSV excerpt:

```text
ranks,baseline_cloud_volume,amr_finest_level,amr_finest_fab_count,amr_regrid_count,amr_cloud_volume,amr_max_X,amr_centroid_shift,amr_downstream_fraction,cloud_rel_vs_ref,peak_rel_vs_ref,centroid_abs_vs_ref,downstream_abs_vs_ref
2,0.017578125,1,36,39,0.0202636719,0.126037342,0.0811247952,0.820912035,0.0,0.0,0.0,0.0
4,0.017578125,1,36,39,0.0202636719,0.126037342,0.0811247952,0.820912035,0.0,0.0,0.0,0.0
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

- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` now records completed source-physics, geometry, and AMR/MPI staged campaigns through the campaign runner.
- `docs/codex_audit/SMOKE_MATRIX.md` now records the AMR/MPI staged campaign evidence and keeps the full production-campaign limitation explicit.

## Remaining Risk

This proves a staged AMR/MPI rank-sweep campaign through the production runner. It does not complete the full 16-case engineering production campaign, production-size MPI scaling, AMR load balance studies, scheduler/affinity policy, overnight stability, real CAD/tank-farm dynamic AMR, fire heat-release metrics, or reference-data accuracy.
