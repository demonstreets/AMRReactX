#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case_dir="$repo_root/examples/engineering/h2_leak_3d"
base_input="$case_dir/input.codex_open_domain_flammable_smoke"
log_dir="${CODEX_H2_LEAK_RELEASE_LOG_DIR:-/tmp/codex_h2_leak_open_domain_release_rate_$(date -u +%Y%m%dT%H%M%SZ)}"
input_dir="$log_dir/inputs"
summary_csv="$log_dir/release_rate_summary.csv"
mkdir -p "$input_dir"

make_input() {
  local name=$1
  local leak_rate=$2
  local dst="$input_dir/${name}.inputs"
  python3 - "$base_input" "$dst" "$leak_rate" <<'PYIN'
from pathlib import Path
import sys
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
leak_rate = float(sys.argv[3])
lines = []
for raw in src.read_text().splitlines():
    stripped = raw.strip()
    if stripped.startswith('prob.leak_rate'):
        lines.append(f'prob.leak_rate = {leak_rate:.8g}')
    else:
        lines.append(raw)
dst.write_text('\n'.join(lines) + '\n')
print(dst)
PYIN
}

run_case() {
  local name=$1
  local leak_rate=$2
  local input
  input=$(make_input "$name" "$leak_rate")
  local case_log_dir="$log_dir/$name"
  printf '[codex-smoke] running H2 open-domain release-rate case=%s leak_rate=%s input=%s\n' "$name" "$leak_rate" "$input"
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

run_case low_release 1.0e-3
run_case high_release 3.0e-3

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
for name in ('low_release', 'high_release'):
    case = log_dir / name
    profile = (case / 'profile_validation.log').read_text()
    hazard = (case / 'hazard_summary.log').read_text()
    planes = (case / 'hazard_planes.log').read_text()
    timeseries = (case / 'hazard_timeseries.log').read_text()
    run_input = next((case / 'run').glob('*.inputs'))
    input_text = run_input.read_text()
    row = {
        'case': name,
        'leak_rate': grab(r'prob\.leak_rate\s*=\s*([0-9.eE+-]+)', input_text, f'{name} leak_rate'),
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

low, high = rows
low_rate = float(low['leak_rate'])
high_rate = float(high['leak_rate'])
low_mass = float(low['h2_mass'])
high_mass = float(high['h2_mass'])
low_cloud_mass = float(low['cloud_species_mass'])
high_cloud_mass = float(high['cloud_species_mass'])
low_peak = float(low['max_X'])
high_peak = float(high['max_X'])
low_cloud_volume = float(low['cloud_volume'])
high_cloud_volume = float(high['cloud_volume'])
if high_rate <= low_rate:
    raise SystemExit(f'FAIL: high leak rate is not greater than low leak rate: low={low_rate}, high={high_rate}')
if high_mass / low_mass < 2.80:
    raise SystemExit(f'FAIL: H2 mass did not scale with leak rate enough: low={low_mass}, high={high_mass}')
if high_cloud_mass / low_cloud_mass < 1.80:
    raise SystemExit(f'FAIL: cloud H2 mass did not increase enough: low={low_cloud_mass}, high={high_cloud_mass}')
if high_peak <= low_peak + 5.0e-2:
    raise SystemExit(f'FAIL: high release peak X did not increase enough: low={low_peak}, high={high_peak}')
if high_cloud_volume < low_cloud_volume:
    raise SystemExit(f'FAIL: high release cloud volume regressed: low={low_cloud_volume}, high={high_cloud_volume}')

out.parent.mkdir(parents=True, exist_ok=True)
with out.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
print('h2_leak_open_domain_release_rate PASS ' +
      f'output={out} low_mass={low_mass:.8e} high_mass={high_mass:.8e} ' +
      f'low_cloud_mass={low_cloud_mass:.8e} high_cloud_mass={high_cloud_mass:.8e} ' +
      f'low_peak_X={low_peak:.8e} high_peak_X={high_peak:.8e} ' +
      f'low_cloud_volume={low_cloud_volume:.8e} high_cloud_volume={high_cloud_volume:.8e}')
PYSUM

printf '[codex-smoke] PASS h2_leak open-domain release-rate sensitivity log_dir=%s summary=%s\n' "$log_dir" "$summary_csv"
