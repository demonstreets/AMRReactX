# Engineering H2 Fire Calibration Digitization Preflight

Status: `PASS-H2-FIRE-CALIBRATION-DIGITIZATION-PREFLIGHT`
Dataset root: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset`
Ready for dataset ingestion: `False`
Clears fire-consequence blocker: `False`

## Summary

- `public_source_registry_available`: `True`
- `radiation_candidate_available`: `True`
- `overpressure_candidate_available`: `True`
- `template_count`: `5`
- `templates_available`: `True`
- `dataset_ingestion_status`: `NOT_READY-H2-FIRE-CALIBRATION-DATASET-INGESTION`
- `metadata_available`: `False`
- `radiation_metrics_available`: `True`
- `overpressure_metrics_available`: `True`
- `ready_for_dataset_ingestion`: `False`
- `missing_artifact_count`: `4`

## Missing Artifacts

- `calibration_metadata.json`: select calibration sources and record source hash, uncertainty, and all case-alignment booleans
- `radiation_metrics.csv`: digitize or obtain heat-flux measurements with distances, tolerances, and source basis
- `overpressure_metrics.csv`: digitize or obtain peak overpressure measurements with distances, tolerances, and source basis
- `calibrated_fire_consequence_report`: rerun the official fire consequence report with the generated calibration dataset JSON

## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `public_source_registry_available` | `PASS` | none |
| `digitization_templates_available` | `PASS` | none |
| `calibration_metadata_ingested` | `MISSING` | Fill and validate calibration_metadata.json. |
| `radiation_metrics_ingested` | `PASS` | none |
| `overpressure_metrics_ingested` | `PASS` | none |
| `dataset_ingestion_ready` | `MISSING` | The official fire calibration dataset ingestion report must PASS. |

## Evidence Files

- `fire_calibration_public_source_triage_report`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_public_source_triage_20260724/fire_calibration_public_source_triage_report.json` sha256 `41249a0709ec1540`
- `fire_calibration_dataset_ingestion_report`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/fire_calibration_dataset_ingestion_report.json` sha256 `ec57ea9833fa93b6`
- `fire_calibration_template_1`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/templates/calibration_metadata_template.json` sha256 `72eed91b6b3de739`
- `fire_calibration_template_2`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/templates/radiation_metrics_template.csv` sha256 `d4833e4fb31ad59c`
- `fire_calibration_template_3`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/templates/overpressure_metrics_template.csv` sha256 `76f0671332b4dd48`
- `fire_calibration_template_4`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/templates/fire_calibration_source_registry_template.csv` sha256 `1b9b10cf59ce3d1b`
- `fire_calibration_template_5`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/templates/fire_calibration_digitization_uncertainty_template.csv` sha256 `7d9f7ca1b7bcf1db`

## Limitations

- This preflight creates and verifies calibration digitization templates only; it does not ingest experimental data.
- The fire-consequence blocker remains open until ingestion, dataset building, and calibrated consequence agreement all pass.
