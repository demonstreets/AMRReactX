#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_CURRENT_CASE_OUTPUT_CLEANUP_MANIFEST_REPORT:-docs/codex_audit/evidence/current_case_output_cleanup_manifest_20260803/current_case_output_cleanup_manifest_report.json}

python3 tools/write_current_case_output_cleanup_manifest_report.py --verify-json "$report"
