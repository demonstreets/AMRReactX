# Academic Droplet and Spray Review Scope Tightening

Date: 2026-07-29

## Scope

This audit records follow-up work from the independent Type A two-phase review. The review found that the ACD-05 and ACD-07 reports were using useful short shock-droplet/spray response gates to clear broader academic validation gaps that still require closed gas+particle budgets and external/reference evidence.

## Changes

- `tools/write_academic_droplet_euler_lagrange_validation_report.py` now separates:
  - `clears_acd_05_response_gate`
  - `clears_acd_05_closed_gas_particle_budget_gap`
  - `clears_acd_05_external_reference_gap`
  - `clears_acd_05_euler_lagrange_gap`
- `tools/write_academic_spray_detonation_validation_report.py` now separates:
  - `clears_acd_07_reacting_spray_response_gate`
  - `clears_acd_07_closed_gas_particle_budget_gap`
  - `clears_acd_07_full_cellular_gas_liquid_detonation_gap`
  - `clears_acd_07_external_reference_gap`
  - `clears_acd_07_spray_detonation_gap`
- `tools/write_engineering_h2_master_plan_traceability_report.py` now treats ACD-05 and ACD-07 as `PARTIAL` until the broader budget/reference gaps are proven.

## Verification Intent

The maintained shock-droplet and reacting-spray cases remain valuable regression gates. They prove that the current coupled paths can run, produce finite plotfiles, move particles, trigger breakup/surface-area growth, evaporate/heat spray quantities, and propagate a reacting high-pressure/high-temperature front. They do not prove a full conservative gas+particle budget, full cellular gas-liquid detonation morphology, or external agreement.

## Remaining Gaps

- Gas+particle mass, momentum, and total-energy budget closure for ACD-05 and ACD-07.
- External shock-droplet breakup/evaporation reference comparison.
- External spray/gas-liquid detonation reference comparison.
- Full cellular gas-liquid detonation morphology.
