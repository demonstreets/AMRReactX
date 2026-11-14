# Engineering Liquefied Breach Source Contract

- Status: `PASS-ENGINEERING-LIQUEFIED-BREACH-SOURCE-CONTRACT`
- Contract ready: `True`
- Fluids: `LNG_CH4, LPG_C3H8`
- Species: `C3H8, CH4`
- Generates external gas-source schedule: `True`
- Production phase-change claim allowed: `False`

## Cases

### lng_ch4_tank_breach_screening

- Fluid/species: `LNG_CH4 / CH4`
- Breach kind: `atmospheric_tank_breach_or_transfer_line_failure`
- Gas mass integral kg: `100.431`
- Peak gas mdot kg/s: `1.81004`
- Vaporized fraction: `0.0726471`
- Contract: `docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/lng_ch4_tank_breach_screening/lng_ch4_tank_breach_screening_breach_contract.json`
- Source CSV: `docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/lng_ch4_tank_breach_screening/lng_ch4_tank_breach_screening_source.csv`

### lpg_c3h8_pipe_rupture_screening

- Fluid/species: `LPG_C3H8 / C3H8`
- Breach kind: `pressurized_lpg_pipe_or_small_vessel_breach`
- Gas mass integral kg: `83.603`
- Peak gas mdot kg/s: `1.48932`
- Vaporized fraction: `0.174382`
- Contract: `docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/lpg_c3h8_pipe_rupture_screening/lpg_c3h8_pipe_rupture_screening_breach_contract.json`
- Source CSV: `docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/lpg_c3h8_pipe_rupture_screening/lpg_c3h8_pipe_rupture_screening_source.csv`

## Boundary

- Allowed: screening LNG/LPG tank-or-pipe breach inputs can produce audited external gas-source schedules for gas dispersion, ignition, and fire simulations
- Disallowed: the CFD solver does not yet solve internal tank rupture, flashing multiphase discharge, liquid-pool spread/boiling, ground heat transfer, or EOS-coupled liquid phase change

## Limitations

- This is an engineering source contract, not a high-fidelity liquefied-gas rupture solver.
- Use measured or process-safety source schedules when available; this contract keeps the screening inputs traceable when they are not.
- A production claim for complete LNG/LPG liquid phase-change CFD still requires dedicated model development and validation evidence.
