# Strict Artifact Intake Manifest

- Status: `READY-MASTER-PLAN-STRICT-ARTIFACT-INTAKE-MANIFEST`
- Intake domains: `3`
- Template files verified: `16`
- Open strict blockers: `3`

## external_plume

- Blocker: `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`
- Drop root: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset`
- Required artifacts:
  - dataset_metadata.json
  - sensor_coordinates.csv
  - baffle_geometry.csv
  - experimental_timeseries.csv
  - digitization_uncertainty_record.csv if digitized plots are used
- Post-intake commands:
  - `python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py`
  - `python3 tools/write_engineering_h2_sbepv5_external_dataset_report.py`
  - `python3 tools/write_engineering_h2_external_plume_benchmark_readiness.py`
  - `python3 tools/write_engineering_production_scorecard.py`
  - `python3 tools/write_engineering_h2_master_plan_traceability_report.py`

## real_cad

- Blocker: `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`
- Drop root: `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package`
- Required artifacts:
  - source_cad/* real source CAD files
  - cleaned_geometry/* cleaned STL/STEP geometry files
  - real_cad_cleanup_manifest.json
  - real_cad_data_room_index.csv
  - real_cad_cleanup_quality_record.csv
  - real_cad_boundary_tags.csv
- Post-intake commands:
  - `python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py`
  - `python3 tools/write_engineering_h2_real_cad_intake_preflight_report.py`
  - `python3 tools/write_engineering_h2_real_cad_boundary_tag_contract_report.py`
  - `python3 tools/write_engineering_production_scorecard.py`
  - `python3 tools/write_engineering_h2_master_plan_traceability_report.py`

## fire_calibration

- Blocker: `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`
- Drop root: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset`
- Required artifacts:
  - calibration_metadata.json
  - radiation_metrics.csv
  - overpressure_metrics.csv
  - fire_calibration_source_registry.csv
  - fire_calibration_digitization_uncertainty.csv if digitized plots are used
- Post-intake commands:
  - `python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py`
  - `python3 tools/write_engineering_h2_fire_calibration_package_report.py`
  - `python3 tools/write_engineering_h2_fire_calibration_dataset_report.py`
  - `python3 tools/write_engineering_production_scorecard.py`
  - `python3 tools/write_engineering_h2_master_plan_traceability_report.py`
