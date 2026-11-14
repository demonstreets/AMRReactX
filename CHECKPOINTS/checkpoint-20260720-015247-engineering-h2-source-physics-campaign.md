# Checkpoint: engineering H2 source-physics campaign execution

Date: 2026-07-20 UTC

## Context

User priority remains engineering production readiness first. The previous pass added `tools/run_engineering_h2_campaign.py` and proved dry-run orchestration plus one pressure-orifice case. This pass exercises the runner on the complete staged `h2-source-physics` suite.

## Campaign

Command:

```text
python3 tools/run_engineering_h2_campaign.py --suite h2-source-physics --campaign engineering-h2-source-physics-staged --output-root /tmp/codex_engineering_h2_campaign_source_physics_20260720 --case-timeout-s 1200
```

Result:

```text
engineering_h2_campaign PASS suite=h2-source-physics cases=7 json=/tmp/codex_engineering_h2_campaign_source_physics_20260720/campaign_run_summary.json md=/tmp/codex_engineering_h2_campaign_source_physics_20260720/campaign_run_summary.md
```

Cases executed through the campaign runner:

```text
pressure-orifice duration=14.25 validation.log:6870743ae13b
real-gas-orifice duration=14.25 validation.log:ba9b0135e493
tank-blowdown duration=14.20 validation.log:49d4b7d71032
real-gas-tank-blowdown duration=13.95 validation.log:f3783cc5c09d
pipe-loss duration=14.20 validation.log:cf59117e435c
linepack-blowdown duration=15.36 validation.log:5b2190d73cc0
linepack-valve-schedule duration=14.66 validation.log:674bcffed1a1
```

JSON spot-check:

```text
PASS h2-source-physics 7
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

- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` now records the completed 7-case source-physics staged campaign.
- `docs/codex_audit/SMOKE_MATRIX.md` now records the same campaign evidence and keeps the full production-campaign limitation explicit.

## Remaining Risk

This proves a staged source-physics campaign through the production runner. It does not complete the full 16-case engineering production campaign, production-size meshes, scheduler/affinity policy, overnight stability, real CAD cleanup, fire heat-release metrics, or reference-data accuracy.
