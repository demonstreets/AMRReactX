#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_leak_3d"
base_input="$case_dir/input.codex_open_domain_flammable_smoke"
log_dir="${CODEX_H2_LEAK_LENGTH_LOG_DIR:-/tmp/codex_h2_leak_open_domain_length_$(date -u +%Y%m%dT%H%M%SZ)}"
input_dir="$log_dir/inputs"
summary_csv="$log_dir/length_summary.csv"
mkdir -p "$input_dir"

make_input() {
  local name=$1
  local x_hi=$2
  local nx=$3
  local max_grid_size=$4
  local dst="$input_dir/${name}.inputs"
  python3 - "$base_input" "$dst" "$x_hi" "$nx" "$max_grid_size" <<'PYIN'
from pathlib import Path
import sys
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
x_hi = float(sys.argv[3])
nx = int(sys.argv[4])
max_grid_size = int(sys.argv[5])
lines = []
for raw in src.read_text().splitlines():
    stripped = raw.strip()
    if stripped.startswith('geometry.prob_hi'):
        lines.append(f'geometry.prob_hi     = {x_hi:.8g} 1.0 1.0')
    elif stripped.startswith('amr.n_cell'):
        lines.append(f'amr.n_cell = {nx} 16 16')
    elif stripped.startswith('amr.max_grid_size'):
        lines.append(f'amr.max_grid_size = {max_grid_size}')
    else:
        lines.append(raw)
dst.write_text('\n'.join(lines) + '\n')
print(dst)
PYIN
}

run_case() {
  local name=$1
  local x_hi=$2
  local nx=$3
  local max_grid_size=$4
  local input
  input=$(make_input "$name" "$x_hi" "$nx" "$max_grid_size")
  local case_log_dir="$log_dir/$name"
  printf '[codex-smoke] running H2 open-domain length case=%s x_hi=%s nx=%s input=%s\n' "$name" "$x_hi" "$nx" "$input"
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
  CODEX_H2_LEAK_HISTORY_MIN_UPSTREAM_FRACTION=0.05 \
  RUN_TIMEOUT="${RUN_TIMEOUT:-600}" \
  JOBS="${JOBS:-4}" \
  "$repo_root/tools/codex_smoke_engineering_h2_leak_flammable_cloud.sh"
}

run_case base_domain 2.0 32 32
run_case long_domain 2.5 40 40

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

def parse_vec(pattern, text, label):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f'FAIL: missing {label}')
    return [float(x) for x in m.group(1).split()]

def cloud_extent(planes_csv, x_hi, dx):
    rows = list(csv.DictReader(planes_csv.open()))
    cloud_x = [float(r['x']) for r in rows if int(r['cloud_cells']) > 0]
    active_x = [float(r['x']) for r in rows if int(r['active_cells']) > 0]
    if not cloud_x:
        raise SystemExit(f'FAIL: no flammable cloud cells in {planes_csv}')
    last_cloud_x = max(cloud_x)
    first_cloud_x = min(cloud_x)
    last_active_x = max(active_x) if active_x else 0.0
    cloud_face_margin = x_hi - (last_cloud_x + 0.5 * dx)
    active_face_margin = x_hi - (last_active_x + 0.5 * dx) if active_x else x_hi
    if cloud_face_margin < 0.0:
        raise SystemExit(f'FAIL: flammable cloud crosses outlet estimate: x_hi={x_hi}, last_cloud_x={last_cloud_x}, dx={dx}')
    return {
        'first_cloud_x': first_cloud_x,
        'last_cloud_x': last_cloud_x,
        'last_active_x': last_active_x,
        'cloud_face_margin': cloud_face_margin,
        'active_face_margin': active_face_margin,
    }

