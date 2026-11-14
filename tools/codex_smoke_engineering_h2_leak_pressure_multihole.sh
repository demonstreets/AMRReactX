#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_PRESSURE_MULTIHOLE_LOG_DIR:-/tmp/codex_h2_leak_pressure_multihole_$(date -u +%Y%m%dT%H%M%SZ)}"

CODEX_H2_LEAK_HISTORY_INPUT=input.codex_pressure_multihole_smoke \
CODEX_H2_LEAK_HISTORY_LOG_DIR="$log_dir" \
CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="${CODEX_H2_LEAK_PRESSURE_MULTIHOLE_MIN_MASS_GROWTH_RATIO:-4.0}" \
CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO="${CODEX_H2_LEAK_PRESSURE_MULTIHOLE_MIN_FINAL_MASS_RATIO:-0.95}" \
CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO="${CODEX_H2_LEAK_PRESSURE_MULTIHOLE_MAX_FINAL_MASS_RATIO:-1.05}" \
"$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"

run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"
input_file="$log_dir/run/input.codex_pressure_multihole_smoke"

grep -q 'Applying H2 leak source: model=pressure_orifice' "$run_log"
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
log = Path(run_log_path).read_text(errors='replace')
validation = Path(validation_path).read_text(errors='replace')
leak_count = int(first_float(vals, 'prob.leak_count'))
if leak_count != 3:
    raise SystemExit(f'FAIL: expected leak_count=3, got {leak_count}')
upstream = first_float(vals, 'prob.leak_tank_pressure')
downstream = first_float(vals, 'prob.leak_ambient_pressure')
temperature = first_float(vals, 'prob.leak_T')
cd = first_float(vals, 'prob.leak_discharge_coeff')
gamma = first_float(vals, 'prob.leak_gamma')
gas_constant = first_float(vals, 'prob.leak_gas_constant')
z = first_float(vals, 'prob.leak_compressibility_factor', 1.0)
areas = []
expected = []
for i in range(leak_count):
    area = first_float(vals, f'prob.leak{i}_orifice_area', 0.0)
    if area <= 0.0:
        area = area_from_diameter(first_float(vals, f'prob.leak{i}_orifice_diameter'))
    areas.append(area)
    expected.append(pressure_orifice_mdot(upstream, downstream, temperature, area, cd, gamma, gas_constant, z))
expected_total = sum(expected)
if expected_total <= 0.0:
    raise SystemExit('FAIL: expected nonpositive total pressure mdot')
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
    raise SystemExit(f'FAIL: missing pressure-driven source rows: {sorted(first_pressure)}')
assigned_sum = 0.0
for i in range(leak_count):
    row = first_pressure[i]
    logged_area = float(row[1])
    logged_pressure_mdot = float(row[2])
    assigned_mdot = float(row[3])
    logged_fraction = float(row[4])
    rel_area = abs(logged_area - areas[i]) / max(areas[i], 1.0e-300)
    rel_mdot = abs(logged_pressure_mdot - expected[i]) / max(expected[i], 1.0e-300)
    expected_fraction = expected[i] / expected_total
    rel_fraction = abs(logged_fraction - expected_fraction) / max(expected_fraction, 1.0e-300)
    if rel_area > 5.0e-6:
        raise SystemExit(f'FAIL: source {i} area mismatch: {logged_area} vs {areas[i]}')
    if rel_mdot > 5.0e-6:
        raise SystemExit(f'FAIL: source {i} mdot mismatch: {logged_pressure_mdot} vs {expected[i]}')
    if abs(assigned_mdot - logged_pressure_mdot) / max(expected[i], 1.0e-300) > 5.0e-6:
        raise SystemExit(f'FAIL: source {i} assigned mdot differs from pressure mdot')
    if rel_fraction > 5.0e-6:
        raise SystemExit(f'FAIL: source {i} mdot fraction mismatch: {logged_fraction} vs {expected_fraction}')
    assigned_sum += assigned_mdot
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
    if abs(source_mdot - expected[i]) / max(expected[i], 1.0e-300) > 5.0e-6:
        raise SystemExit(f'FAIL: source {i} H2 source mdot mismatch: {source_mdot} vs {expected[i]}')
ratio = re.search(r'mass_ratioN=([0-9.eE+-]+)', validation)
if not ratio:
    raise SystemExit('FAIL: missing mass_ratioN in validation log')
mass_ratio = float(ratio.group(1))
if not 0.95 <= mass_ratio <= 1.05:
    raise SystemExit(f'FAIL: pressure multihole mass ratio outside tight bounds: {mass_ratio}')
print(f'h2_leak_pressure_multihole PASS leak_count={leak_count} mdot_sum={assigned_sum:.8e} expected={expected_total:.8e} mass_ratioN={mass_ratio:.8e}')
PYCHK
