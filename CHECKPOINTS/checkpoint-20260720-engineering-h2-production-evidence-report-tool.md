# Checkpoint: engineering H2 production evidence verification report tool

Date: 2026-07-20

## What changed

- Added `tools/write_engineering_h2_production_evidence_verification_report.py`.
- The new tool replaces the previous ad-hoc inline Python used to refresh `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json` and `.md`.
- The tool reads the sanitized `verification.log`, production scorecard, hybrid CFD scout reports, hybrid runtime affinity manifest, scheduler report, MPI scaling report, and 16-rank production-mesh scout report.
- It writes a schema-3 JSON/Markdown verification report and supports `--verify-json` with evidence SHA checks.
- Integrated the report verifier into `tools/verify_engineering_h2_production_evidence.sh`, so the unified evidence verifier now checks that the packaged verification report is internally consistent and hash-matched.
- Updated `docs/codex_audit/ENGINEERING_PRODUCTION_READINESS.md` and `docs/codex_audit/SMOKE_MATRIX.md` to name the maintained report packager.

## Current report status

- Report: `docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json`
- Status: `PASS`
- Score: `92.6/72.3`
- CTest: `22/22 PASS`
- Hybrid production-mesh 600-step scout: `PASS-HYBRID-CFD-SCOUT`

## Verification

- `python3 -m py_compile tools/write_engineering_h2_production_evidence_verification_report.py`: PASS
- `python3 tools/write_engineering_h2_production_evidence_verification_report.py`: PASS
- `python3 tools/write_engineering_h2_production_evidence_verification_report.py --verify-json docs/codex_audit/evidence/engineering_h2_production_evidence_verification_20260720/production_evidence_verification_report.json`: PASS
- `bash -n tools/verify_engineering_h2_production_evidence.sh`: PASS
- `CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE tools/verify_engineering_h2_production_evidence.sh`: PASS
- Full `tools/verify_engineering_h2_production_evidence.sh`: PASS, including `22/22` CTest
- `python3 tools/check_machine_local_paths.py --strict`: PASS, `scanned_files=971`

## Notes

The unified verifier validates the latest packaged report before a newly captured `verification.log` is written by the outer archival command. After capturing a new full verifier log, rerun `tools/write_engineering_h2_production_evidence_verification_report.py` and `--verify-json` so the report hash matches the new log.
