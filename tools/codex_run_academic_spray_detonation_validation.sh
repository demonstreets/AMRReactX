#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root="${CODEX_ACADEMIC_SPRAY_DETONATION_ROOT:-docs/codex_audit/evidence/academic_spray_detonation_validation_20260728}"
case_src="examples/academic/shock_droplet"
case_name="reacting_spray_detonation_1000"
run_dir="$root/$case_name"
input_file="$run_dir/input.$case_name"
log_file="$root/${case_name}.log"
validation_log="$root/validation_${case_name}.log"
manifest="$root/case_manifest.json"
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
    'max_step': '1000',
    'stop_time': '1.0e-4',
    'pelec.do_react': '1',
    'pelec.chem_integrator': '"ReactorCvode"',
    'cvode.solve_type': 'dense_direct',
    'cvode.rtol': '1e-6',
    'cvode.atol': '1e-10',
    'amr.checkpoint_files_output': '0',
    'amr.check_int': '-1',
    'amr.plot_files_output': '1',
    'amr.plot_int': '500',
    'pelec.plot_massfrac': '1',
    'pelec.plot_rhoy': '0',
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
  timeout "$run_timeout" "./$(basename "$exe")" "$(basename "$input_file")" > "$repo_root/$log_file" 2>&1
)

grep -q 'AMReX .* finalized' "$log_file"
if grep -qiE 'nan|SIGSEGV|Segmentation|Backtrace|Abort|Simulation stopped early' "$log_file"; then
  echo '[academic-spray-detonation] failure marker in run log' >&2
  tail -80 "$log_file" >&2
  exit 1
fi

initial_plot="$run_dir/plt00000"
mid_plot="$run_dir/plt00500"
final_plot="$run_dir/plt01000"
if [[ ! -d "$final_plot" ]]; then
  final_plot=$(find "$run_dir" -maxdepth 1 -type d -name 'plt[0-9][0-9][0-9][0-9][0-9]' | sort | tail -n 1)
fi

python3 tools/validate_academic_spray_detonation.py \
  --input "$input_file" \
  --run-log "$log_file" \
  --initial "$initial_plot" \
  --mid "$mid_plot" \
  --final "$final_plot" > "$validation_log"

python3 - "$manifest" "$case_name" "$input_file" "$log_file" "$validation_log" "$initial_plot" "$mid_plot" "$final_plot" <<'PY'
from pathlib import Path
import json
import sys

manifest, case_name, input_file, log_file, validation_log, initial_plot, mid_plot, final_plot = sys.argv[1:]
data = {
    'schema_version': 1,
    'cases': [
        {
            'name': case_name,
            'role': 'reacting_spray_detonation_front_breakup_coupling',
            'input_file': input_file,
            'run_log': log_file,
            'validation_log': validation_log,
            'plotfile_initial': initial_plot,
            'plotfile_mid': mid_plot,
            'plotfile_final': final_plot,
            'max_step': 1000,
        }
    ],
}
path = Path(manifest)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
PY

python3 tools/write_academic_spray_detonation_validation_report.py \
  --manifest "$manifest" \
  --output-json "$root/academic_spray_detonation_validation_report.json" \
  --output-md "$root/academic_spray_detonation_validation_report.md"

python3 tools/write_academic_spray_detonation_validation_report.py \
  --verify-json "$root/academic_spray_detonation_validation_report.json"

printf 'academic_spray_detonation_validation RUNNER-PASS root=%s case=%s final_plot=%s\n' "$root" "$case_name" "$final_plot"
