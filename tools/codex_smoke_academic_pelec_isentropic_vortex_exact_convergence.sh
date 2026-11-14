#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir=${CODEX_ISENTROPIC_VORTEX_EXACT_LOG_DIR:-/tmp/codex_pelec_isentropic_vortex_exact_convergence_$(date -u +%Y%m%dT%H%M%SZ)}
mkdir -p "$log_dir"

CODEX_ISENTROPIC_VORTEX_TREND_LOG_DIR="$log_dir" \
CODEX_VORTEX_EXACT=1 \
CODEX_VORTEX_BETA="${CODEX_VORTEX_BETA:-5.0}" \
CODEX_VORTEX_P_BG="${CODEX_VORTEX_P_BG:-1.0}" \
CODEX_VORTEX_STOP_TIME="${CODEX_VORTEX_STOP_TIME:-0.01}" \
CODEX_VORTEX_MAX_STEP="${CODEX_VORTEX_MAX_STEP:-500}" \
CODEX_VORTEX_CFL="${CODEX_VORTEX_CFL:-0.05}" \
CODEX_VORTEX_MAX_DENSITY_L1="${CODEX_VORTEX_MAX_DENSITY_L1:-2.0e-3}" \
CODEX_VORTEX_MAX_PRESSURE_L1="${CODEX_VORTEX_MAX_PRESSURE_L1:-2.0e-3}" \
CODEX_VORTEX_MAX_VELOCITY_L1="${CODEX_VORTEX_MAX_VELOCITY_L1:-1.0e-2}" \
CODEX_VORTEX_TREND_MAX_VELOCITY_L1="${CODEX_VORTEX_TREND_MAX_VELOCITY_L1:-1.0e-2}" \
CODEX_SKIP_BUILD="${CODEX_SKIP_BUILD:-0}" \
JOBS="${JOBS:-2}" \
RUN_TIMEOUT="${RUN_TIMEOUT:-360}" \
"$repo_root/tools/codex_smoke_academic_pelec_isentropic_vortex_trend.sh"

python3 "$repo_root/tools/validate_pelec_isentropic_vortex_exact_convergence.py" \
  --summary "$log_dir/summary.tsv" \
  --min-density-order-32-64 "${CODEX_VORTEX_EXACT_MIN_DENSITY_ORDER:-1.5}" \
  --min-pressure-order-32-64 "${CODEX_VORTEX_EXACT_MIN_PRESSURE_ORDER:-1.5}" \
  --min-velocity-order-32-64 "${CODEX_VORTEX_EXACT_MIN_VELOCITY_ORDER:-1.5}" \
  --max-velocity-l1 "${CODEX_VORTEX_EXACT_MAX_VELOCITY_L1:-5.0e-4}" \
  | tee "$log_dir/exact_convergence.log"

echo "[codex-isentropic-vortex-exact-convergence] PASS; logs: $log_dir"
