# Engineering H2 Real-CAD Cleanup Package Gate

## Purpose

The production scorecard still blocks engineering readiness on
`geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`.
The maintained campaign already supports a real-CAD cleanup manifest, but the
workflow did not yet provide a durable package, template, or production evidence
gate for receiving actual owner/operator, vendor, plant, or as-built geometry.

## Change

Added `tools/write_engineering_h2_real_cad_cleanup_package_report.py`.

The report creates and verifies:

- `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/README.md`
- `docs/codex_audit/evidence/engineering_h2_real_cad_cleanup_package_20260723/package/real_cad_cleanup_manifest_template.json`
- source CAD and cleaned geometry staging directories
- `real_cad_cleanup_package_report.json`
- `real_cad_cleanup_package_report.md`

The package remains `NOT_READY-H2-REAL-CAD-CLEANUP-PACKAGE` until a real
`real_cad_cleanup_manifest.json` is supplied with non-synthetic provenance,
supported source type, exact SHA-256 hashes, cleanup checks, and at least three
geometries for a large-layout campaign.

## Verification

The production evidence verifier now requires the real-CAD cleanup package
report and verifies it every run. The production evidence verification report
also records the real-CAD package status, manifest presence, geometry count, and
whether it clears the real-CAD blocker.

## Limitation

This change does not fabricate CAD evidence and does not clear the real-CAD
production blocker. It turns the blocker into an explicit, reproducible data
ingestion and validation path.
