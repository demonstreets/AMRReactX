# Engineering H2 Real-CAD Guard Negative Selftest

- Status: `PASS-H2-REAL-CAD-GUARD-NEGATIVE-SELFTEST`
- Positive controls: `3/3`
- Negative cases rejected: `8/8`
- Expected diagnostics seen: `8/8`
- Strict real-CAD blocker cleared: `False`

## Negative Cases

- `manifest_synthetic_true`: rejected `True`, expected diagnostic `True`
- `manifest_missing_provenance_revision`: rejected `True`, expected diagnostic `True`
- `manifest_source_hash_mismatch`: rejected `True`, expected diagnostic `True`
- `manifest_large_layout_too_few_geometries`: rejected `True`, expected diagnostic `True`
- `data_room_index_bad_sha256`: rejected `True`, expected diagnostic `True`
- `cleanup_quality_false_watertight`: rejected `True`, expected diagnostic `True`
- `boundary_tags_placeholder_reviewer`: rejected `True`, expected diagnostic `True`
- `boundary_tags_missing_release_role`: rejected `True`, expected diagnostic `True`

## Limitations

- This is a guard selftest. It does not provide real source CAD or clear the strict real-CAD blocker.
- Positive controls only prove the default reports remain non-claiming until controlled real CAD is supplied.
