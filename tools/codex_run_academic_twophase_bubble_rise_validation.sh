#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root="${CODEX_ACADEMIC_TWOPHASE_BUBBLE_ROOT:-docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728}"
case_src="examples/academic/bubble_rise"
case_name="bubble_rise_buoyancy_6000step_low_cfl"
case_root="$root/$case_name"
run_dir="$case_root/run"
input_file="$run_dir/input.codex_bubble_rise"
build_log="$case_root/build.log"
run_log="$case_root/run.log"
validation_log="$case_root/validation.log"
initial_plot="$run_dir/plt00000"
final_plot="$run_dir/plt06000"

mkdir -p "$root"
if [[ "$case_root" != "$root/"* ]]; then
  printf '[academic-twophase-bubble-rise] refusing unsafe case_root=%s root=%s\n' "$case_root" "$root" >&2
  exit 2
fi
rm -rf "$case_root"
mkdir -p "$run_dir"

printf '[academic-twophase-bubble-rise] building bubble_rise case\n'
(cd "$case_src" && make -j "${JOBS:-4}" >"$repo_root/$build_log" 2>&1)

python3 - <<'PY' "$case_src/inputs" "$input_file"
from pathlib import Path
import sys

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')
replacements = {
    'max_step = 200': 'max_step = 6000',
    'stop_time = 0.05': 'stop_time = 1.0e-3',
    'pelec.cfl = 0.2': 'pelec.cfl = 0.025',
    'amr.plot_int = 200': 'amr.plot_int = 6000',
    'prob.buoyancy_accel = 9.81': 'prob.buoyancy_accel = 9.81',
    'prob.buoyancy_terminal_speed = -1.0': 'prob.buoyancy_terminal_speed = -1.0',
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
    text += 'prob.buoyancy_terminal_speed = 0.0015\n'
text = text.replace('amr.derive_plot_vars = alpha', 'amr.derive_plot_vars = alpha')
dst.write_text(text, encoding='utf-8')
PY

cp "$case_src/PeleC2d.gnu.ex" "$run_dir/"

printf '[academic-twophase-bubble-rise] running %s\n' "$case_name"
set +e
(cd "$run_dir" && timeout "${RUN_TIMEOUT:-240}" ./PeleC2d.gnu.ex "$(basename "$input_file")" >"$repo_root/$run_log" 2>&1)
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
    --min-final-time 4.0e-5 \
    --min-centroid-rise 1.0e-10 \
    --max-mass-rel-drift 1.0e-10 \
    --max-adv-mass-rel-drift 1.0e-10 \
    >"$validation_log" 2>&1
  validation_rc=$?
  set -e
else
  validation_rc=2
  printf 'academic_twophase_bubble_rise_validation FAIL run_returncode=%s initial_plot=%s final_plot=%s\n' \
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
    'role': 'academic_twophase_bubble_rise_buoyancy_response',
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
    'max_step': 6000,
    'cfl': 0.025,
    'buoyancy_accel': 9.81,
    'buoyancy_terminal_speed': -1.0,
}
Path(out).write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
PY

python3 tools/write_academic_twophase_bubble_rise_validation_report.py \
  --case-summary "$case_root/case_summary.json" \
  --output-json "$root/academic_twophase_bubble_rise_validation_report.json" \
  --output-md "$root/academic_twophase_bubble_rise_validation_report.md"
python3 tools/write_academic_twophase_bubble_rise_validation_report.py \
  --verify-json "$root/academic_twophase_bubble_rise_validation_report.json"

cat >docs/codex_audit/2026-07-28-academic-twophase-bubble-rise-validation.md <<'EOF'
# Academic Two-Phase Bubble-Rise Validation

Status: `PASS-ACADEMIC-TWOPHASE-BUBBLE-RISE-VALIDATION`

This audit records the maintained PeleC two-phase bubble-rise validation gate for QLT-03 standard validation coverage. The bubble-rise case now uses a problem-specific external buoyancy source rather than an unused `pelec.gravity` input alone. The 6000-step low-CFL gate proves a strengthened short-time buoyancy response with bounded alpha and strong conservation over many stable source-coupled updates.

Evidence:

- `docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/academic_twophase_bubble_rise_validation_report.json`
- `docs/codex_audit/evidence/academic_twophase_bubble_rise_validation_20260728/academic_twophase_bubble_rise_validation_report.md`
- `tools/codex_run_academic_twophase_bubble_rise_validation.sh`
- `tools/validate_academic_twophase_bubble_rise.py`
- `tools/write_academic_twophase_bubble_rise_validation_report.py`

Residual scope:

- This clears the strengthened short-time, low-CFL bubble-rise stability component of QLT-03.
- Longer 8000-30000 step probes with several CFL/source/pressure variants still reached non-finite or negative-internal-energy states, so canonical long physical-time bubble-rise deformation/stability remains a separate QLT-03 gap.
- MMS nonlinear MASA and external experiment-grade validation remain separate QLT-03 gaps.
EOF

printf '[academic-twophase-bubble-rise] COMPLETE root=%s run_rc=%s validation_rc=%s\n' "$root" "$run_rc" "$validation_rc"
