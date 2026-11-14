# Engineering Fuel-Species Guard Report

- Status: `PASS-ENGINEERING-FUEL-SPECIES-GUARD`
- Source lookup guard ready: `True`
- Invalid species runtime abort passed: `True`
- Invalid species return code: `1`
- Silent H2 fallback detected: `False`
- Unknown species source applied: `False`
- Prevents unknown fuel silent fallback: `True`

## Runtime Probe

- Input: `docs/codex_audit/evidence/engineering_fuel_species_guard_20260806/input.invalid_fuel_species`
- Run log: `docs/codex_audit/evidence/engineering_fuel_species_guard_20260806/invalid_fuel_species_run.log`
- Expected abort marker: `prob.fuel_species was not found in the compiled chemistry mechanism`

## Evidence

- `engineering_h2_leak_prob_h`: `examples/engineering/h2_leak_3d/pelelmex_prob.H`
- `engineering_h2_leak_prob_cpp`: `examples/engineering/h2_leak_3d/pelelmex_prob.cpp`
- `invalid_fuel_species_input`: `docs/codex_audit/evidence/engineering_fuel_species_guard_20260806/input.invalid_fuel_species`
- `invalid_fuel_species_run_log`: `docs/codex_audit/evidence/engineering_fuel_species_guard_20260806/invalid_fuel_species_run.log`
- `invalid_fuel_species_rc`: `docs/codex_audit/evidence/engineering_fuel_species_guard_20260806/invalid_fuel_species_rc.txt`
- `engineering_multi_fuel_operator_runbook_report`: `docs/codex_audit/evidence/engineering_multi_fuel_operator_runbook_20260806/engineering_multi_fuel_operator_runbook_report.json`
- `engineering_multi_fuel_capability_boundary_report`: `docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/engineering_multi_fuel_capability_boundary_report.json`
