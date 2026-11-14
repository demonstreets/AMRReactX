#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_PROFILE_LOG_DIR:-/tmp/codex_h2_leak_plume_profile_$(date -u +%Y%m%dT%H%M%SZ)}"
profile_input="${CODEX_H2_LEAK_PROFILE_INPUT:-input.codex_plume_profile_smoke}"
export CODEX_H2_LEAK_HISTORY_INPUT="$profile_input"
export CODEX_H2_LEAK_HISTORY_LOG_DIR="$log_dir"
export CODEX_H2_LEAK_HISTORY_MIN_PLOTFILES="${CODEX_H2_LEAK_HISTORY_MIN_PLOTFILES:-6}"
export CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="${CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO:-4.5}"
export CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO="${CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO:-0.80}"
export CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO="${CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO:-1.20}"
export CODEX_H2_LEAK_PROFILE_MIN_FINAL_MASS_RATIO="${CODEX_H2_LEAK_PROFILE_MIN_FINAL_MASS_RATIO:-$CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO}"
export CODEX_H2_LEAK_PROFILE_MAX_FINAL_MASS_RATIO="${CODEX_H2_LEAK_PROFILE_MAX_FINAL_MASS_RATIO:-$CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO}"

"$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"

input_base=$(basename "$profile_input")
max_step=$(awk '$1 == "amr.max_step" {print $3}' "$log_dir/run/$input_base")
printf -v final_plot 'plt%05d' "$max_step"

python3 "$repo_root/tools/validate_h2_leak_plume_profile.py" \
  --plotfile "$log_dir/run/$final_plot" \
  --input "$log_dir/run/$input_base" \
  --log "$log_dir/run.log" \
  --max-y-l1 "${CODEX_H2_LEAK_PROFILE_MAX_Y_L1:-0.55}" \
  --max-z-l1 "${CODEX_H2_LEAK_PROFILE_MAX_Z_L1:-0.55}" \
  --min-centroid-shift "${CODEX_H2_LEAK_PROFILE_MIN_CENTROID_SHIFT:-0.03}" \
  --min-downstream-fraction "${CODEX_H2_LEAK_PROFILE_MIN_DOWNSTREAM_FRACTION:-0.65}" \
  --max-lateral-offset "${CODEX_H2_LEAK_PROFILE_MAX_LATERAL_OFFSET:-0.08}" \
  --min-plane-mass-fraction "${CODEX_H2_LEAK_PROFILE_MIN_PLANE_MASS_FRACTION:-0.05}" \
  --min-final-mass-ratio "${CODEX_H2_LEAK_PROFILE_MIN_FINAL_MASS_RATIO:-0.80}" \
  --max-final-mass-ratio "${CODEX_H2_LEAK_PROFILE_MAX_FINAL_MASS_RATIO:-1.20}" | tee "$log_dir/profile_validation.log"

if [ -z "${CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME:-}" ] && \
   [ -z "${CODEX_H2_LEAK_MIN_FLAMMABLE_CELLS:-}" ] && \
   [ -z "${CODEX_H2_LEAK_MIN_FLAMMABLE_VOLUME:-}" ]; then
  CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME=0.0
fi

hazard_args=(
  --plotfile "$log_dir/run/$final_plot"
)
if [ -n "${CODEX_H2_LEAK_MIN_FLAMMABLE_CELLS:-}" ]; then
  hazard_args+=(--min-cloud-cells "$CODEX_H2_LEAK_MIN_FLAMMABLE_CELLS")
fi
if [ -n "${CODEX_H2_LEAK_MIN_FLAMMABLE_VOLUME:-}" ]; then
  hazard_args+=(--min-cloud-volume "$CODEX_H2_LEAK_MIN_FLAMMABLE_VOLUME")
fi
if [ -n "${CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME:-}" ]; then
  hazard_args+=(--max-cloud-volume "$CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME")
fi
if [ -n "${CODEX_H2_LEAK_MIN_MAX_X:-}" ]; then
  hazard_args+=(--min-max-x "$CODEX_H2_LEAK_MIN_MAX_X")
fi
if [ -n "${CODEX_H2_LEAK_MAX_MAX_X:-}" ]; then
  hazard_args+=(--max-max-x "$CODEX_H2_LEAK_MAX_MAX_X")
fi

python3 "$repo_root/tools/validate_h2_leak_hazard_summary.py" "${hazard_args[@]}" | tee "$log_dir/hazard_summary.log"

printf '[codex-smoke] PASS h2_leak plume-profile validation log=%s validation=%s hazard=%s\n' "$log_dir/run.log" "$log_dir/profile_validation.log" "$log_dir/hazard_summary.log"
