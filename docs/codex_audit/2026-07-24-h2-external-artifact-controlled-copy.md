# Engineering H2 External Artifact Controlled Copy Gate

## Purpose

The production H2 evidence chain now has a controlled-copy gate between the external artifact ingestion plan and the controlled evidence tree. The gate records every planned copy action, source validity, target state, copy count, and blocker-clearing limitation before any externally supplied CAD, SBEPV5, or fire-calibration data can affect production-readiness evidence.

## Current State

- Report generator: `tools/write_engineering_h2_external_artifact_controlled_copy_report.py`
- Default report: `docs/codex_audit/evidence/engineering_h2_external_artifact_controlled_copy_20260724/h2_external_artifact_controlled_copy_report.json`
- Current status: `NOT_READY-H2-EXTERNAL-ARTIFACT-CONTROLLED-COPY`
- Ready copy actions: `0/14`
- Copied files: `0`

## Safety Rules

- Default execution is dry-run/audit only and writes no controlled evidence files.
- `--apply` is refused unless the ingestion plan has already reached `PASS-H2-EXTERNAL-ARTIFACT-INGESTION-PLAN`.
- `--apply` also requires `--confirm-controlled-copy H2_EXTERNAL_ARTIFACTS_READY`.
- Existing targets are not overwritten unless `--allow-overwrite` is explicitly supplied.
- The report never clears production blockers by itself; blocker clearance still requires the full rebuild and verifier chain.

## Verification

The controlled-copy report is integrated into:

- `tools/rebuild_engineering_h2_evidence_chain.sh`
- `tools/verify_engineering_h2_production_evidence.sh`
- `tools/write_engineering_h2_production_evidence_verification_report.py`

The production evidence verification schema was advanced to `28` so the controlled-copy gate is included in the auditable summary and hash-checked evidence list.
