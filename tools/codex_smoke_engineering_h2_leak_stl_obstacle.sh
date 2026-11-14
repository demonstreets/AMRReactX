#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_STL_LOG_DIR:-/tmp/codex_h2_leak_stl_obstacle_$(date -u +%Y%m%dT%H%M%SZ)}"
summary_csv="$log_dir/stl_obstacle_summary.csv"

export CODEX_H2_LEAK_PROFILE_INPUT="${CODEX_H2_LEAK_PROFILE_INPUT:-input.codex_stl_obstacle_smoke}"
export CODEX_H2_LEAK_HISTORY_EXTRA_FILES="${CODEX_H2_LEAK_HISTORY_EXTRA_FILES:-cube_obstacle.stl}"
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

python3 - "$log_dir" "$summary_csv" "$(basename "$CODEX_H2_LEAK_PROFILE_INPUT")" <<'PYSUM'
import csv
import re
import sys
from pathlib import Path

log_dir = Path(sys.argv[1])
out = Path(sys.argv[2])
input_base = sys.argv[3]
run_dir = log_dir / 'run'
run_log = (log_dir / 'run.log').read_text()
profile = (log_dir / 'profile_validation.log').read_text()
hazard = (log_dir / 'hazard_summary.log').read_text()
planes = (log_dir / 'hazard_planes.log').read_text()
timeseries = (log_dir / 'hazard_timeseries.log').read_text()
input_path = run_dir / input_base
if not input_path.is_file():
    raise SystemExit(f'FAIL: missing copied STL obstacle input: {input_base}')
input_text = input_path.read_text()

def grab(pattern, text, label):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f'FAIL: missing {label}')
    return m.group(1)

single_stl = re.search(r'prob\.obstacle_stl_file\s*=\s*(\S+)', input_text)
multi_stl = re.search(r'prob\.obstacle_stl_files\s*=\s*(.+)', input_text)
if multi_stl:
    stl_source_files = multi_stl.group(1).split('#', 1)[0].split()
elif single_stl:
    stl_source_files = [single_stl.group(1)]
else:
    raise SystemExit('FAIL: missing obstacle_stl_file or obstacle_stl_files')
for source_file in stl_source_files:
    if not (run_dir / source_file).is_file():
        raise SystemExit(f'FAIL: copied STL asset missing from run directory: {source_file}')

if len(stl_source_files) > 1:
    if ('Engineering leak UserDefined EB STL files:' not in run_log and
        'H2 leak UserDefined EB STL files:' not in run_log):
        raise SystemExit('FAIL: multi-file UserDefined EB STL branch was not constructed')
    if ('buildFromSTLFiles: merging' not in run_log and
        'buildFromSTLFilesWithTransforms: merging' not in run_log):
        raise SystemExit('FAIL: buildFromSTLFiles merge report missing from run log')
else:
    if ('Engineering leak UserDefined EB STL:' not in run_log and
        'H2 leak UserDefined EB STL:' not in run_log):
        raise SystemExit('FAIL: UserDefined EB STL branch was not constructed')
qa = re.search(r'buildFromSTL QA: file=(\S+), format=(\S+), vertices=([0-9]+), .*raw_bounds=\(\[([^\]]+)\],\[([^\]]+)\]\), scaled_bounds=\(\[([^\]]+)\],\[([^\]]+)\]\)', run_log)
if not qa:
    raise SystemExit('FAIL: buildFromSTL QA bounds report missing from run log')
stl_file = qa.group(1)
if not (run_dir / stl_file).is_file():
    raise SystemExit(f'FAIL: built STL asset missing from run directory: {stl_file}')
if 'buildFromSTL: built AMReX EB2 IndexSpace' not in run_log:
    raise SystemExit('FAIL: AMReX EB2 STL IndexSpace was not built')
if 'Resetting fine-covered cells mask' not in run_log:
    raise SystemExit('FAIL: EB fine-covered-cell mask was not initialized')
if 'Unused ParmParse Variables' in run_log:
    raise SystemExit('FAIL: unused ParmParse variables present')
if 'RuntimeWarning' in run_log:
    raise SystemExit('FAIL: runtime warning present in run log')

row = {
    'case': input_base,
    'stl_file': stl_file,
    'stl_source_files': ';'.join(stl_source_files),
    'stl_scale': grab(r'prob\.obstacle_stl_scale\s*=\s*([0-9.eE+-]+)', input_text, 'obstacle_stl_scale'),
    'stl_xc': grab(r'prob\.obstacle_stl_xc\s*=\s*([0-9.eE+-]+)', input_text, 'obstacle_stl_xc'),
    'stl_yc': grab(r'prob\.obstacle_stl_yc\s*=\s*([0-9.eE+-]+)', input_text, 'obstacle_stl_yc'),
    'stl_zc': grab(r'prob\.obstacle_stl_zc\s*=\s*([0-9.eE+-]+)', input_text, 'obstacle_stl_zc'),
    'stl_format': qa.group(2),
    'stl_vertices': qa.group(3),
    'raw_bounds_lo': qa.group(4),
    'raw_bounds_hi': qa.group(5),
    'scaled_bounds_lo': qa.group(6),
    'scaled_bounds_hi': qa.group(7),
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

mass_ratio = float(row['mass_ratio'])
cloud_volume = float(row['cloud_volume'])
active_planes = int(row['active_planes'])
flammable_planes = int(row['flammable_planes'])
plotfiles = int(row['plotfiles'])
stl_vertices = int(row['stl_vertices'])
if stl_vertices <= 0:
    raise SystemExit(f'FAIL: STL QA reported no vertices: {stl_vertices}')
if row['stl_format'] not in {'ascii', 'binary'}:
    raise SystemExit(f'FAIL: unknown STL QA format: {row["stl_format"]}')
if not (0.95 <= mass_ratio <= 1.05):
    raise SystemExit(f'FAIL: STL obstacle mass ratio out of range: {mass_ratio}')
if cloud_volume <= 0.0:
    raise SystemExit('FAIL: STL obstacle case did not produce a flammable cloud')
if active_planes < 3 or flammable_planes < 1:
    raise SystemExit(f'FAIL: insufficient STL obstacle hazard planes: active={active_planes} flammable={flammable_planes}')
if plotfiles < 7:
    raise SystemExit(f'FAIL: insufficient STL obstacle timeseries plotfiles: {plotfiles}')

out.parent.mkdir(parents=True, exist_ok=True)
with out.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=list(row.keys()))
    writer.writeheader()
    writer.writerow(row)
print('h2_leak_stl_obstacle PASS ' +
      f'output={out} mass_ratio={mass_ratio:.8e} cloud_volume={cloud_volume:.8e} ' +
      f'active_planes={active_planes} flammable_planes={flammable_planes} ' +
      f'max_X={float(row["max_X"]):.8e}')
PYSUM

printf '[codex-smoke] PASS h2_leak STL obstacle validation log_dir=%s summary=%s\n' "$log_dir" "$summary_csv"
