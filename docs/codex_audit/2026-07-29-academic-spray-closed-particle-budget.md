# Academic Spray Closed Particle Budget

Date: 2026-07-29

Scope:
- Added a maintained closed fixed-particle spray budget case using `examples/academic/spray_test`.
- The runner enables plotfile output for the periodic fixed-particle case and archives initial/final plotfiles.
- The validator reconstructs native AMReX particle DATA budgets and checks invariant particle count, parcel-mass proxy, coordinates, diameter, and mass-temperature proxy; fixed-particle velocity/momentum is recorded only as an observation because this fixture resets particle velocity.

Evidence:
- `tools/codex_run_academic_spray_closed_particle_budget.sh`
- `tools/validate_academic_spray_closed_particle_budget.py`
- `tools/write_academic_spray_closed_particle_budget_report.py`
- `docs/codex_audit/evidence/academic_spray_closed_particle_budget_20260729/academic_spray_closed_particle_budget_report.json`
- `docs/codex_audit/evidence/academic_spray_closed_particle_budget_20260729/academic_spray_closed_particle_budget_report.md`

Traceability impact:
- Clears a narrow ACD-05 closed fixed-particle budget subgap.
- Does not clear full ACD-05 evaporating gas-particle source-term closure.
- Does not clear ACD-07 reacting spray/gas-liquid detonation budget or morphology.
