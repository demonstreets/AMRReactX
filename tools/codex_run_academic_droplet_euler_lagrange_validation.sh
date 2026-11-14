#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root="${CODEX_ACADEMIC_DROPLET_EL_ROOT:-docs/codex_audit/evidence/academic_droplet_euler_lagrange_validation_20260728}"
case_src="examples/academic/shock_droplet"
case_name="shock_droplet_khrt_1000"
run_dir="$root/$case_name"
input_file="$run_dir/input.$case_name"
log_file="$root/${case_name}.log"
validation_log="$root/validation_${case_name}.log"
manifest="$root/case_manifest.json"
exe="$case_src/PeleC2d.gnu.ex"
jobs="${JOBS:-4}"

rm -rf "$run_dir"
mkdir -p "$run_dir"

if [[ ! -x "$exe" ]]; then
  make -C "$case_src" -j "$jobs" DIM=2 USE_MPI=FALSE USE_OMP=FALSE
fi

cp "$case_src/inputs" "$input_file"
cp "$case_src"/initspraydata*.dat "$run_dir"/

python3 - "$input_file" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text()

replacements = {
    'max_step': '1000',
    'amr.checkpoint_files_output': '0',
    'amr.check_int': '-1',
    'amr.plot_files_output': '1',
    'amr.plot_int': '1000',
    'pelec.sum_interval': '-1',
    'pelec.v': '0',
    'particles.v': '0',
}

lines = []
seen = set()
for raw in text.splitlines():
    stripped = raw.split('#', 1)[0].strip()
    if not stripped or '=' not in stripped:
        lines.append(raw)
        continue
    key = stripped.split('=', 1)[0].strip()
    if key == 'amr.plot_per':
        continue
    if key in replacements:
        lines.append(f'{key} = {replacements[key]}')
        seen.add(key)
    else:
        lines.append(raw)

for key, value in replacements.items():
    if key not in seen:
        lines.append(f'{key} = {value}')

path.write_text('\n'.join(lines) + '\n')
PY

(
  cd "$run_dir"
  "$(realpath "$repo_root/$exe")" "input.$case_name"
) >"$log_file" 2>&1

initial_plot="$run_dir/plt00000"
final_plot="$run_dir/plt01000"
if [[ ! -d "$final_plot" ]]; then
  final_plot=$(find "$run_dir" -maxdepth 1 -type d -name 'plt[0-9][0-9][0-9][0-9][0-9]' | sort | tail -n 1)
fi

python3 tools/validate_academic_droplet_euler_lagrange.py \
  --input "$input_file" \
  --run-log "$log_file" \
  --initial "$initial_plot" \
  --final "$final_plot" >"$validation_log"

python3 - "$manifest" "$case_name" "$input_file" "$log_file" "$validation_log" "$initial_plot" "$final_plot" <<'PY'
from pathlib import Path
import json
import sys

manifest, case_name, input_file, log_file, validation_log, initial_plot, final_plot = sys.argv[1:]
data = {
    'schema_version': 1,
    'cases': [
        {
            'name': case_name,
            'role': 'spray_particle_khrt_breakup_motion_coupling',
            'input_file': input_file,
            'run_log': log_file,
            'validation_log': validation_log,
            'plotfile_initial': initial_plot,
            'plotfile_final': final_plot,
        }
    ],
}
path = Path(manifest)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
PY

python3 tools/write_academic_droplet_euler_lagrange_validation_report.py \
  --manifest "$manifest" \
  --output-json "$root/academic_droplet_euler_lagrange_validation_report.json" \
  --output-md "$root/academic_droplet_euler_lagrange_validation_report.md"

python3 tools/write_academic_droplet_euler_lagrange_validation_report.py \
  --verify-json "$root/academic_droplet_euler_lagrange_validation_report.json"

printf 'academic_droplet_euler_lagrange_validation RUNNER-PASS root=%s case=%s final_plot=%s\n' "$root" "$case_name" "$final_plot"
