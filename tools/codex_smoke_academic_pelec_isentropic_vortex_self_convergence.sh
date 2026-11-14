#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir=${CODEX_ISENTROPIC_VORTEX_SELF_CONV_LOG_DIR:-/tmp/codex_pelec_isentropic_vortex_self_convergence_$(date -u +%Y%m%dT%H%M%SZ)}
mkdir -p "$log_dir"

CODEX_ISENTROPIC_VORTEX_TREND_LOG_DIR="$log_dir" \
CODEX_VORTEX_STOP_TIME="${CODEX_VORTEX_STOP_TIME:-0.01}" \
CODEX_VORTEX_MAX_STEP="${CODEX_VORTEX_MAX_STEP:-200}" \
CODEX_VORTEX_CFL="${CODEX_VORTEX_CFL:-0.2}" \
CODEX_VORTEX_MAX_DENSITY_L1="${CODEX_VORTEX_MAX_DENSITY_L1:-2.0e-3}" \
CODEX_VORTEX_MAX_PRESSURE_L1="${CODEX_VORTEX_MAX_PRESSURE_L1:-2.0e-3}" \
CODEX_VORTEX_MAX_VELOCITY_L1="${CODEX_VORTEX_MAX_VELOCITY_L1:-1.0e-2}" \
CODEX_VORTEX_TREND_MAX_VELOCITY_L1="${CODEX_VORTEX_TREND_MAX_VELOCITY_L1:-1.0e-3}" \
CODEX_SKIP_BUILD="${CODEX_SKIP_BUILD:-0}" \
JOBS="${JOBS:-2}" \
RUN_TIMEOUT="${RUN_TIMEOUT:-300}" \
"$repo_root/tools/codex_smoke_academic_pelec_isentropic_vortex_trend.sh"

cases=()
for n in 16 32 64; do
  run_dir="$log_dir/n${n}/run"
  final_plot=$(find "$run_dir" -maxdepth 1 -type d -name 'plt*' | sort | tail -n 1)
  if [[ -z "$final_plot" || "$(basename "$final_plot")" == "plt00000" ]]; then
    echo "[codex-isentropic-vortex-self-convergence] nx=$n missing final plotfile" >&2
    exit 1
  fi
  cases+=("--case" "${n}=${final_plot}")
done

python3 "$repo_root/tools/validate_pelec_isentropic_vortex_self_convergence.py" \
  "${cases[@]}" \
  --min-order "${CODEX_VORTEX_SELF_CONV_MIN_ORDER:-1.5}" \
  | tee "$log_dir/self_convergence.log"

echo "[codex-isentropic-vortex-self-convergence] PASS; logs: $log_dir"
