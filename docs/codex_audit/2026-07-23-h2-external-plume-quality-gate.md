# Engineering H2 External Plume Quality Gate Tightening

## Purpose

The engineering production scorecard still blocks production readiness on
`reference_agreement_is_threshold_only_not_external_plume_shape_dataset`.
The existing external plume readiness report listed public benchmark candidates
and the highest-level blocker, but it did not expose a production review matrix
showing which SBEPV5/D27 intake, execution, dataset, and agreement gates were
passing or missing.

## Change

Updated `tools/write_engineering_h2_external_plume_benchmark_readiness.py` so
the readiness package now writes and verifies:

- `external_plume_benchmark_intake_checklist.csv`
- a `quality_gate_matrix` in `external_plume_benchmark_readiness_report.json`
- Markdown rows for the external plume readiness gates

The quality matrix covers:

- SBEPV5/D27 benchmark specification
- case package scaffold
- case package preflight and reference source resolution
- case package runnable state
- dataset metadata
- exact sensor coordinates
- exact baffle geometry
- digitized experimental concentration time series
- program sensor sampling output
- program downwind and vertical extent metrics
- external plume dataset JSON generation
- official reference agreement using the external shape dataset

The production evidence verification report was also updated to schema 11 so it
reads the readiness report's `current_outputs` fields instead of leaving the
external plume dataset/shape-agreement summary as null.

## Production Meaning

This still does not clear the external plume blocker. It makes the remaining
work auditable: real or digitized SBEPV5/D27 metadata, sensor coordinates,
baffle geometry, and concentration time series must be supplied, the case must
be runnable, the external dataset builder must emit the dataset JSON, and the
official reference agreement must pass with that dataset.

## Verification

The updated readiness report remains `NOT_READY-EXTERNAL-PLUME-BENCHMARK` until
the full external benchmark chain passes. The full engineering H2 verifier
requires this report and the schema 11 production evidence report.
