#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_PRESSURE_ORIFICE_LOG_DIR:-/tmp/codex_h2_leak_pressure_orifice_$(date -u +%Y%m%dT%H%M%SZ)}"

CODEX_H2_LEAK_HISTORY_INPUT=input.codex_pressure_orifice_smoke \
CODEX_H2_LEAK_HISTORY_LOG_DIR="$log_dir" \
CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="${CODEX_H2_LEAK_PRESSURE_ORIFICE_MIN_MASS_GROWTH_RATIO:-4.0}" \
CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO="${CODEX_H2_LEAK_PRESSURE_ORIFICE_MIN_FINAL_MASS_RATIO:-0.80}" \
CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO="${CODEX_H2_LEAK_PRESSURE_ORIFICE_MAX_FINAL_MASS_RATIO:-1.50}" \
"$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"

run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"
input_file="$log_dir/run/input.codex_pressure_orifice_smoke"

grep -q 'H2 leak pressure-orifice model:' "$run_log"
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

def first_float(vals, key):
    return float(vals[key][0])

input_path, run_log_path, validation_path = sys.argv[1:]
vals = parse_input(input_path)
log = Path(run_log_path).read_text(errors='replace')
validation = Path(validation_path).read_text(errors='replace')

m = re.search(r'H2 leak effective mass flow rate=([0-9.eE+-]+)', log)
if not m:
    raise SystemExit('FAIL: missing effective pressure-orifice mdot')
effective = float(m.group(1))
reference_leak_rate = first_float(vals, 'prob.leak_rate')
if not effective > reference_leak_rate * 1.0e20:
    raise SystemExit(f'FAIL: pressure-orifice effective mdot did not override reference leak_rate: effective={effective} reference={reference_leak_rate}')

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
    expected = cd * area * p0 * math.sqrt(gamma / (r * t)) * (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))
else:
    expected = cd * area * p0 * math.sqrt((2.0 * gamma / (r * t * (gamma - 1.0))) * (pr ** (2.0 / gamma) - pr ** ((gamma + 1.0) / gamma)))
rel = abs(effective - expected) / expected
if rel > 5.0e-6:
    raise SystemExit(f'FAIL: pressure-orifice mdot mismatch: effective={effective} expected={expected} rel={rel}')

vm = re.search(r'exit_velocity=([0-9.eE+-]+)', log)
if not vm or float(vm.group(1)) <= 0.0:
    raise SystemExit('FAIL: pressure-orifice exit velocity missing/nonpositive')
ratio = re.search(r'mass_ratioN=([0-9.eE+-]+)', validation)
if not ratio:
    raise SystemExit('FAIL: missing mass_ratioN in validation log')
print(f'h2_leak_pressure_orifice PASS mdot={effective:.8e} expected={expected:.8e} rel={rel:.3e} mass_ratioN={float(ratio.group(1)):.8e}')
PYCHK
