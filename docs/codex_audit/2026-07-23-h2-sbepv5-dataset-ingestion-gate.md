# 2026-07-23 H2 SBEPV5 D27 Dataset Ingestion Gate

## Scope

Production-readiness blocker:
`reference_agreement_is_threshold_only_not_external_plume_shape_dataset`.

The HySafe SBEPV5 / GexCon D27 benchmark specification is now fixed, but the
external experiment package still needs exact geometry/sensor coordinates and
the experimental concentration histories before the official reference
agreement report can use it. This pass adds a strict ingestion readiness report
for that dataset package.

## Changes

Added `tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py`.

The tool validates the expected dataset package:

- `dataset_metadata.json`
- `sensor_coordinates.csv`
- `baffle_geometry.csv`
- `experimental_timeseries.csv`

It checks source/digitization metadata, 12 sensor records with reliable sensor
classification, four baffle records inside the vessel bounds, monotone 0-120 s
time histories, and finite H2 volume-percent values for the reliable sensors.

`tools/write_engineering_h2_external_plume_benchmark_readiness.py` now consumes
this ingestion report. The readiness report can distinguish a fixed benchmark
specification from a genuinely ingested external experimental dataset.

`tools/verify_engineering_h2_production_evidence.sh` now verifies the ingestion
report as part of the engineering H2 evidence chain.

## Current Status

The ingestion report is expected to be `NOT_READY` until the source data is
digitized or obtained. This is intentional: the new gate makes the remaining
external-data work explicit without pretending that production validation has
already been achieved.
