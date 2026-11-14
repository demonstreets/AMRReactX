# Academic Two-Phase Bubble-Rise Inviscid Long-Window Validation

- Status: `PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-INVISCID-LONG-WINDOW-VALIDATION`
- Max step: `30000`
- Final time: `0.000176280241932`
- Centroid rise: `3.46351031771e-07`
- Mass relative drift: `0.0`
- Advected mass relative drift: `0.0`
- do_mol: `0`
- p0: `1.0`

## Scope

PeleC two-phase VOF bubble-rise long-window stability gate with problem-specific buoyancy source and molecular transport disabled and a smooth phase-consistent initial interface; this proves extended positive, finite, conservative inviscid source-coupled behavior but not canonical viscous bubble-rise validation.

## Gates

| Gate | Status |
| --- | --- |
| `run_finalized_without_failure_tokens` | `PASS` |
| `positive_finite_state` | `PASS` |
| `bounded_vof_alpha` | `PASS` |
| `mass_and_advected_scalar_conservation` | `PASS` |
| `upward_light_phase_centroid_motion` | `PASS` |
| `scope_limited_to_inviscid_long_window` | `PASS` |

## Limitations

- This evidence does not clear the canonical viscous long-time bubble-rise gap because molecular transport is disabled.
- The maintained viscous 6000-step short-time gate and the formal long-window NOT_READY probe remain separate evidence.
