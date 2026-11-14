# Engineering H2 External Artifact Ingestion Plan

Status: `NOT_READY-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN`
Total copy actions: `14`
Ready copy actions: `0`
Missing or invalid copy actions: `14`
Ready for controlled copy: `False`

## Domain Plans

### real_cad_cleanup
- Copy actions: `0/6`
- Ready: `False`
- `real_cad_cleanup_manifest.json`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/real_cad_cleanup_manifest.json` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest.json` valid=`False`
- `source_cad/*`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/source_cad` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/source_cad/` valid=`False`
- `cleaned_geometry/*`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/cleaned_geometry` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/cleaned_geometry/` valid=`False`
- `cleanup_quality_records`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/real_cad_cleanup_quality_record.csv` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record.csv` valid=`False`
- `real_cad_data_room_index.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/real_cad_data_room_index.csv` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index.csv` valid=`False`
- `real_cad_cleanup_quality_record.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/real_cad_cleanup_quality_record.csv` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record.csv` valid=`False`

### external_plume_shape_reference
- Copy actions: `0/4`
- Ready: `False`
- `dataset_metadata.json`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/external_plume_shape_reference/dataset_metadata.json` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata.json` valid=`False`
- `sensor_coordinates.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/external_plume_shape_reference/sensor_coordinates.csv` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates.csv` valid=`False`
- `baffle_geometry.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/external_plume_shape_reference/baffle_geometry.csv` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry.csv` valid=`False`
- `experimental_timeseries.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/external_plume_shape_reference/experimental_timeseries.csv` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries.csv` valid=`False`

### fire_consequence_calibration
- Copy actions: `0/4`
- Ready: `False`
- `calibration_metadata.json`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/fire_consequence_calibration/calibration_metadata.json` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata.json` valid=`False`
- `radiation_metrics.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/fire_consequence_calibration/radiation_metrics.csv` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics.csv` valid=`False`
- `overpressure_metrics.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/fire_consequence_calibration/overpressure_metrics.csv` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics.csv` valid=`False`
- `calibrated_fire_consequence_report`: `docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/fire_consequence_calibration/calibrated_fire_consequence_report.json` -> `docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.json` valid=`False`

## Final Rebuild Commands After Copy

- `python3 tools/write_engineering_production_scorecard.py --output-json docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.json --output-md docs/codex_audit/evidence/engineering_production_scorecard_20260720/engineering_production_scorecard.md`
- `python3 tools/write_engineering_h2_blocker_clearance_preflight_report.py`
- `python3 tools/write_engineering_h2_production_blocker_data_room_report.py`
- `python3 tools/write_engineering_h2_production_blocker_closure_manifest_report.py`
- `python3 tools/write_engineering_h2_external_evidence_intake_kit_manifest.py`
- `python3 tools/write_engineering_h2_external_artifact_drop_validator.py`
- `python3 tools/write_engineering_h2_external_artifact_ingestion_plan.py`
- `python3 tools/write_engineering_h2_production_handoff_report.py`
- `python3 tools/write_engineering_h2_master_plan_traceability_report.py`
- `bash tools/rebuild_engineering_h2_evidence_chain.sh`

## Limitations

- This plan records copy targets and rebuild commands only; it does not copy external artifacts.
- Production readiness can only change after a PASS drop is copied into controlled paths and the full rebuild/verifier chain passes.
