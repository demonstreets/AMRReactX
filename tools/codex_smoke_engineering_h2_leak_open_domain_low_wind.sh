#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_leak_3d"
base_input="$case_dir/input.codex_open_domain_flammable_smoke"
log_dir="${CODEX_H2_LEAK_LOW_WIND_LOG_DIR:-/tmp/codex_h2_leak_open_domain_low_wind_$(date -u +%Y%m%dT%H%M%SZ)}"
input_dir="$log_dir/inputs"
summary_csv="$log_dir/low_wind_summary.csv"
mkdir -p "$input_dir"

make_input() {
  local name=$1
  local wind_u=$2
  local dst="$input_dir/${name}.inputs"
  python3 - "$base_input" "$dst" "$wind_u" <<'PYIN'
from pathlib import Path
import sys
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
wind_u = float(sys.argv[3])
lines = []
for raw in src.read_text().splitlines():
    stripped = raw.strip()
    if stripped.startswith('prob.wind_u'):
        lines.append(f'prob.wind_u = {wind_u:.8g}')
    else:
        lines.append(raw)
dst.write_text('\n'.join(lines) + '\n')
print(dst)
PYIN
}

run_case() {
  local name=$1
  local wind_u=$2
  local min_x=$3
  local min_downstream=$4
  local min_centroid_shift=$5
  local input
  input=$(make_input "$name" "$wind_u")
  local case_log_dir="$log_dir/$name"
  printf '[codex-smoke] running H2 open-domain low-wind case=%s wind_u=%s input=%s\n' "$name" "$wind_u" "$input"
  CODEX_H2_LEAK_PROFILE_INPUT="$input" \
  CODEX_H2_LEAK_FLAMMABLE_LOG_DIR="$case_log_dir" \
  CODEX_H2_LEAK_PLANE_MIN_X="$min_x" \
  CODEX_H2_LEAK_MIN_ACTIVE_PLANES=2 \
  CODEX_H2_LEAK_MIN_FLAMMABLE_PLANES=1 \
  CODEX_H2_LEAK_MIN_FLAMMABLE_VOLUME=2.0e-4 \
  CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME=2.5e-1 \
  CODEX_H2_LEAK_MIN_MAX_X=4.0e-2 \
  CODEX_H2_LEAK_MAX_MAX_X=7.5e-1 \
  CODEX_H2_LEAK_MIN_TIMESERIES_PLOTFILES=6 \
  CODEX_H2_LEAK_HISTORY_MIN_UPSTREAM_FRACTION=0.03 \
  CODEX_H2_LEAK_HISTORY_MIN_DOWNSTREAM_FRACTION="$min_downstream" \
  CODEX_H2_LEAK_PROFILE_MIN_DOWNSTREAM_FRACTION="$min_downstream" \
  CODEX_H2_LEAK_PROFILE_MIN_CENTROID_SHIFT="$min_centroid_shift" \
  RUN_TIMEOUT="${RUN_TIMEOUT:-900}" \
  JOBS="${JOBS:-4}" \
  "$repo_root/tools/codex_smoke_engineering_h2_leak_flammable_cloud.sh"
}

run_case baseline 2.0 0.70 0.65 0.03
run_case low_wind 0.5 0.52 0.55 0.02

python3 - "$log_dir" "$summary_csv" <<'PYSUM'
import csv
import re
import sys
from pathlib import Path

log_dir = Path(sys.argv[1])
out = Path(sys.argv[2])

def grab(pattern, text, label):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f'FAIL: missing {label}')
    return m.group(1)

