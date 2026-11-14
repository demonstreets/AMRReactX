# Checkpoint: engineering campaign manifest

Date: 2026-07-20

## Context

User priority is engineering production readiness first. The H2 reduced-long plan-AMR MPI evidence now has a validated case report, but production handoff also needs a campaign-level index that can validate one or more case reports and collect report/input/summary hashes.

## Changes

- Added `tools/write_engineering_campaign_manifest.py`.
- The tool accepts one or more `--case-report` JSON files.
- It validates `schema_version=1`, `status=PASS`, limitations, reduced-long AMR metrics, positive final hazard metrics, dynamic regrid evidence, AMR drift bounds, AMR overhead ratios, expected log records, report SHA-256, and input/summary hash consistency.
- It writes campaign-level JSON and Markdown manifests.

## Evidence

Manifest root: `/tmp/codex_h2_engineering_campaign_manifest_20260720`.

Command result:

```text
engineering_campaign_manifest PASS campaign=h2-engineering-production-readiness cases=1 json=/tmp/codex_h2_engineering_campaign_manifest_20260720/campaign_manifest.json md=/tmp/codex_h2_engineering_campaign_manifest_20260720/campaign_manifest.md
```

Spot-check:

```text
status=PASS
campaign=h2-engineering-production-readiness
case_count=1
case=h2-open-domain-plan-amr-mpi-reduced-long
ranks=4
max_step=200
plotfiles=11
amr_final_cloud=0.0382080078125
cloud_rel_diff=0.130990415
case_report_sha256_prefix=d8e11313831fec8e
input_hashes=2
evidence_hashes=3
```

Markdown spot-check confirms the manifest includes case report path/hash, evidence root, MPI ranks/steps/plotfiles, final time, hazard metrics, AMR regrid count, overhead ratios, and global limitations.

## Verification

- `python3 -m py_compile tools/write_engineering_campaign_manifest.py tools/write_engineering_h2_case_report.py`
- `python3 tools/write_engineering_campaign_manifest.py --campaign h2-engineering-production-readiness --case-report /tmp/codex_h2_leak_open_domain_plan_amr_mpi_reduced_long_20260720/engineering_case_report.json --output-json /tmp/codex_h2_engineering_campaign_manifest_20260720/campaign_manifest.json --output-md /tmp/codex_h2_engineering_campaign_manifest_20260720/campaign_manifest.md`
- JSON field spot-check via Python
- Markdown first 80 lines inspected
- `python3 tools/check_machine_local_paths.py --strict`: `machine_local_paths PASS scanned_files=955`
- `ctest --test-dir build-codex-smoke --output-on-failure`: `100% tests passed, 0 tests failed out of 22`

## Remaining risk

This is campaign packaging and consistency validation, not a new physical validation result. It does not prove production-size CFD accuracy, real CAD/tank-farm coverage, scheduler/affinity behavior, overnight stability, fire heat-release validation, or experimental/reference-data agreement.
