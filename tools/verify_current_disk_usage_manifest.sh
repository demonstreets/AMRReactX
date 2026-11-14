#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_CURRENT_DISK_USAGE_MANIFEST_REPORT:-docs/codex_audit/evidence/current_disk_usage_manifest_20260803/current_disk_usage_manifest_report.json}

python3 tools/write_current_disk_usage_manifest_report.py --verify-json "$report"
