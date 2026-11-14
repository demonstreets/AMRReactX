# Checkpoint: full engineering H2 production campaign

Date: 2026-07-20 UTC
Scope: engineering-priority H2 gas leak production-readiness campaign execution and manifest packaging.

## What changed

The previous state had all five staged engineering H2 campaign suites passing independently. This checkpoint records the first real full `engineering-h2-production` runner execution across all 16 curated smoke-scale production-readiness cases, plus a manifest-tool extension that can validate a full runner summary, not only a reduced-long case report.

## Full campaign execution

Command:

```bash
python3 tools/run_engineering_h2_campaign.py \
  --suite engineering-h2-production \
  --campaign engineering-h2-production-full-20260720 \
  --output-root /tmp/codex_engineering_h2_campaign_full_20260720 \
  --case-timeout-s 7200
```

Runner result:

```text
engineering_h2_campaign PASS suite=engineering-h2-production cases=16 json=/tmp/codex_engineering_h2_campaign_full_20260720/campaign_run_summary.json md=/tmp/codex_engineering_h2_campaign_full_20260720/campaign_run_summary.md
```

Post-run JSON spot-check:

```text
summary PASS engineering-h2-production 16
summary_sha 7a4c5fea708e4f77
markdown_exists True
md_sha 9e6fccc59cf91335
failures []
```

All 16 cases returned `PASS`, return code 0, no missing required files, and no runner-detected failure markers.

Case duration/hash sample:

```text
open-domain h2-core PASS 0 duration=26.29 req=5 hashes=5 first=18d8c1090358,967a00cf3d2d,a5f8e50037f0
release-rate h2-core PASS 0 duration=52.41 req=1 hashes=1 first=aec5656d84f2
crosswind h2-core PASS 0 duration=53.36 req=1 hashes=1 first=2a86d4dff9f2
low-wind h2-core PASS 0 duration=52.51 req=1 hashes=1 first=d9fe423b3037
pressure-orifice h2-source-physics PASS 0 duration=14.50 req=1 hashes=1 first=6870743ae13b
real-gas-orifice h2-source-physics PASS 0 duration=14.50 req=1 hashes=1 first=ba9b0135e493
tank-blowdown h2-source-physics PASS 0 duration=14.30 req=1 hashes=1 first=49d4b7d71032
real-gas-tank-blowdown h2-source-physics PASS 0 duration=14.15 req=1 hashes=1 first=f3783cc5c09d
pipe-loss h2-source-physics PASS 0 duration=14.35 req=1 hashes=1 first=cf59117e435c
linepack-blowdown h2-source-physics PASS 0 duration=15.35 req=1 hashes=1 first=5b2190d73cc0
linepack-valve-schedule h2-source-physics PASS 0 duration=14.85 req=1 hashes=1 first=674bcffed1a1
tank-farm h2-geometry PASS 0 duration=65.24 req=1 hashes=1 first=d1fde805798b
stl-multifile h2-geometry PASS 0 duration=51.25 req=1 hashes=1 first=c86da1e55209a
stl-perfile-transform h2-geometry PASS 0 duration=50.60 req=1 hashes=1 first=853c049d0e33
plan-amr-mpi-rank-sweep h2-amr-mpi PASS 0 duration=116.30 req=1 hashes=1 first=82524eb74f6a
plan-amr-mpi-reduced-long h2-production-scout PASS 0 duration=108.40 req=3 hashes=3 first=4166ac92139e,c90c9b7877ea,f0bc45cc8093
```

Total summed case duration was `678.38s`.

## Manifest-tool extension

`tools/write_engineering_campaign_manifest.py` now supports two modes:

- `--case-report`, preserving the previous reduced-long case-report validation path.
- `--campaign-run-summary`, validating a full campaign runner summary.

The new runner-summary mode verifies:

- summary schema/status/case count and Markdown summary presence;
- every case is PASS with return code 0;
- no missing required files and no failure markers;
- wrapper scripts, case logs, and required evidence files exist;
- required evidence SHA-256 values still match current files;
- case names are unique;
- repo dirty metadata is compacted to branch/commit/dirty line count/dirty hash instead of embedding the full dirty list.

Compatibility check:

```text
engineering_campaign_manifest PASS campaign=h2-production-scout-compat-check cases=1 json=/tmp/codex_manifest_compat_check_20260720/campaign_manifest.json md=/tmp/codex_manifest_compat_check_20260720/campaign_manifest.md
```

Full summary manifest generation:

```text
engineering_campaign_manifest PASS campaign=engineering-h2-production-full-20260720 cases=16 json=/tmp/codex_engineering_h2_campaign_full_20260720/campaign_manifest.json md=/tmp/codex_engineering_h2_campaign_full_20260720/campaign_manifest.md
```

Manifest spot-check:

```text
manifest PASS campaign_run_summary engineering-h2-production-full-20260720 16 5
manifest_sha b42719b95f920174
manifest_md_sha e8b3e79cb930942b
summary_sha 7a4c5fea708e4f77
summary_md_sha 9e6fccc59cf91335
repo dirty=True dirty_short_line_count=469 dirty_short_sha256=7ba70535fda4cda71131bc1c5701922bae95a366aae097870aa2e42f5f487329
```

A compact project-local copy of the manifest was added at:

```text
docs/codex_audit/evidence/engineering_h2_production_full_20260720/campaign_manifest.json
docs/codex_audit/evidence/engineering_h2_production_full_20260720/campaign_manifest.md
```

## Documentation updated

Updated:

- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
- `docs/codex_audit/SMOKE_MATRIX.md`

The docs now distinguish between:

- full 16-case `engineering-h2-production` smoke-scale campaign: PASS;
- production-grade engineering certification: still incomplete.

## Remaining engineering production gaps

This is a major H2 engineering milestone, but it is not final production certification. Remaining gaps include:

- production-size meshes and stronger hazardous-release strengths;
- overnight or long physical-time stability;
- scheduler/resource-affinity policy and larger MPI scale;
- production-size multi-box and real CAD/tank-farm geometries;
- richer fire metrics, temperature/heat-release acceptance criteria, and fuel-specific limits;
- reference data, engineering correlations, or experimental/literature comparisons;
- full detonation and non-H2 engineering scenario parity with the H2 gas-leak evidence chain.
