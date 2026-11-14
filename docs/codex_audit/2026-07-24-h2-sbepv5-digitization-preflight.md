# Engineering H2 SBEPV5 D27 Digitization Preflight

## Purpose

The engineering H2 scorecard still blocks production readiness on
`reference_agreement_is_threshold_only_not_external_plume_shape_dataset`.
Public SBEPV5 sources describe the D27 geometry, release, sensor reliability,
and the existence of an MS Excel data set, but the original machine-readable
sensor time history is not local. The program must not claim production
external plume agreement from threshold-only checks.

## Change

Added `tools/write_engineering_h2_sbepv5_digitization_preflight_report.py`.

The report creates and verifies templates for:

- `dataset_metadata_template.json`
- `sensor_coordinates_template.csv`
- `baffle_geometry_template.csv`
- `experimental_timeseries_template.csv`
- `digitization_uncertainty_record_template.csv`

It records source triage availability, template availability, missing data
artifacts, and whether the official SBEPV5 dataset ingestion report is ready.

## Verification

The engineering H2 production verifier now requires the digitization preflight
report. The external plume benchmark readiness report also records the
digitization preflight status and missing artifacts before claiming any external
plume shape agreement.

## Limitation

This change does not digitize figures or fabricate experimental data. It keeps
the reference-data blocker open until real or accepted digitized SBEPV5 D27
sensor coordinates, baffle geometry, concentration time series, and metadata are
ingested and passed through the official reference-agreement report.
