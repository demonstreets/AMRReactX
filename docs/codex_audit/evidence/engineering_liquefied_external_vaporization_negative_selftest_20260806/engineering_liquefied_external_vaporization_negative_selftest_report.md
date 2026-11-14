# Engineering Liquefied External Vaporization Negative Selftest

- Status: `PASS-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-NEGATIVE-SELFTEST`
- Positive template conversion passed: `True`
- Negative cases refused: `11/11`

## Negative Cases

- `negative_mdot`: refused=`True` rc=`1` expected=`mdot_kg_s must be nonnegative`
- `negative_vapor_temperature`: refused=`True` rc=`1` expected=`vapor_T_K must be positive`
- `unknown_species`: refused=`True` rc=`1` expected=`fuel_species must be one of`
- `nonmonotonic_time`: refused=`True` rc=`1` expected=`time_s values must be strictly increasing`
- `missing_temperature_column`: refused=`True` rc=`1` expected=`source CSV missing columns`
- `mixed_species`: refused=`True` rc=`1` expected=`exactly one fuel_species`
- `negative_sample_time`: refused=`True` rc=`1` expected=`sample time must be nonnegative`
- `too_many_schedule_rows`: refused=`True` rc=`1` expected=`source CSV supports at most 64 schedule rows`
- `partial_optional_velocity_column`: refused=`True` rc=`1` expected=`optional source CSV column leak_vel_x_m_s must be present on every row or omitted from every row`
- `negative_source_radius`: refused=`True` rc=`1` expected=`source_radius_m must be positive`
- `partial_location_columns`: refused=`True` rc=`1` expected=`source_x_m, source_y_m, and source_z_m must be provided together or omitted together`

## Evidence

- `converter`: `tools/codex_make_external_vaporization_source_input.py`
- `base_input`: `examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke`
- `valid_template`: `examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv`
- `positive_mapping_json`: `docs/codex_audit/evidence/engineering_liquefied_external_vaporization_negative_selftest_20260806/positive/codex_lng_external_vaporization_source_template.json`
- `contract_report`: `docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/engineering_liquefied_external_vaporization_contract_report.json`
