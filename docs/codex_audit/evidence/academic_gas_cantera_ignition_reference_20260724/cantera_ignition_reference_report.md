# Academic Gas Cantera H2/O2 Ignition Reference Curve

Status: `PASS-ACADEMIC-GAS-CANTERA-IGNITION-REFERENCE`
Mechanism: `h2o2.yaml`
Cantera: `3.2.0`
Curve CSV: `docs/codex_audit/evidence/academic_gas_cantera_ignition_reference_20260724/cantera_ignition_reference_curve.csv` sha256 `6b4bbb6ec8fe098f`

## Summary

- `case_count`: `4`
- `min_temperature_k`: `1000.0`
- `max_temperature_k`: `1300.0`
- `min_ignition_delay_s`: `5.4113919943847135e-05`
- `max_ignition_delay_s`: `0.0003212730681333078`
- `delay_monotonic_decreases_with_temperature`: `True`
- `reference_curve_available`: `True`
- `clears_zero_d_ignition_delay_reference_curve_gap`: `True`
- `clears_cantera_mechanism_comparison_gap`: `False`

## Cases

| T0 K | ignition delay s | max OH | max T K | steps |
| --- | --- | --- | --- | --- |
| `1000.0` | `3.21273068e-04` | `3.14856523e-02` | `2908.624` | `1520` |
| `1100.0` | `1.05408667e-04` | `3.30153584e-02` | `2928.370` | `1372` |
| `1200.0` | `6.72169968e-05` | `3.45702594e-02` | `2947.652` | `1348` |
| `1300.0` | `5.41139199e-05` | `3.61474392e-02` | `2966.455` | `1362` |

## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `cantera_importable` | `PASS` | none |
| `mechanism_loadable` | `PASS` | none |
| `multi_temperature_curve` | `PASS` | none |
| `monotonic_temperature_response` | `PASS` | none |
| `pele_mechanism_equivalence` | `MISSING` | This report generates a Cantera reference curve but does not compare PelePhysics generated rates/species against Cantera. |

## Limitations

- This report provides a Cantera reference curve only; it does not prove Pele/PelePhysics mechanism equivalence.
- The curve is constant-volume 0D kinetics evidence and does not prove multidimensional detonation accuracy.
