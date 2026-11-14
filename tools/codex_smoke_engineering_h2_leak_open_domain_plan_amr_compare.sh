#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_root="${CODEX_H2_LEAK_PLAN_AMR_COMPARE_LOG_DIR:-/tmp/codex_h2_leak_open_domain_plan_amr_compare_$(date -u +%Y%m%dT%H%M%SZ)}"
input_dir="$log_root/inputs"
base_input="$repo_root/examples/engineering/h2_leak_3d/input.codex_open_domain_flammable_smoke"
baseline_input="$input_dir/input.codex_open_domain_plan_amr_baseline_smoke"
amr_input="$input_dir/input.codex_open_domain_plan_amr_level1_smoke"
summary_csv="$log_root/plan_amr_compare_summary.csv"
overhead_csv="$log_root/amr_overhead_summary.csv"
reuse_existing="${CODEX_H2_LEAK_PLAN_AMR_COMPARE_REUSE_EXISTING:-FALSE}"
plan_species_gradient="${CODEX_H2_LEAK_PLAN_AMR_SPECIES_GRADIENT:-2.0e-2}"
plan_max_step="${CODEX_H2_LEAK_PLAN_AMR_MAX_STEP:-100}"
plan_plot_int="${CODEX_H2_LEAK_PLAN_AMR_PLOT_INT:-20}"
plan_min_plotfiles="${CODEX_H2_LEAK_PLAN_AMR_MIN_PLOTFILES:-6}"
plan_min_mass_growth_ratio="${CODEX_H2_LEAK_PLAN_AMR_MIN_MASS_GROWTH_RATIO:-4.0}"
plan_max_mass_drop_ratio="${CODEX_H2_LEAK_PLAN_AMR_MAX_MASS_DROP_RATIO:-1.0e-6}"
plan_min_final_mass_ratio="${CODEX_H2_LEAK_PLAN_AMR_MIN_FINAL_MASS_RATIO:-0.80}"
plan_max_final_mass_ratio="${CODEX_H2_LEAK_PLAN_AMR_MAX_FINAL_MASS_RATIO:-1.20}"
plan_min_upstream_fraction="${CODEX_H2_LEAK_PLAN_AMR_MIN_UPSTREAM_FRACTION:-0.0}"
plan_min_plane_mass_fraction="${CODEX_H2_LEAK_PLAN_AMR_MIN_PLANE_MASS_FRACTION:-0.005}"
plan_min_active_planes="${CODEX_H2_LEAK_PLAN_AMR_MIN_ACTIVE_PLANES:-3}"
plan_min_flammable_planes="${CODEX_H2_LEAK_PLAN_AMR_MIN_FLAMMABLE_PLANES:-1}"
plan_base_max_grid_size="${CODEX_H2_LEAK_PLAN_AMR_BASE_MAX_GRID_SIZE:-32}"
plan_amr_max_grid_size="${CODEX_H2_LEAK_PLAN_AMR_LEVEL1_MAX_GRID_SIZE:-16}"
plan_n_cell="${CODEX_H2_LEAK_PLAN_AMR_N_CELL:-}"
plan_prob_hi="${CODEX_H2_LEAK_PLAN_AMR_PROB_HI:-}"

mkdir -p "$input_dir"
python3 - "$base_input" "$baseline_input" "$amr_input" "$plan_species_gradient" "$plan_max_step" "$plan_plot_int" "$plan_base_max_grid_size" "$plan_amr_max_grid_size" "$plan_n_cell" "$plan_prob_hi" <<'PYINPUT'
import sys
from pathlib import Path

base = Path(sys.argv[1])
baseline = Path(sys.argv[2])
amr = Path(sys.argv[3])
plan_species_gradient = sys.argv[4]
plan_max_step = sys.argv[5]
plan_plot_int = sys.argv[6]
plan_base_max_grid_size = sys.argv[7]
plan_amr_max_grid_size = sys.argv[8]
plan_n_cell = sys.argv[9].strip()
plan_prob_hi = sys.argv[10].strip()
text = base.read_text(encoding='utf-8')

def replace_setting(lines, key, value):
    out = []
    replaced = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(key):
            out.append(f'{key} = {value}')
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f'{key} = {value}')
    return out

