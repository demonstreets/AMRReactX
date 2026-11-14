# Checkpoint: engineering H2 production-scout staged campaign

Date: 2026-07-20 UTC
Scope: engineering-priority H2 gas leak production-readiness staged validation.

## Context

The engineering H2 line had already passed the staged `h2-core`, `h2-source-physics`, `h2-geometry`, and `h2-amr-mpi` suites. This checkpoint records the next production-readiness scout: a 4-rank, 200-step, dynamic plan-AMR MPI reduced-long stability case driven through the unified campaign/report/manifest tooling.

This is not a full production campaign. It is the staged long-run scout before expanding to the full 16-case production matrix and production-size overnight runs.

## Campaign execution

Command:

```bash
python3 tools/run_engineering_h2_campaign.py \
  --suite h2-production-scout \
  --campaign engineering-h2-production-scout-staged \
  --output-root /tmp/codex_engineering_h2_campaign_production_scout_20260720 \
  --case-timeout-s 5400
```

Result:

```text
engineering_h2_campaign PASS case=plan-amr-mpi-reduced-long root=/tmp/codex_engineering_h2_campaign_production_scout_20260720/cases/plan-amr-mpi-reduced-long
engineering_h2_campaign PASS suite=h2-production-scout cases=1 json=/tmp/codex_engineering_h2_campaign_production_scout_20260720/campaign_run_summary.json md=/tmp/codex_engineering_h2_campaign_production_scout_20260720/campaign_run_summary.md
```

## Evidence spot-check

Campaign summary and case report were re-read after execution, and the expected report artifacts were present.

```text
PASS h2-production-scout 1
plan-amr-mpi-reduced-long PASS 0 duration=107.54
missing []
markers []
reduced_long_summary.csv 4166ac92139e9683
engineering_case_report.json 54ec20dc6cdfdf3e
engineering_case_report.md 560bcca52304c2dd
md_exists True
report PASS h2-open-domain-plan-amr-mpi-reduced-long
report_amr 4 200 11 1
report_deltas 0.130990415 0.128011581
summary_row baseline 4 200 11 0 0.033203125 0.1973282076444 5
summary_row amr 4 200 11 1 0.0382080078125 0.2262968219809 10 1.30990415e-01
```

Interpretation:

- The runner completed the `h2-production-scout` suite with 1/1 PASS.
- The case report status is PASS for `h2-open-domain-plan-amr-mpi-reduced-long`.
- The AMR branch ran on 4 MPI ranks to step 200, emitted 11 plotfiles, and reached finest_level=1.
- AMR increased final cloud volume from 0.033203125 to 0.0382080078125 and peak cloud volume from 0.1973282076444 to 0.2262968219809 in this reduced scout. These are expected to be monitored as sensitivity metrics, not treated as production validation by themselves.

## Campaign manifest

Command:

```bash
python3 tools/write_engineering_campaign_manifest.py \
  --campaign h2-production-scout-staged \
  --case-report /tmp/codex_engineering_h2_campaign_production_scout_20260720/cases/plan-amr-mpi-reduced-long/engineering_case_report.json \
  --output-json /tmp/codex_engineering_h2_campaign_production_scout_20260720/campaign_manifest.json \
  --output-md /tmp/codex_engineering_h2_campaign_production_scout_20260720/campaign_manifest.md
```

Result:

```text
engineering_campaign_manifest PASS campaign=h2-production-scout-staged cases=1 json=/tmp/codex_engineering_h2_campaign_production_scout_20260720/campaign_manifest.json md=/tmp/codex_engineering_h2_campaign_production_scout_20260720/campaign_manifest.md
```

Manifest spot-check:

```text
PASS h2-production-scout-staged 1
h2-open-domain-plan-amr-mpi-reduced-long 4 200 11 99
54ec20dc6cdfdf3e 2 3
True
```

The manifest records one PASS case, preserves the case report SHA prefix `54ec20dc6cdfdf3e`, includes two input hashes, three evidence hashes, and reports `amr_regrid_count=99` for the AMR run.

## Regression checks after campaign

Commands:

```bash
python3 -m py_compile tools/run_engineering_h2_campaign.py tools/write_engineering_campaign_manifest.py tools/write_engineering_h2_case_report.py
python3 tools/check_machine_local_paths.py --strict
ctest --test-dir build-codex-smoke --output-on-failure
```

Results:

```text
machine_local_paths PASS scanned_files=956
100% tests passed, 0 tests failed out of 22
```

## Documentation updated

Updated:

- `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md`
- `docs/codex_audit/SMOKE_MATRIX.md`

The documentation now states that all five staged H2 engineering suites have passed through the runner path: `h2-core`, `h2-source-physics`, `h2-geometry`, `h2-amr-mpi`, and `h2-production-scout`.

## Remaining production gaps

Engineering H2 readiness is materially advanced, but it is still not full production certification. Remaining work before calling the engineering line production-grade:

- Execute the full 16-case production campaign, not only staged subsets.
- Run production-size meshes and longer physical times, ideally overnight or scheduler-managed.
- Add scheduler/resource-affinity evidence for the intended deployment environment.
- Expand fire-specific metrics and acceptance criteria for large-scale tank/pipeline fire scenarios.
- Exercise real CAD or production geometry ingestion paths, not only reduced fixtures.
- Compare selected scenarios against reference data or accepted engineering correlations.
- Preserve final production manifests and reports under durable project storage instead of only `/tmp` evidence paths.
