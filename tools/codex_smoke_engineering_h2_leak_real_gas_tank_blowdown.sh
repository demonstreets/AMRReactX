#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
log_dir="${CODEX_H2_LEAK_REAL_GAS_TANK_BLOWDOWN_LOG_DIR:-/tmp/codex_h2_leak_real_gas_tank_blowdown_$(date -u +%Y%m%dT%H%M%SZ)}"
input_file="$repo_root/examples/engineering/h2_leak_3d/input.codex_real_gas_tank_blowdown_smoke"

CODEX_H2_LEAK_HISTORY_INPUT=input.codex_real_gas_tank_blowdown_smoke \
CODEX_H2_LEAK_HISTORY_LOG_DIR="$log_dir" \
CODEX_H2_LEAK_HISTORY_MIN_MASS_GROWTH_RATIO="${CODEX_H2_LEAK_REAL_GAS_TANK_BLOWDOWN_MIN_MASS_GROWTH_RATIO:-4.0}" \
CODEX_H2_LEAK_HISTORY_MIN_FINAL_MASS_RATIO="${CODEX_H2_LEAK_REAL_GAS_TANK_BLOWDOWN_MIN_FINAL_MASS_RATIO:-0.80}" \
CODEX_H2_LEAK_HISTORY_MAX_FINAL_MASS_RATIO="${CODEX_H2_LEAK_REAL_GAS_TANK_BLOWDOWN_MAX_FINAL_MASS_RATIO:-1.50}" \
"$repo_root/tools/codex_smoke_engineering_h2_leak_plume_history.sh"

run_log="$log_dir/run.log"
validation_log="$log_dir/validation.log"

grep -q 'H2 leak tank-blowdown model:' "$run_log"
grep -q 'compressibility_factor=' "$run_log"
grep -q 'Applying H2 leak source: model=tank_blowdown' "$run_log"
grep -q 'H2 leak effective mass flow rate=' "$run_log"

python3 - "$input_file" "$run_log" "$validation_log" <<'PYCHK'
import math
import re
import sys
from pathlib import Path

input_path, run_log_path, validation_path = map(Path, sys.argv[1:])

def read_param(name):
    pattern = re.compile(rf'^\s*prob\.{re.escape(name)}\s*=\s*([^#\s]+)')
    for line in input_path.read_text().splitlines():
        match = pattern.search(line)
        if match:
            token = match.group(1)
            if token.lower() in {'pressure_orifice', 'tank_blowdown', 'fixed_mass_flow'}:
                return token
            return float(token)
    raise SystemExit(f'FAIL: missing input parameter prob.{name}')

P0 = read_param('leak_tank_pressure')
Pamb = read_param('leak_ambient_pressure')
T = read_param('leak_T')
D = read_param('leak_orifice_diameter')
Cd = read_param('leak_discharge_coeff')
gamma = read_param('leak_gamma')
R = read_param('leak_gas_constant')
Z = read_param('leak_compressibility_factor')
V = read_param('leak_tank_volume')
if Z <= 1.0:
    raise SystemExit(f'FAIL: real-gas tank smoke requires Z>1, got {Z}')

area = 0.25 * math.pi * D * D
pressure_ratio = Pamb / P0
critical = (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))
if pressure_ratio <= critical:
    exponent = (gamma + 1.0) / (2.0 * (gamma - 1.0))
    expected_mdot = Cd * area * P0 * math.sqrt(gamma / (Z * R * T)) * \
        (2.0 / (gamma + 1.0)) ** exponent
else:
    term = pressure_ratio ** (2.0 / gamma) - pressure_ratio ** ((gamma + 1.0) / gamma)
    expected_mdot = Cd * area * P0 * math.sqrt(
        (2.0 * gamma / (Z * R * T * (gamma - 1.0))) * term)
ideal_mdot = expected_mdot * math.sqrt(Z)

