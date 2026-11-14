#!/usr/bin/env python3
import argparse
import os
import re
import sys

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader
from validate_h2_leak_hazard_summary import fluid_volume_fraction, masked_field3


def parse_input(path):
    values = {}
    with open(path, 'r', encoding='utf-8') as fh:
        for raw in fh:
            line = raw.split('#', 1)[0].strip()
            if not line or '=' not in line:
                continue
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip().split()
    return values


def first_float(values, key, default=None):
    try:
        return float(values[key][0])
    except KeyError:
        if default is None:
            raise
        return default



def effective_mdot(values, log):
    match = re.search(r'H2 leak effective mass flow rate=([0-9.eE+-]+)', log)
    if match:
        return float(match.group(1))
    match = re.search(r'Engineering fuel leak effective mass flow rate=([0-9.eE+-]+)', log)
    if match:
        return float(match.group(1))
    return first_float(values, 'prob.leak_rate')



def source_interval_injected_mass(log, final_time, fallback_mdot):
    current_step = None
    total = 0.0
    used = False
    seen_intervals = set()
    final_time = float(final_time)
    for raw in log.splitlines():
        step_match = re.search(r'STEP \[(-?\d+)\] - Time:', raw)
        if step_match:
            current_step = int(step_match.group(1))
            continue
        match = re.search(
            r'(?:H2 leak|Engineering fuel leak) source interval: time=([0-9.eE+-]+), dt=([0-9.eE+-]+), '
            r'model=([^,]+), mdot=([0-9.eE+-]+), injected_interval=([0-9.eE+-]+)',
            raw)
        if not match or current_step is None or current_step < 0:
            continue
        interval_key = (current_step,) + match.groups()
        if interval_key in seen_intervals:
            continue
        seen_intervals.add(interval_key)
        start = float(match.group(1))
        dt = float(match.group(2))
        mdot = float(match.group(4))
        injected = float(match.group(5))
        if dt <= 0.0 or start >= final_time - 1.0e-14:
            continue
        covered = min(start + dt, final_time) - start
        if covered <= 0.0:
            continue
        if abs(covered - dt) <= max(1.0e-15, 1.0e-10 * dt):
            total += injected
        else:
            total += mdot * covered
        used = True
    if used:
        return total
    return fallback_mdot * final_time

def step_number(path):
    match = re.search(r'plt(\d+)$', os.path.basename(path.rstrip('/')))
    if not match:
        return -1
    return int(match.group(1))


def discover_plotfiles(run_dir):
    paths = []
    for name in os.listdir(run_dir):
        path = os.path.join(run_dir, name)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, 'Header')) and re.match(r'plt\d+$', name):
            paths.append(path)
    return sorted(paths, key=step_number)


def field3(fields, name):
    if name not in fields:
        raise SystemExit(f'FAIL: plotfile lacks {name}')
    arr = np.asarray(fields[name], dtype=float)
    if arr.ndim != 3:
        raise SystemExit(f'FAIL: expected 3D field {name}, got shape {arr.shape}')
    if not np.all(np.isfinite(arr)):
        raise SystemExit(f'FAIL: non-finite values in {name}')
    return arr


def coordinate_mesh(pf):
    x = np.asarray(pf['x'], dtype=float)[:, None, None]
    y = np.asarray(pf['y'], dtype=float)[None, :, None]
    z = np.asarray(pf['z'], dtype=float)[None, None, :]
    return x, y, z


