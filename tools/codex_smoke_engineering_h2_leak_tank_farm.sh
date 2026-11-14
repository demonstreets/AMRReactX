#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_TANK_FARM_LOG_DIR:-/tmp/codex_h2_leak_tank_farm_$(date -u +%Y%m%dT%H%M%SZ)}"
summary_csv="$log_dir/tank_farm_summary.csv"

export CODEX_H2_LEAK_PROFILE_INPUT="${CODEX_H2_LEAK_PROFILE_INPUT:-input.codex_tank_farm_smoke}"
export CODEX_H2_LEAK_FLAMMABLE_LOG_DIR="$log_dir"
export CODEX_H2_LEAK_PLANE_MIN_X="${CODEX_H2_LEAK_PLANE_MIN_X:-0.70}"
export CODEX_H2_LEAK_MIN_ACTIVE_PLANES="${CODEX_H2_LEAK_MIN_ACTIVE_PLANES:-3}"
export CODEX_H2_LEAK_MIN_FLAMMABLE_PLANES="${CODEX_H2_LEAK_MIN_FLAMMABLE_PLANES:-1}"
export CODEX_H2_LEAK_MIN_FLAMMABLE_VOLUME="${CODEX_H2_LEAK_MIN_FLAMMABLE_VOLUME:-2.0e-4}"
export CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME="${CODEX_H2_LEAK_MAX_FLAMMABLE_VOLUME:-2.5e-1}"
export CODEX_H2_LEAK_MIN_MAX_X="${CODEX_H2_LEAK_MIN_MAX_X:-4.0e-2}"
export CODEX_H2_LEAK_MAX_MAX_X="${CODEX_H2_LEAK_MAX_MAX_X:-7.5e-1}"
export CODEX_H2_LEAK_MIN_TIMESERIES_PLOTFILES="${CODEX_H2_LEAK_MIN_TIMESERIES_PLOTFILES:-7}"
export CODEX_H2_LEAK_HISTORY_MIN_UPSTREAM_FRACTION="${CODEX_H2_LEAK_HISTORY_MIN_UPSTREAM_FRACTION:-0.05}"

"$repo_root/tools/codex_smoke_engineering_h2_leak_flammable_cloud.sh"

python3 - "$log_dir" "$summary_csv" <<'PYSUM'
import csv
import re
import sys
from pathlib import Path

log_dir = Path(sys.argv[1])
out = Path(sys.argv[2])
run_log = (log_dir / 'run.log').read_text()
profile = (log_dir / 'profile_validation.log').read_text()
hazard = (log_dir / 'hazard_summary.log').read_text()
planes = (log_dir / 'hazard_planes.log').read_text()
timeseries = (log_dir / 'hazard_timeseries.log').read_text()
run_inputs = list((log_dir / 'run').glob('input.codex_tank_farm_smoke'))
if not run_inputs:
    run_inputs = list((log_dir / 'run').glob('*.inputs'))
if not run_inputs:
    raise SystemExit('FAIL: missing copied tank-farm input')
input_text = run_inputs[0].read_text()

def grab(pattern, text, label):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f'FAIL: missing {label}')
    return m.group(1)

if ('Engineering leak UserDefined EB cylinders: count=3' not in run_log and
    'H2 leak UserDefined EB cylinders: count=3' not in run_log):
    raise SystemExit('FAIL: three-cylinder UserDefined EB union was not constructed')
if '  obstacle2:' not in run_log:
    raise SystemExit('FAIL: third obstacle was not reported in EB setup')
if 'Resetting fine-covered cells mask' not in run_log:
    raise SystemExit('FAIL: EB fine-covered-cell mask was not initialized')
if 'Unused ParmParse Variables' in run_log:
    raise SystemExit('FAIL: unused ParmParse variables present')
if 'RuntimeWarning' in run_log:
    raise SystemExit('FAIL: runtime warning present in run log')