rows = []
for name in ('base_domain', 'long_domain'):
    case = log_dir / name
    profile = (case / 'profile_validation.log').read_text()
    hazard = (case / 'hazard_summary.log').read_text()
    planes_log = (case / 'hazard_planes.log').read_text()
    timeseries = (case / 'hazard_timeseries.log').read_text()
    run_input = next((case / 'run').glob('*.inputs'))
    input_text = run_input.read_text()
    prob_hi = parse_vec(r'geometry\.prob_hi\s*=\s*([^\n]+)', input_text, f'{name} prob_hi')
    n_cell = [int(x) for x in parse_vec(r'amr\.n_cell\s*=\s*([^\n]+)', input_text, f'{name} n_cell')]
    x_hi = prob_hi[0]
    dx = (x_hi - 0.0) / n_cell[0]
    extent = cloud_extent(case / 'hazard_planes.csv', x_hi, dx)
    row = {
        'case': name,
        'x_hi': f'{x_hi:.12e}',
        'nx': str(n_cell[0]),
        'dx': f'{dx:.12e}',
        'mass_ratio': grab(r'mass_ratio=([0-9.eE+-]+)', profile, f'{name} mass_ratio'),
        'h2_mass': grab(r'h2_mass=([0-9.eE+-]+)', profile, f'{name} h2_mass'),
        'centroid_shift': grab(r'centroid_shift=([0-9.eE+-]+)', profile, f'{name} centroid_shift'),
        'downstream_fraction': grab(r'downstream_fraction=([0-9.eE+-]+)', profile, f'{name} downstream_fraction'),
        'cloud_volume': grab(r'cloud_volume=([0-9.eE+-]+)', hazard, f'{name} cloud_volume'),
        'cloud_species_mass': grab(r'cloud_species_mass=([0-9.eE+-]+)', hazard, f'{name} cloud_species_mass'),
        'max_X': grab(r'max_X=([0-9.eE+-]+)', hazard, f'{name} max_X'),
        'active_planes': grab(r'active_planes=([0-9]+)', planes_log, f'{name} active_planes'),
        'flammable_planes': grab(r'flammable_planes=([0-9]+)', planes_log, f'{name} flammable_planes'),
        'final_cloud_volume': grab(r'final_cloud_volume=([0-9.eE+-]+)', timeseries, f'{name} final_cloud_volume'),
        'final_peak_X': grab(r'final_peak_X=([0-9.eE+-]+)', timeseries, f'{name} final_peak_X'),
        'first_cloud_x': f'{extent["first_cloud_x"]:.12e}',
        'last_cloud_x': f'{extent["last_cloud_x"]:.12e}',
        'last_active_x': f'{extent["last_active_x"]:.12e}',
        'cloud_face_margin': f'{extent["cloud_face_margin"]:.12e}',
        'active_face_margin': f'{extent["active_face_margin"]:.12e}',
        'log_dir': str(case),
    }
    rows.append(row)

base, long = rows
base_x_hi = float(base['x_hi'])
long_x_hi = float(long['x_hi'])
base_dx = float(base['dx'])
long_dx = float(long['dx'])
if long_x_hi <= base_x_hi:
    raise SystemExit(f'FAIL: long domain did not increase x_hi: base={base_x_hi}, long={long_x_hi}')
if abs(base_dx - long_dx) > 1.0e-12:
    raise SystemExit(f'FAIL: length sensitivity changed dx: base={base_dx}, long={long_dx}')
for row in rows:
    cloud_margin = float(row['cloud_face_margin'])
    active_margin = float(row['active_face_margin'])
    if cloud_margin < 0.50:
        raise SystemExit(f'FAIL: flammable cloud too close to outlet for {row["case"]}: cloud_face_margin={cloud_margin}')
    if active_margin < 0.25:
        raise SystemExit(f'FAIL: active H2 field too close to outlet for {row["case"]}: active_face_margin={active_margin}')
base_mass = float(base['h2_mass'])
long_mass = float(long['h2_mass'])
base_cloud_volume = float(base['cloud_volume'])
long_cloud_volume = float(long['cloud_volume'])
base_peak = float(base['max_X'])
long_peak = float(long['max_X'])
if abs(base_mass - long_mass) / max(base_mass, long_mass) > 5.0e-3:
    raise SystemExit(f'FAIL: total H2 mass changed with outlet placement: base={base_mass}, long={long_mass}')
if abs(base_cloud_volume - long_cloud_volume) / max(base_cloud_volume, long_cloud_volume) > 0.20:
    raise SystemExit(f'FAIL: cloud volume changed too much with outlet placement: base={base_cloud_volume}, long={long_cloud_volume}')
if abs(base_peak - long_peak) / max(base_peak, long_peak) > 0.20:
    raise SystemExit(f'FAIL: peak X changed too much with outlet placement: base={base_peak}, long={long_peak}')

out.parent.mkdir(parents=True, exist_ok=True)
with out.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
print('h2_leak_open_domain_length PASS ' +
      f'output={out} base_cloud_margin={float(base["cloud_face_margin"]):.8e} ' +
      f'long_cloud_margin={float(long["cloud_face_margin"]):.8e} ' +
      f'base_active_margin={float(base["active_face_margin"]):.8e} ' +
      f'long_active_margin={float(long["active_face_margin"]):.8e} ' +
      f'base_cloud_volume={base_cloud_volume:.8e} long_cloud_volume={long_cloud_volume:.8e} ' +
      f'base_peak_X={base_peak:.8e} long_peak_X={long_peak:.8e}')
PYSUM

printf '[codex-smoke] PASS h2_leak open-domain length sensitivity log_dir=%s summary=%s\n' "$log_dir" "$summary_csv"
