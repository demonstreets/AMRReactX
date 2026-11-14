# HySafe SBEPV5 D27 Digitization Preflight

Status: `PASS-SBEPV5-D27-DIGITIZATION-PREFLIGHT`
Dataset root: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset`
Ready for dataset ingestion: `False`
Clears reference-data blocker: `False`

## Summary

- `public_source_registry_available`: `True`
- `template_count`: `5`
- `templates_available`: `True`
- `dataset_ingestion_status`: `NOT_READY-SBEPV5-D27-DATASET-INGESTION`
- `dataset_metadata_available`: `False`
- `sensor_coordinates_available`: `False`
- `baffle_geometry_available`: `False`
- `experimental_timeseries_available`: `False`
- `ready_for_dataset_ingestion`: `False`
- `missing_artifact_count`: `4`

## Missing Artifacts

- `dataset_metadata.json`: replace the metadata template with URL/DOI, source file hash, digitization method, uncertainty basis, and case-alignment booleans
- `sensor_coordinates.csv`: digitize or obtain Gas01..Gas12 coordinates with reliability tags and <=0.02 m uncertainty
- `baffle_geometry.csv`: digitize or obtain baffles 1..4 bounds with source basis and <=0.02 m uncertainty
- `experimental_timeseries.csv`: obtain original Excel or digitize Gas01..Gas12 concentration histories through at least 120 s

## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `public_source_registry_available` | `PASS` | none |
| `digitization_templates_available` | `PASS` | none |
| `dataset_metadata_ingested` | `MISSING` | Fill and validate dataset_metadata.json. |
| `sensor_coordinates_ingested` | `MISSING` | Fill and validate sensor_coordinates.csv. |
| `baffle_geometry_ingested` | `MISSING` | Fill and validate baffle_geometry.csv. |
| `experimental_timeseries_ingested` | `MISSING` | Fill and validate experimental_timeseries.csv. |
| `dataset_ingestion_ready` | `MISSING` | The official SBEPV5 D27 dataset ingestion report must PASS. |

## Evidence Files

- `public_source_triage_report`: `docs/codex_audit/evidence/engineering_h2_external_plume_public_source_triage_20260724/external_plume_public_source_triage_report.json` sha256 `a2489e6fd7cfc17b`
- `dataset_ingestion_report`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/sbepv5_d27_dataset_ingestion_report.json` sha256 `51a726d2e60369c4`
- `digitization_template_1`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata_template.json` sha256 `ab22faaab2ae8fc1`
- `digitization_template_2`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates_template.csv` sha256 `4f21dd495f09cf2a`
- `digitization_template_3`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry_template.csv` sha256 `b0c22a5bc7df1816`
- `digitization_template_4`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries_template.csv` sha256 `d0c00bf0e30dbc43`
- `digitization_template_5`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/digitization_uncertainty_record_template.csv` sha256 `513612703a3bcade`

## Limitations

- This preflight creates and verifies digitization templates only; it does not ingest original experimental data.
- The reference-data blocker remains open until dataset ingestion, external dataset building, and official reference agreement all pass.
