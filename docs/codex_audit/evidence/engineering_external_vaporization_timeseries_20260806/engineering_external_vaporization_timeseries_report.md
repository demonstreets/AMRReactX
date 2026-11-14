# Engineering External Vaporization Time Series

- Status: `PASS-ENGINEERING-EXTERNAL-VAPORIZATION-TIMESERIES`
- Runtime interpolates schedule: `True`
- Converter emits schedule: `True`
- Smoke log clean: `True`
- Schedule mdot range: `5e-06` to `1.75e-05`
- Schedule temperature range: `270.0` to `310.0`
- Schedule velocity x range: `0.4375` to `1.25`
- Schedule radius range: `0.1075` to `0.1425`
- Schedule center x range: `0.4625` to `0.5875`
- Rising segment: `True`
- Falling segment: `True`

## Evidence

- `problem_cpp`: `examples/engineering/h2_leak_3d/pelelmex_prob.cpp`
- `problem_header`: `examples/engineering/h2_leak_3d/pelelmex_prob.H`
- `converter`: `tools/codex_make_external_vaporization_source_input.py`
- `smoke_input`: `examples/engineering/h2_leak_3d/input.codex_fixed_mass_flow_timeseries_smoke`
- `smoke_log`: `docs/codex_audit/evidence/engineering_external_vaporization_timeseries_20260806/fixed_mass_flow_timeseries_smoke.log`
- `converter_output_input`: `docs/codex_audit/evidence/engineering_external_vaporization_timeseries_20260806/input.codex_lng_external_vaporization_timeseries`
- `converter_output_json`: `docs/codex_audit/evidence/engineering_external_vaporization_timeseries_20260806/external_vaporization_timeseries_mapping.json`
