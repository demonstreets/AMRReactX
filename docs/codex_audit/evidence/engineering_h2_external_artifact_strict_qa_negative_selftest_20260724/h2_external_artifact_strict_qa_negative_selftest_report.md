# Engineering H2 External Artifact Strict-QA Negative Self-Test

Status: `PASS-H2-EXTERNAL-ARTIFACT-STRICT-QA-NEGATIVE-SELFTEST`

## Summary

- `drop_status`: `NOT_READY-H2-EXTERNAL-ARTIFACT-DROP`
- `drop_content_quality_gate_level`: `strict-v5-placeholder-free`
- `drop_placeholder_gap_detected`: `True`
- `drop_domain_quality_gap_count`: `4`
- `drop_present_artifact_count`: `14`
- `drop_valid_artifact_count`: `0`
- `drop_total_expected_artifact_count`: `14`
- `drop_missing_or_invalid_artifact_count`: `14`
- `ingestion_status`: `NOT_READY-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN`
- `ingestion_ready_copy_action_count`: `0`
- `controlled_copy_status`: `NOT_READY-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY`
- `controlled_copy_copied_file_count`: `0`
- `controlled_copy_applied_copy_actions`: `False`
- `apply_refused_returncode`: `2`

## Gap Sample

- `real_cad_cleanup:domain_quality_gap:cad_index_manifest_path_mismatch:pipe_b:cleaned_geometry:cleaned_geometry/pipe_b_index_mismatch.stl!=cleaned_geometry/pipe_b.stl`
- `real_cad_cleanup:domain_quality_gap:cad_unreferenced_file:cleaned_geometry/pipe_b_index_mismatch.stl`
- `real_cad_cleanup_manifest.json:synthetic_or_selftest_marker_present_without_allow_synthetic_selftest`
- `real_cad_cleanup_manifest.json:placeholder_or_template_marker_present_without_replacement`
- `source_cad/*:source_cad_synthetic_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/source_cad/dike_c.stp`
- `source_cad/*:source_cad_placeholder_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/source_cad/dike_c.stp`
- `source_cad/*:source_cad_synthetic_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/source_cad/pipe_b.stp`
- `source_cad/*:source_cad_placeholder_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/source_cad/pipe_b.stp`
- `source_cad/*:source_cad_synthetic_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/source_cad/tank_a.stp`
- `source_cad/*:source_cad_placeholder_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/source_cad/tank_a.stp`
- `cleaned_geometry/*:cleaned_geometry_synthetic_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/cleaned_geometry/dike_c.stl`
- `cleaned_geometry/*:cleaned_geometry_placeholder_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/cleaned_geometry/dike_c.stl`
- `cleaned_geometry/*:cleaned_geometry_synthetic_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/cleaned_geometry/pipe_b.stl`
- `cleaned_geometry/*:cleaned_geometry_placeholder_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/cleaned_geometry/pipe_b.stl`
- `cleaned_geometry/*:cleaned_geometry_synthetic_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/cleaned_geometry/pipe_b_index_mismatch.stl`
- `cleaned_geometry/*:cleaned_geometry_placeholder_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/cleaned_geometry/pipe_b_index_mismatch.stl`
- `cleaned_geometry/*:cleaned_geometry_synthetic_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/cleaned_geometry/tank_a.stl`
- `cleaned_geometry/*:cleaned_geometry_placeholder_marker:docs/codex_audit/evidence/engineering_h2_external_artifact_strict_qa_negative_selftest_20260724/strict_qa_negative_fixture/drop/real_cad_cleanup/cleaned_geometry/tank_a.stl`
- `cleanup_quality_records:cleanup_quality_units_not_m:tank_a`
- `cleanup_quality_records:cleanup_quality_boolean_not_true:tank_a:watertight_or_closed_surface`
- `cleanup_quality_records:cleanup_quality_boolean_not_true:tank_a:positive_volume_or_area`
- `cleanup_quality_records:cleanup_quality_bbox_not_positive:tank_a`
- `cleanup_quality_records:cleanup_quality_units_not_m:pipe_b`
- `cleanup_quality_records:cleanup_quality_boolean_not_true:pipe_b:watertight_or_closed_surface`
- `cleanup_quality_records:cleanup_quality_boolean_not_true:pipe_b:positive_volume_or_area`
- `cleanup_quality_records:cleanup_quality_bbox_not_positive:pipe_b`
- `cleanup_quality_records:cleanup_quality_units_not_m:dike_c`
- `cleanup_quality_records:cleanup_quality_boolean_not_true:dike_c:watertight_or_closed_surface`
- `cleanup_quality_records:cleanup_quality_boolean_not_true:dike_c:positive_volume_or_area`
- `cleanup_quality_records:cleanup_quality_bbox_not_positive:dike_c`

## Quality Gates

- `all_expected_artifacts_are_present_in_fixture`: `PASS`
- `strict_content_qa_rejects_bad_complete_drop`: `PASS`
- `strict_placeholder_qa_rejects_template_values`: `PASS`
- `ingestion_plan_stays_not_ready`: `PASS`
- `controlled_copy_stays_no_write`: `PASS`
- `apply_refused_for_invalid_complete_drop`: `PASS`
- `does_not_clear_production_blockers`: `PASS`

## Limitations

- This negative self-test uses a deliberately invalid complete fixture.
- It proves that all expected files being present is insufficient to pass strict-v5 placeholder-free content QA.
- It must not be used to clear real-CAD, SBEPV5, or fire-calibration blockers.
