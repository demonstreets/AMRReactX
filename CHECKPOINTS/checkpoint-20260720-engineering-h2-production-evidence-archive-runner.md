# Checkpoint: engineering H2 production evidence archive runner

Date: 2026-07-20

## What changed

- Added `tools/run_engineering_h2_production_evidence_verification_archive.sh`.
- Added `CODEX_ENGINEERING_H2_VERIFY_SKIP_REPORT=TRUE` support to `tools/verify_engineering_h2_production_evidence.sh` to avoid a report/log hash chicken-and-egg during archive refresh.
- The archive runner now executes the unified verifier with report self-check skipped, captures raw output, writes sanitized `verification.log`, appends `CODEX_VERIFY_RC:<rc>`, regenerates `production_evidence_verification_report.json/.md`, and verifies the regenerated report.
- The archive runner maps `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE` to `--no-require-ctest` for fast archive checks, while the default full archive keeps CTest required.
- Updated readiness and smoke-matrix docs to point at the archive runner as the preferred reproducible evidence refresh command.

## Verification

- `bash -n tools/verify_engineering_h2_production_evidence.sh tools/run_engineering_h2_production_evidence_verification_archive.sh`: PASS
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE tools/run_engineering_h2_production_evidence_verification_archive.sh`: PASS, report verified with `ctest=None`
- `tools/run_engineering_h2_production_evidence_verification_archive.sh`: PASS, report verified with `ctest=22`
- Latest report: `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json`
- Current score: `92.6/72.3`

## Notes

The archive runner is now the preferred command for refreshing the top-level production evidence verification archive. Use `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE` only for fast checks; the maintained main archive should be refreshed with the default full CTest path before publishing a status snapshot.
