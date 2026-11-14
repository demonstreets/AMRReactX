#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_STRICT_EXTERNAL_ARTIFACT_RECEIVING_PREFLIGHT_ENTRYPOINT_REPORT:-docs/codex_audit/evidence/strict_external_artifact_receiving_preflight_entrypoint_20260820/strict_external_artifact_receiving_preflight_entrypoint_report.json}
python3 tools/write_strict_external_artifact_receiving_preflight_entrypoint_report.py --verify-json "$report"
echo "[strict-external-artifact-receiving-preflight-entrypoint] PASS"
