# Engineering Liquefied External Vaporization Source Contract

This contract is the supported bridge from an external vaporization model into the current PeleLMeX gas-phase engineering leak solver.

## Scope

- The external vaporization model supplies gas-phase source data as a CSV time series.
- The CFD input generated from the CSV uses `prob.leak_model = fixed_mass_flow`.
- The generated input sets `prob.fuel_species`, `prob.leak_rate`, `prob.leak_schedule_times`, `prob.leak_schedule_rates`, `prob.leak_schedule_temperatures`, `prob.leak_schedule_vel_x`, `prob.leak_schedule_vel_y`, `prob.leak_schedule_vel_z`, `prob.leak_schedule_radius`, `prob.leak_schedule_x`, `prob.leak_schedule_y`, `prob.leak_schedule_z`, `prob.leak_T`, source velocity, radius, and location when those columns are present.
- `cfd_solves_liquid_phase_change = false`
- `cfd_solves_flashing_discharge = false`
- `cfd_solves_pool_spread_evaporation = false`
- This is not a production claim for liquid tank rupture, flashing two-phase discharge, cryogenic pool spread, or ground heat-transfer closure.

## Required CSV

Template: `examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv`

Required columns: `time_s`, `mdot_kg_s`, `vapor_T_K`, `fuel_species`. Up to 64 strictly increasing time rows are supported for `mdot(t)`, `vapor_T(t)`, optional `velocity(t)`, and optional single-source `radius/location(t)` coupling.

Optional columns: `leak_vel_x_m_s`, `leak_vel_y_m_s`, `leak_vel_z_m_s`, `source_radius_m`, `source_x_m`, `source_y_m`, `source_z_m`, `source_pressure_Pa`.

## Command

```bash
python3 tools/codex_make_external_vaporization_source_input.py --source-csv examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv --base-input examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke --time 2.0 --output-input docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/input.codex_lng_external_vaporization_source_t2s --output-json docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/external_vaporization_source_mapping_t2s.json
python3 tools/write_engineering_liquefied_external_vaporization_contract_report.py
bash tools/verify_engineering_liquefied_external_vaporization_contract.sh
```

## Operational Meaning

Use this path when a separate thermodynamic, consequence, or process-safety model has already converted a liquefied release into a gas-phase vaporization mass flow rate. The current CFD calculation then starts from that gas-phase source and covers dispersion, ignition, flame development, and obstacle interaction within the already verified gas-phase scope.
