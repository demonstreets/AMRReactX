# Academic Two-Phase Canonical Bubble-Rise Reference Preflight

Status: `NOT_READY-ACADEMIC-TWOPHASE-CANONICAL-BUBBLE-RISE-REFERENCE`

Reference:
- `Hysing-Turek-Kuzmin-Parolini-Burman-Ganesan-Tobiska 2D rising bubble benchmark`
- DOI: `10.1002/fld.1934`

Blocking gaps:
- `canonical_final_time_contract`

Quality gates:

| Gate | Status | Metric | Target |
| --- | --- | --- | --- |
| `domain_aspect_ratio_matches_1x2_column` | `PASS` | `2.0` | `2.0` |
| `initial_bubble_radius_matches_canonical_fraction` | `PASS` | `0.25` | `0.25` |
| `initial_bubble_center_matches_canonical_fraction` | `PASS` | `[0.5, 0.25]` | `[0.5, 0.25]` |
| `density_ratio_matches_hysing_case_1` | `PASS` | `10.0` | `10.0` |
| `gravity_matches_hysing_case_1_scale` | `PASS` | `0.98` | `0.98` |
| `surface_tension_contract_present` | `PASS` | `["prob.surface_tension_sigma", "prob.surface_tension_grad_floor", "prob.surface_tension_force_cap"]` | `"surface tension parameter equivalent to sigma=24.5"` |
| `viscosity_contract_present` | `PASS` | `["prob.phase_viscosity_mu_heavy", "prob.phase_viscosity_mu_light", "prob.phase_viscosity_force_cap"]` | `"liquid/bubble viscosity equivalent to 10/1"` |
| `canonical_observable_timeseries_available` | `PASS` | `{"clears_canonical_observable_timeseries_gap": true, "has_center_of_mass": true, "has_circularity": true, "has_rise_velocity": true, "observables_report_status": "PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-OBSERVABLE-DIAGNOSTICS", "plot_count": 16}` | `{"benchmark_quantities": ["center_of_mass", "mean_rise_velocity", "circularity"], "minimum_time_samples": 16}` |
| `canonical_final_time_contract` | `NOT_READY` | `0.001` | `3.0` |
