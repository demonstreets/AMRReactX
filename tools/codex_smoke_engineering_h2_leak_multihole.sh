#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_MULTIHOLE_LOG_DIR:-/tmp/codex_h2_leak_multihole_$(date -u +%Y%m%dT%H%M%SZ)}"

CODEX_H2_LEAK_HISTORY_INPUT=input.codex_multihole_smoke \
CODEX_H2_LEAK_HISTORY_LOG_DIR="$log_dir" \
CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="${CODEX_H2_LEAK_MULTIHOLE_MIN_MASS_GROWTH_RATIO:-4.0}" \
CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO="${CODEX_H2_LEAK_MULTIHOLE_MIN_FINAL_MASS_RATIO:-0.95}" \
CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO="${CODEX_H2_LEAK_MULTIHOLE_MAX_FINAL_MASS_RATIO:-1.05}" \
"$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"

run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"
input_file="$log_dir/run/input.codex_multihole_smoke"

grep -q 'Applying H2 leak source: model=fixed_mass_flow' "$run_log"
grep -q 'leak_count=3' "$run_log"
grep -q 'H2 leak source\[0\]:' "$run_log"
grep -q 'H2 leak source\[1\]:' "$run_log"
grep -q 'H2 leak source\[2\]:' "$run_log"

python3 - "$input_file" "$run_log" "$validation_log" <<'PYCHK'
import math
import re
import sys
from pathlib import Path

def parse_input(path):
    vals = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line or '=' not in line:
            continue
        key, value = line.split('=', 1)
        vals[key.strip()] = value.strip().split()
    return vals

def first_float(vals, key, default=None):
    if key not in vals:
        if default is None:
            raise KeyError(key)
        return default
    return float(vals[key][0])

input_path, run_log_path, validation_path = sys.argv[1:]
vals = parse_input(input_path)
log = Path(run_log_path).read_text(errors='replace')
validation = Path(validation_path).read_text(errors='replace')
leak_count = int(first_float(vals, 'prob.leak_count'))
if leak_count != 3:
    raise SystemExit(f'FAIL: expected leak_count=3, got {leak_count}')
leak_rate = first_float(vals, 'prob.leak_rate')
fractions = [first_float(vals, f'prob.leak{i}_fraction') for i in range(leak_count)]
fraction_sum = sum(fractions)
if fraction_sum <= 0.0:
    raise SystemExit('FAIL: nonpositive fraction sum')
source_rows = re.findall(
    r'H2 leak source\[(\d+)\]: center=\(([^)]*)\), radius=([0-9.eE+-]+), '
    r'fraction=([0-9.eE+-]+), (?:pressure_fraction=([0-9.eE+-]+), )?'
    r'mdot=([0-9.eE+-]+), active_volume=([0-9.eE+-]+), '
    r'mdot_vol=([0-9.eE+-]+)',
    log)
if len(source_rows) < leak_count:
    raise SystemExit(f'FAIL: expected at least {leak_count} source rows, got {len(source_rows)}')
first_step = {}
for row in source_rows:
    idx = int(row[0])
    if idx not in first_step:
        first_step[idx] = row
if sorted(first_step) != list(range(leak_count)):
    raise SystemExit(f'FAIL: missing source indices in first source block: {sorted(first_step)}')
mdot_sum = 0.0
for idx in range(leak_count):
    row = first_step[idx]
    frac = float(row[3])
    mdot = float(row[5])
    active = float(row[6])
    mdot_vol = float(row[7])
    expected_frac = fractions[idx] / fraction_sum
    expected_mdot = leak_rate * expected_frac
    if abs(frac - expected_frac) > 5.0e-7:
        raise SystemExit(f'FAIL: source {idx} fraction mismatch: {frac} vs {expected_frac}')
    if abs(mdot - expected_mdot) / max(expected_mdot, 1.0e-300) > 5.0e-7:
        raise SystemExit(f'FAIL: source {idx} mdot mismatch: {mdot} vs {expected_mdot}')
    if active <= 0.0 or mdot_vol <= 0.0:
        raise SystemExit(f'FAIL: source {idx} inactive: active={active} mdot_vol={mdot_vol}')
    mdot_sum += mdot
if abs(mdot_sum - leak_rate) / max(leak_rate, 1.0e-300) > 5.0e-7:
    raise SystemExit(f'FAIL: source mdot sum mismatch: {mdot_sum} vs {leak_rate}')
ratio = re.search(r'mass_ratioN=([0-9.eE+-]+)', validation)
if not ratio:
    raise SystemExit('FAIL: missing mass_ratioN in validation log')
mass_ratio = float(ratio.group(1))
if not 0.95 <= mass_ratio <= 1.05:
    raise SystemExit(f'FAIL: multihole mass ratio outside tight bounds: {mass_ratio}')
print(f'h2_leak_multihole PASS leak_count={leak_count} mdot_sum={mdot_sum:.8e} mass_ratioN={mass_ratio:.8e}')
PYCHK
