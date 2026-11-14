# 2026-07-23 H2 Fire Calibration Dataset Builder

## Scope

Production-readiness blocker:
`fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`.

The fire calibration ingestion gate now defines the expected external data
files. This pass adds the builder that converts a passed ingestion package into
the `--calibration-dataset-json` consumed by the official fire consequence
metrics report.

## Changes

Added `tools/write_engineering_h2_fire_calibration_dataset_report.py`.

The builder requires:

- a passing screening fire consequence report;
- `PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION`;
- radiation and overpressure metrics with distances that map to summary keys in
  the fire consequence report;
- both radiation and overpressure metric families.

`tools/write_engineering_h2_fire_consequence_metrics_report.py` now exposes
distance-specific summary keys such as `screening_flux_at_1m_w_m2` and
`screening_overpressure_at_1m_kpa`, so calibration rows can target specific
measurement distances rather than only the maximum screening value.

`tools/verify_engineering_h2_production_evidence.sh` now verifies the builder
report.

## Current Status

The builder is expected to be `NOT_READY` until real calibration metadata and
radiation/overpressure CSVs are supplied. It does not clear the fire blocker by
itself; the official fire consequence report must pass with the generated
dataset JSON before production credit is claimed.
