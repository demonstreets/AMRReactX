#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

report=${CODEX_ENGINEERING_LIQUEFIED_PHASE_CHANGE_OVERCLAIM_GUARD_REPORT:-docs/codex_audit/evidence/engineering_liquefied_phase_change_overclaim_guard_20260811/engineering_liquefied_phase_change_overclaim_guard_report.json}

python3 tools/write_engineering_liquefied_phase_change_overclaim_guard_report.py --verify-json "$report"
echo "[engineering-liquefied-phase-change-overclaim-guard] PASS overclaim guard report"
