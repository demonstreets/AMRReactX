#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_MASTER_PLAN_STRICT_ARTIFACT_INTAKE_MANIFEST_REPORT:-docs/codex_audit/evidence/master_plan_strict_artifact_intake_manifest_20260731/master_plan_strict_artifact_intake_manifest_report.json}

python3 tools/write_master_plan_strict_artifact_intake_manifest_report.py --verify-json "$report"
echo "[master-plan-strict-artifact-intake] PASS strict artifact intake manifest"
