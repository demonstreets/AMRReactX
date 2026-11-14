# Strict External Artifact Drop Index

- Status: `PASS-STRICT-EXTERNAL-ARTIFACT-DROP-INDEX`
- Domains: `3`
- Templates: `16`
- Required contract artifacts: `14`
- Awaiting missing artifacts: `9`
- Strict completion allowed: `False`

## Operator Next Steps

- Copy each *_template file to the matching non-template target path listed in domain_drop_index.
- Fill JSON required keys and CSV headers without renaming columns.
- Run bash tools/verify_strict_artifact_drop_contract_preflight.sh before asking for strict closeout.
- Then run bash tools/run_current_scope_release_refresh.sh to rebuild all closure evidence.

## external_plume

- `external_plume.baffle_geometry`
  target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry.csv`
  template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry_template.csv`
  csv_header: `baffle_id,x_min_m,x_max_m,y_min_m,y_max_m,z_min_m,z_max_m,source_basis,digitization_uncertainty_m`
- `external_plume.dataset_metadata`
  target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata.json`
  template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata_template.json`
  json_keys: `benchmark_id,case_alignment,digitization,digitized_dataset_sha256,original_dataset_sha256,schema_version,source`
- `external_plume.digitization_uncertainty_record`
  target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/digitization_uncertainty_record.csv`
  template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/digitization_uncertainty_record_template.csv`
  csv_header: `artifact,source_basis,method,axis_or_geometry_calibration,estimated_uncertainty,review_status`
- `external_plume.experimental_timeseries`
  target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries.csv`
  template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries_template.csv`
  csv_header: `time_s,Gas01_vol_percent,Gas02_vol_percent,Gas03_vol_percent,Gas04_vol_percent,Gas05_vol_percent,Gas06_vol_percent,Gas07_vol_percent,Gas08_vol_percent,Gas09_vol_percent,Gas10_vol_percent,Gas11_vol_percent,Gas12_vol_percent`
- `external_plume.sensor_coordinates`
  target: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates.csv`
  template: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates_template.csv`
  csv_header: `sensor_id,x_m,y_m,z_m,reliability,source_basis,digitization_uncertainty_m`

## fire_calibration

- `fire_calibration.calibration_metadata`
  target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata.json`
  template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata_template.json`
  json_keys: `case,case_alignment,dataset_type,schema_version,source,source_type,uncertainty`
- `fire_calibration.fire_calibration_digitization_uncertainty`
  target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_digitization_uncertainty.csv`
  template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_digitization_uncertainty_template.csv`
  csv_header: `artifact,source_basis,method,calibration_points_or_table,estimated_uncertainty,review_status`
- `fire_calibration.fire_calibration_source_registry`
  target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_source_registry.csv`
  template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_source_registry_template.csv`
  csv_header: `family,candidate_id,title,url_or_doi,selected_for_calibration,required_digitization`
- `fire_calibration.overpressure_metrics`
  target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics.csv`
  template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics_template.csv`
  csv_header: `metric_id,distance_m,reference_overpressure_kpa,tolerance_abs_kpa,tolerance_rel,source_basis`
- `fire_calibration.radiation_metrics`
  target: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics.csv`
  template: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics_template.csv`
  csv_header: `metric_id,distance_m,reference_flux_w_m2,tolerance_abs_w_m2,tolerance_rel,source_basis`

## real_cad

- `real_cad.real_cad_boundary_tags`
  target: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_boundary_tags.csv`
  template: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_boundary_tags_template.csv`
  csv_header: `label,patch_id,bc_type,face_selector,normal_hint,area_m2,source_basis,engineering_role,reviewer`
- `real_cad.real_cad_cleanup_manifest`
  target: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest.json`
  template: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest_template.json`
  json_keys: `cad_source_is_real,campaign,dataset_type,geometries,large_layout_campaign,provenance,schema_version,source_type,status,synthetic`
- `real_cad.real_cad_cleanup_quality_record`
  target: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record.csv`
  template: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record_template.csv`
  csv_header: `label,units_declared,watertight_or_closed_surface,nondegenerate_elements,positive_volume_or_area,bbox_min_m,bbox_max_m,tool_or_method,reviewer`
- `real_cad.real_cad_data_room_index`
  target: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index.csv`
  template: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index_template.csv`
  csv_header: `file_role,label,relative_path,sha256,source_type,revision,owner_or_supplier,notes`
