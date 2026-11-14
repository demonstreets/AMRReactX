# Engineering H2 Fire Calibration Dataset

This directory is the ingestion root for external H2 fire and blast calibration evidence.

Required production data files:
- `calibration_metadata.json`
- `radiation_metrics.csv`
- `overpressure_metrics.csv`

Templates in this directory show the required schema. The ingestion report remains NOT_READY until real calibration data files pass validation.

`fire_calibration_intake_checklist.csv` lists the production intake rules that must be backed by controlled external evidence.

Production credit is only claimed after the official fire consequence report passes with the generated calibration dataset JSON.
