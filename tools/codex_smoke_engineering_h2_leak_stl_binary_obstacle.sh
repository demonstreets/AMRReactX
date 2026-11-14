#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_STL_BINARY_LOG_DIR:-/tmp/codex_h2_leak_stl_binary_obstacle_$(date -u +%Y%m%dT%H%M%SZ)}"
summary_csv="$log_dir/stl_obstacle_summary.csv"

CODEX_H2_LEAK_PROFILE_INPUT=input.codex_stl_binary_obstacle_smoke \
CODEX_H2_LEAK_HISTORY_EXTRA_FILES=cube_obstacle_binary.stl \
CODEX_H2_LEAK_STL_LOG_DIR="$log_dir" \
  "$repo_root/tools/codex_smoke_engineering_h2_leak_stl_obstacle.sh"

python3 - "$summary_csv" "$log_dir/run.log" <<'PYCHECK'
import csv
import sys
from pathlib import Path
summary = Path(sys.argv[1])
run_log = Path(sys.argv[2]).read_text()
rows = list(csv.DictReader(summary.open(newline='', encoding='utf-8')))
if len(rows) != 1:
    raise SystemExit(f'FAIL: expected one binary STL summary row, got {len(rows)}')
row = rows[0]
if row.get('stl_file') != 'cube_obstacle_binary.stl':
    raise SystemExit(f'FAIL: unexpected STL file {row.get("stl_file")}')
if row.get('stl_format') != 'binary':
    raise SystemExit(f'FAIL: STL QA did not identify binary format: {row.get("stl_format")}')
if int(row.get('stl_vertices', '0')) != 36:
    raise SystemExit(f'FAIL: expected 36 STL vertices, got {row.get("stl_vertices")}')
if row.get('scaled_bounds_lo') != '0.9,0.4,0.4' or row.get('scaled_bounds_hi') != '1.1,0.6,0.6':
    raise SystemExit(f'FAIL: unexpected binary STL scaled bounds: {row.get("scaled_bounds_lo")} {row.get("scaled_bounds_hi")}')
if 'buildFromSTL QA: file=cube_obstacle_binary.stl, format=binary' not in run_log:
    raise SystemExit('FAIL: missing binary buildFromSTL QA log line')
print('h2_leak_stl_binary_obstacle PASS ' +
      f'output={summary} mass_ratio={float(row["mass_ratio"]):.8e} ' +
      f'cloud_volume={float(row["cloud_volume"]):.8e} ' +
      f'active_planes={row["active_planes"]} flammable_planes={row["flammable_planes"]} ' +
      f'max_X={float(row["max_X"]):.8e}')
PYCHECK

printf '[codex-smoke] PASS h2_leak binary STL obstacle validation log_dir=%s summary=%s\n' "$log_dir" "$summary_csv"
