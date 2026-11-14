# Academic Two-Phase Bubble-Rise Long-Window Probe Gate

Status: `NOT_READY-ACADEMIC-TWOPHASE-BUBBLE-RISE-LONG-WINDOW-PROBE-GATE`

Key metrics:
- formal short-time gate status: `PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-VALIDATION`
- formal centroid rise: `2.529826931270e-09`
- energy probe cases: `15`
- stable formal gate steps: `6000`
- non-finite boundary observed near step: `6813`
- failed long-window case count: `2`
- energy-correction probe cases: `4`
- energy-correction NaN cases: `2`
- energy-correction negative-energy cases: `2`
- energy-correction passing cases: `0`
- positivity probe cases: `17`
- positivity probe passing cases: `1`

Energy-correction probe diagnosis:
- Disabling the second-order buoyancy energy correction is not sufficient: molecular-transport cases still stopped on NaNs, while inviscid cases finalized with negative rho_e.

Positivity probe diagnosis:
- Post-timestep rho_e/Temp positivity protection prevents several negative-energy terminal states, but long-window cases still fail canonical bubble-rise motion or viscous NaN stability; source sign and source magnitude probes do not clear the gap.

Readiness:
- short-time bubble response: `True`
- canonical long-time bubble rise: `False`
- broad bubble-rise QLT-03 gap: `False`

Quality gates:

| Gate | Status | Metric |
| --- | --- | --- |
| `formal_6000_step_gate_remains_stable` | `PASS` | `{"centroid_rise": 2.52982693127e-09, "main_status": "PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-VALIDATION", "short_time_clear": true}` |
| `energy_probe_cases_are_attached` | `PASS` | `{"case_count": 15, "energy_status": "NOT_READY-ACADEMIC-TWOPHASE-BUBBLE-RISE-LONG-WINDOW-ENERGY-PROBE"}` |
| `longer_window_failure_boundary_is_reproducible` | `PASS` | `{"nonfinite_boundary_observed_near_step": 6813, "stable_formal_gate_steps": 6000}` |
| `long_window_credit_remains_blocked` | `PASS` | `{"energy_long_clear": false, "longer_long_clear": false, "main_long_clear": false}` |
| `long_window_cases_include_failure_diagnostics` | `PASS` | `{"failed_long_case_count": 2}` |
| `energy_correction_probe_confirms_issue_is_not_single_switch` | `PASS` | `{"case_count": 4, "nan_case_count": 2, "negative_energy_case_count": 2, "passing_case_count": 0}` |
| `positivity_probe_records_remaining_motion_gap` | `PASS` | `{"case_count": 17, "clears_canonical_long_window_bubble_rise": false, "passing_case_count": 1}` |
