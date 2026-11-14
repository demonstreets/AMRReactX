# Engineering H2 External Plume Benchmark Readiness

Status: `NOT_READY-EXTERNAL-PLUME-BENCHMARK`
Clears reference-data blocker: `False`

## Current Outputs

- `public_source_triage_available`: `True`
- `public_source_missing_artifact_count`: `4`
- `digitization_preflight_available`: `True`
- `digitization_preflight_missing_artifact_count`: `4`
- `literature_metric_preflight_available`: `True`
- `literature_metric_anchor_available`: `True`
- `literature_metric_missing_artifact_count`: `2`
- `literature_metric_ready_for_reference_agreement_consumption`: `False`
- `case_spec_report_available`: `True`
- `case_package_report_available`: `True`
- `case_package_preflight_report_available`: `True`
- `case_package_reference_source_resolution_ready`: `True`
- `case_package_runnable`: `False`
- `case_matched_pelelmex_input_template_available`: `True`
- `sbepv5_d27_program_scout_run_available`: `True`
- `sbepv5_d27_program_scout_cuda_run`: `True`
- `sbepv5_d27_program_scout_baffle_stl_count`: `4`
- `sbepv5_d27_program_scout_plotfile_count`: `5`
- `sbepv5_d27_program_scout_sensor_timeseries_rows`: `60`
- `release_geometry_metadata_available`: `True`
- `reliable_sensor_subset_declared`: `True`
- `dataset_ingestion_report_available`: `True`
- `dataset_metadata_available`: `False`
- `exact_sensor_coordinates_available`: `False`
- `exact_baffle_geometry_available`: `False`
- `digitized_experimental_timeseries_available`: `False`
- `external_dataset_builder_report_available`: `True`
- `external_plume_dataset_json_written`: `False`
- `threshold_reference_agreement`: `True`
- `external_plume_shape_dataset_agreement`: `False`
- `amr_peak_x_available`: `True`
- `amr_lel_cloud_volume_available`: `True`
- `amr_final_flammable_planes_available`: `True`
- `sensor_timeseries_sampling_available`: `True`
- `maximum_downwind_extent_available`: `True`
- `maximum_vertical_extent_available`: `True`
- `case_matched_external_dataset_ingested`: `False`
- `plume_observation_report_available`: `True`

## Quality Gate Matrix

| Gate | Status | Gap |
| --- | --- | --- |
| `public_source_triage_ready` | `PASS` | public-source triage report fixes source registry and acquisition gaps |
| `digitization_preflight_ready` | `PASS` | SBEPV5 D27 digitization templates and source triage are available |
| `literature_metric_preflight_ready` | `PASS` | SBEPV5 D27 literature-level arrival and priority sensor metric anchors are available |
| `benchmark_spec_ready` | `PASS` | SBEPV5 D27 benchmark spec report passed |
| `case_package_scaffold_ready` | `PASS` | case scaffold package report passed |
| `case_package_preflight_ready` | `PASS` | case package preflight passed and reference sources resolve |
| `case_package_runnable` | `MISSING` | Provide all source data and generated geometry/input artifacts required to run the SBEPV5 case. |
| `d27_program_scout_runnable` | `PASS` | D27-style program-side CUDA scout ran with baffles, sensors, plume extents and copied evidence |
| `dataset_metadata_available` | `MISSING` | Provide dataset_metadata.json with benchmark id, source URL/DOI, digitization metadata, and source hash. |
| `exact_sensor_coordinates_available` | `MISSING` | Provide sensor_coordinates.csv for Gas01..Gas12 with reliability/source basis/uncertainty. |
| `exact_baffle_geometry_available` | `MISSING` | Provide baffle_geometry.csv for baffles 1..4 with source basis and uncertainty. |
| `digitized_experimental_timeseries_available` | `MISSING` | Provide experimental_timeseries.csv covering Gas01..Gas12 through at least 120 s. |
| `program_sensor_sampling_available` | `PASS` | program plume observation includes sensor time series |
| `program_extent_metrics_available` | `PASS` | program plume observation includes downwind and vertical extents |
| `external_dataset_json_written` | `MISSING` | External dataset builder must write the shape-agreement dataset JSON. |
| `reference_agreement_uses_external_shape_dataset` | `MISSING` | Regenerate h2_reference_agreement_report with the generated external plume dataset JSON and passing checks. |

