# Engineering Liquefied Breach Preset Templates

- Status: `PASS-ENGINEERING-LIQUEFIED-BREACH-PRESET-TEMPLATES`
- Presets ready: `True`
- Editable JSON presets: `True`
- Fluids: `LNG_CH4, LPG_C3H8`
- Species: `C3H8, CH4`
- Generates CFD source CSV: `True`
- Production phase-change claim allowed: `False`

## Cases

### lng_ch4_tank_breach_screening

- Preset: `examples/engineering/h2_leak_3d/liquefied_breach_presets/lng_ch4_tank_breach_screening.json`
- Source CSV: `docs/codex_audit/evidence/engineering_liquefied_breach_preset_templates_20260811/lng_ch4_tank_breach_screening/lng_ch4_tank_breach_screening_source.csv`
- Fluid/species: `LNG_CH4 / CH4`
- Peak gas mdot kg/s: `1.81004`
- Gas mass integral kg: `100.431`

### lpg_c3h8_pipe_rupture_screening

- Preset: `examples/engineering/h2_leak_3d/liquefied_breach_presets/lpg_c3h8_pipe_rupture_screening.json`
- Source CSV: `docs/codex_audit/evidence/engineering_liquefied_breach_preset_templates_20260811/lpg_c3h8_pipe_rupture_screening/lpg_c3h8_pipe_rupture_screening_source.csv`
- Fluid/species: `LPG_C3H8 / C3H8`
- Peak gas mdot kg/s: `1.48932`
- Gas mass integral kg: `83.603`

## Limitations

- Presets are screening source inputs for the gas-phase CFD bridge.
- They are intended to be edited or replaced by measured/process-safety source schedules when available.
- They do not turn PeleLMeX into a complete LNG/LPG liquid phase-change rupture solver.
