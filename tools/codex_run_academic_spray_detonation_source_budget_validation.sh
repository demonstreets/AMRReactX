#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root="${CODEX_ACADEMIC_SPRAY_DETONATION_SOURCE_BUDGET_ROOT:-docs/codex_audit/evidence/academic_spray_detonation_source_budget_validation_20260729}"
case_src="examples/academic/shock_droplet"
case_name="reacting_spray_detonation_source_budget_300"
run_dir="$root/$case_name"
input_file="$run_dir/inputs"
log_file="$run_dir/run.log"
exe="$case_src/PeleC2d.gnu.ex"
jobs="${JOBS:-4}"
run_timeout="${RUN_TIMEOUT:-1500}"

rm -rf "$run_dir"
mkdir -p "$run_dir"

make -C "$case_src" -j "$jobs" DIM=2 USE_MPI=FALSE USE_OMP=FALSE

cp "$exe" "$run_dir/"
cp "$case_src/inputs" "$input_file"
cp "$case_src"/initspraydata*.dat "$run_dir"/

python3 - "$input_file" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
replacements = {
    'max_step': '300',
    'stop_time': '3.0e-5',
    'pelec.do_react': '1',
    'pelec.chem_integrator': '"ReactorCvode"',
    'cvode.solve_type': 'dense_direct',
    'cvode.rtol': '1e-6',
    'cvode.atol': '1e-10',
    'amr.checkpoint_files_output': '0',
    'amr.check_int': '-1',
    'amr.plot_files_output': '1',
    'amr.plot_int': '1',
    'pelec.plot_massfrac': '1',
    'pelec.plot_rhoy': '1',
    'particles.plot_src': '1',
    'amr.derive_plot_vars': 'x_velocity y_velocity pressure',
    'pelec.sum_interval': '-1',
    'amr.v': '1',
    'pelec.v': '0',
    'prob.Y_NC7H16': '0.0621',
    'prob.Y_O2': '0.2186',
    'prob.Y_N2': '0.7193',
    'prob.p_left': '1.8e7',
    'prob.T_left': '2200.0',
    'prob.p_right': '1.013e6',
    'prob.T_right': '300.0',
}
lines = []
seen = set()
for raw in text.splitlines():
    stripped = raw.split('#', 1)[0].strip()
    if stripped and '=' in stripped:
        key = stripped.split('=', 1)[0].strip()
        if key == 'amr.plot_per':
            continue
        if key in replacements:
            lines.append(f'{key} = {replacements[key]}')
            seen.add(key)
            continue
    lines.append(raw)
for key, value in replacements.items():
    if key not in seen:
        lines.append(f'{key} = {value}')
path.write_text('\n'.join(lines) + '\n')
PY

(
  cd "$run_dir"
  timeout "$run_timeout" "./$(basename "$exe")" "$(basename "$input_file")" > "run.log" 2>&1
)

grep -q 'AMReX .* finalized' "$log_file"
if grep -qiE 'nan|SIGSEGV|Segmentation|Backtrace|Abort|Simulation stopped early' "$log_file"; then
  echo '[academic-spray-detonation-source-budget] failure marker in run log' >&2
  tail -80 "$log_file" >&2
  exit 1
fi

python3 tools/write_academic_spray_detonation_source_budget_validation_report.py \
  --run-dir "$run_dir" \
  --input "$input_file" \
  --run-log "$log_file" \
  --output-json "$root/academic_spray_detonation_source_budget_validation_report.json" \
  --output-md "$root/academic_spray_detonation_source_budget_validation_report.md"

python3 tools/write_academic_spray_detonation_source_budget_validation_report.py \
  --verify-json "$root/academic_spray_detonation_source_budget_validation_report.json"

printf 'academic_spray_detonation_source_budget_validation RUNNER-PASS root=%s case=%s\n' "$root" "$case_name"
