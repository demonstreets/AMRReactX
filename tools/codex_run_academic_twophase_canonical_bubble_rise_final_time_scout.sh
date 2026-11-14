#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

root="${CODEX_ACADEMIC_TWOPHASE_CANONICAL_BUBBLE_FINAL_TIME_SCOUT_ROOT:-docs/codex_audit/evidence/academic_twophase_canonical_bubble_rise_final_time_scout_20260730}"
case_src="examples/academic/bubble_rise"
case_name="canonical_bubble_rise_csf_viscosity_5000step_final_time_scout"
case_root="$root/$case_name"
run_dir="$case_root/run"
input_file="$run_dir/input.canonical_bubble_rise_final_time_scout"
build_log="$case_root/build.log"
run_log="$case_root/run.log"
validation_log="$case_root/validation.log"
report_json="$root/canonical_bubble_rise_final_time_scout_report.json"
report_md="$root/canonical_bubble_rise_final_time_scout_report.md"
max_step="${CODEX_CANONICAL_BUBBLE_FINAL_TIME_SCOUT_MAX_STEP:-5000}"
plot_int="$max_step"
target_stop_time="${CODEX_CANONICAL_BUBBLE_FINAL_TIME_SCOUT_STOP_TIME:-3.0}"
scout_cfl="${CODEX_CANONICAL_BUBBLE_FINAL_TIME_SCOUT_CFL:-0.01}"
surface_tension_force_cap="${CODEX_CANONICAL_BUBBLE_FINAL_TIME_SCOUT_SURFACE_TENSION_FORCE_CAP:-1.0}"
phase_viscosity_force_cap="${CODEX_CANONICAL_BUBBLE_FINAL_TIME_SCOUT_PHASE_VISCOSITY_FORCE_CAP:-0.1}"

mkdir -p "$root"
if [[ "$case_root" != "$root/"* ]]; then
  printf '[academic-twophase-canonical-bubble-final-time-scout] refusing unsafe case_root=%s root=%s\n' "$case_root" "$root" >&2
  exit 2
fi
rm -rf "$case_root"
mkdir -p "$run_dir"

printf '[academic-twophase-canonical-bubble-final-time-scout] building bubble_rise case\n'
(cd "$case_src" && make -j "${JOBS:-4}" >"$repo_root/$build_log" 2>&1)

python3 - <<'PY' "$case_src/inputs" "$input_file" "$max_step" "$plot_int" "$target_stop_time" "$scout_cfl" "$surface_tension_force_cap" "$phase_viscosity_force_cap"
from pathlib import Path
import sys

src, dst, max_step, plot_int, target_stop_time, scout_cfl, surface_tension_force_cap, phase_viscosity_force_cap = sys.argv[1:]
text = Path(src).read_text(encoding="utf-8")
replacements = {
    "max_step = 200": f"max_step = {max_step}",
    "stop_time = 0.05": f"stop_time = {target_stop_time}",
    "geometry.prob_hi = 0.2 0.4 0.002": "geometry.prob_hi = 1.0 2.0 0.002",
    "amr.n_cell = 32 64 1": "amr.n_cell = 32 64 1",
    "amr.max_level = 0": "amr.max_level = 0",
    "pelec.cfl = 0.2": f"pelec.cfl = {scout_cfl}",
    "amr.plot_int = 200": f"amr.plot_int = {plot_int}",
    "prob.bubble_cx = 0.1": "prob.bubble_cx = 0.5",
    "prob.bubble_cy = 0.1": "prob.bubble_cy = 0.5",
    "prob.bubble_r = 0.025": "prob.bubble_r = 0.25",
    "prob.interface_width = 0.0": "prob.interface_width = 0.03125",
    "prob.rho_heavy = 1.0": "prob.rho_heavy = 1.0",
    "prob.rho_light = 0.1": "prob.rho_light = 0.1",
    "prob.buoyancy_accel = 9.81": "prob.buoyancy_accel = 0.98",
    "prob.buoyancy_terminal_speed = -1.0": "prob.buoyancy_terminal_speed = -1.0",
    "prob.positivity_rhoe_floor = -1.0": "prob.positivity_rhoe_floor = 1.0e-8",
    "prob.buoyancy_energy_correction = 1.0": f"prob.buoyancy_energy_correction = 1.0\nprob.surface_tension_sigma = 24.5\nprob.surface_tension_grad_floor = 1.0e-10\nprob.surface_tension_force_cap = {surface_tension_force_cap}\nprob.phase_viscosity_mu_heavy = 10.0\nprob.phase_viscosity_mu_light = 1.0\nprob.phase_viscosity_force_cap = {phase_viscosity_force_cap}",
    "prob.positivity_temp_floor = -1.0": "prob.positivity_temp_floor = 1.0e-8",
}
for old, new in replacements.items():
    text = text.replace(old, new)
