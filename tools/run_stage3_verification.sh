#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-build-stage3}"
NP="${NP:-2}"
AMREX_PREFIX="${AMREX_PREFIX:-/home/demonstreets/amrex-install}"

cd "${ROOT_DIR}"

cmake -S . -B "${BUILD_DIR}" \
  -DCMAKE_PREFIX_PATH="${AMREX_PREFIX}" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "${BUILD_DIR}" -j "${JOBS:-4}"

EXE="./${BUILD_DIR}/amrreactx"
PYTHON="${PYTHON:-python3}"

run_case() {
  local name="$1"
  local input="$2"
  local history="$3"

  echo "==> Running ${name}"
  mpirun -np "${NP}" "${EXE}" "${input}"
  "${PYTHON}" tools/check_history.py --case "${name}" --history "${history}"
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
run_case tagging inputs/verify_tagging_3d.in history_verify_tagging.csv
run_case level1_advance inputs/verify_level1_advance_3d.in history_verify_level1_advance.csv
run_case level1_restriction_update inputs/verify_level1_restriction_update_3d.in history_verify_level1_restriction_update.csv

echo "Stage 1/2 + Stage 3.1/3.2/3.4 + early 3.5 verification suite passed."
