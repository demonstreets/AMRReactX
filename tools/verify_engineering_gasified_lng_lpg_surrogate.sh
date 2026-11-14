#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_ENGINEERING_GASIFIED_LNG_LPG_SURROGATE_REPORT:-docs/codex_audit/evidence/engineering_gasified_lng_lpg_surrogate_20260806/engineering_gasified_lng_lpg_surrogate_report.json}

python3 tools/write_engineering_gasified_lng_lpg_surrogate_report.py --verify-json "$report"
echo "[engineering-gasified-lng-lpg-surrogate] PASS capability boundary report"
