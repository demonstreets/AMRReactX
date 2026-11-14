#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_PRESSURE_MULTIHOLE_TANK_LOG_DIR:-/tmp/codex_h2_leak_pressure_multihole_tank_$(date -u +%Y%m%dT%H%M%SZ)}"

CODEX_H2_LEAK_HISTORY_INPUT=input.codex_pressure_multihole_tank_blowdown_smoke \
CODEX_H2_LEAK_HISTORY_LOG_DIR="$log_dir" \
CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="${CODEX_H2_LEAK_PRESSURE_MULTIHOLE_TANK_MIN_MASS_GROWTH_RATIO:-4.0}" \
CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO="${CODEX_H2_LEAK_PRESSURE_MULTIHOLE_TANK_MIN_FINAL_MASS_RATIO:-0.80}" \
CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO="${CODEX_H2_LEAK_PRESSURE_MULTIHOLE_TANK_MAX_FINAL_MASS_RATIO:-1.50}" \
"$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"

run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"
input_file="$log_dir/run/input.codex_pressure_multihole_tank_blowdown_smoke"

grep -q 'H2 leak tank-blowdown model:' "$run_log"
grep -q 'Applying H2 leak source: model=tank_blowdown' "$run_log"
grep -q 'pressure_driven_multihole=1' "$run_log"
grep -q 'H2 leak pressure-driven source\[0\]:' "$run_log"
grep -q 'H2 leak pressure-driven source\[1\]:' "$run_log"
grep -q 'H2 leak pressure-driven source\[2\]:' "$run_log"

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

def area_from_diameter(diameter):
    return 0.25 * math.pi * diameter * diameter if diameter > 0.0 else 0.0

def pressure_orifice_mdot(upstream, downstream, temperature, area, cd, gamma, gas_constant, z):
    if upstream <= downstream or area <= 0.0 or temperature <= 0.0 or cd <= 0.0 or gamma <= 1.0 or gas_constant <= 0.0 or z <= 0.0:
        return 0.0
    pressure_ratio = downstream / upstream
    critical = (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))
    base = cd * area * upstream
    if pressure_ratio <= critical:
        exponent = (gamma + 1.0) / (2.0 * (gamma - 1.0))
        return base * math.sqrt(gamma / (z * gas_constant * temperature)) * (2.0 / (gamma + 1.0)) ** exponent
    term = pressure_ratio ** (2.0 / gamma) - pressure_ratio ** ((gamma + 1.0) / gamma)
    return base * math.sqrt((2.0 * gamma / (z * gas_constant * temperature * (gamma - 1.0))) * term) if term > 0.0 else 0.0

input_path, run_log_path, validation_path = sys.argv[1:]
vals = parse_input(input_path)
log_lines = Path(run_log_path).read_text(errors='replace').splitlines()
log = '\n'.join(log_lines)
validation = Path(validation_path).read_text(errors='replace')
leak_count = int(first_float(vals, 'prob.leak_count'))
if leak_count != 3:
    raise SystemExit(f'FAIL: expected leak_count=3, got {leak_count}')
downstream = first_float(vals, 'prob.leak_ambient_pressure')
temperature = first_float(vals, 'prob.leak_T')
cd = first_float(vals, 'prob.leak_discharge_coeff')
gamma = first_float(vals, 'prob.leak_gamma')
gas_constant = first_float(vals, 'prob.leak_gas_constant')
z = first_float(vals, 'prob.leak_compressibility_factor', 1.0)
tank_volume = first_float(vals, 'prob.leak_tank_volume')
areas = []
for i in range(leak_count):
    area = first_float(vals, f'prob.leak{i}_orifice_area', 0.0)
    if area <= 0.0:
        area = area_from_diameter(first_float(vals, f'prob.leak{i}_orifice_diameter'))
    areas.append(area)
if min(areas) <= 0.0:
    raise SystemExit(f'FAIL: nonpositive per-hole areas: {areas}')

current_step = None
tank_intervals = []
for raw in log_lines:
    sm = re.search(r'STEP \[(-?\d+)\] - Time:', raw)
    if sm:
        current_step = int(sm.group(1))
        continue
    bm = re.search(
        r'H2 leak tank-blowdown model: time=([0-9.eE+-]+), dt=([0-9.eE+-]+), '
        r'tank_volume=([0-9.eE+-]+), compressibility_factor=([0-9.eE+-]+), '
        r'initial_pressure=([0-9.eE+-]+), pressure_start=([0-9.eE+-]+), '
        r'pressure_end=([0-9.eE+-]+), injected_interval=([0-9.eE+-]+), '
        r'cumulative_injected=([0-9.eE+-]+), substeps=(\d+)',
        raw)
    if not bm or current_step is None or current_step < 0:
        continue
    tank_intervals.append({
        'time': float(bm.group(1)),
        'dt': float(bm.group(2)),
        'tank_volume': float(bm.group(3)),
        'z': float(bm.group(4)),
        'initial_pressure': float(bm.group(5)),
        'pressure_start': float(bm.group(6)),
        'pressure_end': float(bm.group(7)),
        'injected': float(bm.group(8)),
        'cumulative': float(bm.group(9)),
        'substeps': int(bm.group(10)),
    })
if len(tank_intervals) < 5:
    raise SystemExit(f'FAIL: too few tank-blowdown intervals: {len(tank_intervals)}')
first = tank_intervals[0]
last = tank_intervals[-1]
if abs(first['tank_volume'] - tank_volume) / tank_volume > 1.0e-12:
    raise SystemExit('FAIL: logged tank volume does not match input')
