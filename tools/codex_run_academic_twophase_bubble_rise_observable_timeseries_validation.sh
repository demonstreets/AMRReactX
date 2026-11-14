#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root="${CODEX_ACADEMIC_TWOPHASE_BUBBLE_OBS_TS_ROOT:-docs/codex_audit/evidence/academic_twophase_bubble_rise_observable_timeseries_20260729}"
case_src="examples/academic/bubble_rise"
case_name="bubble_rise_buoyancy_mol_30000step_sampled_observables"
case_root="$root/$case_name"
run_dir="$case_root/run"
input_file="$run_dir/input.codex_bubble_rise_observable_timeseries"
build_log="$case_root/build.log"
run_log="$case_root/run.log"
validation_log="$case_root/validation.log"
initial_plot="$run_dir/plt00000"
final_plot="$run_dir/plt30000"
observables_json="$root/academic_twophase_bubble_rise_observable_timeseries_report.json"
observables_md="$root/academic_twophase_bubble_rise_observable_timeseries_report.md"
bubble_report="docs/codex_audit/evidence/academic_twophase_bubble_rise_mol_long_window_validation_20260729/academic_twophase_bubble_rise_mol_long_window_validation_report.json"

mkdir -p "$root"
if [[ "$case_root" != "$root/"* ]]; then
  printf '[academic-twophase-bubble-rise-observable-timeseries] refusing unsafe case_root=%s root=%s\n' "$case_root" "$root" >&2
  exit 2
fi
rm -rf "$case_root"
mkdir -p "$run_dir"

printf '[academic-twophase-bubble-rise-observable-timeseries] building bubble_rise case\n'
(cd "$case_src" && make -j "${JOBS:-4}" >"$repo_root/$build_log" 2>&1)

python3 - <<'PY' "$case_src/inputs" "$input_file"
from pathlib import Path
import sys

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')
replacements = {
    'max_step = 200': 'max_step = 30000',
    'stop_time = 0.05': 'stop_time = 1.0e-3',
    'pelec.do_mol = 1': 'pelec.do_mol = 1',
    'pelec.cfl = 0.2': 'pelec.cfl = 0.025',
    'amr.plot_int = 200': 'amr.plot_int = 2000',
    'prob.interface_width = 0.0': 'prob.interface_width = 0.0125',
    'prob.buoyancy_terminal_speed = -1.0': 'prob.buoyancy_terminal_speed = -1.0',
    'prob.positivity_rhoe_floor = -1.0': 'prob.positivity_rhoe_floor = 1.0e-8',
    'prob.positivity_temp_floor = -1.0': 'prob.positivity_temp_floor = 1.0e-8',
    'prob.p0 = 1.0': 'prob.p0 = 1.0',
}
for old, new in replacements.items():
    text = text.replace(old, new)
if 'pelec.add_ext_src' not in text:
    text = text.replace('pelec.do_react = 0', 'pelec.do_react = 0\npelec.add_ext_src = 1')
if 'prob.buoyancy_accel' not in text:
    text += '\nprob.buoyancy_accel = 9.81\n'
if 'prob.buoyancy_start_time' not in text:
    text += 'prob.buoyancy_start_time = 0.0\n'
if 'prob.buoyancy_end_time' not in text:
    text += 'prob.buoyancy_end_time = 1.0e200\n'
if 'prob.buoyancy_ramp_time' not in text:
    text += 'prob.buoyancy_ramp_time = 0.0\n'
if 'prob.buoyancy_terminal_speed' not in text:
    text += 'prob.buoyancy_terminal_speed = -1.0\n'
dst.write_text(text, encoding='utf-8')
PY

cp "$case_src/PeleC2d.gnu.ex" "$run_dir/"

printf '[academic-twophase-bubble-rise-observable-timeseries] running %s\n' "$case_name"
set +e
(cd "$run_dir" && timeout "${RUN_TIMEOUT:-300}" ./PeleC2d.gnu.ex "$(basename "$input_file")" >"$repo_root/$run_log" 2>&1)
run_rc=$?
set -e

python3 - <<'PY' "$repo_root" "$build_log" "$run_log"
import sys
from pathlib import Path

repo_root = sys.argv[1].rstrip('/') + '/'
for name in sys.argv[2:]:
    path = Path(name)
    if path.is_file():
        path.write_text(path.read_text(encoding='utf-8', errors='replace').replace(repo_root, ''), encoding='utf-8')
PY

if [[ "$run_rc" -eq 0 && -d "$initial_plot" && -d "$final_plot" ]]; then
  set +e
  python3 tools/validate_academic_twophase_bubble_rise.py \
    --initial-plotfile "$initial_plot" \
    --final-plotfile "$final_plot" \
    --min-final-time 1.5e-4 \
    --min-centroid-rise 2.0e-10 \
    --max-mass-rel-drift 1.0e-10 \
    --max-adv-mass-rel-drift 1.0e-10 \
    >"$validation_log" 2>&1
  validation_rc=$?
  set -e
else
  validation_rc=2
  printf 'academic_twophase_bubble_rise_observable_timeseries FAIL run_returncode=%s initial_plot=%s final_plot=%s\n' \
    "$run_rc" "$initial_plot" "$final_plot" >"$validation_log"
fi
cat "$validation_log"

python3 - <<'PY' "$case_root/case_summary.json" "$case_name" "$input_file" "$build_log" "$run_log" "$validation_log" "$initial_plot" "$final_plot" "$run_rc" "$validation_rc"
import json
import sys
from pathlib import Path

out, case_name, input_file, build_log, run_log, validation_log, initial_plot, final_plot, run_rc, validation_rc = sys.argv[1:]
summary = {
    'case_name': case_name,
    'role': 'academic_twophase_bubble_rise_observable_timeseries',
    'solver': 'PeleC',
    'dimension': 2,
    'backend': 'CPU-serial',
    'input_file': input_file,
    'build_log': build_log,
    'run_log': run_log,
    'validation_log': validation_log,
    'initial_plot': initial_plot,
    'final_plot': final_plot,
    'run_returncode': int(run_rc),
    'validation_returncode': int(validation_rc),
    'max_step': 30000,
    'plot_int': 2000,
    'expected_plot_samples': 16,
    'cfl': 0.025,
    'do_mol': 1,
    'p0': 1.0,
    'buoyancy_accel': 9.81,
    'buoyancy_terminal_speed': -1.0,
    'interface_width': 0.0125,
    'positivity_rhoe_floor': 1.0e-8,
    'positivity_temp_floor': 1.0e-8,
}
Path(out).write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
PY

python3 tools/write_academic_twophase_bubble_rise_observables_report.py \
  --run-dir "$run_dir" \
  --bubble-report "$bubble_report" \
  --output-json "$observables_json" \
  --output-md "$observables_md"
python3 tools/write_academic_twophase_bubble_rise_observables_report.py \
  --verify-json "$observables_json"

printf '[academic-twophase-bubble-rise-observable-timeseries] COMPLETE root=%s run_rc=%s validation_rc=%s\n' "$root" "$run_rc" "$validation_rc"
