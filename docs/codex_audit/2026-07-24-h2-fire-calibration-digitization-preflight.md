# Engineering H2 Fire Calibration Digitization Preflight

## Purpose

The engineering H2 scorecard still blocks production readiness on
`fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`.
Public source triage identifies candidate radiation and overpressure sources,
but local calibration metadata and metric CSVs are still missing. The program
must not claim production-grade fire consequence agreement from screening-only
radiation and overpressure estimates.

## Change

Added `tools/write_engineering_h2_fire_calibration_digitization_preflight_report.py`.

The report creates and verifies templates for:

- `calibration_metadata_template.json`
- `radiation_metrics_template.csv`
- `overpressure_metrics_template.csv`
- `fire_calibration_source_registry_template.csv`
- `fire_calibration_digitization_uncertainty_template.csv`

It records public-source availability, template availability, missing
calibration artifacts, and whether the official fire calibration dataset
ingestion report is ready.

## Verification

The engineering H2 production verifier now requires the fire calibration
digitization preflight report. The production evidence verification report also
records the preflight status, template availability, and missing artifact count.

## Limitation

This change does not digitize fire/blast figures, does not fabricate calibration
data, and does not clear the fire-consequence blocker. Production credit still
requires real or accepted digitized radiation and overpressure metrics, a
generated calibration dataset JSON, and the official fire consequence report run
against that dataset.