## Benchmark Preparation Gaps

- `dataset_metadata_json_missing`
- `sensor_coordinates_csv_missing`
- `baffle_geometry_csv_missing`
- `experimental_timeseries_csv_missing`

## Public Source Missing Artifacts

- `sensor_coordinates.csv`: digitize Figure 4/source figure or obtain original tabular sensor coordinates
- `baffle_geometry.csv`: digitize Figure 2/source geometry or obtain original CAD/table
- `experimental_timeseries.csv`: obtain original Excel data or digitize published curves with source and uncertainty metadata
- `dataset_metadata.json`: record URL/DOI, source file hashes, digitization method, uncertainty, and case-alignment booleans

## Digitization Missing Artifacts

- `dataset_metadata.json`: replace the metadata template with URL/DOI, source file hash, digitization method, uncertainty basis, and case-alignment booleans
- `sensor_coordinates.csv`: digitize or obtain Gas01..Gas12 coordinates with reliability tags and <=0.02 m uncertainty
- `baffle_geometry.csv`: digitize or obtain baffles 1..4 bounds with source basis and <=0.02 m uncertainty
- `experimental_timeseries.csv`: obtain original Excel or digitize Gas01..Gas12 concentration histories through at least 120 s

## Literature Metric Missing Artifacts

- `experimental_timeseries.csv`: ingest original Excel or reviewed digitized curves for Gas01..Gas12 through at least 120 s
- `literature_metric_acceptance_overlay.json`: after program sensor probes exist, compare Gas09/Gas10 arrival-time metrics to reported intervals

## Candidate Public Benchmarks

### hysafe_sbepv5_d27
- Title: `HySafe CFD validation benchmark SBEPV5, GexCon D27`
- Source type: `literature_digitized`
- URL: https://publikationen.bibliothek.kit.edu/230068969
- Required program outputs:
  - case-matched baffled-box geometry and vent opening
  - transient point-probe/sensor concentration sampling at the 12 monitor locations
  - digitized experimental concentration traces or accepted tabular data
  - arrival-time and concentration tolerance checks for reliable sensors

### large_volume_lh2_open_space_2024
- Title: `Large-volume liquid hydrogen release in open space`
- Source type: `field_test`
- URL: https://www.mdpi.com/2076-3417/14/9/3645
- Required program outputs:
  - cryogenic liquid-hydrogen source model or justified gas-equivalent surrogate
  - flammable-cloud maximum downwind distance and vertical extent over time
  - case-matched wind and terrain/substrate conditions
  - radiation/consequence coupling kept separate from plume-shape validation

## Blocking Gaps

- `case_matched_external_plume_dataset_not_ingested`
- `external_plume_quality_gates_not_all_passed`

## Next Required Artifacts

- case-matched PeleLMeX input and geometry generated from the selected benchmark specification
- exact SBEPV5 D27 baffle placement/wall attachment and sensor coordinates replacing the program-scout approximations
- exact sensor and baffle coordinates digitized from source figures or original tabular data
- program sensor probes compared against SBEPV5 Gas09/Gas10 literature arrival-time anchors
- digitized or tabulated experimental dataset with source metadata and uncertainty/tolerances
- official h2_reference_agreement_report regenerated with --external-plume-dataset-json

## Limitations

- This readiness report does not clear the production reference-data blocker.
- It records public benchmark candidates and machine-checkable output gaps before experimental agreement can be claimed.
