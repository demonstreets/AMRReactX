# Strict Master-Plan Unblock Runbook

This runbook describes what is still required to move from current-scope PASS to
strict completion of the original master plan. It does not change current-scope
readiness; it makes the remaining external-artifact work explicit and reproducible.

## Current Strict Blockers

The strict blocker matrix currently keeps these blockers open:

- `reference_agreement_is_threshold_only_not_external_plume_shape_dataset`
- `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`
- `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`

Authoritative blocker matrix:

```text
docs/codex_audit/evidence/master_plan_strict_blocker_matrix_20260731/master_plan_strict_blocker_matrix_report.json
```

Status checks:

```bash
bash tools/verify_master_plan_strict_blocker_matrix.sh
bash tools/verify_master_plan_strict_external_source_update.sh
bash tools/verify_master_plan_strict_real_cad_update.sh
bash tools/verify_master_plan_strict_fire_calibration_update.sh
```

## Artifact Receipt

Every external artifact package should include an operator receipt before it is
credited. Use the existing template:

```text
docs/codex_audit/evidence/engineering_h2_external_evidence_intake_kit_20260724/templates/operator_receipt_template.json
```

Receipt validation commands:

```bash
python3 tools/write_engineering_h2_external_artifact_operator_receipt_report.py
python3 tools/write_engineering_h2_external_artifact_drop_validator.py
python3 tools/write_engineering_h2_external_artifact_controlled_copy_report.py
```

## Receiving Pack And Drop Contract Preflight

Before copying real external evidence into target paths, print the verified
receiving pack and checklist. These reports are authoritative for what to copy,
where to place it, which template to follow, and which preflight to run.

```text
docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812/strict_external_evidence_receiving_pack_report.md
docs/codex_audit/evidence/strict_external_evidence_receiving_pack_20260812/strict_external_evidence_receiving_pack_report.json
docs/codex_audit/evidence/strict_external_artifact_template_clone_selftest_20260817/strict_external_artifact_template_clone_selftest_report.md
docs/codex_audit/evidence/strict_external_artifact_template_clone_selftest_20260817/strict_external_artifact_template_clone_selftest_report.json
docs/codex_audit/evidence/strict_external_artifact_drop_index_20260812/strict_external_artifact_drop_index_report.md
docs/codex_audit/evidence/strict_external_artifact_drop_checklist_20260812/strict_external_artifact_drop_checklist_report.md
```

Receiving-pack and drop-contract commands:

```bash
python3 tools/codex_print_strict_external_artifact_drop_index.py
python3 tools/codex_print_strict_external_artifact_drop_index.py --json
python3 tools/write_strict_external_evidence_receiving_pack_report.py
bash tools/verify_strict_external_evidence_receiving_pack.sh
python3 tools/write_strict_external_artifact_template_clone_selftest_report.py
bash tools/verify_strict_external_artifact_template_clone_selftest.sh
bash tools/verify_strict_artifact_drop_contract_preflight.sh
```

The receiving pack is a handoff and QA artifact only. It does not credit any
external files, does not close any strict blocker, and does not allow strict
master-plan completion while real external files are still missing.
The template-clone selftest must keep every byte-for-byte template copy rejected,
so copied templates or placeholder files cannot be credited as real external
evidence.

## External Plume Dataset Blocker

Blocker:

```text
reference_agreement_is_threshold_only_not_external_plume_shape_dataset
```

Required input package:

```text
docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/README.md
docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/dataset_metadata_template.json
docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/sensors_template.csv
docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/baffle_geometry_template.csv
docs/codex_audit/evidence/engineering_h2_sbepv5_d27_case_package_20260723/package/experimental_timeseries_template.csv
```

Dataset ingestion templates:

```text
docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/dataset_metadata_template.json
docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/sensor_coordinates_template.csv
docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/baffle_geometry_template.csv
docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/experimental_timeseries_template.csv
docs/codex_audit/evidence/engineering_h2_sbepv5_d27_dataset_ingestion_20260723/dataset/digitization_uncertainty_record_template.csv
```

Primary commands after data are provided:

