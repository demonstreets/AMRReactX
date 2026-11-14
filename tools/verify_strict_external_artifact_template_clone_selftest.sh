#!/bin/sh
set -eu
json="${1:-docs/codex_audit/evidence/strict_external_artifact_template_clone_selftest_20260817/strict_external_artifact_template_clone_selftest_report.json}"
python3 tools/write_strict_external_artifact_template_clone_selftest_report.py --verify-json "$json"
echo "[strict-external-artifact-template-clone-selftest] PASS template clone selftest"
