# Engineering H2 Ignition Consequence Report

Status: `PASS-SMOKE`
Generated UTC: `2026-07-20T03:25:22+00:00`

## Summary

- Ignition delay fine estimate: `4.52388239e-05` s
- Mid/fine ignition-delay relative difference: `5.32379232e-04`
- Mean H2 consumed: `4.91515359e-09`
- Mean O2 consumed: `7.92990513e-08`
- Mean H2O produced: `2.08024893e-09`
- History peak temperature range: `1.99999562e+03` to `2.00000000e+03` K
- History max heat/reaction rate metric: `1.49553322e+07`
- SDC HeatRelease relative Linf: `1.25728742e-03`

## Evidence Logs

- history: `docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/history/validation.log` sha256=`619a389d9ecf2786`
- delay: `docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/delay/validation.log` sha256=`b27647b94d256a5a`
- sdc: `docs/codex_audit/evidence/engineering_h2_ignition_consequence_20260720/sdc/sdc_compare.log` sha256=`f5e894fc36dd3cc4`

## Limitations

- This is a short-time H2 ignition and heat-release consequence smoke report, not a calibrated fire model.
- It does not validate flame speed, radiant heat flux, pool-fire feedback, deflagration overpressure, ventilation effects, or production-scale obstacle fires.
- Ignition-delay evidence uses a homogeneous PelePhysics driver; history/SDC evidence uses the PeleLMeX hot-bubble engineering case.
