#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_LINEPACK_VALVE_LOG_DIR:-/tmp/codex_h2_leak_linepack_valve_schedule_$(date -u +%Y%m%dT%H%M%SZ)}"

CODEX_H2_LEAK_HISTORY_INPUT=input.codex_linepack_valve_schedule_smoke \
CODEX_H2_LEAK_HISTORY_LOG_DIR="$log_dir" \
CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="${CODEX_H2_LEAK_LINEPACK_VALVE_MIN_MASS_GROWTH_RATIO:-4.0}" \
CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO="${CODEX_H2_LEAK_LINEPACK_VALVE_MIN_FINAL_MASS_RATIO:-0.80}" \
CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO="${CODEX_H2_LEAK_LINEPACK_VALVE_MAX_FINAL_MASS_RATIO:-1.50}" \
"$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"

run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"
input_file="$log_dir/run/input.codex_linepack_valve_schedule_smoke"

grep -q 'H2 leak linepack-blowdown model:' "$run_log"
grep -q 'H2 leak pressure-orifice model:' "$run_log"
grep -q 'Applying H2 leak source: model=linepack_blowdown' "$run_log"
grep -q 'valve_scheduled=1' "$run_log"
grep -q 'valve_fraction_mid=' "$run_log"

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
        k, v = line.split('=', 1)
        vals[k.strip()] = v.strip().split()
    return vals

def first_float(vals, key, default=None):
    if key not in vals:
        if default is None:
            raise KeyError(key)
        return default
    return float(vals[key][0])

def orifice_area(diameter, area):
    return area if area > 0.0 else math.pi * diameter * diameter / 4.0

def critical_ratio(gamma):
    return (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))

def mdot_no_line_loss(p0, p1, temp, diameter, area, cd, gamma, gas_constant, z):
    area = orifice_area(diameter, area)
    if p0 <= p1 or area <= 0.0 or temp <= 0.0 or gas_constant <= 0.0 or z <= 0.0:
        return 0.0
    pr = p1 / p0
    if pr <= critical_ratio(gamma):
        return (cd * area * p0 * math.sqrt(gamma / (z * gas_constant * temp)) *
                (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0))))
    term = pr ** (2.0 / gamma) - pr ** ((gamma + 1.0) / gamma)
    return (cd * area * p0 * math.sqrt((2.0 * gamma / (z * gas_constant * temp * (gamma - 1.0))) * term)
            if term > 0.0 else 0.0)

def mdot_with_line_loss(p0, p1, temp, diameter, area, cd, gamma, gas_constant, z,
                        line_diameter, line_length, friction, minor, fraction):
    if fraction <= 0.0:
        return 0.0, p0, max(minor, 0.0)
    area = orifice_area(diameter, area) * fraction
    diameter = 0.0
    loss = max(minor, 0.0)
    if friction > 0.0 and line_length > 0.0 and line_diameter > 0.0:
        loss += friction * line_length / line_diameter
    if loss <= 0.0:
        return mdot_no_line_loss(p0, p1, temp, diameter, area, cd, gamma, gas_constant, z), p0, loss
    line_area = math.pi * line_diameter * line_diameter / 4.0 if line_diameter > 0.0 else orifice_area(diameter, area)
    rho = p0 / (z * gas_constant * temp)
    lo, hi = p1, p0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        mdot = mdot_no_line_loss(mid, p1, temp, diameter, area, cd, gamma, gas_constant, z)
        velocity = mdot / (rho * line_area) if rho > 0.0 and line_area > 0.0 else 0.0
        residual = mid + 0.5 * loss * rho * velocity * velocity - p0
        if residual > 0.0:
            hi = mid
        else:
            lo = mid
    effective_p = 0.5 * (lo + hi)
    return mdot_no_line_loss(effective_p, p1, temp, diameter, area, cd, gamma, gas_constant, z), effective_p, loss

input_path, run_log_path, validation_path = sys.argv[1:]
vals = parse_input(input_path)
log_lines = Path(run_log_path).read_text(errors='replace').splitlines()
validation = Path(validation_path).read_text(errors='replace')

