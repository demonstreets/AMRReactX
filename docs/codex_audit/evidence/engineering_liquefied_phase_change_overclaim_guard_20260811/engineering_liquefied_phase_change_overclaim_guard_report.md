# Engineering Liquefied Phase-Change Overclaim Guard

- Status: `PASS-ENGINEERING-LIQUEFIED-PHASE-CHANGE-OVERCLAIM-GUARD`
- Gasified LNG/LPG bridge ready: `True`
- External vaporization bridge ready: `True`
- Liquefied release screening source ready: `True`
- Liquefied breach source contract ready: `True`
- CUDA runtime ready: `True`
- Negative selftests ready: `True`
- Phase-change overclaim guard ready: `True`

## Current Boundary

- Allowed current claim: external vaporization/gasified source bridge for LNG_CH4 and LPG_C3H8 dispersion, ignition, flame development, and obstacle interaction
- Disallowed current claim: internal tank rupture, flashing multiphase discharge, liquid-pool spread/boiling, droplet breakup, ground heat transfer, or high-fidelity EOS-coupled liquefied-gas phase-change production modeling
- Internal liquid phase-change CFD: `False`
- Pool spread/boiling CFD: `False`
- Flashing discharge CFD: `False`
- Production phase-change claim allowed: `False`

## Evidence

- `multi_fuel_boundary`: `docs/codex_audit/evidence/engineering_multi_fuel_capability_boundary_20260806/engineering_multi_fuel_capability_boundary_report.json`
- `gasified_lng_lpg_surrogate`: `docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/engineering_gasified_lng_lpg_surrogate_report.json`
- `external_vaporization_contract`: `docs/codex_audit/evidence/engineering_liquefied_external_vaporization_contract_20260806/engineering_liquefied_external_vaporization_contract_report.json`
- `external_vaporization_negative_selftest`: `docs/codex_audit/evidence/engineering_liquefied_external_vaporization_negative_selftest_20260806/engineering_liquefied_external_vaporization_negative_selftest_report.json`
- `vaporization_source_model`: `docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/engineering_liquefied_release_vaporization_source_model_report.json`
- `vaporization_source_model_negative_selftest`: `docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_negative_selftest_20260807/engineering_liquefied_release_vaporization_source_model_negative_selftest_report.json`
- `source_balance`: `docs/codex_audit/evidence/engineering_liquefied_release_source_balance_20260807/engineering_liquefied_release_source_balance_report.json`
- `source_balance_negative_selftest`: `docs/codex_audit/evidence/engineering_liquefied_release_source_balance_negative_selftest_20260807/engineering_liquefied_release_source_balance_negative_selftest_report.json`
- `thermal_plausibility`: `docs/codex_audit/evidence/engineering_liquefied_release_thermal_plausibility_20260811/engineering_liquefied_release_thermal_plausibility_report.json`
- `breach_source_contract`: `docs/codex_audit/evidence/engineering_liquefied_breach_source_contract_20260811/engineering_liquefied_breach_source_contract_report.json`
