#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
report=${CODEX_STRICT_EXTERNAL_ARTIFACT_CN_HANDOFF_REPORT:-docs/codex_audit/evidence/strict_external_artifact_cn_handoff_20260818/strict_external_artifact_cn_handoff_report.json}

python3 tools/write_strict_external_artifact_cn_handoff_report.py --verify-json "$report"
echo "[strict-external-artifact-cn-handoff] PASS Chinese handoff guide"
