# Project Closeout Acceptance Gate

- Status: `PASS-PROJECT-CLOSEOUT-ACCEPTANCE-GATE`
- Current phase acceptance allowed: `True`
- Current scope closeout estimate: `0.5-1 day for final handoff notes and optional fresh smoke reruns`
- Strict final acceptance allowed: `False`
- Strict closeout estimate after artifacts: `3-7 days after real CAD/reference/fire calibration artifacts are available`
- Strict external artifacts done: `5/14`
- Strict external artifacts missing: `9/14`
- Open strict blockers: `3`

## Decision

- Current phase: `ACCEPTABLE_TO_CLOSE`
- Strict master-plan: `AWAITING_EXTERNAL_ARTIFACTS`
- Non-overclaim rule: do not mark the active goal complete while strict_final_acceptance_allowed is false

## Required External Artifacts

- [ ] `external_plume` `external_plume.baffle_geometry` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry.csv`
- [ ] `external_plume` `external_plume.dataset_metadata` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata.json`
- [ ] `external_plume` `external_plume.digitization_uncertainty_record` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/digitization_uncertainty_record.csv`
- [ ] `external_plume` `external_plume.experimental_timeseries` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries.csv`
- [ ] `external_plume` `external_plume.sensor_coordinates` -> `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates.csv`
- [x] `fire_calibration` `fire_calibration.calibration_metadata` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata.json`
- [x] `fire_calibration` `fire_calibration.fire_calibration_digitization_uncertainty` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_digitization_uncertainty.csv`
- [x] `fire_calibration` `fire_calibration.fire_calibration_source_registry` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_source_registry.csv`
- [x] `fire_calibration` `fire_calibration.overpressure_metrics` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics.csv`
- [x] `fire_calibration` `fire_calibration.radiation_metrics` -> `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics.csv`
- [ ] `real_cad` `real_cad.real_cad_boundary_tags` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_boundary_tags.csv`
- [ ] `real_cad` `real_cad.real_cad_cleanup_manifest` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest.json`
- [ ] `real_cad` `real_cad.real_cad_cleanup_quality_record` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record.csv`
- [ ] `real_cad` `real_cad.real_cad_data_room_index` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index.csv`
