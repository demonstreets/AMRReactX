# HySafe SBEPV5 / GexCon D27 Benchmark Spec

Status: `PASS-EXTERNAL-PLUME-BENCHMARK-SPEC`
Clears reference-data blocker: `False`

## Source

- Title: `Results of the HySafe CFD Validation Benchmark SBEPV5`
- Venue: `2nd International Conference on Hydrogen Safety, San Sebastian`
- URLs:
  - https://publikationen.bibliothek.kit.edu/230068969
  - https://www.h2knowledgecentre.com/content/conference289
  - https://www.researchgate.net/publication/311396790_Results_of_the_HySafe_CFD_Validation_Benchmark_SBEPV5

## Geometry And Release

- Vessel dimensions m: `{'x_width': 1.2, 'y_depth': 0.2, 'z_height': 0.9}`
- Compartments: `12`
- Baffles: `4`
- Vent opening: `{'wall': 'opposite_release_location', 'description': 'central vent opening about 0.01 m above floor', 'dimensions_m': {'y_width': 0.1, 'z_height': 0.2}, 'exact_position_status': 'requires_source_figure_digitization'}`
- Release: `{'gas': 'pure_H2', 'release_period_s': 60.0, 'nozzle_diameter_m': 0.012, 'exit_velocity_m_s': 10.17, 'flow_rate_normal_l_s': 1.15, 'jet_exit_location_m': {'x': 0.03, 'y': 0.1, 'z': 0.145}, 'release_direction': 'horizontal_toward_vent_wall_from_paper_geometry', 'direction_status': 'requires_case_input_confirmation_against_source_figure'}`

## Measurements

- Reliable sensors: `[1, 2, 5, 7, 8, 9, 10, 12]`
- Unreliable sensors: `[3, 4, 6, 11]`
- Sensor coordinate status: `requires_source_figure_or_tabular_data`
- Dataset ingested: `False`

## Pre-Ingestion Gaps

- `exact_baffle_positions_require_source_figure_digitization`
- `exact_sensor_coordinates_require_source_figure_or_tabular_data`
- `experimental_120s_sensor_timeseries_excel_not_ingested`
- `case_matched_pelelmex_input_not_generated_from_this_spec`

## Required Program Outputs

- case-matched baffled-box geometry including vent and release nozzle
- transient H2 concentration sampling at the 12 monitor locations
- arrival-time metrics for reliable sensors
- peak and late-release concentration metrics for reliable sensors
- source metadata and digitization uncertainty for each literature-derived trace

## Limitations

- This report fixes the public benchmark specification used for future case setup.
- It does not contain digitized experimental traces and does not clear production reference-data validation.
- Exact baffle and sensor coordinates still require source-figure digitization or original tabular data.
