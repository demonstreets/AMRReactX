#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report="docs/codex_audit/evidence/engineering_liquefied_release_vaporization_source_model_20260807/engineering_liquefied_release_vaporization_source_model_report.json"

if [[ ! -f "$report" ]]; then
  python3 tools/write_engineering_liquefied_release_vaporization_source_model_report.py
fi

python3 tools/write_engineering_liquefied_release_vaporization_source_model_report.py --verify-json "$report"
echo "[engineering-liquefied-release-vaporization-source-model] PASS screening source model report"
