# Engineering H2 External Plume Public Source Triage

Status: `PASS-H2-EXTERNAL-PLUME-PUBLIC-SOURCE-TRIAGE`
Benchmark: `hysafe_sbepv5_d27`
Clears reference-data blocker: `False`

## Sources

- `kitopen_230068969`: https://publikationen.bibliothek.kit.edu/230068969 (preferred bibliographic anchor for public source identity)
- `researchgate_311396790`: https://www.researchgate.net/publication/311396790_Results_of_the_HySafe_CFD_Validation_Benchmark_SBEPV5 (publicly readable paper text and figure captions for geometry/release/measurement facts)
- `h2knowledgecentre_conference289`: https://www.h2knowledgecentre.com/content/conference289 (secondary bibliographic record and abstract)
- `slideserve_8677333`: https://www.slideserve.com/nilson/results-of-the-hysafe-cfd-validation-benchmark-sbepv5-powerpoint-ppt-presentation (secondary cross-check for sensor layout, release period, nozzle, exit velocity, and flow rate)

## Extracted Facts

- `vessel_dimensions`: `{'x_width_m': 1.2, 'y_depth_m': 0.2, 'z_height_m': 0.9}` status `usable_for_case_scaffold`
- `test_case`: `{'case_id': 'D27', 'selection_basis': 'low-momentum SBEPV5 validation test'}` status `usable_for_case_scaffold`
- `release_conditions`: `{'release_period_s': 60.0, 'nozzle_diameter_m': 0.012, 'exit_velocity_m_s': 10.17, 'flow_rate_normal_l_s': 1.15, 'jet_exit_location_m': {'x': 0.03, 'y': 0.1, 'z': 0.145}, 'gas': 'pure_H2'}` status `usable_for_case_scaffold`
- `compartment_and_baffle_summary`: `{'compartment_count': 12, 'baffle_count': 4, 'baffle_plate_dimensions_m': {'y_depth': 0.2, 'z_height': 0.3}}` status `usable_for_case_scaffold_but_exact_positions_need_digitization`
- `sensor_summary`: `{'sensor_count': 12, 'sensor_type': 'Oldham OLCT20D thermal-conductivity H2 concentration sensors', 'sensor_accuracy_volume_percent_h2': 1.0, 'reliable_sensor_ids': [1, 2, 5, 7, 8, 9, 10, 12], 'unreliable_sensor_ids': [3, 4, 6, 11]}` status `usable_for_reliable_sensor_filter_but_exact_coordinates_need_digitization`
- `experimental_dataset_summary`: `{'duration_s': 120.0, 'format_reported_by_paper': 'MS Excel', 'quantity': 'volumetric H2 concentration at 12 monitor locations'}` status `not_ingested_original_excel_or_digitized_csv_required`

## Artifact Resolution Matrix

- `dataset_metadata.json`: clearable `False`, local file `False`; download or receive the source document/data package, hash it locally, and record provenance plus case-alignment booleans
- `sensor_coordinates.csv`: clearable `False`, local file `False`; digitize the sensor-position figure or obtain the original Gas01..Gas12 coordinate table with uncertainty records
- `baffle_geometry.csv`: clearable `False`, local file `False`; digitize the geometry figure or obtain original baffle bounds for all four baffles
- `experimental_timeseries.csv`: clearable `False`, local file `False`; obtain the original Excel file or digitize all reliable-sensor curves through 120 s with uncertainty metadata

## Public Fact To Case Input Map

- `geometry.domain_dimensions_m`: `PUBLIC_FACT_AVAILABLE`
- `release.nozzle_diameter_m`: `PUBLIC_FACT_AVAILABLE`
- `release.exit_velocity_m_s`: `PUBLIC_FACT_AVAILABLE`
- `release.duration_s`: `PUBLIC_FACT_AVAILABLE`
- `sensors.coordinates`: `NEEDS_DIGITIZATION_OR_ORIGINAL_TABLE`
- `baffles.bounds`: `NEEDS_DIGITIZATION_OR_ORIGINAL_TABLE`
- `reference.experimental_timeseries`: `NEEDS_ORIGINAL_EXCEL_OR_DIGITIZED_CURVES`

## Missing Artifacts

- `sensor_coordinates.csv`: digitize Figure 4/source figure or obtain original tabular sensor coordinates
- `baffle_geometry.csv`: digitize Figure 2/source geometry or obtain original CAD/table
- `experimental_timeseries.csv`: obtain original Excel data or digitize published curves with source and uncertainty metadata
- `dataset_metadata.json`: record URL/DOI, source file hashes, digitization method, uncertainty, and case-alignment booleans

## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `public_source_registry_available` | `PASS` | none |
| `geometry_release_facts_extracted` | `PASS` | none |
| `sensor_reliability_facts_extracted` | `PASS` | none |
| `artifact_resolution_matrix_retains_blockers` | `PASS` | none |
| `case_input_map_separates_public_facts_from_digitization` | `PASS` | none |
| `exact_sensor_coordinates_available` | `MISSING` | Exact Gas01..Gas12 coordinates are not present as local source-controlled data. |
| `exact_baffle_geometry_available` | `MISSING` | Exact baffle bounds are not present as local source-controlled data. |
| `experimental_timeseries_available` | `MISSING` | Original Excel or accepted digitized 12-sensor concentration time series is not local. |

## Limitations

- This triage report records public-source facts and data-acquisition gaps; it does not ingest experimental data.
- Production reference agreement still requires local exact coordinates, baffle geometry, and concentration time series.
