# Engineering H2 Real-CAD Quality Gate Tightening

## Purpose

The engineering production scorecard still blocks production readiness on
`geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`.
The existing real-CAD package gate created a durable intake folder and manifest
template, but the report did not yet expose the production review checklist as
machine-verifiable evidence.

## Change

Updated the real-CAD package path so the package now writes and verifies:

- `real_cad_intake_checklist.csv`
- a `quality_gate_matrix` in `real_cad_cleanup_package_report.json`
- Markdown rows for each real-CAD production gate

The campaign manifest validator now also requires complete CAD provenance:

- `title`
- `owner_or_supplier`
- `drawing_or_package_id`
- `revision`
- `received_at_utc` in `YYYY-MM-DDTHH:MM:SSZ` form
- `confidentiality`

## Production Meaning

This still does not clear the real-CAD blocker. It prevents incomplete CAD
packages from being accepted as production evidence and turns the blocker into a
reviewable intake contract: provenance, source classification, source-file
hashes, cleaned-geometry hashes, large-layout coverage, nondegenerate meter
bounding boxes, and final scorecard clearance must all pass.

## Verification

The updated report remains `NOT_READY-H2-REAL-CAD-CLEANUP-PACKAGE` until real
owner/operator, as-built, vendor, or plant CAD and cleaned simulation geometry
are supplied. The full engineering H2 verifier continues to require this report
and fails if the report status, hashes, or quality gate matrix are inconsistent.
