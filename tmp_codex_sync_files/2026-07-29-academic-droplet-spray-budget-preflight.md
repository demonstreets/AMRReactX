# Academic Droplet/Spray Budget Preflight

Date: 2026-07-29

Scope:
- Added a maintained ACD-05/ACD-07 budget preflight for the existing shock-droplet and reacting spray-detonation cases.
- The report integrates gas conservative fields and Eulerian spray plotfield projections from archived AMReX plotfiles.
- It reconstructs native per-particle AMReX DATA budgets for liquid mass, momentum, kinetic energy, and mass-temperature proxy.
- It explicitly keeps the closed gas+particle budget gap open until boundary-flux and coupling-source histories, or an equivalent in-code diagnostic, are available.

Evidence:
- `tools/write_academic_droplet_spray_budget_preflight_report.py`
- `docs/codex_audit/evidence/academic_droplet_spray_budget_preflight_20260729/academic_droplet_spray_budget_preflight_report.json`
- `docs/codex_audit/evidence/academic_droplet_spray_budget_preflight_20260729/academic_droplet_spray_budget_preflight_report.md`

Result:
- `PASS-ACADEMIC-DROPLET-SPRAY-PLOTFIELD-BUDGET-PREFLIGHT`
- `clears_projected_plotfield_budget_preflight=true`
- `per_particle_binary_budget_parser_ready=true`
- `clears_full_closed_gas_particle_budget_gap=false`

Traceability impact:
- ACD-05 and ACD-07 evidence now include machine-verified gas/spray plotfield budgets and native particle binary budgets.
- ACD-05 and ACD-07 remain `PARTIAL` because full gas+particle mass, momentum, and total-energy closure including boundary/coupling histories is not yet certified.