base_lines = text.splitlines()
common = replace_setting(base_lines, 'amr.max_step', plan_max_step)
common = replace_setting(common, 'amr.plot_int', plan_plot_int)
common = replace_setting(common, 'amr.max_grid_size', plan_base_max_grid_size)
common = replace_setting(common, 'amr.blocking_factor', '4')
if plan_n_cell:
    common = replace_setting(common, 'amr.n_cell', plan_n_cell)
if plan_prob_hi:
    common = replace_setting(common, 'geometry.prob_hi', plan_prob_hi)

baseline_lines = replace_setting(common, 'amr.max_level', '0')
baseline.write_text('\n'.join(baseline_lines) + '\n', encoding='utf-8')

amr_lines = replace_setting(common, 'amr.max_level', '1')
amr_lines = replace_setting(amr_lines, 'amr.max_grid_size', plan_amr_max_grid_size)
amr_lines.extend([
    '',
    '# Codex plan-AMR smoke: dynamically refine H2 species-gradient regions.',
    'amr.ref_ratio = 2 2 2 2',
    'amr.regrid_int = 2',
    'amr.n_error_buf = 1 1 1 1',
    'amr.grid_eff = 0.7',
    'amr.plan_tagging = 1',
    'amr.plan_max_level = 0',
    'amr.plan_velocity_gradient = 1.0e30',
    'amr.plan_temperature_gradient = 1.0e30',
    f'amr.plan_species_gradient = {plan_species_gradient}',
    'amr.plan_interface_curvature = 1.0e30',
])
amr.write_text('\n'.join(amr_lines) + '\n', encoding='utf-8')
PYINPUT

run_case() {
  local name=$1
  local input=$2
  local log_dir=$3
  CODEX_H2_LEAK_PROFILE_INPUT="$input" \
  CODEX_H2_LEAK_OPEN_DOMAIN_LOG_DIR="$log_dir" \
  CODEX_H2_LEAK_MIN_TIMESERIES_PLOTFILES="$plan_min_plotfiles" \
  CODEX_H2_LEAK_HISTORY_MIN_PLOTFILES="$plan_min_plotfiles" \
  CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="$plan_min_mass_growth_ratio" \
  CODEX_H2_LEAK_HISTORY_MAX_MASS_DROP_RATIO="$plan_max_mass_drop_ratio" \
  CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO="$plan_min_final_mass_ratio" \
  CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO="$plan_max_final_mass_ratio" \
  CODEX_H2_LEAK_HISTORY_MIN_UPSTREAM_FRACTION="$plan_min_upstream_fraction" \
  CODEX_H2_LEAK_PROFILE_MIN_FINAL_MASS_RATIO="$plan_min_final_mass_ratio" \
  CODEX_H2_LEAK_PROFILE_MAX_FINAL_MASS_RATIO="$plan_max_final_mass_ratio" \
  CODEX_H2_LEAK_TIMESERIES_MAX_MASS_DROP_RATIO="$plan_max_mass_drop_ratio" \
  CODEX_H2_LEAK_PROFILE_MIN_PLANE_MASS_FRACTION="$plan_min_plane_mass_fraction" \
  CODEX_H2_LEAK_MIN_ACTIVE_PLANES="$plan_min_active_planes" \
  CODEX_H2_LEAK_MIN_FLAMMABLE_PLANES="$plan_min_flammable_planes" \
  CODEX_H2_LEAK_MIN_FLAMMABLE_VOLUME=2.0e-4 \
  CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME=2.5e-1 \
  RUN_TIMEOUT="${RUN_TIMEOUT:-900}" \
  JOBS="${JOBS:-4}" \
    "$repo_root/tools/codex_smoke_engineering_h2_leak_open_domain.sh"
  printf '[codex-smoke] completed %s log_dir=%s\n' "$name" "$log_dir"
}

if [[ "$reuse_existing" == TRUE ]]; then
  printf '[codex-smoke] reusing existing plan-AMR case outputs root=%s\n' "$log_root"
else
  run_case baseline "$baseline_input" "$log_root/baseline"
  run_case amr "$amr_input" "$log_root/amr"
fi

