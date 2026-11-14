# 2026-07-23 H2 External Plume Benchmark Spec Gate

## Scope

Production-readiness blocker:
`reference_agreement_is_threshold_only_not_external_plume_shape_dataset`.

The external plume readiness report had public benchmark candidates, but the
selected benchmark was still represented as prose. This pass adds a
machine-checkable HySafe SBEPV5 / GexCon D27 case specification so future work
can generate the case input, sensor probes, and experimental comparison dataset
against a stable source record.

## Changes

Added `tools/write_engineering_h2_external_plume_benchmark_spec.py`.

The report records:

- literature source metadata and public URLs;
- D27 vessel dimensions, baffle inventory, vent opening, and release table
  values;
- reliable and unreliable sensor subsets;
- required PeleLMeX outputs and recommended agreement metrics;
- remaining pre-ingestion gaps.

The report explicitly sets `clears_reference_data_blocker = false`. It is a
case-build prerequisite, not experimental agreement evidence.

`tools/write_engineering_h2_external_plume_benchmark_readiness.py` now consumes
the benchmark spec report and exposes preparation fields such as
`case_spec_report_available`, `release_geometry_metadata_available`,
`reliable_sensor_subset_declared`, and
`digitized_experimental_timeseries_available`.

`tools/verify_engineering_h2_production_evidence.sh` now verifies the benchmark
spec report before verifying the readiness report.

## Current Status

The selected public benchmark is now fixed as HySafe SBEPV5 / GexCon D27. The
production blocker remains open until exact sensor/baffle coordinates and the
120 s experimental sensor time series are digitized or obtained, a case-matched
PeleLMeX run is executed, and the official reference-agreement report passes
with `--external-plume-dataset-json`.
