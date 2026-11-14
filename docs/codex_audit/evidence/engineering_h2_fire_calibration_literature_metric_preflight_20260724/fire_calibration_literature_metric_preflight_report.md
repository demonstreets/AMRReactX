# Engineering H2 Fire Calibration Literature Metric Preflight

Status: `PASS-H2-FIRE-CALIBRATION-LITERATURE-METRIC-PREFLIGHT`
Clears fire-consequence blocker: `False`
Ready for dataset ingestion: `False`

## Metric Anchors

- `mdpi_jet_fire_radiometer_layout` (radiation): `{'flame_axis_heights_m': [0.25, 0.5, 0.75, 1.0], 'radial_distances_m': [0.23, 0.5], 'leak_diameters_mm': [1.2, 1.5, 2.0]}`
- `mdpi_jet_fire_reference_flux_bounds` (radiation): `{'max_flux_w_m2_at_0p23m_1p2mm': 952.8, 'max_flux_w_m2_at_0p23m_2p0mm': 3378.1, 'flux_w_m2_1p5mm_0p6mpa_0p23m': 1360.5, 'flux_w_m2_1p5mm_0p6mpa_0p50m': 412.1}`
- `mdpi_jet_fire_model_error_anchor` (radiation): `{'average_error_percent': 13.9, 'max_error_percent': 21.7}`
- `hyindoor_overpressure_scale_anchor` (overpressure): `{'enclosure_volume_m3': 31.0, 'maximum_internal_overpressure_target_kpa': 10.0, 'maximum_h2_concentration_vv_percent': 14.0}`

## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `public_source_triage_ready` | `PASS` | docs/codex_audit/evidence/engineering_h2_fire_calibration_public_source_triage_20260724/fire_calibration_public_source_triage_report.json |
| `digitization_preflight_ready` | `PASS` | docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/fire_calibration_digitization_preflight_report.json |
| `radiation_metric_anchor_available` | `PASS` | MDPI jet-fire radiometer layout and heat-flux examples recorded |
| `overpressure_metric_anchor_available` | `PASS` | HyIndoor low-strength enclosure overpressure scale recorded |
| `local_metric_csvs_still_missing` | `MISSING` | Local radiation_metrics.csv and overpressure_metrics.csv are still required for calibration ingestion. |

## Missing Artifacts

- `radiation_metrics.csv`: digitize or obtain heat-flux rows with distance, tolerance, and source basis
- `overpressure_metrics.csv`: digitize or obtain overpressure rows with gauge location, tolerance, and source basis
- `fire_calibration_acceptance_overlay.json`: after calibrated consequence output exists, compare radiation/overpressure predictions to metric anchors

## Limitations

- The metric anchors are public-literature intake checks, not calibrated consequence agreement.
- The fire-consequence blocker remains until local radiation/overpressure data are ingested and the official calibrated consequence report passes.
