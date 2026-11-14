
# HySafe SBEPV5 / GexCon D27 Case Package

This package is a scaffold generated from the audited public benchmark
specification. It intentionally keeps the runnable flag false until the
following files are filled from source data and pass the ingestion gate:

- `dataset_metadata_template.json`
- `sensors_template.csv`
- `baffle_geometry_template.csv`
- `experimental_timeseries_template.csv`

The `inputs.sbepv5_d27_scout` and `inputs.sbepv5_d27_reference` files encode
the vessel size and release metadata from the benchmark specification. They are
not an external validation claim. After exact geometry and sensor data are
ingested, the case should be run to 120 s, plume observations should be
extracted with matching sensor IDs, and the SBEPV5 external dataset builder
should generate the official `external_plume_dataset_json`.
