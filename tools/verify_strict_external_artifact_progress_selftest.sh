#!/bin/sh
set -eu
json="${1:-docs/codex_audit/evidence/strict_external_artifact_progress_selftest_20260812/strict_external_artifact_progress_selftest_report.json}"
python3 tools/write_strict_external_artifact_progress_selftest_report.py --verify-json "$json"
