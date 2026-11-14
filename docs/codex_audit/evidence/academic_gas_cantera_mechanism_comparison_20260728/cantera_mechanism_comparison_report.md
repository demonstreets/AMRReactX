# Academic Gas Cantera Mechanism Comparison

Status: `PASS-ACADEMIC-GAS-CANTERA-MECHANISM-COMPARISON`
Scope: `Cantera-loadable PelePhysics LiDryer vs Cantera h2o2 thermochemistry, finite rates, and 0D ignition-delay comparison`
Cantera: `3.2.0`
PelePhysics mechanism: `external/PelePhysics/Mechanisms/LiDryer/mechanism.yaml`
Reference mechanism: `h2o2.yaml`
CSV: `docs/codex_audit/evidence/academic_gas_cantera_mechanism_comparison_20260728/cantera_mechanism_comparison_curve.csv`

## Summary

- `mechanism_count`: `2`
- `shared_required_h2_species`: `['H', 'H2', 'H2O', 'H2O2', 'HO2', 'N2', 'O', 'O2', 'OH']`
- `state_rate_sample_count`: `8`
- `ignition_case_count`: `8`
- `ignition_delay_pair_count`: `4`
- `max_ignition_delay_ratio`: `1.4254867317045181`
- `ignition_delay_ratio_limit`: `50.0`
- `pelephysics_yaml_loads_in_cantera`: `True`
- `reference_h2o2_yaml_loads_in_cantera`: `True`
- `thermochemistry_samples_finite`: `True`
- `reaction_rate_samples_finite`: `True`
- `ignition_delay_curves_monotonic`: `True`
- `ignition_delay_curves_same_order`: `True`
- `clears_cantera_mechanism_comparison_gap`: `True`
- `clears_full_pelephysics_source_rate_equivalence`: `False`

## Ignition Delay Comparison

| T0 K | PelePhysics LiDryer s | Cantera h2o2 s | Ratio |
| --- | --- | --- | --- |
| `1000.0` | `2.25377803e-04` | `3.21273068e-04` | `1.425` |
| `1100.0` | `9.00797700e-05` | `1.05408667e-04` | `1.170` |
| `1200.0` | `5.47785737e-05` | `6.72169968e-05` | `1.227` |
| `1300.0` | `4.02218548e-05` | `5.41139199e-05` | `1.345` |

## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `cantera_importable` | `PASS` | none |
| `pelephysics_lidryer_loadable` | `PASS` | none |
| `reference_h2o2_loadable` | `PASS` | none |
| `required_h2_species_shared` | `PASS` | none |
| `finite_thermochemistry_samples` | `PASS` | none |
| `finite_reaction_rate_samples` | `PASS` | none |
| `paired_0d_ignition_delay_curves` | `PASS` | none |
| `compiled_pelephysics_rate_kernel_equivalence` | `PARTIAL` | Not exercised here; this report compares the PelePhysics YAML through Cantera, not the generated C++ rate kernel. |

## Limitations

- This clears the readiness-level Cantera mechanism comparison gap by checking two Cantera-loaded mechanisms.
- It does not prove bitwise or tolerance-bound equivalence between Cantera and the compiled PelePhysics C++ rate kernel.
- The 0D ignition-delay ratio is a coarse same-order gate, not a detonation validation benchmark.
