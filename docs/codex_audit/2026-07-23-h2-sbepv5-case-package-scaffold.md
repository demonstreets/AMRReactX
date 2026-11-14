# 2026-07-23 H2 SBEPV5 D27 Case Package Scaffold

## Scope

Production-readiness blocker:
`reference_agreement_is_threshold_only_not_external_plume_shape_dataset`.

The external-data gates now define what must be ingested and how the official
reference-agreement dataset JSON will be built. This pass adds a generated
PeleLMeX case package scaffold for the selected HySafe SBEPV5 / GexCon D27
benchmark.

## Changes

Added `tools/write_engineering_h2_sbepv5_case_package_report.py`.

The package generator writes:

- `inputs.sbepv5_d27_scout`
- `inputs.sbepv5_d27_reference`
- `sensors_template.csv`
- `baffle_geometry_template.csv`
- `dataset_metadata_template.json`
- `experimental_timeseries_template.csv`
- `README.md`

The generated inputs encode the audited vessel dimensions, release period,
nozzle diameter, exit velocity, normal flow rate, and jet exit location from
the SBEPV5/D27 benchmark specification. The package deliberately reports
`case_runnable = false` until the dataset ingestion gate has exact baffle
geometry, sensor coordinates, source metadata, and experimental time histories.

`tools/write_engineering_h2_external_plume_benchmark_readiness.py` now records
whether the case package exists, whether the input template exists, and whether
the package is runnable.

`tools/verify_engineering_h2_production_evidence.sh` now verifies the case
package report.

## Current Status

This is a reproducibility improvement, not an external validation claim. It
makes the future SBEPV5 run path concrete while preventing the scaffold from
being treated as production-ready evidence before the external dataset has been
ingested.