log_lines = run_log_path.read_text(errors='replace').splitlines()
current_step = None
intervals = []
effective_mdot = None
logged_z = None
for raw in log_lines:
    sm = re.search(r'STEP \[(-?\d+)\] - Time:', raw)
    if sm:
        current_step = int(sm.group(1))
        continue
    em = re.search(r'H2 leak effective mass flow rate=([0-9.eE+-]+)', raw)
    if em and current_step == 0 and effective_mdot is None:
        effective_mdot = float(em.group(1))
    bm = re.search(r'H2 leak tank-blowdown model: time=([0-9.eE+-]+), dt=([0-9.eE+-]+), tank_volume=([0-9.eE+-]+), compressibility_factor=([0-9.eE+-]+), initial_pressure=([0-9.eE+-]+), pressure_start=([0-9.eE+-]+), pressure_end=([0-9.eE+-]+), injected_interval=([0-9.eE+-]+), cumulative_injected=([0-9.eE+-]+), substeps=(\d+)', raw)
    if not bm or current_step is None or current_step < 0:
        continue
    logged_z = float(bm.group(4))
    intervals.append({
        'time': float(bm.group(1)),
        'dt': float(bm.group(2)),
        'volume': float(bm.group(3)),
        'z': logged_z,
        'initial_pressure': float(bm.group(5)),
        'pressure_start': float(bm.group(6)),
        'pressure_end': float(bm.group(7)),
        'injected': float(bm.group(8)),
        'cumulative': float(bm.group(9)),
        'substeps': int(bm.group(10)),
    })

if not intervals:
    raise SystemExit('FAIL: no tank-blowdown intervals found')
first = intervals[0]
last = intervals[-1]
if logged_z is None or abs(logged_z - Z) > 1.0e-12:
    raise SystemExit(f'FAIL: logged Z mismatch: input={Z} logged={logged_z}')
if effective_mdot is None:
    raise SystemExit('FAIL: missing first-step effective mdot')
mdot_rel = abs(effective_mdot - expected_mdot) / max(expected_mdot, 1.0e-300)
if not (0.99 * expected_mdot <= effective_mdot <= expected_mdot):
    raise SystemExit(f'FAIL: first-step average mdot is not bounded by the real-gas start-of-step formula: got={effective_mdot} start_expected={expected_mdot} rel={mdot_rel}')
ratio = expected_mdot / ideal_mdot
expected_ratio = 1.0 / math.sqrt(Z)
if abs(ratio - expected_ratio) > 5.0e-12:
    raise SystemExit(f'FAIL: start-of-step mdot ratio mismatch: got={ratio} expected={expected_ratio}')
pressure_drop = first['pressure_start'] - first['pressure_end']
expected_pressure_drop = first['injected'] * Z * R * T / V
pd_rel = abs(pressure_drop - expected_pressure_drop) / max(expected_pressure_drop, 1.0e-300)
if pd_rel > 5.0e-6:
    raise SystemExit(f'FAIL: pressure drop does not match real-gas tank inventory: got={pressure_drop} expected={expected_pressure_drop} rel={pd_rel}')
if not last['pressure_end'] < first['pressure_start']:
    raise SystemExit('FAIL: tank pressure did not decrease')
if not last['injected'] / last['dt'] < first['injected'] / first['dt']:
    raise SystemExit('FAIL: tank mdot did not decrease')

validation = validation_path.read_text(errors='replace')
vm = re.search(r'injectedN=([0-9.eE+-]+) mass_ratioN=([0-9.eE+-]+)', validation)
if not vm:
    raise SystemExit('FAIL: missing validation injectedN/mass_ratioN')
injected_n = float(vm.group(1))
mass_ratio = float(vm.group(2))
if abs(injected_n - last['cumulative']) / max(injected_n, 1.0e-300) > 2.0e-6:
    raise SystemExit('FAIL: validation injected mass does not match tank cumulative')
if not 0.95 <= mass_ratio <= 1.05:
    raise SystemExit(f'FAIL: mass_ratioN outside tight bounds: {mass_ratio}')
print(
    f'h2_leak_real_gas_tank_blowdown PASS Z={Z:.8e} mdot={effective_mdot:.8e} '
    f'ideal_mdot={ideal_mdot:.8e} ratio={ratio:.8e} first_pressure_drop={pressure_drop:.8e} '
    f'mass_ratioN={mass_ratio:.8e}'
)
PYCHK