def weighted_centroid(mass, x, y, z):
    total = float(np.sum(mass))
    if total <= 0.0:
        raise SystemExit('FAIL: nonpositive H2 mass in centroid calculation')
    return (float(np.sum(mass * x) / total),
            float(np.sum(mass * y) / total),
            float(np.sum(mass * z) / total))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-dir', required=True)
    ap.add_argument('--input', required=True)
    ap.add_argument('--log', required=True)
    ap.add_argument('--species-name', default='H2')
    ap.add_argument('--min-plotfiles', type=int, default=6)
    ap.add_argument('--min-mass-growth-ratio', type=float, default=4.0)
    ap.add_argument('--max-mass-drop-ratio', type=float, default=1.0e-6,
                    help='Maximum allowed single-interval H2 mass drop normalized by final mass')
    ap.add_argument('--min-final-mass-ratio', type=float, default=0.80)
    ap.add_argument('--max-final-mass-ratio', type=float, default=1.50)
    ap.add_argument('--max-center-offset', type=float, default=0.10)
    ap.add_argument('--min-downstream-fraction', type=float, default=0.30)
    ap.add_argument('--min-upstream-fraction', type=float, default=0.20)
    args = ap.parse_args()

    vals = parse_input(args.input)
    leak_x = first_float(vals, 'prob.leak_xc')
    leak_y = first_float(vals, 'prob.leak_yc')
    leak_z = first_float(vals, 'prob.leak_zc')

    with open(args.log, 'r', encoding='utf-8', errors='replace') as fh:
        log = fh.read()
    if 'Unused ParmParse Variables' in log:
        raise SystemExit('FAIL: unused ParmParse variables in run log')
    if 'H2 leak discrete active volume=' not in log and 'Engineering fuel leak discrete active volume=' not in log:
        raise SystemExit('FAIL: leak normalization line missing from run log')
    mdot = effective_mdot(vals, log)
    species_name = args.species_name.strip()
    if not species_name:
        raise SystemExit('FAIL: --species-name cannot be empty')
    species_field = f'Y({species_name})'

    plotfiles = discover_plotfiles(args.run_dir)
    if len(plotfiles) < args.min_plotfiles:
        raise SystemExit(f'FAIL: expected at least {args.min_plotfiles} plotfiles, found {len(plotfiles)}')

    masses = []
    times = []
    max_yfuel = []
    centers = []
    downstream_fractions = []
    upstream_fractions = []
    observed_grids = []

    for path in plotfiles:
        pf = amrex_reader.read_plotfile(path)
        fields = pf['fields']
        raw_shape = field3(fields, 'density').shape
        volume_fraction = fluid_volume_fraction(fields, raw_shape)
        fluid = volume_fraction > 0.0
        yfuel = np.maximum(masked_field3(fields, species_field, volume_fraction, max_abs=10.0), 0.0)
        rho = np.maximum(masked_field3(fields, 'density', volume_fraction, max_abs=1.0e6), 0.0)
        grid = (pf['grid']['nx'], pf['grid']['ny'], pf['grid'].get('nz', 1))
        if not observed_grids or observed_grids[-1] != grid:
            observed_grids.append(grid)
        cell_volume = float(np.prod(pf['dx'][:pf['ndim']]))
        h2_mass_density = yfuel * rho
        h2_mass = h2_mass_density * (cell_volume * volume_fraction)
        total_mass = float(np.sum(h2_mass))
        masses.append(total_mass)
        times.append(float(pf['time']))
        max_yfuel.append(float(np.max(yfuel[fluid])) if np.any(fluid) else 0.0)
        x, y, z = coordinate_mesh(pf)
        if total_mass > 0.0:
            centers.append(weighted_centroid(h2_mass, x, y, z))
            downstream_mask = np.broadcast_to(x >= leak_x, h2_mass.shape)
            upstream_mask = np.broadcast_to(x < leak_x, h2_mass.shape)
            downstream_fractions.append(float(np.sum(h2_mass[downstream_mask]) / total_mass))
            upstream_fractions.append(float(np.sum(h2_mass[upstream_mask]) / total_mass))
        else:
            centers.append((float('nan'), float('nan'), float('nan')))
            downstream_fractions.append(float('nan'))
            upstream_fractions.append(float('nan'))

    if not np.all(np.diff(np.asarray(times)) > 0.0):
        raise SystemExit(f'FAIL: plotfile times are not strictly increasing: {times}')
    if max_yfuel[-1] <= 0.0:
        raise SystemExit(f'FAIL: final {species_name} maximum is nonpositive')

    positive_masses = masses[1:]
    if min(positive_masses) <= 0.0:
        raise SystemExit(f'FAIL: nonpositive H2 mass history: {masses}')
    mass_growth_ratio = masses[-1] / positive_masses[0]
    if mass_growth_ratio < args.min_mass_growth_ratio:
        raise SystemExit(f'FAIL: {species_name} mass growth ratio too small: {mass_growth_ratio}')
    max_negative_step = float(np.max(-np.diff(np.asarray(masses))))
    allowed_mass_drop = max(1.0e-14, args.max_mass_drop_ratio * masses[-1])
    if max_negative_step > allowed_mass_drop:
        raise SystemExit(
            f'FAIL: {species_name} mass history is not monotone enough: '
            f'max_drop={max_negative_step} allowed={allowed_mass_drop}'
        )

    final_injected = source_interval_injected_mass(log, times[-1], mdot)
    final_ratio = masses[-1] / final_injected if final_injected > 0.0 else 0.0
    if final_ratio < args.min_final_mass_ratio or final_ratio > args.max_final_mass_ratio:
        raise SystemExit(f'FAIL: final {species_name} mass/injected ratio outside bounds: {final_ratio}')

    cx, cy, cz = centers[-1]
    if not np.all(np.isfinite(np.asarray([cx, cy, cz]))):
        raise SystemExit(f'FAIL: final {species_name} centroid is not finite')
    lateral_offset = ((cy - leak_y) ** 2 + (cz - leak_z) ** 2) ** 0.5
    if lateral_offset > args.max_center_offset:
        raise SystemExit(f'FAIL: final plume lateral/vertical centroid moved too far: {lateral_offset}')
    if downstream_fractions[-1] < args.min_downstream_fraction:
        raise SystemExit(f'FAIL: downstream {species_name} mass fraction too small: {downstream_fractions[-1]}')
    if upstream_fractions[-1] < args.min_upstream_fraction:
        raise SystemExit(f'FAIL: upstream/source-side {species_name} mass fraction too small: {upstream_fractions[-1]}')

    pass_label = 'h2_leak_plume_history_validation' if species_name == 'H2' else 'fuel_leak_plume_history_validation'
    species_part = '' if species_name == 'H2' else f'species={species_name} '
    max_part = (
        f'max_YH2={max(max_yfuel):.8e} '
        if species_name == 'H2'
        else f'max_YFuel={max(max_yfuel):.8e} max_Y{species_name}={max(max_yfuel):.8e} '
    )
    print(f'{pass_label} PASS ' + species_part +
          f'nplot={len(plotfiles)} time0={times[0]:.8g} timeN={times[-1]:.8g} ' +
          f'mass0={masses[0]:.8e} mass1={masses[1]:.8e} massN={masses[-1]:.8e} ' +
          f'injectedN={final_injected:.8e} mass_ratioN={final_ratio:.8e} ' +
          f'mass_growth_ratio={mass_growth_ratio:.8e} max_mass_drop={max_negative_step:.8e} ' +
          f'max_mass_drop_ratio={max_negative_step / max(masses[-1], 1.0e-300):.8e} '
          + max_part +
          f'grid_shapes={observed_grids} ' +
          f'centroid=({cx:.8e},{cy:.8e},{cz:.8e}) lateral_offset={lateral_offset:.8e} ' +
          f'downstream_fraction={downstream_fractions[-1]:.8e} upstream_fraction={upstream_fractions[-1]:.8e}')


if __name__ == '__main__':
    main()
