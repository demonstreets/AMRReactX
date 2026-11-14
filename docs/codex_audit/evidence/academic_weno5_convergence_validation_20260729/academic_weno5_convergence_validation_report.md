# Academic WENO5 Convergence Validation

Status: `PASS-ACADEMIC-WENO5-CONVERGENCE-VALIDATION`

Scope: Maintained WENO5/WENO5-Z smooth-field convergence gate using the current CTest weno5_smoke and pelec_weno_smoke executables. This promotes the historical smooth sine regression into a reproducible report with explicit order and baseline-improvement gates.

## Summary

- `standalone_weno5_sine_order`: `4.93`
- `pelec_weno5z_p32_64`: `4.911286070252`
- `pelec_weno5z_p64_128`: `4.955275049333`
- `pelec_weno5z_l1_n64`: `9.117999350597e-08`
- `second_order_face_average_l1_n64`: `0.001102731849977`
- `weno_to_second_order_error_ratio`: `8.268555361656759e-05`
- `clears_acd_01_weno5_order_gap`: `True`
- `clears_qlt_03_weno5_mms_order_subgap`: `True`

## Quality Gates

- `weno_ctests_built_and_passed`: `PASS`
- `standalone_weno5_sine_order`: `PASS`
- `pelec_weno5z_sine_order`: `PASS`
- `weno5z_beats_second_order_baseline`: `PASS`

## Limitations

- This is a smooth scalar/cell-average WENO order gate; it does not prove characteristic projection accuracy.
- This report strengthens ACD-01/QLT-03 order evidence but does not replace full-flow WENO-vs-PPM detonation comparisons.
- The gate uses current CTest output as authoritative evidence, so report verification also hashes the test sources and logs.
