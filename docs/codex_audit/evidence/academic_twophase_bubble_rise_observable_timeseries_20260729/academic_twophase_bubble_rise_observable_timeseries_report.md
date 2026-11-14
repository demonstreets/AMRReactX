# Academic Bubble-Rise Canonical Observable Diagnostics

Status: `PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-OBSERVABLE-DIAGNOSTICS`

Key diagnostics:
- plot count: `16`
- final time: `1.765215992784e-04`
- center-of-mass rise: `2.073149924370e-07`
- max finite-difference rise velocity: `1.476187261285e-03`
- min circularity estimate: `8.615439736424e-01`
- light volume relative drift: `6.673847249049e-06`

Quality gates:

| Gate | Status | Metric |
| --- | --- | --- |
| `observable_fields_present` | `PASS` | `["density", "rho_adv_0", "ymom"]` |
| `at_least_endpoint_observables` | `PASS` | `16` |
| `canonical_timeseries_sampling` | `PASS` | `16` |
| `center_of_mass_history_available` | `PASS` | `[0.10000011020238767, 0.1000003175173801]` |
| `rise_velocity_history_available` | `PASS` | `{"max_fd_velocity": 0.0014761872612848942, "min_fd_velocity": 0.0009632412473304209}` |
| `circularity_history_available` | `PASS` | `{"max": 0.8615468485632067, "min": 0.8615439736423774}` |
| `light_volume_conservation_diagnostic` | `NOT_READY` | `6.673847249048797e-06` |
