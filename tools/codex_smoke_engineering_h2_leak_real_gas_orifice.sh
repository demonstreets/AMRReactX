#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_REAL_GAS_ORIFICE_LOG_DIR:-/tmp/codex_h2_leak_real_gas_orifice_$(date -u +%Y%m%dT%H%M%SZ)}"

CODEX_H2_LEAK_HISTORY_INPUT=input.codex_real_gas_orifice_smoke \
CODEX_H2_LEAK_HISTORY_LOG_DIR="$log_dir" \
CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="${CODEX_H2_LEAK_REAL_GAS_ORIFICE_MIN_MASS_GROWTH_RATIO:-4.0}" \
CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO="${CODEX_H2_LEAK_REAL_GAS_ORIFICE_MIN_FINAL_MASS_RATIO:-0.80}" \
CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO="${CODEX_H2_LEAK_REAL_GAS_ORIFICE_MAX_FINAL_MASS_RATIO:-1.50}" \
"$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"

run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"
input_file="$log_dir/run/input.codex_real_gas_orifice_smoke"

grep -q 'H2 leak pressure-orifice model:' "$run_log"
grep -q 'compressibility_factor=' "$run_log"
grep -q 'Applying H2 leak source: model=pressure_orifice' "$run_log"
grep -q 'H2 leak effective mass flow rate=' "$run_log"

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

input_path, run_log_path, validation_path = sys.argv[1:]
vals = parse_input(input_path)
log = Path(run_log_path).read_text(errors='replace')
validation = Path(validation_path).read_text(errors='replace')

m = re.search(r'H2 leak effective mass flow rate=([0-9.eE+-]+)', log)
if not m:
    raise SystemExit('FAIL: missing effective real-gas mdot')
effective = float(m.group(1))
z = first_float(vals, 'prob.leak_compressibility_factor')
if z <= 1.0:
    raise SystemExit(f'FAIL: real-gas smoke requires Z>1, got {z}')

lm = re.search(r'compressibility_factor=([0-9.eE+-]+)', log)
if not lm:
    raise SystemExit('FAIL: missing logged compressibility factor')
logged_z = float(lm.group(1))
if abs(logged_z - z) > 1.0e-12:
    raise SystemExit(f'FAIL: logged Z mismatch: logged={logged_z} input={z}')

p0 = first_float(vals, 'prob.leak_tank_pressure')
p1 = first_float(vals, 'prob.leak_ambient_pressure')
t = first_float(vals, 'prob.leak_T')
d = first_float(vals, 'prob.leak_orifice_diameter')
cd = first_float(vals, 'prob.leak_discharge_coeff')
gamma = first_float(vals, 'prob.leak_gamma')
r = first_float(vals, 'prob.leak_gas_constant')
area = math.pi * d * d / 4.0
pr = p1 / p0
critical = (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))
if pr <= critical:
    shape = (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))
    expected = cd * area * p0 * math.sqrt(gamma / (z * r * t)) * shape
    ideal = cd * area * p0 * math.sqrt(gamma / (r * t)) * shape
else:
    term = pr ** (2.0 / gamma) - pr ** ((gamma + 1.0) / gamma)
    expected = cd * area * p0 * math.sqrt((2.0 * gamma / (z * r * t * (gamma - 1.0))) * term)
    ideal = cd * area * p0 * math.sqrt((2.0 * gamma / (r * t * (gamma - 1.0))) * term)
rel = abs(effective - expected) / expected
if rel > 5.0e-6:
    raise SystemExit(f'FAIL: real-gas mdot mismatch: effective={effective} expected={expected} rel={rel}')
if not effective < ideal:
    raise SystemExit(f'FAIL: real-gas mdot should be below ideal: effective={effective} ideal={ideal}')
ratio = effective / ideal
expected_ratio = 1.0 / math.sqrt(z)
if abs(ratio - expected_ratio) > 5.0e-6:
    raise SystemExit(f'FAIL: real-gas mdot ratio mismatch: ratio={ratio} expected={expected_ratio}')
vm = re.search(r'exit_velocity=([0-9.eE+-]+)', log)
if not vm or float(vm.group(1)) <= 0.0:
    raise SystemExit('FAIL: pressure-orifice exit velocity missing/nonpositive')
mr = re.search(r'mass_ratioN=([0-9.eE+-]+)', validation)
if not mr:
    raise SystemExit('FAIL: missing mass_ratioN in validation log')
print(f'h2_leak_real_gas_orifice PASS Z={z:.8e} mdot={effective:.8e} ideal_mdot={ideal:.8e} ratio={ratio:.8e} mass_ratioN={float(mr.group(1)):.8e}')
PYCHK
