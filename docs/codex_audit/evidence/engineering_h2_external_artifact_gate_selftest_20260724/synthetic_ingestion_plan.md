# Engineering H2 External Artifact Ingestion Plan

Status: `PASS-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN`
Total copy actions: `14`
Ready copy actions: `14`
Missing or invalid copy actions: `0`
Ready for controlled copy: `True`

## Domain Plans

### real_cad_cleanup
- Copy actions: `6/6`
- Ready: `True`
- `real_cad_cleanup_manifest.json`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/real_cad_cleanup/real_cad_cleanup_manifest.json` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/real_cad_cleanup/real_cad_cleanup_manifest.json` valid=`True`
- `source_cad/*`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/real_cad_cleanup/source_cad` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/real_cad_cleanup/source_cad/` valid=`True`
- `cleaned_geometry/*`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/real_cad_cleanup/cleaned_geometry` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/real_cad_cleanup/cleaned_geometry/` valid=`True`
- `cleanup_quality_records`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/real_cad_cleanup/real_cad_cleanup_quality_record.csv` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/real_cad_cleanup/real_cad_cleanup_quality_record.csv` valid=`True`
- `real_cad_data_room_index.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/real_cad_cleanup/real_cad_data_room_index.csv` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/real_cad_cleanup/real_cad_data_room_index.csv` valid=`True`
- `real_cad_cleanup_quality_record.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/real_cad_cleanup/real_cad_cleanup_quality_record.csv` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/real_cad_cleanup/real_cad_cleanup_quality_record.csv` valid=`True`

### external_plume_shape_reference
- Copy actions: `4/4`
- Ready: `True`
- `dataset_metadata.json`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/external_plume_shape_reference/dataset_metadata.json` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/external_plume_shape_reference/dataset_metadata.json` valid=`True`
- `sensor_coordinates.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/external_plume_shape_reference/sensor_coordinates.csv` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/external_plume_shape_reference/sensor_coordinates.csv` valid=`True`
- `baffle_geometry.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/external_plume_shape_reference/baffle_geometry.csv` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/external_plume_shape_reference/baffle_geometry.csv` valid=`True`
- `experimental_timeseries.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/external_plume_shape_reference/experimental_timeseries.csv` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/external_plume_shape_reference/experimental_timeseries.csv` valid=`True`

### fire_consequence_calibration
- Copy actions: `4/4`
- Ready: `True`
- `calibration_metadata.json`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/fire_consequence_calibration/calibration_metadata.json` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/fire_consequence_calibration/calibration_metadata.json` valid=`True`
- `radiation_metrics.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/fire_consequence_calibration/radiation_metrics.csv` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/fire_consequence_calibration/radiation_metrics.csv` valid=`True`
- `overpressure_metrics.csv`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/fire_consequence_calibration/overpressure_metrics.csv` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/fire_consequence_calibration/overpressure_metrics.csv` valid=`True`
- `calibrated_fire_consequence_report`: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/drop/fire_consequence_calibration/calibrated_fire_consequence_report.json` -> `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_selftest_20260724/synthetic_fixture/controlled_targets/fire_consequence_calibration/fire_consequence_metrics_report.json` valid=`True`

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
