#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_LINEPACK_BLOWDOWN_LOG_DIR:-/tmp/codex_h2_leak_linepack_blowdown_$(date -u +%Y%m%dT%H%M%SZ)}"

CODEX_H2_LEAK_HISTORY_INPUT=input.codex_linepack_blowdown_smoke \
CODEX_H2_LEAK_HISTORY_LOG_DIR="$log_dir" \
CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="${CODEX_H2_LEAK_LINEPACK_BLOWDOWN_MIN_MASS_GROWTH_RATIO:-4.0}" \
CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO="${CODEX_H2_LEAK_LINEPACK_BLOWDOWN_MIN_FINAL_MASS_RATIO:-0.80}" \
CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO="${CODEX_H2_LEAK_LINEPACK_BLOWDOWN_MAX_FINAL_MASS_RATIO:-1.50}" \
"$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"

run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"
input_file="$log_dir/run/input.codex_linepack_blowdown_smoke"

grep -q 'H2 leak linepack-blowdown model:' "$run_log"
grep -q 'H2 leak pressure-orifice model:' "$run_log"
grep -q 'Applying H2 leak source: model=linepack_blowdown' "$run_log"
grep -q 'linepack_volume=' "$run_log"
grep -q 'line_loss_total=' "$run_log"

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
                        line_diameter, line_length, friction, minor):
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
initial_linepack_pressure = first_float(vals, 'prob.leak_linepack_pressure')
tank_pressure = first_float(vals, 'prob.leak_tank_pressure')
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

current_step = None
intervals = []
pressure_rows = []
for raw in log_lines:
    sm = re.search(r'STEP \[(-?\d+)\] - Time:', raw)
    if sm:
        current_step = int(sm.group(1))
        continue
    bm = re.search(r'H2 leak linepack-blowdown model: time=([0-9.eE+-]+), dt=([0-9.eE+-]+), linepack_volume=([0-9.eE+-]+), configured_linepack_volume=([0-9.eE+-]+), linepack_pressure=([0-9.eE+-]+), line_diameter=([0-9.eE+-]+), line_length=([0-9.eE+-]+), compressibility_factor=([0-9.eE+-]+), initial_pressure=([0-9.eE+-]+), pressure_start=([0-9.eE+-]+), pressure_end=([0-9.eE+-]+), injected_interval=([0-9.eE+-]+), cumulative_injected=([0-9.eE+-]+), substeps=(\d+)', raw)
    if bm and current_step is not None and current_step >= 0:
        intervals.append({
            'time': float(bm.group(1)),
            'dt': float(bm.group(2)),
            'volume': float(bm.group(3)),
            'configured_volume': float(bm.group(4)),
            'linepack_pressure': float(bm.group(5)),
            'line_diameter': float(bm.group(6)),
            'line_length': float(bm.group(7)),
            'z': float(bm.group(8)),
            'initial_pressure': float(bm.group(9)),
            'pressure_start': float(bm.group(10)),
            'pressure_end': float(bm.group(11)),
            'injected': float(bm.group(12)),
            'cumulative': float(bm.group(13)),
            'substeps': int(bm.group(14)),
        })
        continue
    pm = re.search(r'H2 leak pressure-orifice model: tank_pressure=([0-9.eE+-]+), supply_pressure=([0-9.eE+-]+).*linepack_pressure=([0-9.eE+-]+), linepack_volume=([0-9.eE+-]+), line_loss_total=([0-9.eE+-]+)', raw)
    if pm and current_step is not None and current_step >= 0:
        pressure_rows.append({
            'effective_pressure': float(pm.group(1)),
            'supply_pressure': float(pm.group(2)),
            'linepack_pressure': float(pm.group(3)),
            'linepack_volume': float(pm.group(4)),
            'line_loss_total': float(pm.group(5)),
        })

if len(intervals) < 5:
    raise SystemExit(f'FAIL: too few linepack-blowdown intervals: {len(intervals)}')
if not pressure_rows:
    raise SystemExit('FAIL: missing pressure-orifice rows for linepack blowdown')
