#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_TANK_BLOWDOWN_LOG_DIR:-/tmp/codex_h2_leak_tank_blowdown_$(date -u +%Y%m%dT%H%M%SZ)}"

CODEX_H2_LEAK_HISTORY_INPUT=input.codex_tank_blowdown_smoke \
CODEX_H2_LEAK_HISTORY_LOG_DIR="$log_dir" \
CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="${CODEX_H2_LEAK_TANK_BLOWDOWN_MIN_MASS_GROWTH_RATIO:-4.0}" \
CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO="${CODEX_H2_LEAK_TANK_BLOWDOWN_MIN_FINAL_MASS_RATIO:-0.80}" \
CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO="${CODEX_H2_LEAK_TANK_BLOWDOWN_MAX_FINAL_MASS_RATIO:-1.50}" \
"$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"

run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"

grep -q 'H2 leak tank-blowdown model:' "$run_log"
grep -q 'Applying H2 leak source: model=tank_blowdown' "$run_log"
grep -q 'H2 leak source interval:' "$run_log"

python3 - "$run_log" "$validation_log" <<'PYCHK'
import re
import sys
from pathlib import Path

run_log_path, validation_path = sys.argv[1:]
log_lines = Path(run_log_path).read_text(errors='replace').splitlines()
validation = Path(validation_path).read_text(errors='replace')
current_step = None
intervals = []
for raw in log_lines:
    sm = re.search(r'STEP \[(-?\d+)\] - Time:', raw)
    if sm:
        current_step = int(sm.group(1))
        continue
    bm = re.search(r'H2 leak tank-blowdown model: time=([0-9.eE+-]+), dt=([0-9.eE+-]+), tank_volume=([0-9.eE+-]+), (?:compressibility_factor=([0-9.eE+-]+), )?initial_pressure=([0-9.eE+-]+), pressure_start=([0-9.eE+-]+), pressure_end=([0-9.eE+-]+), injected_interval=([0-9.eE+-]+), cumulative_injected=([0-9.eE+-]+), substeps=(\d+)', raw)
    if not bm or current_step is None or current_step < 0:
        continue
    intervals.append({
        'time': float(bm.group(1)),
        'dt': float(bm.group(2)),
        'volume': float(bm.group(3)),
        'compressibility_factor': float(bm.group(4)) if bm.group(4) is not None else 1.0,
        'initial_pressure': float(bm.group(5)),
        'pressure_start': float(bm.group(6)),
        'pressure_end': float(bm.group(7)),
        'injected': float(bm.group(8)),
        'cumulative': float(bm.group(9)),
        'substeps': int(bm.group(10)),
    })

if len(intervals) < 5:
    raise SystemExit(f'FAIL: too few tank-blowdown intervals: {len(intervals)}')
first = intervals[0]
last = intervals[-1]
if not last['pressure_end'] < first['pressure_start']:
    raise SystemExit(f'FAIL: tank pressure did not decrease: first={first} last={last}')
if not last['injected'] / last['dt'] < first['injected'] / first['dt']:
    raise SystemExit(f'FAIL: tank blowdown mdot did not decrease: first={first} last={last}')
if not all(row['injected'] > 0.0 for row in intervals):
    raise SystemExit('FAIL: nonpositive tank-blowdown interval injection')
if not all(intervals[i + 1]['cumulative'] > intervals[i]['cumulative'] for i in range(len(intervals) - 1)):
    raise SystemExit('FAIL: tank-blowdown cumulative injection is not increasing')

vm = re.search(r'injectedN=([0-9.eE+-]+) mass_ratioN=([0-9.eE+-]+)', validation)
if not vm:
    raise SystemExit('FAIL: missing injectedN/mass_ratioN in validation')
injected_n = float(vm.group(1))
mass_ratio = float(vm.group(2))
rel = abs(injected_n - last['cumulative']) / max(injected_n, 1.0e-300)
if rel > 2.0e-6:
    raise SystemExit(f'FAIL: validation injected mass does not match blowdown cumulative: validation={injected_n} cumulative={last["cumulative"]} rel={rel}')
if not 0.95 <= mass_ratio <= 1.05:
    raise SystemExit(f'FAIL: tank-blowdown mass ratio outside tight smoke bounds: {mass_ratio}')
pressure_drop = first['pressure_start'] - last['pressure_end']
mdot_drop = first['injected'] / first['dt'] - last['injected'] / last['dt']
print(f'h2_leak_tank_blowdown PASS intervals={len(intervals)} pressure_drop={pressure_drop:.8e} mdot_drop={mdot_drop:.8e} injected={injected_n:.8e} mass_ratioN={mass_ratio:.8e}')
PYCHK
