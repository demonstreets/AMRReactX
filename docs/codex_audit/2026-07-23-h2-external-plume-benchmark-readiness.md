# 2026-07-23 H2 External Plume Benchmark Readiness Gate

## Scope

Production-readiness blocker:
`reference_agreement_is_threshold_only_not_external_plume_shape_dataset`.

The previous external-plume ingestion path made the blocker machine-actionable,
but it still allowed weak evidence classes to pass if a user supplied a
case-matched JSON file. This pass tightens that gate and records a concrete
benchmark-readiness report.

## Changes

`tools/write_engineering_h2_reference_agreement_report.py` now only accepts
external plume datasets from:

- `field_test`
- `wind_tunnel`
- `literature_digitized`

The report no longer accepts `validated_reference_model` as production evidence
for clearing the reference-data blocker. External datasets must also declare
case alignment for geometry, release rate, release direction, and boundary
conditions; metric tolerances must be positive, with relative tolerances capped
at 50%; and at least one metric must be a plume-shape metric type
(`plume_extent`, `sensor_concentration`, or `arrival_time`).

`tools/write_engineering_h2_external_plume_benchmark_readiness.py` was added to
record the current output gaps against public benchmark candidates. It is
included in `tools/verify_engineering_h2_production_evidence.sh`; its current
`NOT_READY-EXTERNAL-PLUME-BENCHMARK` status verifies successfully as an audit
artifact but does not clear the production blocker.

## Public Benchmark Candidates

- HySafe SBEPV5 / GexCon D27: baffled compartment H2 dispersion benchmark,
  with release conditions and transient sensor data described in KIT repository
  metadata and the ICHS 2007 benchmark paper.
- Large-volume open-space liquid hydrogen release: field-test paper reporting
  large LH2 release conditions and farthest flammable-cloud extent.

## Verification

- Python compile passed for both reference-agreement and readiness tools.
- Legacy official reference report still verifies.
- Guard dataset with `source_type = validated_reference_model` is rejected.
- Guard dataset with `tolerance_rel = 1.50` is rejected.
- Readiness report verifies with four current gaps:
  - `case_matched_external_plume_dataset_not_ingested`
  - `transient_sensor_probe_output_missing_for_sbepv5_style_validation`
  - `flammable_cloud_downwind_extent_metric_missing`
  - `flammable_cloud_vertical_extent_metric_missing`

## Current Status

This is a production-quality guardrail improvement, not a production claim. The
external reference-data blocker remains open until a case-matched experiment or
literature-digitized plume dataset is simulated and passed through the official
reference-agreement report.