python3 - "$repo_root" "$log_root" "$baseline_input" "$amr_input" "$summary_csv" "$plan_species_gradient" "$plan_min_active_planes" "$plan_min_flammable_planes" "$plan_min_final_mass_ratio" "$plan_max_final_mass_ratio" <<'PYCHECK'
import csv
import re
import sys
from pathlib import Path

repo = Path(sys.argv[1])
log_root = Path(sys.argv[2])
baseline_input = Path(sys.argv[3])
amr_input = Path(sys.argv[4])
summary = Path(sys.argv[5])
plan_species_gradient = sys.argv[6]
min_active_planes = int(sys.argv[7])
min_flammable_planes = int(sys.argv[8])
min_final_mass_ratio = float(sys.argv[9])
max_final_mass_ratio = float(sys.argv[10])
sys.path.insert(0, str(repo / 'tools'))
import amrex_reader  # noqa: E402


def grab(pattern, text, label):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f'FAIL: missing {label}')
    return m.group(1)


def read_text(path):
    return Path(path).read_text(encoding='utf-8', errors='replace')


def parse_case(name, input_path):
    case_dir = log_root / name
    run_dir = case_dir / 'run'
    copied_input = run_dir / input_path.name
    if not copied_input.is_file():
        raise SystemExit(f'FAIL: missing copied input for {name}: {copied_input}')
    input_text = read_text(copied_input)
    max_step = int(grab(r'amr\.max_step\s*=\s*([0-9]+)', input_text, f'{name} max_step'))
    plot = run_dir / f'plt{max_step:05d}'
    if not plot.is_dir():
        raise SystemExit(f'FAIL: missing final plotfile for {name}: {plot}')
    meta = amrex_reader._parse_header(str(plot / 'Header'))
    cell_h = plot / f'Level_{meta["finest_level"]}' / 'Cell_H'
    if not cell_h.is_file():
        raise SystemExit(f'FAIL: missing finest Cell_H for {name}: {cell_h}')
    fab_count = sum(1 for line in read_text(cell_h).splitlines()
                    if line.strip().startswith('FabOnDisk:'))
    validation = read_text(case_dir / 'validation.log')
    profile = read_text(case_dir / 'profile_validation.log')
    hazard = read_text(case_dir / 'hazard_summary.log')
    planes = read_text(case_dir / 'hazard_planes.log')
    timeseries = read_text(case_dir / 'hazard_timeseries.log')
    run_log = read_text(case_dir / 'run.log')
    for marker in ['Unused ParmParse Variables', 'RuntimeWarning', 'Traceback']:
        if marker in run_log:
            raise SystemExit(f'FAIL: {marker} in {name} run log')
    return {
        'case': name,
        'input': str(input_path),
        'log_dir': str(case_dir),
        'plan_species_gradient': plan_species_gradient if name == 'amr' else '',
        'finest_level': meta['finest_level'],
        'finest_fab_count': fab_count,
        'regrid_count': run_log.count('Regridding'),
        'made_level1': int(('Making new level 1 from scratch' in run_log) or ('Making new level 1 from coarse' in run_log)),
        'mass_ratio': float(grab(r'mass_ratio=([0-9.eE+-]+)', profile, f'{name} mass_ratio')),
        'mass_ratioN': float(grab(r'mass_ratioN=([0-9.eE+-]+)', validation, f'{name} mass_ratioN')),
        'centroid_shift': float(grab(r'centroid_shift=([0-9.eE+-]+)', profile, f'{name} centroid_shift')),
        'downstream_fraction': float(grab(r'downstream_fraction=([0-9.eE+-]+)', profile, f'{name} downstream_fraction')),
        'cloud_volume': float(grab(r'cloud_volume=([0-9.eE+-]+)', hazard, f'{name} cloud_volume')),
        'cloud_species_mass': float(grab(r'cloud_species_mass=([0-9.eE+-]+)', hazard, f'{name} cloud_species_mass')),
        'max_X': float(grab(r'max_X=([0-9.eE+-]+)', hazard, f'{name} max_X')),
        'active_planes': int(grab(r'active_planes=([0-9]+)', planes, f'{name} active_planes')),
        'flammable_planes': int(grab(r'flammable_planes=([0-9]+)', planes, f'{name} flammable_planes')),
        'plotfiles': int(grab(r'plotfiles=([0-9]+)', timeseries, f'{name} plotfiles')),
        'final_cloud_volume': float(grab(r'final_cloud_volume=([0-9.eE+-]+)', timeseries, f'{name} final_cloud_volume')),
        'final_peak_X': float(grab(r'final_peak_X=([0-9.eE+-]+)', timeseries, f'{name} final_peak_X')),
    }


