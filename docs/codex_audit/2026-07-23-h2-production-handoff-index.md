# Engineering H2 Production Handoff Index

## Purpose

The engineering H2 evidence chain now has a full verifier, a production
scorecard, and a blocker-clearance preflight report. The next maintainability
gap was handoff: a future engineer or operator still had to inspect multiple
JSON files to understand the current state, which commands are authoritative,
and which data drops are required before production readiness can be claimed.

## Change

Added `tools/write_engineering_h2_production_handoff_report.py`.

The report reads:

- `production_evidence_verification_report.json`
- `h2_blocker_clearance_preflight_report.json`

It writes:

- `h2_production_handoff_report.json`
- `h2_production_handoff_report.md`

The report records:

- current functional and production credibility scores
- CTest and full-verifier status
- scorecard blocker count
- cleared and remaining blocker count
- verified entrypoint commands
- next data requirements grouped by blocker domain

## Dependency Shape

The handoff report references the production evidence report, so the full
verifier checks the handoff report after the production evidence report. The
production evidence report does not hash the handoff report, avoiding a circular
hash dependency.

## Production Meaning

This report is a handoff index, not a production claim. It remains
`NOT_READY-H2-PRODUCTION-HANDOFF` until the blocker-clearance preflight is ready
and the scorecard has no production blockers.