first = intervals[0]
last = intervals[-1]
first_pressure = pressure_rows[0]
if abs(first['volume'] - expected_volume) / max(expected_volume, 1.0e-300) > 5.0e-6:
    raise SystemExit(f'FAIL: linepack volume mismatch: log={first["volume"]} expected={expected_volume}')
if first['configured_volume'] != 0.0:
    raise SystemExit(f'FAIL: this smoke should use derived linepack volume, got configured={first["configured_volume"]}')
if abs(first['linepack_pressure'] - initial_linepack_pressure) / initial_linepack_pressure > 5.0e-8:
    raise SystemExit('FAIL: linepack initial pressure was not used')
if abs(first['linepack_pressure'] - tank_pressure) / max(tank_pressure, 1.0e-300) < 1.0e-3:
    raise SystemExit('FAIL: linepack pressure unexpectedly collapsed to tank pressure')
if not last['pressure_end'] < first['pressure_start']:
    raise SystemExit('FAIL: linepack pressure did not decrease')
if not last['injected'] / last['dt'] < first['injected'] / first['dt']:
    raise SystemExit('FAIL: linepack mdot did not decrease')
if not all(row['injected'] > 0.0 for row in intervals):
    raise SystemExit('FAIL: nonpositive linepack interval injection')
if not all(intervals[i + 1]['cumulative'] > intervals[i]['cumulative'] for i in range(len(intervals) - 1)):
    raise SystemExit('FAIL: linepack cumulative injection is not increasing')

expected_drop = first['injected'] * z * gas_constant * temp / first['volume']
actual_drop = first['pressure_start'] - first['pressure_end']
if abs(actual_drop - expected_drop) / max(expected_drop, 1.0e-300) > 2.0e-5:
    raise SystemExit(f'FAIL: first pressure drop mismatch: actual={actual_drop} expected={expected_drop}')
start_mdot, expected_effective_pressure, expected_loss = mdot_with_line_loss(
    first['pressure_start'], p1, temp, diameter, area, cd, gamma, gas_constant, z,
    line_diameter, line_length, friction, minor)
first_avg_mdot = first['injected'] / first['dt']
if not 0.0 < first_avg_mdot <= start_mdot * 1.0001:
    raise SystemExit(f'FAIL: first average mdot outside expected bound: avg={first_avg_mdot} start={start_mdot}')
if abs(first_pressure['line_loss_total'] - expected_loss) / max(expected_loss, 1.0e-300) > 5.0e-6:
    raise SystemExit(f'FAIL: line loss mismatch: log={first_pressure["line_loss_total"]} expected={expected_loss}')
if abs(first_pressure['effective_pressure'] - expected_effective_pressure) / max(expected_effective_pressure, 1.0e-300) > 2.0e-5:
    raise SystemExit(f'FAIL: effective pressure mismatch: log={first_pressure["effective_pressure"]} expected={expected_effective_pressure}')

vm = re.search(r'injectedN=([0-9.eE+-]+) mass_ratioN=([0-9.eE+-]+)', validation)
if not vm:
    raise SystemExit('FAIL: missing injectedN/mass_ratioN in validation')
injected_n = float(vm.group(1))
mass_ratio = float(vm.group(2))
rel = abs(injected_n - last['cumulative']) / max(injected_n, 1.0e-300)
if rel > 2.0e-6:
    raise SystemExit(f'FAIL: validation injected mass does not match linepack cumulative: validation={injected_n} cumulative={last["cumulative"]} rel={rel}')
if not 0.95 <= mass_ratio <= 1.05:
    raise SystemExit(f'FAIL: linepack-blowdown mass ratio outside tight bounds: {mass_ratio}')
print(f'h2_leak_linepack_blowdown PASS intervals={len(intervals)} volume={first["volume"]:.8e} first_avg_mdot={first_avg_mdot:.8e} start_mdot={start_mdot:.8e} pressure_drop={actual_drop:.8e} injected={injected_n:.8e} mass_ratioN={mass_ratio:.8e}')
PYCHK
