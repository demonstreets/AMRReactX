#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_ENGINEERING_H2_REAL_CAD_NEGATIVE_SELFTEST_REPORT:-docs/codex_audit/evidence/engineering_h2_real_cad_guard_negative_selftest_20260807/real_cad_guard_negative_selftest_report.json}

python3 tools/write_engineering_h2_real_cad_negative_selftest_report.py --verify-json "$report"
echo "[engineering-h2-real-cad-negative-selftest] PASS real-CAD guard negative selftest"
