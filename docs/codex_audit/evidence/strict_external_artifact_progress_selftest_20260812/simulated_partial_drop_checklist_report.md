# Strict External Artifact Drop Checklist

- Status: `PASS-STRICT-EXTERNAL-ARTIFACT-DROP-CHECKLIST`
- Source index: `PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX`
- Domains: `3`
- Required files: `14`
- Missing files: `11`
- Strict completion allowed: `False`

## Checklist

- [x] `external_plume` / `external_plume.baffle_geometry`
  - target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry.csv`
  - template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry_template.csv`
- [ ] `external_plume` / `external_plume.dataset_metadata`
  - target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata.json`
  - template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata_template.json`
- [ ] `external_plume` / `external_plume.digitization_uncertainty_record`
  - target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/digitization_uncertainty_record.csv`
  - template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/digitization_uncertainty_record_template.csv`
- [ ] `external_plume` / `external_plume.experimental_timeseries`
  - target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries.csv`
  - template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries_template.csv`
- [ ] `external_plume` / `external_plume.sensor_coordinates`
  - target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates.csv`
  - template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates_template.csv`
- [x] `fire_calibration` / `fire_calibration.calibration_metadata`
  - target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata.json`
  - template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata_template.json`
- [ ] `fire_calibration` / `fire_calibration.fire_calibration_digitization_uncertainty`
  - target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_digitization_uncertainty.csv`
  - template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_digitization_uncertainty_template.csv`
- [ ] `fire_calibration` / `fire_calibration.fire_calibration_source_registry`
  - target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_source_registry.csv`
  - template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_source_registry_template.csv`
- [ ] `fire_calibration` / `fire_calibration.overpressure_metrics`
  - target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics.csv`
  - template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics_template.csv`
- [ ] `fire_calibration` / `fire_calibration.radiation_metrics`
  - target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics.csv`
  - template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics_template.csv`
- [x] `real_cad` / `real_cad.real_cad_boundary_tags`
  - target: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_boundary_tags.csv`
  - template: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_boundary_tags_template.csv`
- [ ] `real_cad` / `real_cad.real_cad_cleanup_manifest`
  - target: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest.json`
  - template: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest_template.json`
- [ ] `real_cad` / `real_cad.real_cad_cleanup_quality_record`
  - target: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record.csv`
  - template: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record_template.csv`
- [ ] `real_cad` / `real_cad.real_cad_data_room_index`
  - target: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index.csv`
  - template: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index_template.csv`

## Commands

```bash
python3 tools/codex_print_strict_external_artifact_drop_index.py
bash tools/verify_strict_artifact_drop_contract_preflight.sh
bash tools/run_current_scope_release_refresh.sh
```
