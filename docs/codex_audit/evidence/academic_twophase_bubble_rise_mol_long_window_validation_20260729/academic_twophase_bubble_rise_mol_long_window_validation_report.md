# Academic Two-Phase Bubble-Rise MOL Long-Window Validation

- Status: `PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-MOL-LONG-WINDOW-VALIDATION`
- Max step: `30000`
- Final time: `0.000176521599278`
- Centroid rise: `2.07314992437e-07`
- Mass relative drift: `8.55404198409e-15`
- Advected mass relative drift: `8.31766543588e-15`
- do_mol: `1`
- p0: `1.0`

## Scope

PeleC two-phase VOF bubble-rise long-window stability gate with problem-specific buoyancy source and PeleC do_mol=1 hydro path and a smooth phase-consistent initial interface; this proves extended positive, finite, conservative MOL-hydro source-coupled behavior but not canonical viscous bubble-rise validation.

## Gates

| Gate | Status |
| --- | --- |
| `run_finalized_without_failure_tokens` | `PASS` |
| `positive_finite_state` | `PASS` |
| `bounded_vof_alpha` | `PASS` |
| `mass_and_advected_scalar_conservation` | `PASS` |
| `upward_light_phase_centroid_motion` | `PASS` |
| `scope_limited_to_mol_long_window` | `PASS` |

## Limitations

- This evidence clears the maintained PeleC do_mol=1 long-window stability gate, but it is still an in-repository smooth-interface numerical gate rather than an external canonical bubble-rise benchmark.
- The maintained 6000-step short-time gate, inviscid long-window gate, and formal historical NOT_READY probes remain separate evidence.
