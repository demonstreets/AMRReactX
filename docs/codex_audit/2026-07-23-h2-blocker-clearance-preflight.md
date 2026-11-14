# Engineering H2 Blocker Clearance Preflight

## Purpose

The engineering H2 production scorecard now has three explicit production
blockers with their own detailed quality gates:

- external plume shape reference agreement
- real-CAD cleanup evidence
- calibrated fire radiation/overpressure consequence evidence

Before this change, the full verifier checked those reports independently, but
there was no single machine-verifiable report showing whether every scorecard
blocker was covered by a domain gate, which gate still failed, and what evidence
would be required before production readiness can be claimed.

## Change

Added `tools/write_engineering_h2_blocker_clearance_preflight_report.py`.

The report reads:

- `engineering_production_scorecard.json`
- `real_cad_cleanup_package_report.json`
- `fire_calibration_package_report.json`
- `external_plume_benchmark_readiness_report.json`

It writes:

- `h2_blocker_clearance_preflight_report.json`
- `h2_blocker_clearance_preflight_report.md`

The report is also required by `tools/verify_engineering_h2_production_evidence.sh`
and is included in the schema 12 production evidence verification report.

## Production Meaning

This report does not clear any blocker by itself. It is a coordination gate. A
blocker is considered cleared only when the corresponding domain report reaches
its PASS status and the production scorecard no longer lists that blocker.

For the current state, the report remains
`NOT_READY-H2-BLOCKER-CLEARANCE-PREFLIGHT` and preserves the same three
scorecard blockers.

## Verification

The full engineering H2 verifier fails if the preflight report is missing, if
any evidence hash is stale, if a scorecard blocker is uncovered by a domain
gate, or if a NOT_READY preflight report incorrectly claims production
clearance.
