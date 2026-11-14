# 2026-07-23 H2 Fire Calibration Dataset Ingestion Gate

## Scope

Production-readiness blocker:
`fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`.

The fire consequence report already supports a strict calibration dataset, but
there was no separate ingestion gate that made the required external dataset
files and schemas visible. This pass adds that gate.

## Changes

Added `tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py`.

The ingestion report expects:

- `calibration_metadata.json`
- `radiation_metrics.csv`
- `overpressure_metrics.csv`

It checks that metadata uses
`dataset_type = h2_fire_consequence_calibration_agreement`, declares an
experimental or literature-digitized source, includes public source metadata,
and marks case alignment for fuel, release/cloud mass, ignition/burn basis,
radiation measurement basis, overpressure measurement basis, and boundary
conditions.

Radiation metrics must provide distance, reference heat flux, absolute and
relative tolerances, and a source basis. Overpressure metrics must provide
distance, reference overpressure, absolute and relative tolerances, and a
source basis.

`tools/verify_engineering_h2_production_evidence.sh` now verifies this
ingestion report as part of the engineering H2 production evidence chain.

## Current Status

The report is expected to be `NOT_READY` until real calibration data is
supplied. It does not clear the fire-consequence blocker; the official fire
consequence metrics report must still pass with `--calibration-dataset-json`.
