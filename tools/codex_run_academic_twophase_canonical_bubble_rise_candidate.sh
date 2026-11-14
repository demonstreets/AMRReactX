#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root="${CODEX_ACADEMIC_TWOPHASE_CANONICAL_BUBBLE_CANDIDATE_ROOT:-docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_candidate_20260730}"
case_src="examples/academic/bubble_rise"
case_name="canonical_bubble_rise_geometry_gravity_csf_viscosity_1000step_smoke"
case_root="$root/$case_name"
run_dir="$case_root/run"
input_file="$run_dir/input.canonical_bubble_rise_candidate"
build_log="$case_root/build.log"
run_log="$case_root/run.log"
validation_log="$case_root/validation.log"
initial_plot="$run_dir/plt00000"
final_plot="$run_dir/plt01000"
report_json="$root/canonical_bubble_rise_candidate_report.json"
report_md="$root/canonical_bubble_rise_candidate_report.md"

mkdir -p "$root"
if [[ "$case_root" != "$root/"* ]]; then
  printf '[academic-twophase-canonical-bubble-candidate] refusing unsafe case_root=%s root=%s\n' "$case_root" "$root" >&2
  exit 2
fi
rm -rf "$case_root"
mkdir -p "$run_dir"

printf '[academic-twophase-canonical-bubble-candidate] building bubble_rise case\n'
(cd "$case_src" && make -j "${JOBS:-4}" >"$repo_root/$build_log" 2>&1)

python3 - <<'PY' "$case_src/inputs" "$input_file"
from pathlib import Path
import sys

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(encoding="utf-8")
replacements = {
    "max_step = 200": "max_step = 1000",
    "stop_time = 0.05": "stop_time = 1.0e-3",
    "geometry.prob_hi = 0.2 0.4 0.002": "geometry.prob_hi = 1.0 2.0 0.002",
    "amr.n_cell = 32 64 1": "amr.n_cell = 32 64 1",
    "pelec.do_mol = 1": "pelec.do_mol = 1",
    "pelec.cfl = 0.2": "pelec.cfl = 0.025",
    "amr.plot_int = 200": "amr.plot_int = 1000",
    "prob.bubble_cx = 0.1": "prob.bubble_cx = 0.5",
    "prob.bubble_cy = 0.1": "prob.bubble_cy = 0.5",
    "prob.bubble_r = 0.025": "prob.bubble_r = 0.25",
    "prob.interface_width = 0.0": "prob.interface_width = 0.03125",
    "prob.buoyancy_accel = 9.81": "prob.buoyancy_accel = 0.98",
    "prob.buoyancy_terminal_speed = -1.0": "prob.buoyancy_terminal_speed = -1.0",
    "prob.positivity_rhoe_floor = -1.0": "prob.positivity_rhoe_floor = 1.0e-8",
    "prob.buoyancy_energy_correction = 1.0": "prob.buoyancy_energy_correction = 1.0\nprob.surface_tension_sigma = 24.5\nprob.surface_tension_grad_floor = 1.0e-10\nprob.surface_tension_force_cap = 1.0e1\nprob.phase_viscosity_mu_heavy = 10.0\nprob.phase_viscosity_mu_light = 1.0\nprob.phase_viscosity_force_cap = 1.0",
    "prob.positivity_temp_floor = -1.0": "prob.positivity_temp_floor = 1.0e-8",
}
for old, new in replacements.items():
    text = text.replace(old, new)
if "pelec.add_ext_src" not in text:
    text = text.replace("pelec.do_react = 0", "pelec.do_react = 0\npelec.add_ext_src = 1")
dst.write_text(text, encoding="utf-8")
PY

cp "$case_src/PeleC2d.gnu.ex" "$run_dir/"

printf '[academic-twophase-canonical-bubble-candidate] running %s\n' "$case_name"
set +e
(cd "$run_dir" && timeout "${RUN_TIMEOUT:-240}" ./PeleC2d.gnu.ex "$(basename "$input_file")" >"$repo_root/$run_log" 2>&1)
run_rc=$?
set -e

python3 - <<'PY' "$repo_root" "$build_log" "$run_log"
import sys
from pathlib import Path

repo_root = sys.argv[1].rstrip("/") + "/"
for name in sys.argv[2:]:
    path = Path(name)
    if path.is_file():
        path.write_text(path.read_text(encoding="utf-8", errors="replace").replace(repo_root, ""), encoding="utf-8")
PY

if [[ "$run_rc" -eq 0 && -d "$initial_plot" && -d "$final_plot" ]]; then
  set +e
  python3 tools/validate_academic_twophase_bubble_rise.py \
    --initial-plotfile "$initial_plot" \
    --final-plotfile "$final_plot" \
    --min-final-time 2.0e-5 \
    --min-centroid-rise=-1.0e-7 \
    --max-mass-rel-drift 1.0e-10 \
    --max-adv-mass-rel-drift 1.0e-10 \
    >"$validation_log" 2>&1
  validation_rc=$?
  set -e
else
  validation_rc=2
  printf 'academic_twophase_canonical_bubble_rise_candidate FAIL run_returncode=%s initial_plot=%s final_plot=%s\n' \
    "$run_rc" "$initial_plot" "$final_plot" >"$validation_log"
fi
cat "$validation_log"

python3 - <<'PY' "$case_root/case_summary.json" "$case_name" "$input_file" "$build_log" "$run_log" "$validation_log" "$initial_plot" "$final_plot" "$run_rc" "$validation_rc"
import json
import sys
from pathlib import Path

out, case_name, input_file, build_log, run_log, validation_log, initial_plot, final_plot, run_rc, validation_rc = sys.argv[1:]
summary = {
    "case_name": case_name,
    "role": "academic_twophase_canonical_bubble_rise_geometry_gravity_candidate",
    "solver": "PeleC",
    "dimension": 2,
    "backend": "CPU-serial",
    "input_file": input_file,
    "build_log": build_log,
    "run_log": run_log,
    "validation_log": validation_log,
    "initial_plot": initial_plot,
    "final_plot": final_plot,
    "run_returncode": int(run_rc),
    "validation_returncode": int(validation_rc),
    "max_step": 1000,
    "plot_int": 1000,
    "expected_plot_samples": 2,
    "stop_time": 1.0e-3,
    "domain": [1.0, 2.0],
    "grid": [32, 64],
    "bubble_center": [0.5, 0.5],
    "bubble_radius": 0.25,
    "density_ratio_heavy_over_light": 10.0,
    "gravity": 0.98,
    "surface_tension_sigma": 24.5,
    "surface_tension_force_cap": 1.0e1,
    "phase_viscosity_mu_heavy": 10.0,
    "phase_viscosity_mu_light": 1.0,
    "phase_viscosity_force_cap": 1.0,
    "cfl": 0.025,
    "do_mol": 1,
    "interface_width": 0.03125,
    "positivity_rhoe_floor": 1.0e-8,
    "positivity_temp_floor": 1.0e-8,
}
Path(out).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

python3 tools/write_academic_twophase_canonical_bubble_rise_candidate_report.py \
  --case-summary "$case_root/case_summary.json" \
  --output-json "$report_json" \
  --output-md "$report_md"
python3 tools/write_academic_twophase_canonical_bubble_rise_candidate_report.py \
  --verify-json "$report_json"

printf '[academic-twophase-canonical-bubble-candidate] COMPLETE root=%s run_rc=%s validation_rc=%s\n' "$root" "$run_rc" "$validation_rc"
