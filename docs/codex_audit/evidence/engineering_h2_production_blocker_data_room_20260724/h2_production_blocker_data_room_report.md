# Engineering H2 Production Blocker Data Room

Status: `PASS-H2-PRODUCTION-BLOCKER-DATA-ROOM`
Ready for production scorecard clearance: `False`
Remaining blockers: `3`
Total missing artifacts: `14`

## Domains

### real_cad_cleanup
- Blocker: `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`
- Preflight status: `PASS-H2-REAL-CAD-INTAKE-PREFLIGHT`
- Ready for blocker clearance: `False`
- Missing artifact count: `6`
  - `real_cad_cleanup_manifest.json`: fill the package manifest from the template with controlled provenance and exact file hashes
  - `source_cad/*`: stage at least three real source CAD files for a tank/pipe large-layout campaign
  - `cleaned_geometry/*`: stage at least three cleaned simulation geometries derived from the source CAD files
  - `cleanup_quality_records`: record units, watertightness, degeneracy, positive volume/area, and meter-space bounding boxes per geometry
  - `real_cad_data_room_index.csv`: provide a controlled data-room index with source/cleaned file roles, labels, relative paths, hashes, source type, revision, and owner/supplier
  - `real_cad_cleanup_quality_record.csv`: provide cleanup quality records for at least three geometries with true cleanup checks, bbox fields, tool/method, and reviewer

### external_plume_shape_reference
- Blocker: `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`
- Preflight status: `PASS-SBEPV5-D27-DIGITIZATION-PREFLIGHT`
- Ready for blocker clearance: `False`
- Missing artifact count: `4`
  - `dataset_metadata.json`: replace the metadata template with URL/DOI, source file hash, digitization method, uncertainty basis, and case-alignment booleans
  - `sensor_coordinates.csv`: digitize or obtain Gas01..Gas12 coordinates with reliability tags and <=0.02 m uncertainty
  - `baffle_geometry.csv`: digitize or obtain baffles 1..4 bounds with source basis and <=0.02 m uncertainty
  - `experimental_timeseries.csv`: obtain original Excel or digitize Gas01..Gas12 concentration histories through at least 120 s

### fire_consequence_calibration
- Blocker: `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`
- Preflight status: `PASS-H2-FIRE-CALIBRATION-DIGITIZATION-PREFLIGHT`
- Ready for blocker clearance: `False`
- Missing artifact count: `4`
  - `calibration_metadata.json`: select calibration sources and record source hash, uncertainty, and all case-alignment booleans
  - `radiation_metrics.csv`: digitize or obtain heat-flux measurements with distances, tolerances, and source basis
  - `overpressure_metrics.csv`: digitize or obtain peak overpressure measurements with distances, tolerances, and source basis
  - `calibrated_fire_consequence_report`: rerun the official fire consequence report with the generated calibration dataset JSON


## Quality Gates

| Gate | Status | Gap |
| --- | --- | --- |
| `all_domain_preflights_pass` | `PASS` | none |
| `blocker_preflight_attached` | `PASS` | none |
| `missing_artifacts_retained_until_ready` | `PASS` | none |
| `scorecard_clearance_consistency` | `PASS` | none |

## Evidence Files

- `real_cad_intake_preflight_report`: `docs/codex_audit/evidence/engineering_h2_real_cad_intake_preflight_20260724/real_cad_intake_preflight_report.json` sha256 `33e882ad5cc94663`
- `sbepv5_digitization_preflight_report`: `docs/codex_audit/evidence/engineering_h2_sbepv5_d27_digitization_preflight_20260724/sbepv5_d27_digitization_preflight_report.json` sha256 `dc9d74003eee5c1e`
- `fire_calibration_digitization_preflight_report`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/fire_calibration_digitization_preflight_report.json` sha256 `de64e9cc2e3ffd0e`
- `blocker_clearance_preflight_report`: `docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723/h2_blocker_clearance_preflight_report.json` sha256 `320fe14cf656f817`

## Limitations

- This report is a consolidated production data-room intake ledger; it does not supply missing external evidence.
- Production readiness still requires each domain report to pass its full ingestion/build/agreement path and the blocker preflight to clear.
