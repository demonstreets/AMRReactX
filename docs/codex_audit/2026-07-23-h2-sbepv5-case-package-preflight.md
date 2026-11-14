# 2026-07-23 H2 SBEPV5 D27 Case Package Preflight

## Scope

Production-readiness blocker:
`reference_agreement_is_threshold_only_not_external_plume_shape_dataset`.

The SBEPV5 case package scaffold now exists. This pass adds a preflight report
that checks whether the generated PeleLMeX inputs and data templates are
self-consistent before any long external-validation run is attempted.

## Changes

Added `tools/write_engineering_h2_sbepv5_case_package_preflight_report.py`.

The preflight checks:

- both scout and reference input files contain required PeleLMeX, AMR,
  geometry, release, sensor, and data-template keys;
- the vessel dimensions are 1.20 m x 0.20 m x 0.90 m;
- the release is pure H2, 60 s, 12 mm nozzle, 10.17 m/s, 1.15 normal L/s,
  with the audited jet exit location;
- the run horizon covers the 120 s experimental time series;
- sensor templates contain all 12 monitor points with the audited reliable and
  unreliable subsets;
- baffle and experimental time-series templates contain the expected schema;
- the reference input has at least two cells across the 12 mm source scale.

The reference template grid was raised from 120 x 20 x 90 to 240 x 40 x 180,
giving a 5 mm base spacing and about 2.4 cells across the 12 mm nozzle scale.

`tools/write_engineering_h2_external_plume_benchmark_readiness.py` now records
the preflight report and its source-resolution flag.

`tools/verify_engineering_h2_production_evidence.sh` now verifies the preflight
report.

## Current Status

The package preflight passes as a scaffold check, while `production_validation_ready`
remains false. The case still must wait for exact external data ingestion and a
120 s case-matched run before it can support production validation.
