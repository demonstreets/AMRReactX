# Engineering H2 Master Plan Traceability Matrix

## Purpose

The project objective is measured against `/home/cj/pele_cfd_master_plan.md`,
but the maintained evidence chain previously reported engineering readiness
without a requirement-by-requirement trace back to the master plan IDs.

## Change

Added `tools/write_engineering_h2_master_plan_traceability_report.py`.

The report parses the master plan requirement tables and verifies that the
expected IDs are present:

- `ENG-01` through `ENG-14`
- `ACD-01` through `ACD-10`
- `QLT-01` through `QLT-05`

It writes:

- `h2_master_plan_traceability_report.json`
- `h2_master_plan_traceability_report.md`

The report maps each master-plan requirement to current maintained evidence and
marks it as `PASS`, `PARTIAL`, `NOT_READY`, or `DEFERRED`. It also records the
current production scores, CTest count, handoff state, and remaining blocker
domains.

## Production Meaning

This report does not create new CFD validation and does not clear any blocker.
It is a traceability artifact: it prevents broad claims like "the master plan is
complete" unless every parsed requirement is covered by evidence and the
production scorecard is ready.

For the current state, the report remains
`NOT_READY-H2-MASTER-PLAN-TRACEABILITY`.

## Verification

The full engineering H2 verifier now requires the traceability report and fails
if the master-plan hash changes, requirement IDs are missing, evidence hashes are
stale, or a non-PASS row lacks a remaining gap.
