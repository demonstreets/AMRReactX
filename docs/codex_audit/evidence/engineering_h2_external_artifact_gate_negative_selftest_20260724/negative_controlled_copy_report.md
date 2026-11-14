# Engineering H2 External Artifact Controlled Copy Report

Status: `NOT_READY-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY`
Apply requested: `False`
Copied files: `0`
Ready copy actions: `0/14`
Missing or invalid copy actions: `14`
Source filesystem gate: `strict-v1-regular-nonempty-files`
Source integrity gaps: `0`
Preexisting target conflicts: `0`

## Copy Actions

- `real_cad_cleanup/real_cad_cleanup_manifest.json`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/real_cad_cleanup/real_cad_cleanup_manifest.json` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest.json` valid=`False` files=`1` source_gaps=`0` copied=`0`
- `real_cad_cleanup/source_cad/*`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/real_cad_cleanup/source_cad` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/source_cad/` valid=`False` files=`1` source_gaps=`0` copied=`0`
- `real_cad_cleanup/cleaned_geometry/*`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/real_cad_cleanup/cleaned_geometry` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/cleaned_geometry/` valid=`False` files=`0` source_gaps=`0` copied=`0`
- `real_cad_cleanup/cleanup_quality_records`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/real_cad_cleanup/real_cad_cleanup_quality_record.csv` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record.csv` valid=`False` files=`0` source_gaps=`0` copied=`0`
- `real_cad_cleanup/real_cad_data_room_index.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/real_cad_cleanup/real_cad_data_room_index.csv` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index.csv` valid=`False` files=`0` source_gaps=`0` copied=`0`
- `real_cad_cleanup/real_cad_cleanup_quality_record.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/real_cad_cleanup/real_cad_cleanup_quality_record.csv` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record.csv` valid=`False` files=`0` source_gaps=`0` copied=`0`
- `external_plume_shape_reference/dataset_metadata.json`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/external_plume_shape_reference/dataset_metadata.json` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata.json` valid=`False` files=`0` source_gaps=`0` copied=`0`
- `external_plume_shape_reference/sensor_coordinates.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/external_plume_shape_reference/sensor_coordinates.csv` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates.csv` valid=`False` files=`0` source_gaps=`0` copied=`0`
- `external_plume_shape_reference/baffle_geometry.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/external_plume_shape_reference/baffle_geometry.csv` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry.csv` valid=`False` files=`0` source_gaps=`0` copied=`0`
- `external_plume_shape_reference/experimental_timeseries.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/external_plume_shape_reference/experimental_timeseries.csv` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries.csv` valid=`False` files=`0` source_gaps=`0` copied=`0`
- `fire_consequence_calibration/calibration_metadata.json`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/fire_consequence_calibration/calibration_metadata.json` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata.json` valid=`False` files=`0` source_gaps=`0` copied=`0`
- `fire_consequence_calibration/radiation_metrics.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/fire_consequence_calibration/radiation_metrics.csv` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics.csv` valid=`False` files=`0` source_gaps=`0` copied=`0`
- `fire_consequence_calibration/overpressure_metrics.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/fire_consequence_calibration/overpressure_metrics.csv` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics.csv` valid=`False` files=`0` source_gaps=`0` copied=`0`
- `fire_consequence_calibration/calibrated_fire_consequence_report`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/fire_consequence_calibration/calibrated_fire_consequence_report.json` -> `docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.json` valid=`False` files=`0` source_gaps=`0` copied=`0`

## Limitations

- Default execution is an auditable dry run and copies no files.
- Applying external evidence requires --apply and the explicit confirmation token.
- This report does not clear production blockers; blocker clearance requires the full rebuild and verifier chain.
