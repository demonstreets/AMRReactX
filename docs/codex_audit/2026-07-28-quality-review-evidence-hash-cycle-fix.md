# Quality Review Evidence Hash Cycle Fix

Date: 2026-07-28

## Issue

The evidence-chain verifier exposed a metadata cycle:

- `production_evidence_verification_report` reads `h2_quality_review_coverage_report`.
- `h2_quality_review_coverage_report` was also storing the production evidence report in its hashed `evidence_files` list.

Regenerating either side changed the other's expected SHA256 and made the full evidence verification order-sensitive.

## Fix

`tools/write_engineering_h2_quality_review_coverage_report.py` was updated so the production evidence report remains a checked status reference in `referenced_reports`, while the hashed `evidence_files` list records the quality-review generator script itself. This preserves traceability without creating a self-referential hash cycle.

## Verification

After regenerating the command-contract, quality-review, production-evidence, handoff, and master-plan traceability reports, the evidence verifier passed:

`CODEX_ENGINEERING_H2_VERIFY_SKIP_CTEST=TRUE bash tools/verify_engineering_h2_production_evidence.sh`

Result: `VERIFY_RC=0`, final verifier status `PASS engineering H2 production evidence verification`.
