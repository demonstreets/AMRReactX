# Engineering production scorecard checkpoint

Date: 2026-07-20

## Scope

This checkpoint adds a machine-readable engineering production scorecard to keep progress reporting stable and evidence-driven. It separates engineering functional coverage from production credibility so smoke-scale functionality cannot be confused with production-grade validation.

## Changes

- Added `tools/write_engineering_production_scorecard.py`.
- Generated scorecard evidence under `docs/codex_audit/evidence/engineering_production_scorecard_20260720/`.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` with the scorecard result.
- Fixed the previous placement of the H2 ignition consequence evidence row so it lives in the maintained-evidence table, not the production-gate hierarchy.

## Evidence

- `engineering_production_scorecard PASS ... status=NOT_PRODUCTION_READY functional=85.0 production=62.6`.
- `engineering_production_scorecard VERIFY-PASS ... status=NOT_PRODUCTION_READY functional=85.0 production=62.6`.
- The scorecard verifies hashes for the campaign manifest, release evidence pack, runtime-affinity manifest, scheduler report, and H2 ignition consequence report.

## Interpretation

- Engineering functional coverage is now tracked as `85.0%`.
- Engineering production credibility is now tracked as `62.6%`.
- The two values are intentionally different. Functional coverage measures maintained workflow breadth; production credibility measures evidence strength for production use.

## Remaining blockers

- Scheduler-run outputs are still not PASS.
- Production-size mesh campaigns are missing.
- Overnight/long-duration stability campaigns are missing.
- Reference-data agreement is missing.
- Real-CAD cleanup campaigns are missing.
- Calibrated fire radiation/overpressure metrics are missing.
