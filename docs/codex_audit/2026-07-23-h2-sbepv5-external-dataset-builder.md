# 2026-07-23 H2 SBEPV5 External Dataset Builder

## Scope

Production-readiness blocker:
`reference_agreement_is_threshold_only_not_external_plume_shape_dataset`.

The dataset ingestion gate defines the required SBEPV5 files. This pass adds
the next bridge: a builder that turns a passed SBEPV5 ingestion package and a
case-matched plume-observation report into the external plume dataset JSON
consumed by `tools/write_engineering_h2_reference_agreement_report.py`.

## Changes

Added `tools/write_engineering_h2_sbepv5_external_dataset_report.py`.

The builder requires:

- `PASS-SBEPV5-D27-DATASET-INGESTION`;
- a passing H2 scout report;
- a passing plume-observation report with
  `case_matched_external_benchmark = true`;
- observation time coverage through 120 s;
- all reliable SBEPV5 sensor IDs present in the simulated point probes;
- dataset metadata declaring true case alignment for geometry, release rate,
  release direction, and boundary conditions.

Only after those checks pass does the builder write
`sbepv5_d27_external_plume_dataset.json`. The builder report itself still sets
`clears_reference_data_blocker = false`; final production credit remains owned
by the official reference-agreement report after it consumes the generated
dataset.

`tools/write_engineering_h2_external_plume_benchmark_readiness.py` now tracks
whether the builder report exists and whether the external dataset JSON has
actually been written.

`tools/verify_engineering_h2_production_evidence.sh` now verifies the builder
report.

## Current Status

The builder is expected to be `NOT_READY` with the current evidence because the
experimental dataset files and SBEPV5 case-matched plume-observation run are
not yet present. This prevents the existing open-domain engineering plume
evidence from being misused as SBEPV5 experimental validation.
