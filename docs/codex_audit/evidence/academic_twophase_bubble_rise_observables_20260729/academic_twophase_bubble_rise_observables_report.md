# Academic Bubble-Rise Canonical Observable Diagnostics

Status: `PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-OBSERVABLE-DIAGNOSTICS`

Key diagnostics:
- plot count: `2`
- final time: `4.490387009927e-05`
- center-of-mass rise: `2.529826931275e-09`
- max finite-difference rise velocity: `5.633872816935e-05`
- min circularity estimate: `7.988340904664e-01`
- light volume relative drift: `1.624562732202e-07`

Quality gates:

| Gate | Status | Metric |
| --- | --- | --- |
| `observable_fields_present` | `PASS` | `["density", "rho_adv_0", "ymom"]` |
| `at_least_endpoint_observables` | `PASS` | `2` |
| `canonical_timeseries_sampling` | `NOT_READY` | `2` |
| `center_of_mass_history_available` | `PASS` | `[0.1, 0.10000000252982694]` |
| `rise_velocity_history_available` | `PASS` | `{"max_fd_velocity": 5.633872816934542e-05, "min_fd_velocity": 5.633872816934542e-05}` |
| `circularity_history_available` | `PASS` | `{"max": 0.7988341553541805, "min": 0.7988340904663678}` |
| `light_volume_conservation_diagnostic` | `NOT_READY` | `1.6245627322019312e-07` |