```bash
python3 tools/write_dataverse_open_channel_amr_source_projection_contract_report.py
bash tools/verify_dataverse_open_channel_amr_source_projection_contract.sh
python3 tools/write_engineering_h2_sbepv5_dataset_ingestion_report.py
python3 tools/write_engineering_h2_sbepv5_external_dataset_report.py
python3 tools/write_engineering_h2_sbepv5_literature_metric_preflight_report.py
bash tools/verify_master_plan_strict_external_source_update.sh
```

Current DataverseNO AMR source projection precondition:

```text
docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_contract_20260811/dataverse_open_channel_amr_source_projection_contract_report.json
```

Clearance condition:

The strict external-source update must report that the external plume blocker is
cleared, and the downstream strict blocker matrix must no longer list
`reference_agreement_is_threshold_only_not_external_plume_shape_dataset`.

## Real CAD Cleanup Blocker

Blocker:

```text
geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup
```

Required input package:

```text
docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/source_cad/README.md
docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest_template.json
docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record_template.csv
docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_boundary_tags_template.csv
docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_data_room_index_template.csv
```

The real CAD package must include source CAD provenance, hashes, cleaned geometry,
quality records, and boundary tags for inlet, outlet, walls, leak sources, obstacles,
and monitoring regions.

Primary commands after CAD artifacts are provided:

```bash
python3 tools/write_engineering_h2_real_cad_cleanup_package_report.py
python3 tools/write_engineering_h2_real_cad_boundary_tag_contract_report.py
bash tools/verify_master_plan_strict_real_cad_update.sh
```

Clearance condition:

The strict real-CAD update must report that the real CAD blocker is cleared, source
CAD file count is nonzero, the cleanup package clears the blocker, and the boundary
contract is ready for credit. The downstream strict blocker matrix must no longer
list `geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`.

## Fire Calibration Blocker

Blocker:

```text
fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure
```

Required input package:

```text
docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/README.md
docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata_template.json
docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics_template.csv
docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics_template.csv
docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_source_registry_template.csv
docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_digitization_uncertainty_template.csv
docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_intake_checklist.csv
```

Alternative digitization preflight templates:

```text
docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/templates/calibration_metadata_template.json
docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/templates/radiation_metrics_template.csv
docs/codex_audit/evidence/engineering_h2_fire_calibration_digitization_preflight_20260724/templates/overpressure_metrics_template.csv
```

Primary commands after fire calibration artifacts are provided:

```bash
python3 tools/write_engineering_h2_fire_calibration_dataset_ingestion_report.py
python3 tools/write_engineering_h2_fire_calibration_dataset_report.py
python3 tools/write_engineering_h2_fire_calibration_package_report.py
bash tools/verify_master_plan_strict_fire_calibration_update.sh
```

Clearance condition:

The strict fire-calibration update must report that radiation and overpressure
calibration packages are ready, and the downstream strict blocker matrix must no
longer list `fire_consequence_evidence_is_screening_not_calibrated_radiation_overpressure`.

## Full Strict Recheck

After any external artifact package is ingested, rerun:

```bash
bash tools/verify_master_plan_strict_external_source_update.sh
bash tools/verify_master_plan_strict_real_cad_update.sh
bash tools/verify_master_plan_strict_fire_calibration_update.sh
bash tools/verify_master_plan_strict_artifact_intake_manifest.sh
bash tools/verify_master_plan_strict_artifact_drop_preflight.sh
bash tools/verify_strict_artifact_drop_contract_preflight.sh
python3 tools/write_strict_external_evidence_receiving_pack_report.py
bash tools/verify_strict_external_evidence_receiving_pack.sh
python3 tools/write_strict_external_artifact_template_clone_selftest_report.py
bash tools/verify_strict_external_artifact_template_clone_selftest.sh
bash tools/verify_master_plan_strict_blocker_matrix.sh
bash tools/codex_verify_current_scope.sh
bash tools/run_current_scope_release_refresh.sh
```

Strict completion can only be claimed when the strict blocker matrix reports zero
open strict blockers and the final readiness report no longer records strict
master-plan completion as deferred.
