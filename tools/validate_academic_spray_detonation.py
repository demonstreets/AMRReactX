#!/usr/bin/env python3
"""Validate a reacting spray detonation-style shock-droplet gate."""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import amrex_reader  # noqa: E402


def fail(message: str) -> None:
    raise SystemExit(f'FAIL: {message}')


def parse_inputs(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def require_input_switches(values: dict[str, str]) -> None:
    expected = {
        'pelec.do_react': '1',
        'pelec.do_spray_particles': '1',
        'particles.mom_transfer': '1',
        'particles.mass_transfer': '1',
        'particles.fixed_parts': '0',
    }
    for key, want in expected.items():
        got = values.get(key)
        if got != want:
            fail(f'input {key}={got!r}, expected {want!r}')
    if values.get('pelec.chem_integrator') != 'ReactorCvode':
        fail('input must use ReactorCvode for this stiff reacting spray gate')
    if values.get('cvode.solve_type') != 'dense_direct':
        fail('input must set cvode.solve_type=dense_direct')
    if values.get('particles.use_breakup_model', '').upper() != 'KHRT':
        fail('input must use KHRT breakup')
    for key in ('prob.Y_NC7H16', 'prob.Y_O2', 'prob.Y_N2'):
        try:
            value = float(values.get(key, 'nan'))
        except ValueError:
            fail(f'input {key} is not numeric')
        if not math.isfinite(value) or value <= 0.0:
            fail(f'input {key} must be positive for reacting spray detonation gate')


def log_is_clean(path: Path) -> None:
    text = path.read_text(errors='replace')
    if 'AMReX' not in text or 'finalized' not in text:
        fail(f'run log does not show AMReX finalized: {path}')
    if re.search(r'\b(?:nan|SIGSEGV|Segmentation|Backtrace|Abort|Simulation stopped early)\b', text, re.IGNORECASE):
        fail(f'run log contains failure token: {path}')


def read_plot(path: Path) -> dict[str, object]:
    if not path.is_dir():
        fail(f'missing plotfile: {path}')
    return amrex_reader.read_plotfile(str(path))


def field(plot: dict[str, object], name: str) -> np.ndarray:
    fields = plot.get('fields')
    if not isinstance(fields, dict) or name not in fields:
        fail(f'missing plot field {name}')
    arr = np.asarray(fields[name], dtype=float)
    if not np.isfinite(arr).all():
        fail(f'non-finite plot field {name}')
    return arr


def stats(arr: np.ndarray) -> dict[str, float]:
    return {
        'min': float(np.min(arr)),
        'max': float(np.max(arr)),
        'sum': float(np.sum(arr)),
        'absmax': float(np.max(np.abs(arr))),
    }


def rightmost_front(plot: dict[str, object], name: str, threshold: float) -> float:
    arr = field(plot, name)
    x = np.asarray(plot['x'], dtype=float)
    axes = tuple(range(1, arr.ndim))
    line = np.max(arr, axis=axes) if axes else arr
    idx = np.where(line > threshold)[0]
    if idx.size == 0:
        fail(f'{name} has no cells above threshold {threshold}')
    return float(x[int(idx[-1])])


def parse_particle_count(plot: Path) -> int:
    header = plot / 'particles' / 'Header'
    if not header.is_file():
        fail(f'missing particle Header: {header}')
    lines = header.read_text().splitlines()
    if len(lines) < 16:
        fail(f'particle Header too short: {header}')
    try:
        return int(lines[15].strip())
    except ValueError as exc:
        fail(f'cannot parse particle count from {header}: {exc}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--run-log', required=True)
    parser.add_argument('--initial', required=True)
    parser.add_argument('--mid')
    parser.add_argument('--final', required=True)
    parser.add_argument('--pressure-front-threshold', type=float, default=2.0e6)
    parser.add_argument('--temp-front-threshold', type=float, default=1000.0)
    parser.add_argument('--min-pressure-front-shift', type=float, default=0.5)
    parser.add_argument('--min-temp-front-shift', type=float, default=0.4)
    parser.add_argument('--min-front-shift-cells', type=float, default=5.0)
    parser.add_argument('--min-heat-release-absmax', type=float, default=1.0)
    parser.add_argument('--min-o2-consumption', type=float, default=1.0e-4)
    parser.add_argument('--min-fuel-vapor-increase', type=float, default=5.0e-4)
    parser.add_argument('--min-particle-growth', type=float, default=2.0)
    parser.add_argument('--min-spray-velocity', type=float, default=100.0)
    parser.add_argument('--min-spray-temp-increase', type=float, default=50.0)
    parser.add_argument('--min-spray-mass-loss-rel', type=float, default=1.0e-5)
    parser.add_argument('--max-species-closure-rel', type=float, default=2.0e-12)
    args = parser.parse_args()

    input_path = Path(args.input)
    run_log = Path(args.run_log)
    initial_path = Path(args.initial)
    final_path = Path(args.final)

    require_input_switches(parse_inputs(input_path))
    log_is_clean(run_log)

    p0 = read_plot(initial_path)
    p1 = read_plot(final_path)
    if float(p1['time']) <= float(p0['time']):
        fail('final time is not after initial time')

    required = [
        'density', 'Temp', 'pressure', 'Y(NC7H16)', 'Y(O2)', 'Y(N2)',
        'heatRelease', 'rhoe_dot', 'spray_mass', 'num_parcels', 'spray_x_vel',
        'spray_temp', 'spray_surf_area', 'd32',
    ]
    f0 = {name: field(p0, name) for name in required}
    f1 = {name: field(p1, name) for name in required}
    s0 = {name: stats(arr) for name, arr in f0.items()}
    s1 = {name: stats(arr) for name, arr in f1.items()}

    for name in ('density', 'Temp', 'pressure'):
        if s0[name]['min'] <= 0.0 or s1[name]['min'] <= 0.0:
            fail(f'{name} became nonphysical')

    y_sum = f1['Y(NC7H16)'] + f1['Y(O2)'] + f1['Y(N2)']
    species_closure_rel = float(np.max(np.abs(y_sum - 1.0)))
    if species_closure_rel > args.max_species_closure_rel:
        fail(f'species mass-fraction closure too large: {species_closure_rel:.8e}')

    pressure_front0 = rightmost_front(p0, 'pressure', args.pressure_front_threshold)
    pressure_front1 = rightmost_front(p1, 'pressure', args.pressure_front_threshold)
    temp_front0 = rightmost_front(p0, 'Temp', args.temp_front_threshold)
    temp_front1 = rightmost_front(p1, 'Temp', args.temp_front_threshold)
    dx = float(p1['dx'][0])
    pressure_front_shift = pressure_front1 - pressure_front0
    temp_front_shift = temp_front1 - temp_front0
    pressure_front_shift_cells = pressure_front_shift / dx
    if pressure_front_shift < args.min_pressure_front_shift:
        fail(f'pressure front shift too small: {pressure_front_shift:.8g}')
    if temp_front_shift < args.min_temp_front_shift:
        fail(f'temperature front shift too small: {temp_front_shift:.8g}')
    if pressure_front_shift_cells < args.min_front_shift_cells:
        fail(f'pressure front shift too small in cells: {pressure_front_shift_cells:.8g}')

    heat_release_absmax = s1['heatRelease']['absmax']
    if heat_release_absmax < args.min_heat_release_absmax:
        fail(f'heatRelease response too small: {heat_release_absmax:.8g}')
    o2_consumption = s0['Y(O2)']['max'] - s1['Y(O2)']['min']
    if o2_consumption < args.min_o2_consumption:
        fail(f'O2 consumption too small: {o2_consumption:.8e}')
    fuel_vapor_increase = s1['Y(NC7H16)']['max'] - s0['Y(NC7H16)']['max']
    if fuel_vapor_increase < args.min_fuel_vapor_increase:
        fail(f'fuel vapor response too small: {fuel_vapor_increase:.8e}')

    count0 = parse_particle_count(initial_path)
    count1 = parse_particle_count(final_path)
    if count0 <= 0:
        fail('initial particle count is not positive')
    particle_growth = count1 / count0
    if particle_growth < args.min_particle_growth:
        fail(f'particle growth too small: {particle_growth:.8g}')

    spray_mass0 = s0['spray_mass']['sum']
    spray_mass1 = s1['spray_mass']['sum']
    if spray_mass0 <= 0.0 or spray_mass1 <= 0.0:
        fail('spray mass is not positive')
    spray_mass_loss_rel = max(0.0, spray_mass0 - spray_mass1) / spray_mass0
    if spray_mass_loss_rel < args.min_spray_mass_loss_rel:
        fail(f'spray mass loss too small: {spray_mass_loss_rel:.8e}')
    if s1['spray_x_vel']['absmax'] < args.min_spray_velocity:
        fail(f'spray velocity response too small: {s1["spray_x_vel"]["absmax"]:.8g}')
    spray_temp_increase = s1['spray_temp']['max'] - s0['spray_temp']['max']
    if spray_temp_increase < args.min_spray_temp_increase:
        fail(f'spray temperature increase too small: {spray_temp_increase:.8g}')
    surface_area_ratio = s1['spray_surf_area']['sum'] / s0['spray_surf_area']['sum']
    if surface_area_ratio <= 1.0:
        fail('spray surface area did not grow under breakup')
    if s1['d32']['max'] > s0['d32']['max'] * (1.0 + 1.0e-8):
        fail('Sauter mean diameter increased unexpectedly')

    metrics = {
        'time0': float(p0['time']),
        'time1': float(p1['time']),
        'pressure_front0': pressure_front0,
        'pressure_front1': pressure_front1,
        'pressure_front_shift': pressure_front_shift,
        'pressure_front_shift_cells': pressure_front_shift_cells,
        'temp_front0': temp_front0,
        'temp_front1': temp_front1,
        'temp_front_shift': temp_front_shift,
        'heat_release_absmax': heat_release_absmax,
        'heat_release_sum': s1['heatRelease']['sum'],
        'rhoe_dot_absmax': s1['rhoe_dot']['absmax'],
        'o2_consumption': o2_consumption,
        'fuel_vapor_increase': fuel_vapor_increase,
        'species_closure_rel': species_closure_rel,
        'particle_count0': float(count0),
        'particle_count1': float(count1),
        'particle_growth_factor': particle_growth,
        'spray_mass_loss_rel': spray_mass_loss_rel,
        'spray_x_vel_absmax': s1['spray_x_vel']['absmax'],
        'spray_temp_max1': s1['spray_temp']['max'],
        'spray_temp_increase': spray_temp_increase,
        'surface_area_ratio': surface_area_ratio,
        'd32_max1': s1['d32']['max'],
    }
    if not all(math.isfinite(v) for v in metrics.values()):
        fail('non-finite validation metric')

    print(
        'academic_spray_detonation_validation PASS '
        f'time={metrics["time1"]:.12g} '
        f'pressure_front={pressure_front0:.8g}:{pressure_front1:.8g} '
        f'pressure_front_shift={pressure_front_shift:.8g} '
        f'pressure_front_shift_cells={pressure_front_shift_cells:.8g} '
        f'temp_front={temp_front0:.8g}:{temp_front1:.8g} '
        f'temp_front_shift={temp_front_shift:.8g} '
        f'heat_release_absmax={heat_release_absmax:.8e} '
        f'o2_consumption={o2_consumption:.8e} '
        f'fuel_vapor_increase={fuel_vapor_increase:.8e} '
        f'particles={count0}:{count1} '
        f'particle_growth={particle_growth:.8g} '
        f'spray_mass_loss_rel={spray_mass_loss_rel:.8e} '
        f'spray_x_vel_absmax={metrics["spray_x_vel_absmax"]:.8e} '
        f'spray_temp_increase={spray_temp_increase:.8e} '
        f'surface_area_ratio={surface_area_ratio:.8e} '
        f'd32_max={metrics["d32_max1"]:.8e} '
        f'species_closure_rel={species_closure_rel:.8e}'
    )


if __name__ == '__main__':
    main()
