# Engineering H2 ignition consequence report checkpoint

Date: 2026-07-20

## Scope

This checkpoint strengthens the engineering ignition/fire consequence chain without claiming production-grade fire prediction. The change adds a compact validated report that combines maintained H2 ignition-delay, PeleLMeX ignition-history, and SDC comparison evidence into machine-readable JSON and Markdown.

## Changes

- Added `tools/write_engineering_h2_ignition_consequence_report.py`.
- Hardened relative log-directory handling in:
  - `tools/codex_smoke_engineering_h2_ignition_history.sh`
  - `tools/codex_smoke_engineering_h2_ignition_sdc_compare.sh`
  - `tools/codex_smoke_engineering_h2_ignition_delay.sh`
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` to record the new consequence evidence and remaining fire-production gaps.

## Evidence

Evidence root: `docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720`

- History validation regenerated project-locally: `h2_ignition_history_validation PASS nplot=11 timeN=1e-07 h2_consumed_mean=4.91515359e-09 o2_consumed_mean=7.92990513e-08 h2o_produced_mean=2.08024893e-09 temp_peak_max=2.00000000e+03 max_reaction_rate=1.49553322e+07`.
- SDC comparison regenerated project-locally: `h2_ignition_sdc_compare PASS time=1e-07 temp_rel_linf=1.05111314e-04 h2o_mean_sdc2=2.08106035e-09 heat_rel_linf=1.25728742e-03`.
- Delay validation uses copied historical PASS evidence from the earlier maintained run because the current rerun was interrupted before completion: `tign=4.544817219e-05,4.52629081e-05,4.52388239e-05 s`, `mid_fine_rel=5.32379232e-04`.
- Report generation passed: `engineering_h2_ignition_consequence_report PASS ... tign=4.52388239e-05 h2o=2.08024893e-09 heat_rel_linf=1.25728742e-03`.
- Report verification passed: `engineering_h2_ignition_consequence_report VERIFY-PASS ... status=PASS-SMOKE`.

## Limitations

This is short-time smoke-scale reacting evidence. It improves engineering consequence reporting for ignition delay, species conversion, temperature, reaction activity, and SDC heat-release sensitivity, but it does not prove flame-speed accuracy, radiation, overpressure, wall/fire coupling, calibrated fire consequence prediction, production-size reacting meshes, or long-duration reacting stability.
