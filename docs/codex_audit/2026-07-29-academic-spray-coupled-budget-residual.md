# Academic Spray Coupled Budget Residual Diagnostics

Date: 2026-07-29

Scope:
- Added a maintained ACD-05/ACD-07 residual diagnostic for droplet and reacting spray evidence.
- The report reuses archived plotfiles from the academic droplet Euler-Lagrange and reacting spray detonation gates.
- It verifies particle-binary mass and spray plotfield mass consistency, confirms mass-transfer sign sanity, and records gas+particle endpoint residuals.
- It intentionally remains `NOT_READY` for full coupled gas-particle mass, momentum, and energy closure because the archived cases do not include closed-control-volume/source-history accounting.

Evidence:
- `tools/write_academic_spray_coupled_budget_residual_report.py`
- `docs/codex_audit/evidence/academic_spray_coupled_budget_residual_20260729/academic_spray_coupled_budget_residual_report.json`
- `docs/codex_audit/evidence/academic_spray_coupled_budget_residual_20260729/academic_spray_coupled_budget_residual_report.md`

Traceability impact:
- Strengthens ACD-05/ACD-07 by adding explicit coupled-budget residual diagnostics.
- Prevents response-only droplet/spray evidence from being promoted to full conservation-budget credit.
- Does not clear full ACD-05 evaporating spray closure.
- Does not clear ACD-07 reacting spray/gas-liquid detonation closure or morphology.
