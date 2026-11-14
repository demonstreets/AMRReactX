#!/usr/bin/env bash
set -euo pipefail

report=${1:-docs/codex_audit/evidence/engineering_liquefied_breach_preset_templates_20260811/engineering_liquefied_breach_preset_templates_report.json}
python3 tools/write_engineering_liquefied_breach_preset_templates_report.py --verify-json "$report"
