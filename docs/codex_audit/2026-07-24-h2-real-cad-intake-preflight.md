# Engineering H2 Real-CAD Intake Preflight

## Purpose

The engineering H2 scorecard still blocks production readiness on
`geometry_evidence_is_synthetic_tank_farm_stl_not_real_cad_cleanup`.
The cleanup package gate already prevents synthetic geometry from receiving
production credit. This change adds a separate intake preflight so the remaining
data-room requirements are explicit, reproducible, and machine checked.

## Change

Added `tools/write_engineering_h2_real_cad_intake_preflight_report.py`.

The report creates and verifies:

- `real_cad_data_room_index_template.csv`
- `real_cad_cleanup_quality_record_template.csv`
- `real_cad_intake_preflight_report.json`
- `real_cad_intake_preflight_report.md`

It records whether the package scaffold exists, whether source CAD and cleaned
geometry files are local, whether the controlled manifest validates, whether the
large-layout requirement is met, and whether the cleanup package can clear the
real-CAD blocker.

## Verification

The engineering H2 production verifier now requires the real-CAD intake
preflight report and verifies it every run. The production evidence verification
report records the intake status, template availability, local source/cleaned
geometry counts, manifest validity, large-layout validity, and missing artifact
count.

## Limitation

This change does not fabricate CAD evidence and does not clear the real-CAD
production blocker. It narrows the blocker to controlled source CAD, cleaned
simulation geometry, exact hashes, provenance, cleanup quality records, and
large-layout coverage.
