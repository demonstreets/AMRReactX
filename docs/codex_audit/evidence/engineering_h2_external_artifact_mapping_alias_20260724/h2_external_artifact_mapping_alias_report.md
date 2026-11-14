# Engineering H2 External Artifact Mapping Alias Report

Status: `PASS-H2-EXTERNAL-ARTIFACT-MAPPING-ALIAS`

## Summary

- `domain_count`: `3`
- `artifact_row_count`: `14`
- `alias_group_count`: `1`
- `observed_allowed_alias_group_count`: `1`
- `duplicate_target_group_count`: `1`
- `duplicate_drop_group_count`: `1`
- `unexpected_duplicate_target_group_count`: `0`
- `unexpected_duplicate_drop_group_count`: `0`
- `worksheet_target_mismatch_count`: `0`
- `worksheet_drop_mismatch_count`: `0`

## Allowed Alias Groups

- `real_cad_cleanup_quality_record_legacy_alias`: `real_cad_cleanup` `cleanup_quality_records, real_cad_cleanup_quality_record.csv` -> `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record.csv`

## Duplicate Target Groups

- `real_cad_cleanup` `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_quality_record.csv` artifacts=`cleanup_quality_records, real_cad_cleanup_quality_record.csv`

## Duplicate Drop Groups

- `real_cad_cleanup` `docs/codex_audit/evidence/engineering_h2_external_artifact_drop_20260724/drop/real_cad_cleanup/real_cad_cleanup_quality_record.csv` artifacts=`cleanup_quality_records, real_cad_cleanup_quality_record.csv`

## Quality Gates

- `all_artifact_rows_are_cross_referenced`: `PASS`
- `duplicate_target_paths_are_declared_aliases`: `PASS`
- `duplicate_drop_paths_are_declared_aliases`: `PASS`
- `alias_audit_does_not_clear_blockers`: `PASS`

## Limitations

- This report audits external artifact target/drop path aliasing only.
- It does not supply external CAD, plume-reference, or calibrated fire data and cannot clear production blockers.
