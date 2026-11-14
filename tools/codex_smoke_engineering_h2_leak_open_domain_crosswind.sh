#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_leak_3d"
base_input="$case_dir/input.codex_open_domain_flammable_smoke"
log_dir="${CODEX_H2_LEAK_CROSSWIND_LOG_DIR:-/tmp/codex_h2_leak_open_domain_crosswind_$(date -u +%Y%m%dT%H%M%SZ)}"
input_dir="$log_dir/inputs"
summary_csv="$log_dir/crosswind_summary.csv"
mkdir -p "$input_dir"

make_input() {
  local name=$1
  local wind_v=$2
  local dst="$input_dir/${name}.inputs"
  python3 - "$base_input" "$dst" "$wind_v" <<'PYIN'
from pathlib import Path
import sys
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
wind_v = float(sys.argv[3])
lines = []
for raw in src.read_text().splitlines():
    stripped = raw.strip()
    if stripped.startswith('prob.wind_v'):
        lines.append(f'prob.wind_v = {wind_v:.8g}')
    elif stripped.startswith('prob.leak_vel_y'):
        lines.append(f'prob.leak_vel_y = {wind_v:.8g}')
    else:
        lines.append(raw)
dst.write_text('\n'.join(lines) + '\n')
print(dst)
PYIN
}

run_case() {
  local name=$1
  local wind_v=$2
  local input
  input=$(make_input "$name" "$wind_v")
  local case_log_dir="$log_dir/$name"
  printf '[codex-smoke] running H2 open-domain crosswind case=%s wind_v=%s input=%s\n' "$name" "$wind_v" "$input"
  CODEX_H2_LEAK_PROFILE_INPUT="$input" \
  CODEX_H2_LEAK_FLAMMABLE_LOG_DIR="$case_log_dir" \
  CODEX_H2_LEAK_PLANE_MIN_X=0.70 \
  CODEX_H2_LEAK_MIN_ACTIVE_PLANES=2 \
  CODEX_H2_LEAK_MIN_FLAMMABLE_PLANES=1 \
  CODEX_H2_LEAK_MIN_FLAMMABLE_VOLUME=2.0e-4 \
  CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME=2.5e-1 \
  CODEX_H2_LEAK_MIN_MAX_X=4.0e-2 \
  CODEX_H2_LEAK_MAX_MAX_X=7.5e-1 \
  CODEX_H2_LEAK_MIN_TIMESERIES_PLOTFILES=6 \
  CODEX_H2_LEAK_HISTORY_MIN_UPSTREAM_FRACTION=0.03 \
  CODEX_H2_LEAK_HISTORY_MAX_CENTER_OFFSET=0.16 \
  CODEX_H2_LEAK_PROFILE_MAX_LATERAL_OFFSET=0.16 \
  RUN_TIMEOUT="${RUN_TIMEOUT:-900}" \
  JOBS="${JOBS:-4}" \
  "$repo_root/tools/codex_smoke_engineering_h2_leak_flammable_cloud.sh"
}

run_case baseline 0.0
run_case crosswind 1.5

python3 - "$log_dir" "$summary_csv" <<'PYSUM'
import csv
import re
import sys
from pathlib import Path

log_dir = Path(sys.argv[1])
out = Path(sys.argv[2])

def match(pattern, text, label):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f'FAIL: missing {label}')
    return m


def grab(pattern, text, label):
    return match(pattern, text, label).group(1)

rows = []
for name in ('baseline', 'crosswind'):
    case = log_dir / name
    profile = (case / 'profile_validation.log').read_text()
    hazard = (case / 'hazard_summary.log').read_text()
    planes = (case / 'hazard_planes.log').read_text()
    timeseries = (case / 'hazard_timeseries.log').read_text()
    run_input = next((case / 'run').glob('*.inputs'))
    input_text = run_input.read_text()
    cm = match(
        r'centroid=\(([0-9.eE+-]+),([0-9.eE+-]+),([0-9.eE+-]+)\)',
        profile,
        f'{name} centroid',
    )
    cx, cy, cz = (float(cm.group(1)), float(cm.group(2)), float(cm.group(3)))
    leak_y = float(grab(r'prob\.leak_yc\s*=\s*([0-9.eE+-]+)', input_text, f'{name} leak_y'))
    wind_v = float(grab(r'prob\.wind_v\s*=\s*([0-9.eE+-]+)', input_text, f'{name} wind_v'))
    row = {
        'case': name,
        'wind_v': f'{wind_v:.8e}',
        'centroid_x': f'{cx:.8e}',
        'centroid_y': f'{cy:.8e}',
        'centroid_z': f'{cz:.8e}',
        'lateral_y_shift': f'{cy - leak_y:.8e}',
        'centroid_shift_x': grab(r'centroid_shift=([0-9.eE+-]+)', profile, f'{name} centroid_shift'),
        'downstream_fraction': grab(r'downstream_fraction=([0-9.eE+-]+)', profile, f'{name} downstream_fraction'),
        'cloud_volume': grab(r'cloud_volume=([0-9.eE+-]+)', hazard, f'{name} cloud_volume'),
        'max_X': grab(r'max_X=([0-9.eE+-]+)', hazard, f'{name} max_X'),
        'active_planes': grab(r'active_planes=([0-9]+)', planes, f'{name} active_planes'),
        'flammable_planes': grab(r'flammable_planes=([0-9]+)', planes, f'{name} flammable_planes'),
        'final_cloud_volume': grab(r'final_cloud_volume=([0-9.eE+-]+)', timeseries, f'{name} final_cloud_volume'),
        'final_peak_X': grab(r'final_peak_X=([0-9.eE+-]+)', timeseries, f'{name} final_peak_X'),
        'log_dir': str(case),
    }
    rows.append(row)

base, cross = rows
base_y = float(base['lateral_y_shift'])
cross_y = float(cross['lateral_y_shift'])
if abs(base_y) > 1.0e-3:
    raise SystemExit(f'FAIL: baseline plume has unexpected lateral y shift: {base_y}')
if cross_y < 2.5e-2:
    raise SystemExit(f'FAIL: crosswind plume y shift too small: {cross_y}')
if cross_y <= base_y + 2.5e-2:
    raise SystemExit(f'FAIL: crosswind y shift did not separate from baseline: baseline={base_y}, crosswind={cross_y}')
base_down = float(base['downstream_fraction'])
cross_down = float(cross['downstream_fraction'])
if cross_down < 0.70:
    raise SystemExit(f'FAIL: crosswind downstream fraction too small: {cross_down}')
base_cloud = float(base['cloud_volume'])
cross_cloud = float(cross['cloud_volume'])
if not (base_cloud > 0.0 and cross_cloud > 0.0):
    raise SystemExit(f'FAIL: expected nonzero flammable clouds, baseline={base_cloud}, crosswind={cross_cloud}')
if abs(cross_cloud - base_cloud) / base_cloud > 0.25:
    raise SystemExit(f'FAIL: crosswind cloud volume drift too large: baseline={base_cloud}, crosswind={cross_cloud}')

out.parent.mkdir(parents=True, exist_ok=True)
with out.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
print('h2_leak_open_domain_crosswind PASS ' +
      f'output={out} baseline_y_shift={base_y:.8e} crosswind_y_shift={cross_y:.8e} ' +
      f'baseline_downstream={base_down:.8e} crosswind_downstream={cross_down:.8e} ' +
      f'baseline_cloud={base_cloud:.8e} crosswind_cloud={cross_cloud:.8e}')
PYSUM

printf '[codex-smoke] PASS h2_leak open-domain crosswind log_dir=%s summary=%s\n' "$log_dir" "$summary_csv"
