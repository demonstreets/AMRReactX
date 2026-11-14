# H2 Fire Calibration Literature Metric Preflight

Date: 2026-07-24

## Purpose

Add a machine-checkable preflight for public literature metrics that can seed H2 fire
consequence calibration. This records radiation and overpressure metric anchors without
claiming calibrated production agreement.

## Added Evidence

- `tools/write_engineering_h2_fire_calibration_literature_metric_preflight_report.py`
- `docs/codex_audit/evidence/engineering_h2_fire_calibration_literature_metric_preflight_20260724/fire_calibration_literature_metric_preflight_report.json`
- `docs/codex_audit/evidence/engineering_h2_fire_calibration_literature_metric_preflight_20260724/fire_calibration_literature_metric_preflight_report.md`

## Metric Anchors

- Hydrogen jet-fire radiation measurement heights: 0.25 m, 0.50 m, 0.75 m, 1.00 m.
- Hydrogen jet-fire radial measurement distances: 0.23 m and 0.50 m.
- Example reported heat flux values from public literature are retained as sanity-scale anchors.
- HyIndoor low-strength enclosure overpressure scale: 31 m3 enclosure, 10 kPa target internal overpressure, up to 14% v/v H2.

## Production Rule

This report must not clear `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`.
It is an intermediate intake gate. Production clearance still requires:

- `calibration_metadata.json`,
- `radiation_metrics.csv`,
- `overpressure_metrics.csv`,
- generated calibration dataset JSON,
- official calibrated fire consequence report.
