# Academic Two-Phase Canonical Bubble-Rise Final-Time Scout

Status: `PASS-ACADEMIC-TWOPHASE-CANONICAL-BUBBLE-RISE-FINAL-TIME-SCOUT`

Quality gates:

| Gate | Status | Metric |
| --- | --- | --- |
| `final_time_scout_run_finalized` | `PASS` | `[]` |
| `long_window_stability_probe` | `PASS` | `{"adv_mass_rel_drift": 2.49622493539e-16, "mass_rel_drift": 1.21934707339e-16, "time1": 6.13050828568e-05}` |
| `canonical_contract_inputs_retained` | `PASS` | `{"average_physical_dt": 1.2261016571360001e-08, "bubble_center_over_domain": [0.5, 0.25], "bubble_radius_over_domain_width": 0.25, "density_ratio_heavy_over_light": 10.0, "domain_aspect_height_over_width": 2.0, "domain_height": 2.0, "domain_width": 1.0, "estimated_steps_to_t3_at_scout_dt": 244677918, "estimated_wall_seconds_to_t3_at_scout_rate": 685098.1704, "gravity": 0.98, "max_step": 5000, "phase_viscosity_mu_heavy": 10.0, "phase_viscosity_mu_light": 1.0, "plot_int": 5000, "surface_tension_sigma": 24.5, "target_stop_time": 3.0}` |
| `canonical_final_time_contract` | `NOT_READY` | `6.13050828568e-05` |
| `direct_t3_runtime_viability` | `NOT_READY` | `{"estimated_steps_to_t3": 244677918, "estimated_wall_seconds_to_t3": 685098.1704}` |
