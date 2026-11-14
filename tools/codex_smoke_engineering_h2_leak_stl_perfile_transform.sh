#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_STL_PERFILE_LOG_DIR:-/tmp/codex_h2_leak_stl_perfile_transform_$(date -u +%Y%m%dT%H%M%SZ)}"
summary_csv="$log_dir/stl_obstacle_summary.csv"
input_dir="$log_dir/inputs"
input_file="$input_dir/input.codex_stl_perfile_transform_smoke"
base_input="$repo_root/examples/engineering/h2_leak_3d/input.codex_stl_obstacle_smoke"

mkdir -p "$input_dir"
python3 - "$base_input" "$input_file" <<'PYINPUT'
import sys
from pathlib import Path

base = Path(sys.argv[1])
out = Path(sys.argv[2])
lines = base.read_text(encoding='utf-8').splitlines()
skip_prefixes = (
    'prob.obstacle_geometry',
    'prob.obstacle_stl_file',
    'prob.obstacle_stl_files',
    'prob.obstacle_stl_merged_file',
    'prob.obstacle_stl_scale',
    'prob.obstacle_stl_xc',
    'prob.obstacle_stl_yc',
    'prob.obstacle_stl_zc',
    'prob.obstacle_stl_reverse_normal',
    'prob.obstacle_stl_ngrow',
    'prob.obstacle_xc',
    'prob.obstacle_yc',
    'prob.obstacle_zc',
)
kept = [line for line in lines if not line.strip().startswith(skip_prefixes)]
kept.extend([
    '',
    '# Codex per-file STL transform smoke geometry.',
    'prob.obstacle_geometry = stl',
    'prob.obstacle_stl_files = cube_obstacle_binary.stl cube_obstacle_binary.stl',
    'prob.obstacle_stl_merged_file = codex_merged_perfile_transform_obstacles.stl',
    'prob.obstacle_stl_scale = 1.0',
    'prob.obstacle_stl_xc = 0.0',
    'prob.obstacle_stl_yc = 0.0',
    'prob.obstacle_stl_zc = 0.0',
    'prob.obstacle_stl_scales = 0.10 0.08',
    'prob.obstacle_stl_xcs = 0.95 1.30',
    'prob.obstacle_stl_ycs = 0.40 0.65',
    'prob.obstacle_stl_zcs = 0.50 0.50',
    'prob.obstacle_stl_reverse_normal = 0',
    'prob.obstacle_stl_ngrow = 4',
    '# Keep scalar center fields populated so STL defaults and diagnostics remain stable.',
    'prob.obstacle_xc = 0.0',
    'prob.obstacle_yc = 0.0',
    'prob.obstacle_zc = 0.0',
])
out.write_text('\n'.join(kept) + '\n', encoding='utf-8')
PYINPUT

CODEX_H2_LEAK_PROFILE_INPUT="$input_file" \
CODEX_H2_LEAK_HISTORY_EXTRA_FILES="cube_obstacle_binary.stl" \
CODEX_H2_LEAK_STL_LOG_DIR="$log_dir" \
RUN_TIMEOUT="${RUN_TIMEOUT:-900}" \
JOBS="${JOBS:-4}" \
  "$repo_root/tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh"

python3 - "$summary_csv" "$log_dir/run.log" <<'PYCHECK'
import csv
import math
import sys
from pathlib import Path

summary = Path(sys.argv[1])
run_log = Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
rows = list(csv.DictReader(summary.open(newline='', encoding='utf-8')))
if len(rows) != 1:
    raise SystemExit(f'FAIL: expected one per-file STL transform summary row, got {len(rows)}')
row = rows[0]
expected_sources = 'cube_obstacle_binary.stl;cube_obstacle_binary.stl'
if row.get('stl_source_files') != expected_sources:
    raise SystemExit(f'FAIL: unexpected STL source list {row.get("stl_source_files")}')
if row.get('stl_file') != 'codex_merged_perfile_transform_obstacles.stl':
    raise SystemExit(f'FAIL: unexpected merged STL file {row.get("stl_file")}')
if row.get('stl_format') != 'binary':
    raise SystemExit(f'FAIL: merged STL QA did not identify binary format: {row.get("stl_format")}')
if int(row.get('stl_vertices', '0')) != 72:
    raise SystemExit(f'FAIL: expected 72 merged STL vertices, got {row.get("stl_vertices")}')

def parse_vec(text):
    return [float(x) for x in text.split(',')]

def assert_close_vec(label, actual, expected, tol=2.5e-7):
    if len(actual) != len(expected):
        raise SystemExit(f'FAIL: {label} dimension mismatch: {actual}')
    for a, e in zip(actual, expected):
        if not math.isclose(a, e, rel_tol=0.0, abs_tol=tol):
            raise SystemExit(f'FAIL: {label} expected {expected}, got {actual}')

assert_close_vec('raw_bounds_lo', parse_vec(row['raw_bounds_lo']), [0.85, 0.30, 0.40])
assert_close_vec('raw_bounds_hi', parse_vec(row['raw_bounds_hi']), [1.38, 0.73, 0.60])
assert_close_vec('scaled_bounds_lo', parse_vec(row['scaled_bounds_lo']), [0.85, 0.30, 0.40])
assert_close_vec('scaled_bounds_hi', parse_vec(row['scaled_bounds_hi']), [1.38, 0.73, 0.60])
for needle in [
    ('Engineering leak UserDefined EB STL files: count=2', 'H2 leak UserDefined EB STL files: count=2'),
    'per_file_transforms=1',
    'buildFromSTLFilesWithTransforms: merging 2 STL files into codex_merged_perfile_transform_obstacles.stl',
    'stl_file[0]=cube_obstacle_binary.stl, scale=0.1, center=(0.95,0.4,0.5)',
    'stl_file[1]=cube_obstacle_binary.stl, scale=0.08, center=(1.3,0.65,0.5)',
    'buildFromSTL QA: file=codex_merged_perfile_transform_obstacles.stl, format=binary',
]:
    if isinstance(needle, tuple):
        ok = any(item in run_log for item in needle)
    else:
        ok = needle in run_log
    if not ok:
        raise SystemExit(f'FAIL: missing per-file STL transform log marker: {needle}')
if float(row['cloud_volume']) <= 0.0:
    raise SystemExit('FAIL: per-file STL transform case did not produce a flammable cloud')
print('h2_leak_stl_perfile_transform PASS ' +
      f'output={summary} mass_ratio={float(row["mass_ratio"]):.8e} ' +
      f'cloud_volume={float(row["cloud_volume"]):.8e} ' +
      f'active_planes={row["active_planes"]} flammable_planes={row["flammable_planes"]} ' +
      f'max_X={float(row["max_X"]):.8e}')
PYCHECK

printf '[codex-smoke] PASS h2_leak per-file STL transform validation log_dir=%s summary=%s\n' "$log_dir" "$summary_csv"
