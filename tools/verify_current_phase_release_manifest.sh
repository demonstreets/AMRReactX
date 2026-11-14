#!/usr/bin/env bash
set -euo pipefail
json="${1:-docs/codex_audit/evidence/current_phase_release_manifest_20260812/current_phase_release_manifest_report.json}"
python3 tools/write_current_phase_release_manifest_report.py --verify-json "$json"
