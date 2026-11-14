# Engineering H2 External Artifact Drop Validator

Status: `NOT_READY-H2-EXTERNAL-ARTIFACT-DROP`
Drop root: `docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop`
Content QA: `strict-v5-placeholder-free`
Allow test fixture data: `False`
Expected artifacts: `14`
Valid artifacts: `0`
Missing or invalid artifacts: `14`
Domain quality gaps: `0`
Ready for controlled ingestion: `False`

## Domain Records

### real_cad_cleanup
- Artifacts: `0/6`
- Domain quality gaps: `0`
- Ready: `False`
- `real_cad_cleanup_manifest.json`: valid=`False` gaps=`json_missing_key:docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/real_cad_cleanup/real_cad_cleanup_manifest.json:geometries`
- `source_cad/*`: valid=`False` gaps=`source_cad_file_count:1<3;source_cad_synthetic_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/real_cad_cleanup/source_cad/only_one.stp`
- `cleaned_geometry/*`: valid=`False` gaps=`cleaned_geometry_file_count:0<3`
- `cleanup_quality_records`: valid=`False` gaps=`missing_csv:docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/real_cad_cleanup/real_cad_cleanup_quality_record.csv`
- `real_cad_data_room_index.csv`: valid=`False` gaps=`missing_csv:docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/real_cad_cleanup/real_cad_data_room_index.csv`
- `real_cad_cleanup_quality_record.csv`: valid=`False` gaps=`missing_csv:docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/real_cad_cleanup/real_cad_cleanup_quality_record.csv`

### external_plume_shape_reference
- Artifacts: `0/4`
- Domain quality gaps: `0`
- Ready: `False`
- `dataset_metadata.json`: valid=`False` gaps=`missing_json:docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/external_plume_shape_reference/dataset_metadata.json`
- `sensor_coordinates.csv`: valid=`False` gaps=`missing_csv:docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/external_plume_shape_reference/sensor_coordinates.csv`
- `baffle_geometry.csv`: valid=`False` gaps=`missing_csv:docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/external_plume_shape_reference/baffle_geometry.csv`
- `experimental_timeseries.csv`: valid=`False` gaps=`missing_csv:docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/external_plume_shape_reference/experimental_timeseries.csv`

### fire_consequence_calibration
- Artifacts: `0/4`
- Domain quality gaps: `0`
- Ready: `False`
- `calibration_metadata.json`: valid=`False` gaps=`missing_json:docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/fire_consequence_calibration/calibration_metadata.json`
- `radiation_metrics.csv`: valid=`False` gaps=`missing_csv:docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/fire_consequence_calibration/radiation_metrics.csv`
- `overpressure_metrics.csv`: valid=`False` gaps=`missing_csv:docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/fire_consequence_calibration/overpressure_metrics.csv`
- `calibrated_fire_consequence_report`: valid=`False` gaps=`missing_json:docs/codex_audit/evidence/engineering_h2_external_artifact_gate_negative_selftest_20260724/negative_fixture/drop/fire_consequence_calibration/calibrated_fire_consequence_report.json`

## Quality Gates

- `closure_manifest_attached`: `PASS`
- `drop_scaffold_exists`: `PASS`
- `artifact_count_matches_closure_manifest`: `PASS`
- `not_ready_state_preserves_missing_external_data`: `PASS`
- `does_not_clear_production_blockers`: `PASS`
- `strict_content_quality_checks_enabled`: `PASS`

## Limitations

- This validator checks an external artifact drop before ingestion; it does not copy files into the controlled evidence tree.
- A PASS drop still requires domain ingestion reports, scorecard, blocker preflight, rebuild manifest, and final verifier to pass before production readiness can change.