rows = []
for name in ('baseline', 'low_wind'):
    case = log_dir / name
    profile = (case / 'profile_validation.log').read_text()
    hazard = (case / 'hazard_summary.log').read_text()
    planes = (case / 'hazard_planes.log').read_text()
    timeseries = (case / 'hazard_timeseries.log').read_text()
    run_input = next((case / 'run').glob('*.inputs'))
    input_text = run_input.read_text()
    wind_u = float(grab(r'prob\.wind_u\s*=\s*([0-9.eE+-]+)', input_text, f'{name} wind_u'))
    x_hi = float(grab(r'geometry\.prob_hi\s*=\s*([0-9.eE+-]+)', input_text, f'{name} x_hi'))
    centroid_x = float(grab(r'centroid=\(([0-9.eE+-]+),', profile, f'{name} centroid_x'))
    max_x = float(grab(r'max_X=([0-9.eE+-]+)', hazard, f'{name} max_X'))
    row = {
        'case': name,
        'wind_u': f'{wind_u:.8e}',
        'centroid_x': f'{centroid_x:.8e}',
        'centroid_shift': grab(r'centroid_shift=([0-9.eE+-]+)', profile, f'{name} centroid_shift'),
        'downstream_fraction': grab(r'downstream_fraction=([0-9.eE+-]+)', profile, f'{name} downstream_fraction'),
        'cloud_volume': grab(r'cloud_volume=([0-9.eE+-]+)', hazard, f'{name} cloud_volume'),
        'max_X': f'{max_x:.8e}',
        'cloud_face_margin': f'{x_hi - centroid_x:.8e}',
        'active_planes': grab(r'active_planes=([0-9]+)', planes, f'{name} active_planes'),
        'flammable_planes': grab(r'flammable_planes=([0-9]+)', planes, f'{name} flammable_planes'),
        'final_cloud_volume': grab(r'final_cloud_volume=([0-9.eE+-]+)', timeseries, f'{name} final_cloud_volume'),
        'final_peak_X': grab(r'final_peak_X=([0-9.eE+-]+)', timeseries, f'{name} final_peak_X'),
        'log_dir': str(case),
    }
    rows.append(row)

base, low = rows
base_shift = float(base['centroid_shift'])
low_shift = float(low['centroid_shift'])
if low_shift < 2.0e-2:
    raise SystemExit(f'FAIL: low_wind centroid shift too small to resolve jet transport: {low_shift}')
if low_shift > base_shift - 4.0e-2:
    raise SystemExit(f'FAIL: low_wind plume did not show expected reduced advection: baseline={base_shift}, low={low_shift}')
base_down = float(base['downstream_fraction'])
low_down = float(low['downstream_fraction'])
if low_down < 0.55:
    raise SystemExit(f'FAIL: low_wind downstream fraction too small to resolve downstream hazard: {low_down}')
if low_down > base_down - 0.10:
    raise SystemExit(f'FAIL: low_wind downstream fraction did not show expected source-region retention: baseline={base_down}, low={low_down}')
base_cloud = float(base['cloud_volume'])
low_cloud = float(low['cloud_volume'])
if not (base_cloud > 0.0 and low_cloud > 0.0):
    raise SystemExit(f'FAIL: expected nonzero flammable clouds, baseline={base_cloud}, low={low_cloud}')
cloud_ratio = low_cloud / base_cloud
if not (0.20 <= cloud_ratio <= 3.00):
    raise SystemExit(f'FAIL: low_wind cloud volume ratio outside smoke envelope: baseline={base_cloud}, low={low_cloud}, ratio={cloud_ratio}')
low_margin = float(low['cloud_face_margin'])
if low_margin < 0.9:
    raise SystemExit(f'FAIL: low_wind centroid too close to outlet: margin={low_margin}')

out.parent.mkdir(parents=True, exist_ok=True)
with out.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
print('h2_leak_open_domain_low_wind PASS ' +
      f'output={out} baseline_shift={base_shift:.8e} low_shift={low_shift:.8e} ' +
      f'baseline_downstream={base_down:.8e} low_downstream={low_down:.8e} ' +
      f'baseline_cloud={base_cloud:.8e} ' +
      f'low_cloud={low_cloud:.8e} low_margin={low_margin:.8e}')
PYSUM

printf '[codex-smoke] PASS h2_leak open-domain low-wind log_dir=%s summary=%s\n' "$log_dir" "$summary_csv"
