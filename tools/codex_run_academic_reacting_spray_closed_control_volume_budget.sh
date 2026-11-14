#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root="${CODEX_ACADEMIC_REACTING_SPRAY_CV_BUDGET_ROOT:-docs/codex_audit/evidence/academic_reacting_spray_closed_control_volume_budget_20260729}"
case_src="examples/academic/shock_droplet"
case_name="reacting_closed_control_volume_evap_40step"
run_dir="$root/$case_name"
input_file="$run_dir/inputs"
init_file="$run_dir/initspraydata_2d_single.dat"
log_file="$run_dir/run.log"
exe="$case_src/PeleC2d.gnu.ex"
jobs="${JOBS:-4}"
run_timeout="${RUN_TIMEOUT:-900}"

if [[ -e "$run_dir" && "${CODEX_ACADEMIC_REACTING_SPRAY_CV_BUDGET_FORCE:-FALSE}" != TRUE ]]; then
  printf '[academic-reacting-spray-cv-budget] FAIL run dir exists; set CODEX_ACADEMIC_REACTING_SPRAY_CV_BUDGET_FORCE=TRUE to replace: %s\n' "$run_dir" >&2
  exit 1
fi
if [[ -e "$run_dir" ]]; then
  rm -rf "$run_dir"
fi
mkdir -p "$run_dir"

make -C "$case_src" -j "$jobs" DIM=2 USE_MPI=FALSE USE_OMP=FALSE
cp "$exe" "$run_dir/"
cp "$case_src/inputs" "$input_file"
cp "$case_src/initspraydata_2d_single.dat" "$init_file"

python3 - "$init_file" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
lines = path.read_text().splitlines()
parts = lines[1].split()
parts[2] = '100.0'
parts[3] = '0.0'
lines[1] = ' '.join(parts)
path.write_text('\n'.join(lines) + '\n')
PY

cat >> "$input_file" <<'EOF_INPUT_CONTRACT'

# Codex ACD-07 reacting closed control-volume budget overrides
max_step = 40
stop_time = 5.0e-5
amr.plot_int = 1
amr.check_int = -1
amr.n_cell = 64 32
amr.max_grid_size = 64 32
geometry.is_periodic = 1 1
pelec.lo_bc = Interior Interior
pelec.hi_bc = Interior Interior
pelec.do_react = 1
pelec.chem_integrator = ReactorCvode
cvode.solve_type = dense_direct
cvode.rtol = 1e-6
cvode.atol = 1e-10
pelec.do_mol = 0
pelec.do_hydro = 1
pelec.cfl = 0.02
pelec.plot_rhoy = 1
pelec.plot_massfrac = 1
particles.init_file = initspraydata_2d_single.dat
particles.plot_src = 1
particles.mass_transfer = 1
particles.mom_transfer = 1
particles.fixed_parts = 0
particles.use_breakup_model = None
prob.Y_NC7H16 = 0.0621
prob.Y_O2 = 0.2186
prob.Y_N2 = 0.7193
prob.p_left = 1.013e6
prob.T_left = 2200.0
prob.p_right = 1.013e6
prob.T_right = 2200.0
prob.diaphragm = 25.0
amr.derive_plot_vars = x_velocity y_velocity pressure
EOF_INPUT_CONTRACT

(
  cd "$run_dir"
  timeout "$run_timeout" "./$(basename "$exe")" "$(basename "$input_file")" \
    max_step=40 stop_time=5.0e-5 \
    amr.plot_int=1 amr.check_int=-1 amr.n_cell='64 32' amr.max_grid_size='64 32' \
    geometry.is_periodic='1 1' pelec.lo_bc='Interior Interior' pelec.hi_bc='Interior Interior' \
    pelec.do_react=1 pelec.chem_integrator=ReactorCvode cvode.solve_type=dense_direct cvode.rtol=1e-6 cvode.atol=1e-10 \
    pelec.do_mol=0 pelec.do_hydro=1 pelec.cfl=0.02 pelec.plot_rhoy=1 pelec.plot_massfrac=1 \
    particles.init_file='initspraydata_2d_single.dat' particles.plot_src=1 particles.mass_transfer=1 \
    particles.mom_transfer=1 particles.fixed_parts=0 particles.use_breakup_model=None \
    prob.Y_NC7H16=0.0621 prob.Y_O2=0.2186 prob.Y_N2=0.7193 \
    prob.p_left=1.013e6 prob.T_left=2200.0 prob.p_right=1.013e6 prob.T_right=2200.0 prob.diaphragm=25.0 \
    amr.derive_plot_vars='x_velocity y_velocity pressure' \
    > "$(basename "$log_file")" 2>&1
)

grep -q 'AMReX .* finalized' "$log_file"
if grep -qiE 'nan|SIGSEGV|Segmentation|Backtrace|Abort|Simulation stopped early' "$log_file"; then
  echo '[academic-reacting-spray-cv-budget] failure marker in run log' >&2
  tail -80 "$log_file" >&2
  exit 1
fi

python3 tools/write_academic_reacting_spray_closed_control_volume_budget_report.py \
  --run-dir "$run_dir" \
  --input "$input_file" \
  --run-log "$log_file" \
  --init-file "$init_file" \
  --output-json "$root/academic_reacting_spray_closed_control_volume_budget_report.json" \
  --output-md "$root/academic_reacting_spray_closed_control_volume_budget_report.md"

python3 tools/write_academic_reacting_spray_closed_control_volume_budget_report.py \
  --verify-json "$root/academic_reacting_spray_closed_control_volume_budget_report.json"

printf 'academic_reacting_spray_closed_control_volume_budget RUNNER-PASS root=%s case=%s\n' "$root" "$case_name"
