# Strict Artifact Drop Preflight

- Status: `AWAITING-MASTER-PLAN-STRICT-ARTIFACT-DROP-PREFLIGHT-EXTERNAL-ARTIFACTS`
- Ready for artifact drop: `True`
- Complete domains: `1/3`

## Domains

### external_plume

- Status: `AWAITING_EXTERNAL_ARTIFACTS`
- Drop root: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset`
- Missing required artifacts: `dataset_metadata.json, sensor_coordinates.csv, baffle_geometry.csv, experimental_timeseries.csv`
- Missing required file groups: `none`
- Primary post-intake command: `python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py`

### fire_calibration

- Status: `COMPLETE`
- Drop root: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset`
- Missing required artifacts: `none`
- Missing required file groups: `none`
- Primary post-intake command: `python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py`

### real_cad

- Status: `AWAITING_EXTERNAL_ARTIFACTS`
- Drop root: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package`
- Missing required artifacts: `real_cad_cleanup_manifest.json, real_cad_data_room_index.csv, real_cad_cleanup_quality_record.csv, real_cad_boundary_tags.csv`
- Missing required file groups: `source_cad_files, cleaned_geometry_files`
- Primary post-intake command: `python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py`
