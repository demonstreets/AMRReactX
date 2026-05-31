#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-build-stage2}"
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

run_case leak inputs/leak_3d_open.in history_leak_3d_open.csv
run_case advection inputs/verify_advection_3d.in history_verify_advection.csv
run_case diffusion inputs/verify_diffusion_3d.in history_verify_diffusion.csv
run_case wall inputs/verify_wall_3d.in history_verify_wall.csv
run_case box inputs/verify_box_source_3d.in history_verify_box_source.csv
run_case source_total_rate inputs/verify_source_total_rate_3d.in history_verify_source_total_rate.csv
run_case auto_dt inputs/verify_auto_dt_3d.in history_verify_auto_dt.csv
run_case volume_fraction inputs/verify_volume_fraction_3d.in history_verify_volume_fraction.csv
run_case boundary_faces inputs/verify_boundary_faces_3d.in history_verify_boundary_faces.csv
run_case inlet_scalar inputs/verify_inlet_scalar_3d.in history_verify_inlet_scalar.csv
run_case open_backflow inputs/verify_open_backflow_3d.in history_verify_open_backflow.csv

echo "Stage 1/2 verification suite passed."
