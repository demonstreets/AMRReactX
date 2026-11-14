#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_leak_3d"
base_input="$case_dir/input.codex_open_domain_flammable_smoke"
log_dir="${CODEX_H2_LEAK_SENSITIVITY_LOG_DIR:-/tmp/codex_h2_leak_open_domain_sensitivity_$(date -u +%Y%m%dT%H%M%SZ)}"
input_dir="$log_dir/inputs"
summary_csv="$log_dir/sensitivity_summary.csv"
mkdir -p "$input_dir"

make_input() {
  local name=$1
  local wind=$2
  local dst="$input_dir/${name}.inputs"
  python3 - "$base_input" "$dst" "$wind" <<'PYIN'
from pathlib import Path
import sys
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
wind = float(sys.argv[3])
lines = []
for raw in src.read_text().splitlines():
    stripped = raw.strip()
    if stripped.startswith('prob.wind_u'):
        lines.append(f'prob.wind_u = {wind:.8g}')
    elif stripped.startswith('prob.leak_vel_x'):
        lines.append(f'prob.leak_vel_x = {wind:.8g}')
    else:
        lines.append(raw)
dst.write_text('\n'.join(lines) + '\n')
print(dst)
PYIN
}

run_case() {
  local name=$1
  local wind=$2
  local min_x=$3
  local min_upstream=$4
  local input
  input=$(make_input "$name" "$wind")
  local case_log_dir="$log_dir/$name"
  printf '[codex-smoke] running H2 open-domain sensitivity case=%s wind=%s input=%s\n' "$name" "$wind" "$input"
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
  CODEX_H2_LEAK_HISTORY_MIN_UPSTREAM_FRACTION="$min_upstream" \
  RUN_TIMEOUT="${RUN_TIMEOUT:-600}" \
  JOBS="${JOBS:-4}" \
  "$repo_root/tools/codex_smoke_engineering_h2_leak_flammable_cloud.sh"
}

run_case low_wind 1.5 0.62 0.08
run_case high_wind 2.5 0.72 0.03

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
for name in ('low_wind', 'high_wind'):
    case = log_dir / name
    profile = (case / 'profile_validation.log').read_text()
    hazard = (case / 'hazard_summary.log').read_text()
    planes = (case / 'hazard_planes.log').read_text()
    timeseries = (case / 'hazard_timeseries.log').read_text()
    run_input = next((case / 'run').glob('*.inputs'))
    input_text = run_input.read_text()
    wind = grab(r'prob\.wind_u\s*=\s*([0-9.eE+-]+)', input_text, f'{name} wind')
    row = {
        'case': name,
        'wind_u': wind,
        'centroid_shift': grab(r'centroid_shift=([0-9.eE+-]+)', profile, f'{name} centroid_shift'),
        'downstream_fraction': grab(r'downstream_fraction=([0-9.eE+-]+)', profile, f'{name} downstream_fraction'),
        'profile_y_l1': grab(r'y_l1=([0-9.eE+-]+)', profile, f'{name} y_l1'),
        'cloud_volume': grab(r'cloud_volume=([0-9.eE+-]+)', hazard, f'{name} cloud_volume'),
        'max_X': grab(r'max_X=([0-9.eE+-]+)', hazard, f'{name} max_X'),
        'active_planes': grab(r'active_planes=([0-9]+)', planes, f'{name} active_planes'),
        'flammable_planes': grab(r'flammable_planes=([0-9]+)', planes, f'{name} flammable_planes'),
        'final_cloud_volume': grab(r'final_cloud_volume=([0-9.eE+-]+)', timeseries, f'{name} final_cloud_volume'),
        'final_peak_X': grab(r'final_peak_X=([0-9.eE+-]+)', timeseries, f'{name} final_peak_X'),
        'log_dir': str(case),
    }
    rows.append(row)

low, high = rows
low_shift = float(low['centroid_shift'])
high_shift = float(high['centroid_shift'])
if high_shift <= low_shift + 2.5e-2:
    raise SystemExit(f'FAIL: expected high_wind centroid shift to exceed low_wind by >2.5e-2, low={low_shift}, high={high_shift}')
low_down = float(low['downstream_fraction'])
high_down = float(high['downstream_fraction'])
if high_down < low_down - 2.0e-2:
    raise SystemExit(f'FAIL: high_wind downstream fraction regressed, low={low_down}, high={high_down}')

out.parent.mkdir(parents=True, exist_ok=True)
with out.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
print('h2_leak_open_domain_sensitivity PASS ' +
      f'output={out} low_shift={low_shift:.8e} high_shift={high_shift:.8e} ' +
      f'low_downstream={low_down:.8e} high_downstream={high_down:.8e}')
PYSUM

printf '[codex-smoke] PASS h2_leak open-domain sensitivity log_dir=%s summary=%s\n' "$log_dir" "$summary_csv"
