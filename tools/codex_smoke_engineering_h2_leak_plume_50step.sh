#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export CODEX_H2_LEAK_HISTORY_INPUT=input.codex_plume_50step_smoke
export CODEX_H2_LEAK_HISTORY_LOG_DIR="${CODEX_H2_LEAK_50STEP_LOG_DIR:-/tmp/codex_h2_leak_plume_50step_$(date -u +%Y%m%dT%H%M%SZ)}"
export CODEX_H2_LEAK_HISTORY_MIN_PLOTFILES=11
export CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO=9.5
export CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO=0.50
export CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO=1.75
exec "$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"
