#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report='docs/codex_audit/evidence/master_plan_strict_artifact_drop_preflight_20260731/master_plan_strict_artifact_drop_preflight_report.json'

python3 tools/write_master_plan_strict_artifact_drop_preflight_report.py --output-json "$report"
python3 tools/write_master_plan_strict_artifact_drop_preflight_report.py --verify-json "$report"

printf '[master-plan-strict-artifact-drop-preflight] PASS strict artifact drop preflight\n'
