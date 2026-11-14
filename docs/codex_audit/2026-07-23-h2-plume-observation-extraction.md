# 2026-07-23 H2 Plume Observation Extraction

## Scope

External plume validation currently lacks case-matched experimental data, but
the code also needed benchmark-style outputs that can be compared to such data:
transient point-probe concentrations and flammable-cloud spatial extents.

## Change

Added `tools/write_engineering_h2_plume_observation_report.py`.

The tool reads a 3D AMReX run directory, discovers plotfiles, and writes:

- `plume_extents.csv`: flammable H2 cloud volume, peak mole fraction, and
  min/max flammable x/y/z bounds for every plotfile.
- `sensor_timeseries.csv`: nearest-cell H2 mole fraction at user-supplied
  sensors, or a default centerline probe set for extraction smoke evidence.
- `h2_plume_observation_report.json/.md`: hash-tracked report verifying that
  plume extents and point-probe time series are available.

Sensor coordinates are checked against the plotfile physical domain before
sampling. Out-of-domain sensors fail the report instead of silently snapping to
the nearest boundary cell. The tool now supports two explicit sensor sampling
modes:

- `trilinear` (default): interpolates H2 mole fraction at the requested sensor
  coordinate and fails if the coordinate is outside the cell-center
  interpolation range.
- `nearest`: samples the nearest cell center for compatibility or boundary
  probes.

The generated sensor CSV records the requested point, sample point, nearest
cell center, and nearest-cell distance. The report records
`max_sensor_sample_distance` and `max_nearest_cell_distance`, so case-matched
experimental probe mapping error is visible in evidence.

`tools/write_engineering_h2_external_plume_benchmark_readiness.py` now reads
the plume-observation report. With this evidence present, it no longer lists
generic missing-output gaps for sensor time series or flammable cloud extents.
The remaining external-plume readiness gap is the real production blocker:
`case_matched_external_plume_dataset_not_ingested`.

`tools/verify_engineering_h2_production_evidence.sh` now verifies the plume
observation report before the external-plume readiness report.

## Verification

The official observation evidence was generated from the archived AMR run:

`docs/codex_audit/evidence/engineering_scheduler_h2_20260720/campaign_run/cases/plan-amr-mpi-reduced-long/amr/run`

The full engineering verification chain passed after adding this report.

Additional guard verification rejects a sensor JSON whose probe coordinate lies
outside the AMReX physical domain.

## Status

This closes an output-capability gap for external plume validation, but it does
not clear the external reference-data blocker. A case-matched public benchmark
or digitized experiment still must be simulated and ingested through
`--external-plume-dataset-json`.
