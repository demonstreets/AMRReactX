#!/usr/bin/env python3
"""Validate academic Euler-Lagrange droplet motion, breakup, and coupling."""
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
        'pelec.do_spray_particles': '1',
        'particles.mom_transfer': '1',
        'particles.mass_transfer': '1',
        'particles.fixed_parts': '0',
    }
    for key, want in expected.items():
        got = values.get(key)
        if got != want:
            fail(f'input {key}={got!r}, expected {want!r}')
    breakup = values.get('particles.use_breakup_model', '').upper()
    if breakup != 'KHRT':
        fail(f'input particles.use_breakup_model={breakup!r}, expected KHRT')


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


def read_plot(path: Path) -> dict[str, object]:
    if not path.is_dir():
        fail(f'missing plotfile: {path}')
    return amrex_reader.read_plotfile(str(path))


def log_is_clean(path: Path) -> None:
    text = path.read_text(errors='replace')
    if 'AMReX' not in text or 'finalized' not in text:
        fail(f'run log does not show AMReX finalized: {path}')
    if re.search(r'\b(?:nan|inf|SIGSEGV|Segmentation|Backtrace|Abort)\b', text, re.IGNORECASE):
        fail(f'run log contains failure token: {path}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--run-log', required=True)
    parser.add_argument('--initial', required=True)
    parser.add_argument('--final', required=True)
    parser.add_argument('--min-particle-growth', type=float, default=2.0)
    parser.add_argument('--min-spray-velocity', type=float, default=100.0)
    parser.add_argument('--min-mass-loss-rel', type=float, default=1.0e-5)
    parser.add_argument('--max-gas-fuel-abs-sum', type=float, default=1.0e-12)
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

    count0 = parse_particle_count(initial_path)
    count1 = parse_particle_count(final_path)
    if count0 <= 0:
        fail('initial particle count is not positive')
    particle_growth = count1 / count0
    if particle_growth < args.min_particle_growth:
        fail(f'particle growth too small: {particle_growth:.8g}')

    required = [
        'density', 'Temp', 'pressure', 'rho_NC7H16',
        'spray_mass', 'spray_num', 'spray_surf_area', 'd10', 'd32',
        'spray_temp', 'num_parcels', 'spray_x_vel', 'spray_y_vel',
    ]
    f0 = {name: field(p0, name) for name in required}
    f1 = {name: field(p1, name) for name in required}
    s0 = {name: stats(arr) for name, arr in f0.items()}
    s1 = {name: stats(arr) for name, arr in f1.items()}

    for name in ('density', 'Temp', 'pressure'):
        if s0[name]['min'] <= 0.0 or s1[name]['min'] <= 0.0:
            fail(f'{name} became nonphysical')

    spray_mass0 = s0['spray_mass']['sum']
    spray_mass1 = s1['spray_mass']['sum']
    if spray_mass0 <= 0.0 or spray_mass1 <= 0.0:
        fail('spray mass is not positive')
    mass_loss_rel = max(0.0, spray_mass0 - spray_mass1) / spray_mass0
    if mass_loss_rel < args.min_mass_loss_rel:
        fail(f'spray mass loss too small: {mass_loss_rel:.8e}')

    if s1['spray_x_vel']['absmax'] < args.min_spray_velocity:
        fail(f'spray x velocity response too small: {s1["spray_x_vel"]["absmax"]:.8g}')
    if s1['spray_temp']['max'] <= s0['spray_temp']['max']:
        fail('spray temperature did not increase')
    if s1['spray_surf_area']['sum'] <= s0['spray_surf_area']['sum']:
        fail('spray surface area did not increase under breakup')
    if s1['d32']['max'] > s0['d32']['max'] * (1.0 + 1.0e-8):
        fail('Sauter mean diameter increased unexpectedly')
    if s1['num_parcels']['sum'] <= s0['num_parcels']['sum']:
        fail('Eulerian num_parcels did not increase')
    if abs(s1['rho_NC7H16']['sum']) > args.max_gas_fuel_abs_sum:
        fail(f'gas fuel mass closure drift too high: {s1["rho_NC7H16"]["sum"]:.8e}')

    metrics = {
        'time0': float(p0['time']),
        'time1': float(p1['time']),
        'particle_count0': float(count0),
        'particle_count1': float(count1),
        'particle_growth_factor': float(particle_growth),
        'spray_mass0': spray_mass0,
        'spray_mass1': spray_mass1,
        'spray_mass_loss_rel': mass_loss_rel,
        'spray_x_vel_absmax': s1['spray_x_vel']['absmax'],
        'spray_y_vel_absmax': s1['spray_y_vel']['absmax'],
        'spray_temp_max0': s0['spray_temp']['max'],
        'spray_temp_max1': s1['spray_temp']['max'],
        'spray_surface_area_sum0': s0['spray_surf_area']['sum'],
        'spray_surface_area_sum1': s1['spray_surf_area']['sum'],
        'd32_max0': s0['d32']['max'],
        'd32_max1': s1['d32']['max'],
        'num_parcels_sum0': s0['num_parcels']['sum'],
        'num_parcels_sum1': s1['num_parcels']['sum'],
        'gas_fuel_sum1': s1['rho_NC7H16']['sum'],
        'density_min1': s1['density']['min'],
        'pressure_min1': s1['pressure']['min'],
        'temperature_min1': s1['Temp']['min'],
    }
    if not all(math.isfinite(v) for v in metrics.values()):
        fail('non-finite validation metric')

    print(
        'academic_droplet_euler_lagrange_validation PASS '
        f'time={metrics["time1"]:.12g} '
        f'particles={count0}:{count1} '
        f'particle_growth={particle_growth:.8g} '
        f'spray_mass_loss_rel={mass_loss_rel:.8e} '
        f'spray_x_vel_absmax={metrics["spray_x_vel_absmax"]:.8e} '
        f'spray_temp_max={metrics["spray_temp_max1"]:.8e} '
        f'surface_area_ratio={metrics["spray_surface_area_sum1"] / metrics["spray_surface_area_sum0"]:.8e} '
        f'd32_max={metrics["d32_max1"]:.8e} '
        f'gas_fuel_sum={metrics["gas_fuel_sum1"]:.8e}'
    )


if __name__ == '__main__':
    main()
