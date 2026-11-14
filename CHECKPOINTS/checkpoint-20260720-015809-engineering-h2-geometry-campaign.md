# Checkpoint: engineering H2 geometry campaign execution

Date: 2026-07-20 UTC

## Context

User priority remains engineering production readiness first. The source-physics staged suite is already executed through `tools/run_engineering_h2_campaign.py`; this pass exercises the geometry suite that covers tank-farm EB union, multi-file STL merge, and per-file STL transform plumbing.

## Campaign

Command:

```text
python3 tools/run_engineering_h2_campaign.py --suite h2-geometry --campaign engineering-h2-geometry-staged --output-root /tmp/codex_engineering_h2_campaign_geometry_20260720 --case-timeout-s 1500
```

Result:

```text
engineering_h2_campaign PASS suite=h2-geometry cases=3 json=/tmp/codex_engineering_h2_campaign_geometry_20260720/campaign_run_summary.json md=/tmp/codex_engineering_h2_campaign_geometry_20260720/campaign_run_summary.md
```

Cases executed through the campaign runner:

```text
tank-farm duration=65.34 tank_farm_summary.csv:097c7989ccdc
stl-multifile duration=50.80 stl_obstacle_summary.csv:e6b3a0c86ffd
stl-perfile-transform duration=50.50 stl_obstacle_summary.csv:94bffbdb1a52
```

JSON spot-check:

```text
PASS h2-geometry 3
bad_cases []
markers []
md_exists True
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

- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` now records completed source-physics and geometry staged campaigns through the campaign runner.
- `docs/codex_audit/SMOKE_MATRIX.md` now records the geometry staged campaign evidence and keeps the full production-campaign limitation explicit.

## Remaining Risk

This proves a staged geometry campaign through the production runner. It does not complete the full 16-case engineering production campaign, production-size meshes, real CAD cleanup, broader CAD mesh quality classification, scheduler/affinity policy, overnight stability, fire heat-release metrics, or reference-data accuracy.