if "pelec.add_ext_src" not in text:
    text = text.replace("pelec.do_react = 0", "pelec.do_react = 0\npelec.add_ext_src = 1")
Path(dst).write_text(text, encoding="utf-8")
PY

cp "$case_src/PeleC2d.gnu.ex" "$run_dir/"

printf '[academic-twophase-canonical-bubble-final-time-scout] running %s max_step=%s stop_time=%s\n' "$case_name" "$max_step" "$target_stop_time"
start_epoch=$(date +%s)
set +e
(cd "$run_dir" && timeout "${RUN_TIMEOUT:-600}" ./PeleC2d.gnu.ex "$(basename "$input_file")" >"$repo_root/$run_log" 2>&1)
run_rc=$?
set -e
end_epoch=$(date +%s)
wall_seconds=$((end_epoch - start_epoch))

initial_plot="$run_dir/plt00000"
final_plot=$(find "$run_dir" -maxdepth 1 -type d -name 'plt*' | sort | tail -n 1)

if [[ "$run_rc" -eq 0 && -d "$initial_plot" && -d "$final_plot" ]]; then
  set +e
  python3 tools/validate_academic_twophase_bubble_rise.py \
    --initial-plotfile "$initial_plot" \
    --final-plotfile "$final_plot" \
    --min-final-time 5.0e-5 \
    --min-centroid-rise=-1.0e-6 \
    --max-mass-rel-drift 1.0e-10 \
    --max-adv-mass-rel-drift 1.0e-10 \
    --min-ymom-sum=-1.0e-6 \
    >"$validation_log" 2>&1
  validation_rc=$?
  set -e
else
  validation_rc=2
  printf 'academic_twophase_canonical_bubble_rise_final_time_scout FAIL run_returncode=%s initial_plot=%s final_plot=%s\n' \
    "$run_rc" "$initial_plot" "$final_plot" >"$validation_log"
fi
cat "$validation_log"

python3 - <<'PY' "$case_root/case_summary.json" "$case_name" "$input_file" "$build_log" "$run_log" "$validation_log" "$initial_plot" "$final_plot" "$run_rc" "$validation_rc" "$wall_seconds" "$max_step" "$target_stop_time" "$scout_cfl" "$surface_tension_force_cap" "$phase_viscosity_force_cap"
import json
from pathlib import Path
import sys

(
    out,
    case_name,
    input_file,
    build_log,
    run_log,
    validation_log,
    initial_plot,
    final_plot,
    run_rc,
    validation_rc,
    wall_seconds,
    max_step,
    target_stop_time,
    scout_cfl,
    surface_tension_force_cap,
    phase_viscosity_force_cap,
) = sys.argv[1:]
summary = {
    "case_name": case_name,
    "role": "academic_twophase_canonical_bubble_rise_final_time_scout",
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
    "wall_seconds": int(wall_seconds),
    "max_step": int(max_step),
    "target_stop_time": float(target_stop_time),
    "domain": [1.0, 2.0],
    "grid": [32, 64, 1],
    "bubble_center": [0.5, 0.5],
    "bubble_radius": 0.25,
    "density_ratio_heavy_over_light": 10.0,
    "gravity": 0.98,
    "surface_tension_sigma": 24.5,
    "surface_tension_force_cap": float(surface_tension_force_cap),
    "phase_viscosity_mu_heavy": 10.0,
    "phase_viscosity_mu_light": 1.0,
    "phase_viscosity_force_cap": float(phase_viscosity_force_cap),
    "cfl": float(scout_cfl),
    "do_mol": 1,
    "interface_width": 0.03125,
    "positivity_rhoe_floor": 1.0e-8,
    "positivity_temp_floor": 1.0e-8,
}
Path(out).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

python3 tools/write_academic_twophase_canonical_bubble_rise_final_time_scout_report.py \
  --case-summary "$case_root/case_summary.json" \
  --output-json "$report_json" \
  --output-md "$report_md"
python3 tools/write_academic_twophase_canonical_bubble_rise_final_time_scout_report.py \
  --verify-json "$report_json"

printf '[academic-twophase-canonical-bubble-final-time-scout] COMPLETE root=%s run_rc=%s validation_rc=%s wall_seconds=%s\n' "$root" "$run_rc" "$validation_rc" "$wall_seconds"
