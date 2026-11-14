#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
root="${CODEX_TWOPHASE_RT_ROOT:-$repo_root/docs/codex_audit/evidence/academic_twophase_rayleigh_taylor_validation_20260728}"
run_root="$root/runs"
manifest="$root/case_manifest.json"

rm -rf "$run_root"
mkdir -p "$run_root"

CODEX_RAYLEIGH_TAYLOR_TREND_LOG_DIR="$run_root" \
  CODEX_RAYLEIGH_TAYLOR_TREND_STOP_TIME="${CODEX_TWOPHASE_RT_STOP_TIME:-1.6e-2}" \
  CODEX_RAYLEIGH_TAYLOR_TREND_MAX_STEP="${CODEX_TWOPHASE_RT_MAX_STEP:-4000}" \
  CODEX_RAYLEIGH_TAYLOR_TREND_NX="${CODEX_TWOPHASE_RT_NX:-32 64 96}" \
  RUN_TIMEOUT="${RUN_TIMEOUT:-600}" \
  JOBS="${JOBS:-4}" \
  "$repo_root/tools/codex_smoke_academic_rayleigh_taylor_resolution_trend.sh"

python3 - "$manifest" "$run_root" <<'PY'
import json
import re
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
run_root = Path(sys.argv[2])
cases = []
for run_dir in sorted(run_root.glob('run_*x*')):
    match = re.search(r'run_(\d+)x(\d+)$', run_dir.name)
    if not match:
        continue
    nx = int(match.group(1))
    ny = int(match.group(2))
    plotfiles = sorted(p.name for p in run_dir.glob('plt[0-9][0-9][0-9][0-9][0-9]') if p.name != 'plt00000')
    if not plotfiles:
        raise SystemExit(f'{run_dir} has no final plotfile')
    input_files = sorted(run_dir.glob('input.codex_growth_*x*'))
    if len(input_files) != 1:
        raise SystemExit(f'{run_dir} has unexpected input files: {input_files}')
    cases.append({
        'name': f'rt_{nx}x{ny}',
        'n_cell': [nx, ny, 1],
        'run_dir': str(run_dir),
        'input_file': str(input_files[0]),
        'run_log': str(run_root / f'run_{nx}x{ny}.log'),
        'conservation_log': str(run_root / f'conservation_{nx}x{ny}.log'),
        'growth_log': str(run_root / f'growth_{nx}x{ny}.log'),
        'plotfile_initial': str(run_dir / 'plt00000'),
        'plotfile_final': str(run_dir / plotfiles[-1]),
    })
if len(cases) < 3:
    raise SystemExit(f'expected at least three cases, got {len(cases)}')
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps({
    'cases': cases,
    'build_log': str(run_root / 'build.log'),
    'resolution_trend_log': str(run_root / 'resolution_trend.log'),
}, indent=2, sort_keys=True) + '\n', encoding='utf-8')
PY

python3 "$repo_root/tools/write_academic_twophase_rayleigh_taylor_validation_report.py" \
  --manifest "$manifest"
python3 "$repo_root/tools/write_academic_twophase_rayleigh_taylor_validation_report.py" \
  --verify-json "$root/academic_twophase_rayleigh_taylor_validation_report.json"

printf '[academic-twophase-rt] PASS root=%s\n' "$root"
