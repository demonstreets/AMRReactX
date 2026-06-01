#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-build-stage4}"
NP="${NP:-2}"
AMREX_PREFIX="${AMREX_PREFIX:-/home/demonstreets/amrex-install}"

cd "${ROOT_DIR}"

cmake -S . -B "${BUILD_DIR}" \
  -DCMAKE_PREFIX_PATH="${AMREX_PREFIX}" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "${BUILD_DIR}" -j "${JOBS:-4}"

EXE="./${BUILD_DIR}/amrreactx"
PYTHON="${PYTHON:-python3}"
CLEAN_PLOTFILES="${CLEAN_PLOTFILES:-1}"
CLEAN_HISTORIES="${CLEAN_HISTORIES:-1}"

plotfile_prefix_from_input() {
  local input="$1"
  awk -F '=' '
    /^[[:space:]]*plotfile_prefix[[:space:]]*=/ {
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2)
      print $2
    }
  ' "${input}" | tail -n 1
}

cleanup_plotfiles() {
  local input="$1"
  if [[ "${CLEAN_PLOTFILES}" == "0" ]]; then
    return
  fi

  local prefix
  prefix="$(plotfile_prefix_from_input "${input}")"
  if [[ -z "${prefix}" || "${prefix}" != plt_* ]]; then
    echo "Skipping plotfile cleanup for ${input}: missing or unexpected prefix '${prefix}'"
    return
  fi

  rm -rf -- "${prefix}"*
}

cleanup_history() {
  local history="$1"
  if [[ "${CLEAN_HISTORIES}" == "0" ]]; then
    return
  fi

  if [[ -z "${history}" || "${history}" == /* || "${history}" == *".."* || "${history}" != *.csv ]]; then
    echo "Skipping history cleanup: unexpected path '${history}'"
    return
  fi

  rm -f -- "${history}"
}

run_case() {
  local name="$1"
  local input="$2"
  local history="$3"

  echo "==> Running ${name}"
  mpirun -np "${NP}" "${EXE}" "${input}"
  "${PYTHON}" tools/check_history.py --case "${name}" --history "${history}"
  cleanup_plotfiles "${input}"
  cleanup_history "${history}"
}

run_case porosity_obstacle inputs/verify_porosity_obstacle_3d.in history_verify_porosity_obstacle.csv
run_case porosity_source_total_rate inputs/verify_porosity_source_total_rate_3d.in history_verify_porosity_source_total_rate.csv
run_case porosity_cylinder inputs/verify_porosity_cylinder_3d.in history_verify_porosity_cylinder.csv
run_case porosity_tagging inputs/verify_porosity_tagging_3d.in history_verify_porosity_tagging.csv
run_case porosity_level1_advance inputs/verify_porosity_level1_advance_3d.in history_verify_porosity_level1_advance.csv
run_case porosity_level1_restriction_update inputs/verify_porosity_level1_restriction_update_3d.in history_verify_porosity_level1_restriction_update.csv
run_case porosity_level1_reflux_update inputs/verify_porosity_level1_reflux_update_3d.in history_verify_porosity_level1_reflux_update.csv
run_case porosity_level1_diffusive_reflux_update inputs/verify_porosity_level1_diffusive_reflux_update_3d.in history_verify_porosity_level1_diffusive_reflux_update.csv

echo "Stage 4 porosity fallback verification passed."
