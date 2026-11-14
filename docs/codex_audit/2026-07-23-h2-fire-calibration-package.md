# Engineering H2 Fire Calibration Package Gate

## Purpose

The fire consequence chain already has:

- a screening fire/radiation/overpressure report,
- a strict calibration dataset ingestion report,
- a builder that can turn passed ingestion data into the calibration JSON used
  by the official fire consequence report.

The missing workflow piece was a durable data package with templates for the
external calibration files that must be supplied before production credit can be
claimed.

## Change

Added `tools/write_engineering_h2_fire_calibration_package_report.py`.

The package writes templates in the ingestion dataset root:

- `README.md`
- `calibration_metadata_template.json`
- `radiation_metrics_template.csv`
- `overpressure_metrics_template.csv`

The report remains `NOT_READY-H2-FIRE-CALIBRATION-PACKAGE` until the ingestion
report passes with real:

- `calibration_metadata.json`
- `radiation_metrics.csv`
- `overpressure_metrics.csv`

## Verification

`tools/verify_engineering_h2_production_evidence.sh` now requires and verifies
the fire calibration package report. The production evidence verification report
records package readiness, metadata availability, radiation metrics availability,
and overpressure metrics availability.

## Limitation

This change does not create experimental fire/blast evidence and does not clear
the fire-consequence production blocker. It makes the missing external
calibration data path explicit, reproducible, and machine-verifiable.
