# Checkpoint: engineering H2 campaign runner

Date: 2026-07-20 UTC

## Context

User priority is engineering production readiness first. The H2 engineering line already had many case-level wrappers plus a reduced-long case report and a campaign manifest, but full production readiness also needs a reproducible runner that can launch curated multi-case campaigns, capture per-case logs, and package execution metadata.

## Changes

- Added `tools/run_engineering_h2_campaign.py`.
- Defined 16 curated engineering H2 campaign cases across `h2-core`, `h2-source-physics`, `h2-geometry`, `h2-amr-mpi`, and `h2-production-scout`.
- Added dry-run validation, suite aliases, `--only` case selection, per-case output roots, wrapper log-env assignment, return-code/duration capture, required-output SHA-256 capture, missing-output tracking, log-failure-marker scanning, git/host metadata, and JSON/Markdown summary writing.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`.
- Updated `docs/codex_audit/SMOKE_MATRIX.md`.

## Evidence

Dry-run production-suite enumeration:

```text
engineering_h2_campaign DRY-RUN suite=engineering-h2-production cases=16 json=/tmp/codex_engineering_h2_campaign_dryrun_20260720/campaign_run_summary.json md=/tmp/codex_engineering_h2_campaign_dryrun_20260720/campaign_run_summary.md
```

Dry-run JSON spot-check:

```text
DRY-RUN engineering-h2-production 16
open-domain plan-amr-mpi-reduced-long
['h2-amr-mpi', 'h2-core', 'h2-geometry', 'h2-production-scout', 'h2-source-physics']
True
```

Real runner execution for one source-physics case:

```text
engineering_h2_campaign PASS case=pressure-orifice root=/tmp/codex_engineering_h2_campaign_pressure_orifice_20260720/cases/pressure-orifice
engineering_h2_campaign PASS suite=engineering-h2-core cases=1 json=/tmp/codex_engineering_h2_campaign_pressure_orifice_20260720/campaign_run_summary.json md=/tmp/codex_engineering_h2_campaign_pressure_orifice_20260720/campaign_run_summary.md
```

Real-run JSON spot-check:

```text
PASS 1 PASS 0
pressure-orifice True 1 [] []
validation.log 6870743ae13b6841
```

## Verification

Commands run:

```text
python3 -m py_compile tools/run_engineering_h2_campaign.py
python3 tools/run_engineering_h2_campaign.py --suite engineering-h2-production --dry-run --output-root /tmp/codex_engineering_h2_campaign_dryrun_20260720
python3 tools/run_engineering_h2_campaign.py --only pressure-orifice --output-root /tmp/codex_engineering_h2_campaign_pressure_orifice_20260720 --case-timeout-s 900
```

Additional regression still to run after this checkpoint: strict path audit, CTest, and targeted grep verification after doc updates.

## Remaining Risk

This is an orchestration and evidence-packaging improvement. It does not complete production CFD validation. Full `engineering-h2-production` execution, production-size meshes, scheduler/affinity policy, overnight stability, fire heat-release metrics, real CAD cleanup, and reference-data validation remain open.
