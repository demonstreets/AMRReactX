#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_STRICT_ARTIFACT_TEMPLATE_LINT_REPORT:-docs/codex_audit/evidence/strict_artifact_template_lint_20260803/strict_artifact_template_lint_report.json}

python3 tools/write_strict_artifact_template_lint_report.py --verify-json "$report"
