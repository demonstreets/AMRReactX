# Engineering H2 External Plume Evidence Ledger

## Purpose

The production evidence verifier already checks the HySafe SBEPV5 / GexCon D27
external plume benchmark scaffold, dataset ingestion report, case package,
preflight report, external dataset builder report, and readiness report.

The top-level production evidence verification report did not yet hash and
summarize these external benchmark artifacts directly, which made the remaining
`reference_agreement_is_threshold_only_not_external_plume_shape_dataset` blocker
less visible in the durable evidence ledger.

## Change

Updated `tools/write_engineering_h2_production_evidence_verification_report.py`
to record and verify:

- `external_plume_benchmark_readiness_report.json`
- `sbepv5_d27_dataset_ingestion_report.json`
- `sbepv5_d27_external_dataset_report.json`
- `sbepv5_d27_case_package_report.json`
- `sbepv5_d27_case_package_preflight_report.json`

The report now records whether the external plume dataset JSON has been written,
whether external plume shape agreement exists, whether the SBEPV5 data files are
available, whether the case package is runnable, and whether the preflight
passes.

## Current Expected Status

The current status is expected to remain `NOT_READY` because real case-matched
SBEPV5/D27 experimental metadata, sensor coordinates, exact baffle geometry, and
experimental time series are not yet ingested.

## Limitation

This change does not fabricate or clear external plume validation evidence. It
makes the missing external benchmark data path explicit in the top-level
evidence report.
