# Engineering H2 Fire Calibration Quality Gate Tightening

## Purpose

The engineering production scorecard still blocks production readiness on
`fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`.
The existing fire calibration package created templates for external
radiation/overpressure data, but the package report did not expose a production
review checklist or a machine-verifiable quality gate matrix.

## Change

Updated `tools/write_engineering_h2_fire_calibration_package_report.py` so the
package now writes and verifies:

- `fire_calibration_intake_checklist.csv`
- a `quality_gate_matrix` in `fire_calibration_package_report.json`
- Markdown rows for the calibration package quality gates

The quality matrix covers:

- ingestion report status
- metadata availability
- experimental source type and public source identifier
- case alignment for fuel, release/cloud mass, ignition/burn basis,
  radiation measurement, overpressure measurement, and boundary conditions
- radiation metric rows
- overpressure metric rows
- radiation and overpressure family coverage
- readiness for the calibration dataset builder
- explicit non-claim that the package itself clears the fire consequence blocker

## Production Meaning

This still does not clear the fire-consequence blocker. The package remains an
intake and validation contract. Production credit requires real external
calibration data to pass ingestion, the dataset builder to emit the calibration
dataset JSON, and the official fire consequence report to pass with that
dataset.

## Verification

The updated report remains `NOT_READY-H2-FIRE-CALIBRATION-PACKAGE` until real
metadata, radiation metrics, and overpressure metrics are supplied. The full
engineering H2 verifier continues to require this report and fails if its
status, hashes, or quality matrix are inconsistent.
