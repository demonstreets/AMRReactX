#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_ENGINEERING_LOG_MARKER_COMPATIBILITY_REPORT:-docs/codex_audit/evidence/engineering_log_marker_compatibility_20260806/engineering_log_marker_compatibility_report.json}

python3 tools/write_engineering_log_marker_compatibility_report.py --verify-json "$report"
echo "[engineering-log-marker-compatibility] PASS log marker compatibility report"
