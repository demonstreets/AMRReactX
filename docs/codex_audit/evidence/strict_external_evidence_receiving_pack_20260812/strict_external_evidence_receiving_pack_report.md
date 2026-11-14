# Strict External Evidence Receiving Pack

- Status: `PASS-STRICT-EXTERNAL-EVIDENCE-RECEIVING-PACK`
- Ready: `True`
- Required files: `14`
- Present files: `5`
- Missing files: `9`
- Strict completion allowed: `False`

## Commands

```bash
python3 tools/codex_print_strict_external_artifact_drop_index.py
python3 tools/codex_print_strict_external_artifact_drop_index.py --json
bash tools/verify_strict_artifact_drop_contract_preflight.sh
bash tools/run_current_scope_release_refresh.sh
```

## Receiving Domains

### external_plume

- Required: `5`
- Present: `0`
- Missing: `5`

- `external_plume.baffle_geometry`
  target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry.csv`
  template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry_template.csv`
- `external_plume.dataset_metadata`
  target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata.json`
  template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata_template.json`
- `external_plume.digitization_uncertainty_record`
  target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/digitization_uncertainty_record.csv`
  template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/digitization_uncertainty_record_template.csv`
- `external_plume.experimental_timeseries`
  target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries.csv`
  template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries_template.csv`
- `external_plume.sensor_coordinates`
  target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates.csv`
  template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates_template.csv`
### fire_calibration

- Required: `5`
- Present: `5`
- Missing: `0`

- `fire_calibration.calibration_metadata`
  target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata.json`
  template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata_template.json`
- `fire_calibration.fire_calibration_digitization_uncertainty`
  target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_digitization_uncertainty.csv`
  template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_digitization_uncertainty_template.csv`
- `fire_calibration.fire_calibration_source_registry`
  target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_source_registry.csv`
  template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_source_registry_template.csv`
- `fire_calibration.overpressure_metrics`
  target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics.csv`
  template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics_template.csv`
- `fire_calibration.radiation_metrics`
  target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics.csv`
  template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics_template.csv`
### real_cad

- Required: `4`
- Present: `0`
- Missing: `4`

- `real_cad.real_cad_boundary_tags`
  target: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_boundary_tags.csv`
  template: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_boundary_tags_template.csv`
- `real_cad.real_cad_cleanup_manifest`
  target: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest.json`
  template: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest_template.json`
- `real_cad.real_cad_cleanup_quality_record`
  target: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record.csv`
  template: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record_template.csv`
- `real_cad.real_cad_data_room_index`
  target: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index.csv`
  template: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index_template.csv`

## Strict Boundary

- This receiving pack does not mark external artifacts complete.
- This receiving pack does not allow strict master-plan closure.
- Real external files are still required before strict closeout.
