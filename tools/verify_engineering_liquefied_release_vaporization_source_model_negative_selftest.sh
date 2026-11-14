#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report="docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_negative_selftest_20260807/engineering_liquefied_release_vaporization_source_model_negative_selftest_report.json"

if [[ ! -f "$report" ]]; then
  python3 tools/write_engineering_liquefied_release_vaporization_source_model_negative_selftest_report.py
fi

python3 tools/write_engineering_liquefied_release_vaporization_source_model_negative_selftest_report.py --verify-json "$report"
echo "[engineering-liquefied-release-vaporization-source-model-negative-selftest] PASS generator negative selftest report"