line_diameter = first_float(vals, 'prob.leak_line_diameter')
line_length = first_float(vals, 'prob.leak_line_length')
configured_volume = first_float(vals, 'prob.leak_linepack_volume', 0.0)
expected_volume = configured_volume if configured_volume > 0.0 else math.pi * line_diameter * line_diameter * line_length / 4.0
p1 = first_float(vals, 'prob.leak_ambient_pressure')
temp = first_float(vals, 'prob.leak_T')
diameter = first_float(vals, 'prob.leak_orifice_diameter')
area = first_float(vals, 'prob.leak_orifice_area', 0.0)
cd = first_float(vals, 'prob.leak_discharge_coeff')
gamma = first_float(vals, 'prob.leak_gamma')
gas_constant = first_float(vals, 'prob.leak_gas_constant')
z = first_float(vals, 'prob.leak_compressibility_factor', 1.0)
friction = first_float(vals, 'prob.leak_line_friction_factor')
minor = first_float(vals, 'prob.leak_line_loss_coeff')
open_time = first_float(vals, 'prob.leak_valve_open_time')
ramp_time = first_float(vals, 'prob.leak_valve_ramp_time')
initial_fraction = first_float(vals, 'prob.leak_valve_initial_fraction')
final_fraction = first_float(vals, 'prob.leak_valve_final_fraction')

def schedule_fraction(t):
    t = max(t, 0.0)
    if t <= open_time:
        return initial_fraction
    if ramp_time <= 0.0:
        return final_fraction
    ramp = (t - open_time) / ramp_time
    if ramp >= 1.0:
        return final_fraction
    return initial_fraction + ramp * (final_fraction - initial_fraction)

current_step = None
intervals = []
pressure_rows = []
for raw in log_lines:
    sm = re.search(r'STEP \[(-?\d+)\] - Time:', raw)
    if sm:
        current_step = int(sm.group(1))
        continue
    bm = re.search(
        r'H2 leak linepack-blowdown model: time=([0-9.eE+-]+), dt=([0-9.eE+-]+), '
        r'linepack_volume=([0-9.eE+-]+), configured_linepack_volume=([0-9.eE+-]+), '
        r'linepack_pressure=([0-9.eE+-]+), line_diameter=([0-9.eE+-]+), '
        r'line_length=([0-9.eE+-]+), compressibility_factor=([0-9.eE+-]+), '
        r'initial_pressure=([0-9.eE+-]+), pressure_start=([0-9.eE+-]+), '
        r'pressure_end=([0-9.eE+-]+), injected_interval=([0-9.eE+-]+), '
        r'cumulative_injected=([0-9.eE+-]+), substeps=(\d+), '
        r'valve_open_time=([0-9.eE+-]+), valve_ramp_time=([0-9.eE+-]+), '
        r'valve_fraction_start=([0-9.eE+-]+), valve_fraction_mid=([0-9.eE+-]+), '
        r'valve_fraction_end=([0-9.eE+-]+)', raw)
    if bm and current_step is not None and current_step >= 0:
        intervals.append({
            'time': float(bm.group(1)),
            'dt': float(bm.group(2)),
            'volume': float(bm.group(3)),
            'configured_volume': float(bm.group(4)),
            'pressure_start': float(bm.group(10)),
            'pressure_end': float(bm.group(11)),
            'injected': float(bm.group(12)),
            'cumulative': float(bm.group(13)),
            'valve_open_time': float(bm.group(15)),
            'valve_ramp_time': float(bm.group(16)),
            'fraction_start': float(bm.group(17)),
            'fraction_mid': float(bm.group(18)),
            'fraction_end': float(bm.group(19)),
        })
        continue
    pm = re.search(r'H2 leak pressure-orifice model: tank_pressure=([0-9.eE+-]+), supply_pressure=([0-9.eE+-]+).*line_loss_total=([0-9.eE+-]+).*valve_fraction_mid=([0-9.eE+-]+)', raw)
    if pm and current_step is not None and current_step >= 0:
        pressure_rows.append({
            'effective_pressure': float(pm.group(1)),
            'supply_pressure': float(pm.group(2)),
            'line_loss_total': float(pm.group(3)),
            'fraction_mid': float(pm.group(4)),
        })

if len(intervals) < 5:
    raise SystemExit(f'FAIL: too few scheduled linepack intervals: {len(intervals)}')
if not pressure_rows:
    raise SystemExit('FAIL: missing pressure-orifice rows')
if abs(intervals[0]['volume'] - expected_volume) / max(expected_volume, 1.0e-300) > 5.0e-6:
    raise SystemExit('FAIL: linepack volume mismatch')
if abs(intervals[0]['valve_open_time'] - open_time) > 1.0e-12 or abs(intervals[0]['valve_ramp_time'] - ramp_time) > 1.0e-12:
    raise SystemExit('FAIL: valve schedule times were not logged from input')
