# Academic Spray Source Budget Validation

Status: `PASS-ACADEMIC-SPRAY-SOURCE-BUDGET-VALIDATION`

This evidence validates PeleC spray source-field mapping and gas-side source-history accounting in a closed periodic spray smoke case.

Key metrics:
- gas mass delta: `5.9424687393061504e-14`
- integrated `spray_rho_src`: `5.9422218613892786e-14`
- gas/source relative error: `4.154640e-05`
- fuel mass delta: `5.9422226838582686e-14`
- integrated `spray_rhoY_NC7H16_src`: `5.9422218613892786e-14`
- fuel/source relative error: `1.384110e-07`
- particle/source relative mismatch: `1.513826e-07`
- 2D spray effective thickness factor: `7.812500e-01`

Readiness:
- plot source output fixed: `True`
- mapped spray source bug fixed: `True`
- ACD-05 gas source-history budget: `True`
- ACD-05 full gas-particle budget: `True`

Full gas-particle closure is cleared for this closed periodic spray source-history case using the PeleC 2D spray effective-thickness convention.
