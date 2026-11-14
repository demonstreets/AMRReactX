#!/usr/bin/env bash
set -euo pipefail
json="${1:-docs/codex_audit/evidence/current_operator_quickstart_smoke_20260812/current_operator_quickstart_smoke_report.json}"
python3 tools/write_current_operator_quickstart_smoke_report.py --verify-json "$json"