for row in intervals:
    expected_fraction = schedule_fraction(row['time'] + 0.5 * row['dt'])
    if abs(row['fraction_mid'] - expected_fraction) > 5.0e-8:
        raise SystemExit(f'FAIL: valve fraction mismatch at time={row["time"]}: log={row["fraction_mid"]} expected={expected_fraction}')
closed = [row for row in intervals if row['time'] + 0.5 * row['dt'] <= open_time]
ramping = [row for row in intervals if 0.0 < row['fraction_mid'] < 1.0]
open_rows = [row for row in intervals if abs(row['fraction_mid'] - 1.0) < 1.0e-12]
if not closed:
    raise SystemExit('FAIL: missing closed intervals before rupture time')
if not ramping:
    raise SystemExit('FAIL: missing ramping intervals')
if not open_rows:
    raise SystemExit('FAIL: missing fully open intervals after ramp')
for row in closed:
    if abs(row['injected']) > 1.0e-20:
        raise SystemExit(f'FAIL: closed interval injected mass: {row}')
    if abs(row['pressure_start'] - row['pressure_end']) > max(row['pressure_start'], 1.0) * 1.0e-12:
        raise SystemExit(f'FAIL: closed interval changed pressure: {row}')
if not any(row['injected'] > 0.0 for row in ramping):
    raise SystemExit('FAIL: ramping intervals did not inject mass')
if not all(intervals[i + 1]['cumulative'] >= intervals[i]['cumulative'] for i in range(len(intervals) - 1)):
    raise SystemExit('FAIL: cumulative injection is not nondecreasing')
if not intervals[-1]['cumulative'] > intervals[0]['cumulative']:
    raise SystemExit('FAIL: scheduled linepack cumulative injection did not grow')
first_positive = next(row for row in intervals if row['injected'] > 0.0)
expected_drop = first_positive['injected'] * z * gas_constant * temp / first_positive['volume']
actual_drop = first_positive['pressure_start'] - first_positive['pressure_end']
if abs(actual_drop - expected_drop) / max(expected_drop, 1.0e-300) > 2.0e-5:
    raise SystemExit(f'FAIL: first positive pressure drop mismatch: actual={actual_drop} expected={expected_drop}')
start_mdot, expected_effective_pressure, expected_loss = mdot_with_line_loss(
    first_positive['pressure_start'], p1, temp, diameter, area, cd, gamma,
    gas_constant, z, line_diameter, line_length, friction, minor,
    first_positive['fraction_mid'])
first_avg_mdot = first_positive['injected'] / first_positive['dt']
if not 0.0 < first_avg_mdot <= start_mdot * 1.0001:
    raise SystemExit(f'FAIL: first positive average mdot outside expected bound: avg={first_avg_mdot} start={start_mdot}')
matching_pressure = next(row for row in pressure_rows if abs(row['fraction_mid'] - first_positive['fraction_mid']) < 5.0e-8)
if abs(matching_pressure['line_loss_total'] - expected_loss) / max(expected_loss, 1.0e-300) > 5.0e-6:
    raise SystemExit('FAIL: line loss mismatch')
if abs(matching_pressure['effective_pressure'] - expected_effective_pressure) / max(expected_effective_pressure, 1.0e-300) > 2.0e-5:
    raise SystemExit(f'FAIL: effective pressure mismatch: log={matching_pressure["effective_pressure"]} expected={expected_effective_pressure}')
vm = re.search(r'injectedN=([0-9.eE+-]+) mass_ratioN=([0-9.eE+-]+)', validation)
if not vm:
    raise SystemExit('FAIL: missing injectedN/mass_ratioN in validation')
injected_n = float(vm.group(1))
mass_ratio = float(vm.group(2))
rel = abs(injected_n - intervals[-1]['cumulative']) / max(injected_n, 1.0e-300)
if rel > 2.0e-6:
    raise SystemExit(f'FAIL: validation injected mass does not match cumulative: validation={injected_n} cumulative={intervals[-1]["cumulative"]} rel={rel}')
if not 0.95 <= mass_ratio <= 1.05:
    raise SystemExit(f'FAIL: scheduled linepack mass ratio outside tight bounds: {mass_ratio}')
print(f'h2_leak_linepack_valve_schedule PASS intervals={len(intervals)} closed_intervals={len(closed)} ramp_intervals={len(ramping)} volume={intervals[0]["volume"]:.8e} first_positive_avg_mdot={first_avg_mdot:.8e} first_positive_fraction={first_positive["fraction_mid"]:.8e} injected={injected_n:.8e} mass_ratioN={mass_ratio:.8e}')
PYCHK
