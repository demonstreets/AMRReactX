# Engineering H2 Production Blocker Closure Manifest

Status: `PASS-H2-PRODUCTION-BLOCKER-CLOSURE-MANIFEST`
Remaining blockers: `3`
Total missing artifacts: `14`

## Domain Closure Records

### real_cad_cleanup
- Blocker: `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`
- Missing artifact count: `6`
- `real_cad_cleanup_manifest.json` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest.json`
- `source_cad/*` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/source_cad/`
- `cleaned_geometry/*` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/cleaned_geometry/`
- `cleanup_quality_records` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record.csv`
- `real_cad_data_room_index.csv` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index.csv`
- `real_cad_cleanup_quality_record.csv` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record.csv`
- Commands:
  - `python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py`
  - `python3 tools/write_engineering_h2_real_cad_intake_preflight_report.py`
  - `python3 tools/write_engineering_production_scorecard.py`
  - `python3 tools/write_engineering_h2_blocker_clearance_preflight_report.py`

### external_plume_shape_reference
- Blocker: `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`
- Missing artifact count: `4`
- `dataset_metadata.json` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata.json`
- `sensor_coordinates.csv` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates.csv`
- `baffle_geometry.csv` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry.csv`
- `experimental_timeseries.csv` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries.csv`
- Commands:
  - `python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py`
  - `python3 tools/write_engineering_h2_sbepv5_external_dataset_report.py`
  - `python3 tools/write_engineering_h2_reference_agreement_report.py --external-plume-dataset-json <generated_external_plume_dataset_json>`
  - `python3 tools/write_engineering_h2_external_plume_benchmark_readiness.py`
  - `python3 tools/write_engineering_production_scorecard.py`
  - `python3 tools/write_engineering_h2_blocker_clearance_preflight_report.py`

### fire_consequence_calibration
- Blocker: `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`
- Missing artifact count: `4`
- `calibration_metadata.json` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata.json`
- `radiation_metrics.csv` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics.csv`
- `overpressure_metrics.csv` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics.csv`
- `calibrated_fire_consequence_report` -> `docs/codex_audit/evidence/engineering_h2_fire_consequence_metrics_20260720/fire_consequence_metrics_report.json`
- Commands:
  - `python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py`
  - `python3 tools/write_engineering_h2_fire_calibration_package_report.py`
  - `python3 tools/write_engineering_h2_fire_calibration_dataset_report.py`
  - `python3 tools/write_engineering_h2_fire_consequence_metrics_report.py --calibration-dataset-json <generated_fire_calibration_dataset_json>`
  - `python3 tools/write_engineering_production_scorecard.py`
  - `python3 tools/write_engineering_h2_blocker_clearance_preflight_report.py`

## Final Rebuild Commands

- `python3 tools/write_engineering_h2_production_blocker_data_room_report.py`
- `python3 tools/write_engineering_h2_production_blocker_closure_manifest_report.py`
- `python3 tools/write_engineering_h2_production_handoff_report.py`
- `python3 tools/write_engineering_h2_master_plan_traceability_report.py`
- `bash tools/verify_engineering_h2_production_evidence.sh`

## Limitations

- This manifest defines closure targets and command order; it does not provide missing external CAD, plume, or fire calibration data.
- A blocker is still open until its domain report, production scorecard, blocker preflight, and final verifier all pass.
