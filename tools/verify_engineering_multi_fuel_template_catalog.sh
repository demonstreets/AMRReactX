#!/usr/bin/env bash
set -euo pipefail

report=${CODEX_ENGINEERING_MULTI_FUEL_TEMPLATE_CATALOG_REPORT:-docs/codex_audit/evidence/engineering_multi_fuel_template_catalog_20260811/engineering_multi_fuel_template_catalog_report.json}

python3 tools/write_engineering_multi_fuel_template_catalog_report.py --verify-json "$report"
