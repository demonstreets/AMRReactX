#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_PIPE_LOSS_LOG_DIR:-/tmp/codex_h2_leak_pipe_loss_$(date -u +%Y%m%dT%H%M%SZ)}"

CODEX_H2_LEAK_HISTORY_INPUT=input.codex_pipe_loss_smoke \
CODEX_H2_LEAK_HISTORY_LOG_DIR="$log_dir" \
CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="${CODEX_H2_LEAK_PIPE_LOSS_MIN_MASS_GROWTH_RATIO:-4.0}" \
CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO="${CODEX_H2_LEAK_PIPE_LOSS_MIN_FINAL_MASS_RATIO:-0.80}" \
CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO="${CODEX_H2_LEAK_PIPE_LOSS_MAX_FINAL_MASS_RATIO:-1.50}" \
"$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"

run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"
input_file="$log_dir/run/input.codex_pipe_loss_smoke"

grep -q 'H2 leak pressure-orifice model:' "$run_log"
grep -q 'Applying H2 leak source: model=pressure_orifice' "$run_log"
grep -q 'line_loss_total=' "$run_log"
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

def orifice_mdot(p0, p1, temp, diameter, area, cd, gamma, gas_constant):
    area = area if area > 0.0 else math.pi * diameter * diameter / 4.0
    if p0 <= p1 or area <= 0.0:
        return 0.0
    pr = p1 / p0
    critical = (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))
    if pr <= critical:
        return cd * area * p0 * math.sqrt(gamma / (gas_constant * temp)) * (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))
    term = pr ** (2.0 / gamma) - pr ** ((gamma + 1.0) / gamma)
    return cd * area * p0 * math.sqrt((2.0 * gamma / (gas_constant * temp * (gamma - 1.0))) * term) if term > 0.0 else 0.0

input_path, run_log_path, validation_path = sys.argv[1:]
vals = parse_input(input_path)
log = Path(run_log_path).read_text(errors='replace')
validation = Path(validation_path).read_text(errors='replace')

m = re.search(r'H2 leak effective mass flow rate=([0-9.eE+-]+)', log)
if not m:
    raise SystemExit('FAIL: missing effective mdot')
effective = float(m.group(1))

p0 = first_float(vals, 'prob.leak_tank_pressure')
p1 = first_float(vals, 'prob.leak_ambient_pressure')
temp = first_float(vals, 'prob.leak_T')
diameter = first_float(vals, 'prob.leak_orifice_diameter')
area = first_float(vals, 'prob.leak_orifice_area', 0.0)
cd = first_float(vals, 'prob.leak_discharge_coeff')
gamma = first_float(vals, 'prob.leak_gamma')
gas_constant = first_float(vals, 'prob.leak_gas_constant')
line_diameter = first_float(vals, 'prob.leak_line_diameter')
line_length = first_float(vals, 'prob.leak_line_length')
friction = first_float(vals, 'prob.leak_line_friction_factor')
minor = first_float(vals, 'prob.leak_line_loss_coeff')
loss_total_expected = minor + friction * line_length / line_diameter
no_loss = orifice_mdot(p0, p1, temp, diameter, area, cd, gamma, gas_constant)

lm = re.search(r'tank_pressure=([0-9.eE+-]+), supply_pressure=([0-9.eE+-]+).*line_loss_total=([0-9.eE+-]+)', log)
if not lm:
    raise SystemExit('FAIL: missing tank/effective pressure or line-loss total in run log')
effective_pressure = float(lm.group(1))
supply_pressure = float(lm.group(2))
loss_total = float(lm.group(3))
if abs(loss_total - loss_total_expected) / max(loss_total_expected, 1.0e-300) > 5.0e-6:
    raise SystemExit(f'FAIL: line loss coefficient mismatch: log={loss_total} expected={loss_total_expected}')
if not p1 < effective_pressure < supply_pressure:
    raise SystemExit(f'FAIL: effective pressure not between ambient and supply: eff={effective_pressure} supply={supply_pressure} ambient={p1}')
if not effective < no_loss * 0.95:
    raise SystemExit(f'FAIL: pipe loss did not reduce mdot enough: effective={effective} no_loss={no_loss}')

ratio = re.search(r'mass_ratioN=([0-9.eE+-]+)', validation)
if not ratio:
    raise SystemExit('FAIL: missing mass_ratioN in validation log')
mass_ratio = float(ratio.group(1))
if not 0.95 <= mass_ratio <= 1.05:
    raise SystemExit(f'FAIL: pipe-loss mass ratio outside tight bounds: {mass_ratio}')
print(f'h2_leak_pipe_loss PASS mdot={effective:.8e} no_loss_mdot={no_loss:.8e} reduction={effective/no_loss:.8e} effective_pressure={effective_pressure:.8e} supply_pressure={supply_pressure:.8e} line_loss_total={loss_total:.8e} mass_ratioN={mass_ratio:.8e}')
PYCHK