def rel_diff(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1.0e-30)

base = parse_case('baseline', baseline_input)
amr = parse_case('amr', amr_input)
if base['finest_level'] != 0:
    raise SystemExit(f'FAIL: baseline finest_level expected 0, got {base["finest_level"]}')
if amr['finest_level'] < 1 or amr['finest_fab_count'] <= 0 or amr['made_level1'] != 1:
    raise SystemExit(f'FAIL: plan-AMR did not dynamically produce populated Level_1: {amr}')
for case in (base, amr):
    if not (min_final_mass_ratio <= case['mass_ratio'] <= max_final_mass_ratio):
        raise SystemExit(f'FAIL: {case["case"]} mass_ratio out of range: {case["mass_ratio"]}')
    if (case['cloud_volume'] <= 0.0
            or case['flammable_planes'] < min_flammable_planes
            or case['active_planes'] < min_active_planes):
        raise SystemExit(f'FAIL: weak hazard metrics in {case["case"]}: {case} thresholds={{"min_active_planes": min_active_planes, "min_flammable_planes": min_flammable_planes}}')

cloud_rel = rel_diff(base['cloud_volume'], amr['cloud_volume'])
peak_rel = rel_diff(base['max_X'], amr['max_X'])
centroid_abs = abs(base['centroid_shift'] - amr['centroid_shift'])
downstream_abs = abs(base['downstream_fraction'] - amr['downstream_fraction'])
if cloud_rel > 0.45:
    raise SystemExit(f'FAIL: plan-AMR cloud volume drift too large: rel={cloud_rel:.3g}')
if peak_rel > 0.50:
    raise SystemExit(f'FAIL: plan-AMR max_X drift too large: rel={peak_rel:.3g}')
if centroid_abs > 0.08:
    raise SystemExit(f'FAIL: plan-AMR centroid drift too large: abs={centroid_abs:.3g}')
if downstream_abs > 0.15:
    raise SystemExit(f'FAIL: plan-AMR downstream drift too large: abs={downstream_abs:.3g}')

summary.parent.mkdir(parents=True, exist_ok=True)
fieldnames = list(base.keys()) + ['cloud_rel_diff', 'peak_rel_diff', 'centroid_abs_diff', 'downstream_abs_diff']
with summary.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow({**base, 'cloud_rel_diff': '', 'peak_rel_diff': '', 'centroid_abs_diff': '', 'downstream_abs_diff': ''})
    writer.writerow({**amr, 'cloud_rel_diff': f'{cloud_rel:.8e}', 'peak_rel_diff': f'{peak_rel:.8e}', 'centroid_abs_diff': f'{centroid_abs:.8e}', 'downstream_abs_diff': f'{downstream_abs:.8e}'})
print('h2_leak_open_domain_plan_amr_compare PASS ' +
      f'output={summary} plan_species_gradient={plan_species_gradient} ' +
      f'amr_finest_level={amr["finest_level"]} amr_finest_fabs={amr["finest_fab_count"]} ' +
      f'regrid_count={amr["regrid_count"]} cloud_rel_diff={cloud_rel:.8e} ' +
      f'peak_rel_diff={peak_rel:.8e} centroid_abs_diff={centroid_abs:.8e} ' +
      f'downstream_abs_diff={downstream_abs:.8e}')
PYCHECK

python3 "$repo_root/tools/summarize_h2_leak_amr_overhead.py" \
  --baseline-dir "$log_root/baseline" \
  --amr-dir "$log_root/amr" \
  --output "$overhead_csv" \
  --max-mean-ncells-ratio 8.0 \
  --max-advance-seconds-ratio 20.0 \
  --max-final-plotfile-bytes-ratio 20.0

printf '[codex-smoke] overhead summary=%s\n' "$overhead_csv"
printf '[codex-smoke] PASS h2_leak open-domain plan-AMR comparison log_root=%s summary=%s\n' "$log_root" "$summary_csv"
