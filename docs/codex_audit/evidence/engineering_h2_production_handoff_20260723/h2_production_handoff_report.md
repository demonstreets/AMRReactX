# Engineering H2 Production Handoff Index

Status: `NOT_READY-H2-PRODUCTION-HANDOFF`
Handoff decision: `continue_engineering_hardening_and_external_data_ingestion`

## Current Status

- `production_evidence_status`: `PASS`
- `production_evidence_schema_version`: `62`
- `functional_coverage_percent`: `96.9`
- `production_credibility_percent`: `82.2`
- `ctest_tests`: `22`
- `ctest_passed`: `True`
- `scorecard_status`: `NOT_PRODUCTION_READY`
- `remaining_blocker_count`: `3`
- `cleared_blocker_count`: `0`
- `ready_for_production_scorecard_clearance`: `False`

## Next Data Requirements

- `external_plume_shape_reference`: failed gates `case_package_runnable; dataset_metadata_available; exact_sensor_coordinates_available; exact_baffle_geometry_available; digitized_experimental_timeseries_available; external_dataset_json_written; reference_agreement_uses_external_shape_dataset`; gaps `case_matched_external_plume_dataset_not_ingested; external_plume_quality_gates_not_all_passed`
  - required artifact: case-matched PeleLMeX input and geometry generated from the selected benchmark specification
  - required artifact: exact SBEPV5 D27 baffle placement/wall attachment and sensor coordinates replacing the program-scout approximations
  - required artifact: exact sensor and baffle coordinates digitized from source figures or original tabular data
  - required artifact: program sensor probes compared against SBEPV5 Gas09/Gas10 literature arrival-time anchors
  - required artifact: digitized or tabulated experimental dataset with source metadata and uncertainty/tolerances
  - required artifact: official h2_reference_agreement_report regenerated with --external-plume-dataset-json
- `real_cad_cleanup`: failed gates `manifest_present; provenance_complete; real_cad_source_classified; source_cad_hashes_verified; cleaned_geometry_hashes_verified; large_layout_coverage; bbox_non_degenerate_m; scorecard_blocker_clearance`; gaps `real_cad_cleanup_manifest_missing; source_cad_files_missing; cleaned_geometry_files_missing; large_layout_requires_at_least_three_real_geometries`
  - required artifact: real_cad_cleanup_manifest.json in the cleanup package root
  - required artifact: source CAD/STL files for at least three representative large-layout geometries
  - required artifact: complete source provenance, units, coordinate frame, and engineering simplification notes
  - required artifact: sha256 hashes for every source CAD file and cleaned geometry file
  - required artifact: cleaned watertight STL/geometry files with non-degenerate meter-scale bounding boxes
  - required artifact: boundary tag map covering leak source, walls, vents/openings, outlets, and far-field regions
  - required artifact: regenerated real CAD cleanup and boundary-tag contract reports showing scorecard blocker clearance
- `calibrated_fire_radiation_overpressure`: failed gates `ingestion_report_passed; metadata_available; case_alignment_complete; package_ready_for_dataset_builder`; gaps `fire_calibration_dataset_ingestion_not_passed; fire_calibration_metadata_case_alignment_release_or_cloud_mass_not_true; fire_calibration_metadata_case_alignment_ignition_or_burn_basis_not_true; fire_calibration_metadata_case_alignment_boundary_conditions_not_true`
  - required artifact: calibration_metadata.json with source, scenario, fuel, geometry, wind, and uncertainty metadata
  - required artifact: radiation_metrics.csv containing experimental or authoritative reference heat-flux metrics
  - required artifact: overpressure_metrics.csv containing experimental or authoritative reference pressure metrics
  - required artifact: case-alignment table mapping every metric to program inputs, probes, tolerances, and units
  - required artifact: radiation and overpressure reference families covering the intended fire/consequence claim
  - required artifact: regenerated fire calibration dataset-ingestion and package reports showing production gate clearance

## Verified Entrypoints

- `bash tools/verify_engineering_h2_production_evidence.sh`: Full maintained engineering H2 production evidence gate.
- `python3 tools/write_engineering_h2_blocker_clearance_preflight_report.py --verify-json docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723/h2_blocker_clearance_preflight_report.json`: Verify all production blockers are covered by domain gates.
- `python3 tools/write_engineering_h2_production_evidence_verification_report.py --verify-json docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json`: Verify top-level evidence ledger hashes and summary invariants.

## Evidence Files

- `production_evidence_verification_report`: `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json` sha256 `eebc2a5aa0d10b8c`
- `blocker_clearance_preflight_report`: `docs/codex_audit/evidence/engineering_h2_blocker_clearance_preflight_20260723/h2_blocker_clearance_preflight_report.json` sha256 `320fe14cf656f817`

## Limitations

- This handoff report is an index over verified evidence; it does not launch CFD or clear production blockers.
- Production readiness still requires the scorecard to become PRODUCTION_READY with no blocking gaps.
