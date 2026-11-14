#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
case_dir="${repo_root}/examples/academic/shock_droplet"
evidence_dir="${repo_root}/docs/codex_audit/evidence/academic_spray_source_budget_validation_20260729"
mkdir -p "${evidence_dir}"

(
  cd "${case_dir}"
  make -j"${CODEX_BUILD_JOBS:-8}"
)

run_dir="$(mktemp -d /tmp/codex_academic_spray_source_budget.XXXXXX)"
cp "${case_dir}/PeleC2d.gnu.ex" "${case_dir}/inputs" "${case_dir}/initspraydata_2d_single.dat" "${run_dir}/"

(
  cd "${run_dir}"
  ./PeleC2d.gnu.ex inputs \
    max_step=20 stop_time=2.0e-5 \
    amr.plot_int=1 amr.check_int=-1 amr.n_cell='64 32' amr.max_grid_size='64 32' \
    geometry.is_periodic='1 1' pelec.lo_bc='Interior Interior' pelec.hi_bc='Interior Interior' \
    pelec.do_react=0 pelec.do_mol=0 pelec.do_hydro=1 pelec.cfl=0.02 pelec.plot_rhoy=1 \
    particles.init_file='initspraydata_2d_single.dat' particles.plot_src=1 particles.mass_transfer=1 \
    particles.mom_transfer=0 particles.fixed_parts=0 particles.use_breakup_model=None \
    > run.log 2>&1
)

git -C "${repo_root}" diff -- \
  external/PeleC/Source/Advance.cpp \
  external/PeleC/Source/PeleC.H \
  external/PeleC/Source/PeleCAmr.cpp \
  external/PeleC/Submodules/PelePhysics/Source/Spray/SpraySetup.cpp \
  external/PeleC/Submodules/PelePhysics/Source/Spray/Drag.H \
  > "${evidence_dir}/spray_source_mapping_code_diff.patch"

cp "${run_dir}/run.log" "${evidence_dir}/run.log"
cp "${run_dir}/inputs" "${evidence_dir}/inputs"
python3 "${repo_root}/tools/write_academic_spray_source_budget_validation_report.py" \
  --run-dir "${run_dir}" \
  --output-json "${evidence_dir}/academic_spray_source_budget_validation_report.json" \
  --output-md "${evidence_dir}/academic_spray_source_budget_validation_report.md"

printf 'RUN_DIR=%s\n' "${run_dir}" | tee "${evidence_dir}/run_dir.txt"