if not last['pressure_end'] < first['pressure_start']:
    raise SystemExit(f'FAIL: tank pressure did not decrease: first={first} last={last}')
if not last['injected'] / last['dt'] < first['injected'] / first['dt']:
    raise SystemExit(f'FAIL: interval mdot did not decrease: first={first} last={last}')
expected_drop = first['injected'] * z * gas_constant * temperature / tank_volume
logged_drop = first['pressure_start'] - first['pressure_end']
if abs(logged_drop - expected_drop) / max(abs(expected_drop), 1.0e-300) > 5.0e-6:
    raise SystemExit(f'FAIL: first pressure drop mismatch: logged={logged_drop} expected={expected_drop}')
expected_start = [pressure_orifice_mdot(first['pressure_start'], downstream, temperature, area, cd, gamma, gas_constant, z) for area in areas]
expected_total_start = sum(expected_start)
if expected_total_start <= 0.0:
    raise SystemExit('FAIL: expected nonpositive start mdot')
pressure_rows = re.findall(
    r'H2 leak pressure-driven source\[(\d+)\]: orifice_area=([0-9.eE+-]+), '
    r'pressure_mdot=([0-9.eE+-]+), assigned_mdot=([0-9.eE+-]+), mdot_fraction=([0-9.eE+-]+)',
    log)
first_pressure = {}
for row in pressure_rows:
    idx = int(row[0])
    if idx not in first_pressure:
        first_pressure[idx] = row
if sorted(first_pressure) != list(range(leak_count)):
    raise SystemExit(f'FAIL: missing first pressure source block: {sorted(first_pressure)}')
assigned_sum = 0.0
for i in range(leak_count):
    row = first_pressure[i]
    logged_area = float(row[1])
    pressure_mdot = float(row[2])
    assigned_mdot = float(row[3])
    mdot_fraction = float(row[4])
    expected_fraction = expected_start[i] / expected_total_start
    if abs(logged_area - areas[i]) / areas[i] > 5.0e-6:
        raise SystemExit(f'FAIL: source {i} area mismatch: {logged_area} vs {areas[i]}')
    if abs(pressure_mdot - expected_start[i]) / expected_start[i] > 5.0e-6:
        raise SystemExit(f'FAIL: source {i} pressure mdot mismatch: {pressure_mdot} vs {expected_start[i]}')
    if abs(mdot_fraction - expected_fraction) / expected_fraction > 5.0e-6:
        raise SystemExit(f'FAIL: source {i} mdot fraction mismatch: {mdot_fraction} vs {expected_fraction}')
    expected_assigned = first['injected'] / first['dt'] * expected_fraction
    if abs(assigned_mdot - expected_assigned) / max(expected_assigned, 1.0e-300) > 5.0e-6:
        raise SystemExit(f'FAIL: source {i} assigned mdot mismatch: {assigned_mdot} vs {expected_assigned}')
    assigned_sum += assigned_mdot
first_avg = first['injected'] / first['dt']
if not 0.0 < first_avg <= expected_total_start:
    raise SystemExit(f'FAIL: first average mdot not bounded by start mdot: avg={first_avg} start={expected_total_start}')
if abs(assigned_sum - first_avg) / max(first_avg, 1.0e-300) > 5.0e-6:
    raise SystemExit(f'FAIL: assigned mdot sum mismatch: {assigned_sum} vs {first_avg}')
source_rows = re.findall(
    r'H2 leak source\[(\d+)\]: center=\(([^)]*)\), radius=([0-9.eE+-]+), '
    r'fraction=([0-9.eE+-]+), pressure_fraction=([0-9.eE+-]+), mdot=([0-9.eE+-]+), '
    r'active_volume=([0-9.eE+-]+), mdot_vol=([0-9.eE+-]+)',
    log)
first_sources = {}
for row in source_rows:
    idx = int(row[0])
    if idx not in first_sources:
        first_sources[idx] = row
if sorted(first_sources) != list(range(leak_count)):
    raise SystemExit(f'FAIL: missing H2 leak source rows: {sorted(first_sources)}')
for i in range(leak_count):
    source_mdot = float(first_sources[i][5])
    active = float(first_sources[i][6])
    mdot_vol = float(first_sources[i][7])
    if active <= 0.0 or mdot_vol <= 0.0:
        raise SystemExit(f'FAIL: source {i} inactive: active={active} mdot_vol={mdot_vol}')
    if abs(source_mdot - float(first_pressure[i][3])) / max(source_mdot, 1.0e-300) > 5.0e-6:
        raise SystemExit(f'FAIL: source {i} source mdot differs from assigned mdot')
vm = re.search(r'injectedN=([0-9.eE+-]+) mass_ratioN=([0-9.eE+-]+)', validation)
if not vm:
    raise SystemExit('FAIL: missing injectedN/mass_ratioN in validation')
injected_n = float(vm.group(1))
mass_ratio = float(vm.group(2))
if abs(injected_n - last['cumulative']) / max(injected_n, 1.0e-300) > 2.0e-6:
    raise SystemExit(f'FAIL: validation injected mass mismatch: {injected_n} vs {last["cumulative"]}')
if not 0.95 <= mass_ratio <= 1.05:
    raise SystemExit(f'FAIL: mass_ratioN outside tight bounds: {mass_ratio}')
print(f'h2_leak_pressure_multihole_tank_blowdown PASS leak_count={leak_count} first_avg_mdot={first_avg:.8e} start_mdot={expected_total_start:.8e} pressure_drop={first["pressure_start"]-last["pressure_end"]:.8e} injected={injected_n:.8e} mass_ratioN={mass_ratio:.8e}')
PYCHK
