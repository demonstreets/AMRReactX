# Engineering Liquefied External Vaporization Contract Report

- Status: `PASS-ENGINEERING-LIQUEFIED-EXTERNAL-VAPORIZATION-CONTRACT`
- External vaporization contract ready: `True`
- Generated gas-source input ready: `True`
- CFD solves liquid phase change: `False`
- CFD solves flashing discharge: `False`
- CFD solves pool spread/evaporation: `False`
- Supported surrogate species: `H2, CH4, C3H8`

## Evidence

- `contract_doc`: `docs/codex_audit/engineering_liquefied_external_vaporization_source_contract.md`
- `source_csv_template`: `examples/engineering/h2_leak_3d/codex_lng_external_vaporization_source_template.csv`
- `base_gasified_lng_input`: `examples/engineering/h2_leak_3d/input.codex_gasified_lng_ch4_surrogate_smoke`
- `generated_input`: `docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/input.codex_lng_external_vaporization_source_t2s`
- `generated_mapping_json`: `docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/external_vaporization_source_mapping_t2s.json`
- `converter`: `tools/codex_make_external_vaporization_source_input.py`
- `multi_fuel_boundary`: `docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/engineering_multi_fuel_capability_boundary_report.json`
- `gasified_surrogate`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/engineering_gasified_lng_lpg_surrogate_report.json`
- `fuel_species_guard`: `docs/codex_audit/evidence/engineering_fuel_species_guard_20260806/engineering_fuel_species_guard_report.json`
- `pelelmex_prob_cpp`: `examples/engineering/h2_leak_3d/pelelmex_prob.cpp`
- `pelelmex_prob_h`: `examples/engineering/h2_leak_3d/pelelmex_prob.H`