row = {
    'case': 'tank_farm_3cyl',
    'obstacle_count': grab(r'prob\.obstacle_count\s*=\s*([0-9]+)', input_text, 'obstacle_count'),
    'obstacle0_xc': grab(r'prob\.obstacle0_xc\s*=\s*([0-9.eE+-]+)', input_text, 'obstacle0_xc'),
    'obstacle0_yc': grab(r'prob\.obstacle0_yc\s*=\s*([0-9.eE+-]+)', input_text, 'obstacle0_yc'),
    'obstacle1_xc': grab(r'prob\.obstacle1_xc\s*=\s*([0-9.eE+-]+)', input_text, 'obstacle1_xc'),
    'obstacle1_yc': grab(r'prob\.obstacle1_yc\s*=\s*([0-9.eE+-]+)', input_text, 'obstacle1_yc'),
    'obstacle2_xc': grab(r'prob\.obstacle2_xc\s*=\s*([0-9.eE+-]+)', input_text, 'obstacle2_xc'),
    'obstacle2_yc': grab(r'prob\.obstacle2_yc\s*=\s*([0-9.eE+-]+)', input_text, 'obstacle2_yc'),
    'mass_ratio': grab(r'mass_ratio=([0-9.eE+-]+)', profile, 'mass_ratio'),
    'h2_mass': grab(r'h2_mass=([0-9.eE+-]+)', profile, 'h2_mass'),
    'centroid_shift': grab(r'centroid_shift=([0-9.eE+-]+)', profile, 'centroid_shift'),
    'downstream_fraction': grab(r'downstream_fraction=([0-9.eE+-]+)', profile, 'downstream_fraction'),
    'cloud_volume': grab(r'cloud_volume=([0-9.eE+-]+)', hazard, 'cloud_volume'),
    'cloud_species_mass': grab(r'cloud_species_mass=([0-9.eE+-]+)', hazard, 'cloud_species_mass'),
    'max_X': grab(r'max_X=([0-9.eE+-]+)', hazard, 'max_X'),
    'active_planes': grab(r'active_planes=([0-9]+)', planes, 'active_planes'),
    'flammable_planes': grab(r'flammable_planes=([0-9]+)', planes, 'flammable_planes'),
    'final_cloud_volume': grab(r'final_cloud_volume=([0-9.eE+-]+)', timeseries, 'final_cloud_volume'),
    'final_peak_X': grab(r'final_peak_X=([0-9.eE+-]+)', timeseries, 'final_peak_X'),
    'plotfiles': grab(r'plotfiles=([0-9]+)', timeseries, 'plotfiles'),
    'log_dir': str(log_dir),
}

if row['obstacle_count'] != '3':
    raise SystemExit(f'FAIL: expected obstacle_count=3, got {row["obstacle_count"]}')
mass_ratio = float(row['mass_ratio'])
cloud_volume = float(row['cloud_volume'])
active_planes = int(row['active_planes'])
flammable_planes = int(row['flammable_planes'])
plotfiles = int(row['plotfiles'])
if not (0.95 <= mass_ratio <= 1.05):
    raise SystemExit(f'FAIL: tank-farm mass ratio out of range: {mass_ratio}')
if cloud_volume <= 0.0:
    raise SystemExit('FAIL: tank-farm case did not produce a flammable cloud')
if active_planes < 3 or flammable_planes < 1:
    raise SystemExit(f'FAIL: insufficient tank-farm hazard planes: active={active_planes} flammable={flammable_planes}')
if plotfiles < 7:
    raise SystemExit(f'FAIL: insufficient tank-farm timeseries plotfiles: {plotfiles}')

out.parent.mkdir(parents=True, exist_ok=True)
with out.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=list(row.keys()))
    writer.writeheader()
    writer.writerow(row)
print('h2_leak_tank_farm PASS ' +
      f'output={out} mass_ratio={mass_ratio:.8e} cloud_volume={cloud_volume:.8e} ' +
      f'active_planes={active_planes} flammable_planes={flammable_planes} ' +
      f'max_X={float(row["max_X"]):.8e}')
PYSUM

printf '[codex-smoke] PASS h2_leak tank-farm validation log_dir=%s summary=%s\n' "$log_dir" "$summary_csv"
