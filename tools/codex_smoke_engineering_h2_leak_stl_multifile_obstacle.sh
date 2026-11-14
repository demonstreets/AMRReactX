#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_STL_MULTIFILE_LOG_DIR:-/tmp/codex_h2_leak_stl_multifile_obstacle_$(date -u +%Y%m%dT%H%M%SZ)}"
summary_csv="$log_dir/stl_obstacle_summary.csv"

CODEX_H2_LEAK_PROFILE_INPUT=input.codex_stl_multifile_obstacle_smoke \
CODEX_H2_LEAK_HISTORY_EXTRA_FILES="multi_cube_obstacle_a_binary.stl multi_cube_obstacle_b_binary.stl" \
CODEX_H2_LEAK_STL_LOG_DIR="$log_dir" \
  "$repo_root/tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh"

python3 - "$summary_csv" "$log_dir/run.log" <<'PYCHECK'
import csv
import math
import sys
from pathlib import Path

summary = Path(sys.argv[1])
run_log = Path(sys.argv[2]).read_text()
rows = list(csv.DictReader(summary.open(newline='', encoding='utf-8')))
if len(rows) != 1:
    raise SystemExit(f'FAIL: expected one multi-file STL summary row, got {len(rows)}')
row = rows[0]
expected_sources = 'multi_cube_obstacle_a_binary.stl;multi_cube_obstacle_b_binary.stl'
if row.get('stl_source_files') != expected_sources:
    raise SystemExit(f'FAIL: unexpected STL source list {row.get("stl_source_files")}')
if row.get('stl_file') != 'codex_merged_two_cube_obstacles.stl':
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

assert_close_vec('scaled_bounds_lo', parse_vec(row['scaled_bounds_lo']), [0.9, 0.28, 0.4])
assert_close_vec('scaled_bounds_hi', parse_vec(row['scaled_bounds_hi']), [1.38, 0.72, 0.6])
for needle in [
    ('Engineering leak UserDefined EB STL files: count=2', 'H2 leak UserDefined EB STL files: count=2'),
    'buildFromSTLFiles: merging 2 STL files into codex_merged_two_cube_obstacles.stl',
    'stl_file[0]=multi_cube_obstacle_a_binary.stl',
    'stl_file[1]=multi_cube_obstacle_b_binary.stl',
    'buildFromSTL QA: file=codex_merged_two_cube_obstacles.stl, format=binary',
]:
    if isinstance(needle, tuple):
        ok = any(item in run_log for item in needle)
    else:
        ok = needle in run_log
    if not ok:
        raise SystemExit(f'FAIL: missing multi-file STL log marker: {needle}')
if float(row['cloud_volume']) <= 0.0:
    raise SystemExit('FAIL: multi-file STL case did not produce a flammable cloud')
print('h2_leak_stl_multifile_obstacle PASS ' +
      f'output={summary} mass_ratio={float(row["mass_ratio"]):.8e} ' +
      f'cloud_volume={float(row["cloud_volume"]):.8e} ' +
      f'active_planes={row["active_planes"]} flammable_planes={row["flammable_planes"]} ' +
      f'max_X={float(row["max_X"]):.8e}')
PYCHECK

printf '[codex-smoke] PASS h2_leak multi-file STL obstacle validation log_dir=%s summary=%s\n' "$log_dir" "$summary_csv"
