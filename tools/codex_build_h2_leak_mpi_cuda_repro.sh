#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="${repo_root}/examples/engineering/h2_leak_3d"
evidence_dir="${repo_root}/docs/codex_audit/evidence/dataverse_open_channel_amr_source_projection_implementation_20260811"
log="${evidence_dir}/build_mpi_cuda_sundials_local.log"
jobs=${JOBS:-2}
ebase=${EBASE:-codex_amr_source_projection_impl}

mkdir -p "${evidence_dir}"
source "${repo_root}/tools/codex_setup_cuda126_sundials_env.sh"

cd "${case_dir}"
make -j "${jobs}" USE_MPI=TRUE USE_CUDA=TRUE USE_OMP=FALSE \
  SUNDIALS_LIB_DIR="${SUNDIALS_LIB_DIR}" EBASE="${ebase}" >"${log}" 2>&1
printf 'SUCCESS\n' >>"${log}"
printf 'CUDA_BUILD_RC=0\n' >>"${log}"
printf 'h2_leak_mpi_cuda_repro_build PASS log=%s exe=%s\n' \
  "${log}" "${case_dir}/${ebase}3d.gnu.MPI.CUDA.ex"
