# Engineering H2 Fire Calibration Package

Status: `NOT_READY-H2-FIRE-CALIBRATION-PACKAGE`
Dataset root: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset`
Ingestion status: `NOT_READY-H2-FIRE-CALIBRATION-DATASET-INGESTION`
Package ready for dataset builder: `False`
Clears fire-consequence blocker: `False`

## Current Inputs

- `metadata_available`: `False`
- `radiation_metrics_available`: `True`
- `overpressure_metrics_available`: `True`
- `ingestion_schema_version`: `2`
- `ingestion_content_quality_gate_level`: `strict-v1-placeholder-free-and-non-synthetic`
- `ingestion_selftest_status`: `PASS-H2-FIRE-CALIBRATION-DATASET-INGESTION-SELFTEST`
- `ingestion_selftest_positive_passed_count`: `2`
- `ingestion_selftest_negative_refused_count`: `1`
- `ingestion_selftest_placeholder_negative_refused`: `True`
- `ingestion_selftest_duplicate_metric_negative_refused`: `True`
- `public_source_triage_available`: `True`
- `public_source_missing_artifact_count`: `4`
- `literature_metric_anchor_available`: `True`
- `literature_metric_missing_artifact_count`: `3`

## Required Dataset Files

- `calibration_metadata_json`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata.json`
- `radiation_metrics_csv`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics.csv`
- `overpressure_metrics_csv`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics.csv`

## Blocking Gaps

- `fire_calibration_dataset_ingestion_not_passed`
- `fire_calibration_metadata_case_alignment_release_or_cloud_mass_not_true`
- `fire_calibration_metadata_case_alignment_ignition_or_burn_basis_not_true`
- `fire_calibration_metadata_case_alignment_boundary_conditions_not_true`

## Quality Gate Matrix

| Gate | Status | Gap |
| --- | --- | --- |
| `public_source_triage_ready` | `PASS` | public fire calibration source triage passed |
| `radiation_and_overpressure_candidates_available` | `PASS` | radiation and overpressure public source candidates identified |
| `literature_metric_preflight_ready` | `PASS` | public radiation and overpressure metric anchors are machine-checkable |
| `ingestion_report_passed` | `MISSING` | Fire calibration dataset ingestion must pass before package is builder-ready. |
| `ingestion_strict_gate_selftest_passed` | `PASS` | fire calibration ingestion strict-gate selftest passed |
| `metadata_available` | `MISSING` | Provide calibration_metadata.json with the required schema. |
| `experimental_source_identified` | `PASS` | literature_digitized with public identifier |
| `case_alignment_complete` | `MISSING` | Set all required fuel, release/cloud mass, burn/ignition, measurement, and boundary-condition alignment fields to true with evidence. |
| `radiation_metrics_available` | `PASS` | 4 radiation metric row(s) accepted |
| `overpressure_metrics_available` | `PASS` | 4 overpressure metric row(s) accepted |
| `radiation_and_overpressure_families_present` | `PASS` | radiation=4, overpressure=4 |
| `package_ready_for_dataset_builder` | `MISSING` | The package is not builder-ready until every ingestion and quality gate passes. |
| `package_does_not_claim_final_calibration` | `PASS` | package remains an intake gate; final blocker clearance requires calibrated consequence report |

## Evidence Files

- `fire_calibration_dataset_ingestion_report`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/fire_calibration_dataset_ingestion_report.json` sha256 `ec57ea9833fa93b6`
- `fire_calibration_dataset_ingestion_selftest_report`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_selftest_20260727/fire_calibration_dataset_ingestion_selftest_report.json` sha256 `9d7a4e5f9ee9ac97`
- `fire_calibration_public_source_triage_report`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_public_source_triage_20260724/fire_calibration_public_source_triage_report.json` sha256 `41249a0709ec1540`
- `fire_calibration_literature_metric_preflight_report`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_literature_metric_preflight_20260724/fire_calibration_literature_metric_preflight_report.json` sha256 `5bef644b1ee189ee`
- `README`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/README.md` sha256 `e8d9fea1ad6aa6f6`
- `calibration_metadata_template`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/calibration_metadata_template.json` sha256 `757224382e1c667f`
- `radiation_metrics_template`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/radiation_metrics_template.csv` sha256 `ceaf0cc1f31a6a4c`
- `overpressure_metrics_template`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/overpressure_metrics_template.csv` sha256 `6856b661c785344a`
- `fire_calibration_intake_checklist`: `docs/codex_audit/evidence/engineering_h2_fire_calibration_dataset_ingestion_20260723/dataset/fire_calibration_intake_checklist.csv` sha256 `a869dea963fe0b4e`

## Limitations

- This package prepares external fire/blast calibration data for ingestion and does not clear the fire-consequence blocker by itself.
- The default package is NOT_READY until real metadata, radiation, and overpressure calibration files pass ingestion.
- Production credit requires the official fire consequence report to pass with the generated calibration dataset JSON.
