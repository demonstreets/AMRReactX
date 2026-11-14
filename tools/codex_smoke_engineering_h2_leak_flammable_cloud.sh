#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export CODEX_H2_LEAK_PROFILE_INPUT="${CODEX_H2_LEAK_PROFILE_INPUT:-input.codex_flammable_cloud_smoke}"
export CODEX_H2_LEAK_PROFILE_LOG_DIR="${CODEX_H2_LEAK_FLAMMABLE_LOG_DIR:-/tmp/codex_h2_leak_flammable_cloud_$(date -u +%Y%m%dT%H%M%SZ)}"
export CODEX_H2_LEAK_MIN_FLAMMABLE_CELLS="${CODEX_H2_LEAK_MIN_FLAMMABLE_CELLS:-1}"
export CODEX_H2_LEAK_MIN_FLAMMABLE_VOLUME="${CODEX_H2_LEAK_MIN_FLAMMABLE_VOLUME:-2.0e-4}"
export CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME="${CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME:-5.0e-2}"
export CODEX_H2_LEAK_MIN_MAX_X="${CODEX_H2_LEAK_MIN_MAX_X:-4.0e-2}"
export CODEX_H2_LEAK_MAX_MAX_X="${CODEX_H2_LEAK_MAX_MAX_X:-7.5e-1}"

"$repo_root/tools/codex_smoke_engineering_h2_leak_plume_profile.sh"

input_base=$(basename "$CODEX_H2_LEAK_PROFILE_INPUT")
input_file="$CODEX_H2_LEAK_PROFILE_LOG_DIR/run/$input_base"
max_step=$(awk '$1 == "amr.max_step" {print $3}' "$input_file")
printf -v final_plot 'plt%05d' "$max_step"

python3 "$repo_root/tools/validate_h2_leak_hazard_planes.py" \
  --plotfile "$CODEX_H2_LEAK_PROFILE_LOG_DIR/run/$final_plot" \
  --output "$CODEX_H2_LEAK_PROFILE_LOG_DIR/hazard_planes.csv" \
  --min-x "${CODEX_H2_LEAK_PLANE_MIN_X:-0.5}" \
  --min-active-planes "${CODEX_H2_LEAK_MIN_ACTIVE_PLANES:-2}" \
  --min-flammable-planes "${CODEX_H2_LEAK_MIN_FLAMMABLE_PLANES:-1}" \
  --min-total-cloud-volume "${CODEX_H2_LEAK_MIN_FLAMMABLE_VOLUME:-2.0e-4}" \
  --max-total-cloud-volume "${CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME:-5.0e-2}" \
  --min-peak-x "${CODEX_H2_LEAK_MIN_MAX_X:-4.0e-2}" \
  --max-peak-x "${CODEX_H2_LEAK_MAX_MAX_X:-7.5e-1}" | tee "$CODEX_H2_LEAK_PROFILE_LOG_DIR/hazard_planes.log"

python3 "$repo_root/tools/validate_h2_leak_hazard_timeseries.py" \
  --run-dir "$CODEX_H2_LEAK_PROFILE_LOG_DIR/run" \
  --output "$CODEX_H2_LEAK_PROFILE_LOG_DIR/hazard_timeseries.csv" \
  --min-x "${CODEX_H2_LEAK_PLANE_MIN_X:-0.5}" \
  --min-plotfiles "${CODEX_H2_LEAK_MIN_TIMESERIES_PLOTFILES:-6}" \
  --require-monotone-mass \
  --max-mass-drop-ratio "${CODEX_H2_LEAK_TIMESERIES_MAX_MASS_DROP_RATIO:-1.0e-6}" \
  --max-initial-cloud-volume "${CODEX_H2_LEAK_MAX_INITIAL_CLOUD_VOLUME:-0.0}" \
  --min-final-active-planes "${CODEX_H2_LEAK_MIN_ACTIVE_PLANES:-2}" \
  --min-final-flammable-planes "${CODEX_H2_LEAK_MIN_FLAMMABLE_PLANES:-1}" \
  --min-max-flammable-planes "${CODEX_H2_LEAK_MIN_FLAMMABLE_PLANES:-1}" \
  --min-final-cloud-volume "${CODEX_H2_LEAK_MIN_FLAMMABLE_VOLUME:-2.0e-4}" \
  --max-final-cloud-volume "${CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME:-5.0e-2}" \
  --min-final-peak-x "${CODEX_H2_LEAK_MIN_MAX_X:-4.0e-2}" \
  --max-final-peak-x "${CODEX_H2_LEAK_MAX_MAX_X:-7.5e-1}" | tee "$CODEX_H2_LEAK_PROFILE_LOG_DIR/hazard_timeseries.log"

printf '[codex-smoke] PASS h2_leak flammable-cloud validation log_dir=%s planes=%s timeseries=%s\n' "$CODEX_H2_LEAK_PROFILE_LOG_DIR" "$CODEX_H2_LEAK_PROFILE_LOG_DIR/hazard_planes.csv" "$CODEX_H2_LEAK_PROFILE_LOG_DIR/hazard_timeseries.csv"
