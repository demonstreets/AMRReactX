#!/usr/bin/env bash
set -euo pipefail
json="${1:-docs/codex_audit/evidence/current_phase_closure_certificate_20260812/current_phase_closure_certificate_report.json}"
python3 tools/write_current_phase_closure_certificate_report.py --verify-json "$json"
