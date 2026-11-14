# Engineering Multi-Fuel Template Catalog

- Status: `PASS-ENGINEERING-MULTI-FUEL-TEMPLATE-CATALOG`
- Templates: `5/5`
- Fuel species seen: `C3H8, CH4, H2`
- CSV template ready: `True`
- Liquefied nonclaim comments present: `True`
- CFD-internal liquid phase-change claim allowed: `False`

## Templates

- `h2_fixed_mass_flow_timeseries`: `examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_timeseries_smoke`, fuel=`H2`, ready=`True`
- `h2_fixed_mass_flow_valve_schedule`: `examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_valve_schedule_smoke`, fuel=`H2`, ready=`True`
- `gasified_lng_ch4_cold_source`: `examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke`, fuel=`CH4`, ready=`True`
- `gasified_lng_ch4_warmed_fire`: `examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_warmed_fire_surrogate_mpicuda_500step`, fuel=`CH4`, ready=`True`
- `gasified_lpg_c3h8_fire`: `examples/engineering/h2_leak_3d/input.codex_gasified_lpg_c3h8_surrogate_smoke`, fuel=`C3H8`, ready=`True`

## CSV Template

- Path: `examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv`
- Rows: `4`
- Species: `CH4`
