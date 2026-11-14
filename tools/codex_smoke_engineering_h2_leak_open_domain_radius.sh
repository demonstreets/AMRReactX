#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_leak_3d"
base_input="$case_dir/input.codex_open_domain_flammable_smoke"
log_dir="${CODEX_H2_LEAK_RADIUS_LOG_DIR:-/tmp/codex_h2_leak_open_domain_radius_$(date -u +%Y%m%dT%H%M%SZ)}"
input_dir="$log_dir/inputs"
summary_csv="$log_dir/radius_summary.csv"
mkdir -p "$input_dir"

make_input() {
  local name=$1
  local radius=$2
  local dst="$input_dir/${name}.inputs"
  python3 - "$base_input" "$dst" "$radius" <<'PYIN'
from pathlib import Path
import sys
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
radius = float(sys.argv[3])
lines = []
for raw in src.read_text().splitlines():
    stripped = raw.strip()
    if stripped.startswith('prob.leak_radius'):
        lines.append(f'prob.leak_radius = {radius:.8g}')
    else:
        lines.append(raw)
dst.write_text('\n'.join(lines) + '\n')
print(dst)
PYIN
}

run_case() {
  local name=$1
  local radius=$2
  local input
  input=$(make_input "$name" "$radius")
  local case_log_dir="$log_dir/$name"
  printf '[codex-smoke] running H2 open-domain radius case=%s radius=%s input=%s\n' "$name" "$radius" "$input"
  CODEX_H2_LEAK_PROFILE_INPUT="$input" \
  CODEX_H2_LEAK_FLAMMABLE_LOG_DIR="$case_log_dir" \
  CODEX_H2_LEAK_PLANE_MIN_X=0.70 \
  CODEX_H2_LEAK_MIN_ACTIVE_PLANES=2 \
  CODEX_H2_LEAK_MIN_FLAMMABLE_PLANES=1 \
  CODEX_H2_LEAK_MIN_FLAMMABLE_VOLUME=2.0e-4 \
  CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME=2.5e-1 \
  CODEX_H2_LEAK_MIN_MAX_X=3.0e-2 \
  CODEX_H2_LEAK_MAX_MAX_X=7.5e-1 \
  CODEX_H2_LEAK_MIN_TIMESERIES_PLOTFILES=6 \
  CODEX_H2_LEAK_HISTORY_MIN_UPSTREAM_FRACTION=0.05 \
  RUN_TIMEOUT="${RUN_TIMEOUT:-600}" \
  JOBS="${JOBS:-4}" \
  "$repo_root/tools/codex_smoke_engineering_h2_leak_flammable_cloud.sh"
}

run_case small_radius 0.10
run_case large_radius 0.20

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
for name in ('small_radius', 'large_radius'):
    case = log_dir / name
    run_log = (case / 'run.log').read_text()
    profile = (case / 'profile_validation.log').read_text()
    hazard = (case / 'hazard_summary.log').read_text()
    planes = (case / 'hazard_planes.log').read_text()
    timeseries = (case / 'hazard_timeseries.log').read_text()
    run_input = next((case / 'run').glob('*.inputs'))
    input_text = run_input.read_text()
    row = {
        'case': name,
        'leak_radius': grab(r'prob\.leak_radius\s*=\s*([0-9.eE+-]+)', input_text, f'{name} radius'),
        'active_volume': grab(r'H2 leak discrete active volume=([0-9.eE+-]+)', run_log, f'{name} active volume'),
        'mdot_vol': grab(r'mdot_vol=([0-9.eE+-]+)', run_log, f'{name} mdot_vol'),
        'mass_ratio': grab(r'mass_ratio=([0-9.eE+-]+)', profile, f'{name} mass_ratio'),
        'h2_mass': grab(r'h2_mass=([0-9.eE+-]+)', profile, f'{name} h2_mass'),
        'centroid_shift': grab(r'centroid_shift=([0-9.eE+-]+)', profile, f'{name} centroid_shift'),
        'downstream_fraction': grab(r'downstream_fraction=([0-9.eE+-]+)', profile, f'{name} downstream_fraction'),
        'cloud_volume': grab(r'cloud_volume=([0-9.eE+-]+)', hazard, f'{name} cloud_volume'),
        'cloud_species_mass': grab(r'cloud_species_mass=([0-9.eE+-]+)', hazard, f'{name} cloud_species_mass'),
        'max_X': grab(r'max_X=([0-9.eE+-]+)', hazard, f'{name} max_X'),
        'active_planes': grab(r'active_planes=([0-9]+)', planes, f'{name} active_planes'),
        'flammable_planes': grab(r'flammable_planes=([0-9]+)', planes, f'{name} flammable_planes'),
        'final_cloud_volume': grab(r'final_cloud_volume=([0-9.eE+-]+)', timeseries, f'{name} final_cloud_volume'),
        'final_peak_X': grab(r'final_peak_X=([0-9.eE+-]+)', timeseries, f'{name} final_peak_X'),
        'log_dir': str(case),
    }
    rows.append(row)

small, large = rows
small_radius = float(small['leak_radius'])
large_radius = float(large['leak_radius'])
small_active = float(small['active_volume'])
large_active = float(large['active_volume'])
small_mdot_vol = float(small['mdot_vol'])
large_mdot_vol = float(large['mdot_vol'])
small_mass = float(small['h2_mass'])
large_mass = float(large['h2_mass'])
small_peak = float(small['max_X'])
large_peak = float(large['max_X'])
small_cloud_volume = float(small['cloud_volume'])
large_cloud_volume = float(large['cloud_volume'])
if not small_radius < large_radius:
    raise SystemExit(f'FAIL: expected small radius < large radius: small={small_radius}, large={large_radius}')
if not small_active < large_active:
    raise SystemExit(f'FAIL: active volume did not increase with radius: small={small_active}, large={large_active}')
if not small_mdot_vol > large_mdot_vol:
    raise SystemExit(f'FAIL: mdot_vol did not decrease with radius: small={small_mdot_vol}, large={large_mdot_vol}')
if abs(small_mass - large_mass) / max(small_mass, large_mass) > 5.0e-3:
    raise SystemExit(f'FAIL: same leak rate produced different total mass: small={small_mass}, large={large_mass}')
if small_peak <= large_peak + 2.0e-2:
    raise SystemExit(f'FAIL: small radius peak X did not exceed large radius enough: small={small_peak}, large={large_peak}')
if small_cloud_volume <= 0.0 or large_cloud_volume <= 0.0:
    raise SystemExit(f'FAIL: expected both radius cases to produce flammable clouds: small={small_cloud_volume}, large={large_cloud_volume}')

out.parent.mkdir(parents=True, exist_ok=True)
with out.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
print('h2_leak_open_domain_radius PASS ' +
      f'output={out} small_active={small_active:.8e} large_active={large_active:.8e} ' +
      f'small_mdot_vol={small_mdot_vol:.8e} large_mdot_vol={large_mdot_vol:.8e} ' +
      f'small_mass={small_mass:.8e} large_mass={large_mass:.8e} ' +
      f'small_peak_X={small_peak:.8e} large_peak_X={large_peak:.8e} ' +
      f'small_cloud_volume={small_cloud_volume:.8e} large_cloud_volume={large_cloud_volume:.8e}')
PYSUM

printf '[codex-smoke] PASS h2_leak open-domain radius sensitivity log_dir=%s summary=%s\n' "$log_dir" "$summary_csv"
