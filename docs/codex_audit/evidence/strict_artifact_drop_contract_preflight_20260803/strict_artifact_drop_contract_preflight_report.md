# Strict Artifact Drop Contract Preflight

- Status: `PASS-STRICT-ARTIFACT-DROP-CONTRACT-PREFLIGHT`
- Contract checks: `14`
- Present contract artifacts: `5`
- Invalid present artifacts: `0`
- Awaiting missing artifacts: `9`

## Domains

- `external_plume` present=`0` invalid=`0` root=`docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset`
- `real_cad` present=`0` invalid=`0` root=`docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package`
- `fire_calibration` present=`5` invalid=`0` root=`docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset`

## Checks

- `external_plume.dataset_metadata` `json` awaiting ready=`True`
- `real_cad.real_cad_cleanup_manifest` `json` awaiting ready=`True`
- `fire_calibration.calibration_metadata` `json` present ready=`True`
- `external_plume.sensor_coordinates` `csv` awaiting ready=`True`
- `external_plume.baffle_geometry` `csv` awaiting ready=`True`
- `external_plume.experimental_timeseries` `csv` awaiting ready=`True`
- `external_plume.digitization_uncertainty_record` `csv` awaiting ready=`True`
- `real_cad.real_cad_data_room_index` `csv` awaiting ready=`True`
- `real_cad.real_cad_cleanup_quality_record` `csv` awaiting ready=`True`
- `real_cad.real_cad_boundary_tags` `csv` awaiting ready=`True`
- `fire_calibration.radiation_metrics` `csv` present ready=`True`
- `fire_calibration.overpressure_metrics` `csv` present ready=`True`
- `fire_calibration.fire_calibration_source_registry` `csv` present ready=`True`
- `fire_calibration.fire_calibration_digitization_uncertainty` `csv` present ready=`True`
