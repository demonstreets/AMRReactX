#!/usr/bin/env python3
import argparse
import math
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
            r'H2 leak source interval: time=([0-9.eE+-]+), dt=([0-9.eE+-]+), '
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

def field3(fields, name):
    if name not in fields:
        raise SystemExit(f'FAIL: plotfile lacks {name}')
    arr = np.asarray(fields[name], dtype=float)
    if arr.ndim != 3:
        raise SystemExit(f'FAIL: expected 3D field {name}, got shape {arr.shape}')
    if not np.all(np.isfinite(arr)):
        raise SystemExit(f'FAIL: non-finite values in {name}')
    return arr



def effective_mdot(values, log):
    match = re.search(r'H2 leak effective mass flow rate=([0-9.eE+-]+)', log)
    if match:
        return float(match.group(1))
    return first_float(values, 'prob.leak_rate')

def gaussian_profile(coords, center, sigma):
    if sigma <= 0.0 or not math.isfinite(sigma):
        raise SystemExit(f'FAIL: invalid Gaussian sigma {sigma}')
    arr = np.exp(-0.5 * ((np.asarray(coords, dtype=float) - center) / sigma) ** 2)
    total = float(np.sum(arr))
    if total <= 0.0 or not math.isfinite(total):
        raise SystemExit('FAIL: invalid Gaussian profile normalization')
    return arr / total


def normalized_profile(values, label):
    arr = np.maximum(np.asarray(values, dtype=float), 0.0)
    total = float(np.sum(arr))
    if total <= 0.0 or not math.isfinite(total):
        raise SystemExit(f'FAIL: nonpositive {label} profile mass')
    return arr / total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plotfile', required=True)
    ap.add_argument('--input', required=True)
    ap.add_argument('--log', required=True)
    ap.add_argument('--max-y-l1', type=float, default=0.55)
    ap.add_argument('--max-z-l1', type=float, default=0.55)
    ap.add_argument('--min-centroid-shift', type=float, default=0.03)
    ap.add_argument('--min-downstream-fraction', type=float, default=0.65)
    ap.add_argument('--max-lateral-offset', type=float, default=0.08)
    ap.add_argument('--min-plane-mass-fraction', type=float, default=0.05)
    ap.add_argument('--min-final-mass-ratio', type=float, default=0.80)
    ap.add_argument('--max-final-mass-ratio', type=float, default=1.20)
    args = ap.parse_args()

    vals = parse_input(args.input)
    leak_x = first_float(vals, 'prob.leak_xc')
    leak_y = first_float(vals, 'prob.leak_yc')
    leak_z = first_float(vals, 'prob.leak_zc')
    leak_radius = first_float(vals, 'prob.leak_radius')

    with open(args.log, 'r', encoding='utf-8', errors='replace') as fh:
        log = fh.read()
    if 'Unused ParmParse Variables' in log:
        raise SystemExit('FAIL: unused ParmParse variables in run log')
    if 'H2 leak discrete active volume=' not in log:
        raise SystemExit('FAIL: leak normalization line missing from run log')
    mdot = effective_mdot(vals, log)

    pf = amrex_reader.read_plotfile(args.plotfile)
    fields = pf['fields']
    raw_shape = field3(fields, 'density').shape
    volume_fraction = fluid_volume_fraction(fields, raw_shape)
    fluid = volume_fraction > 0.0
    yh2 = np.maximum(masked_field3(fields, 'Y(H2)', volume_fraction, max_abs=10.0), 0.0)
    rho = np.maximum(masked_field3(fields, 'density', volume_fraction, max_abs=1.0e6), 0.0)
    h2_mass_density = yh2 * rho
    cell_volume = float(np.prod(pf['dx'][:pf['ndim']]))
    cell_volumes = cell_volume * volume_fraction
    h2_mass = float(np.sum(h2_mass_density * cell_volumes))
    injected = source_interval_injected_mass(log, float(pf['time']), mdot)
    if injected <= 0.0:
        raise SystemExit('FAIL: nonpositive injected mass reference')
    mass_ratio = h2_mass / injected
    if mass_ratio < args.min_final_mass_ratio or mass_ratio > args.max_final_mass_ratio:
        raise SystemExit(f'FAIL: final H2 mass/injected ratio outside bounds: {mass_ratio}')

    x = np.asarray(pf['x'], dtype=float)[:, None, None]
    y = np.asarray(pf['y'], dtype=float)[None, :, None]
    z = np.asarray(pf['z'], dtype=float)[None, None, :]
    h2_mass_cells = h2_mass_density * cell_volumes
    total_density_mass = float(np.sum(h2_mass_cells))
    if total_density_mass <= 0.0:
        raise SystemExit('FAIL: nonpositive H2 mass')
    cx = float(np.sum(h2_mass_cells * x) / total_density_mass)
    cy = float(np.sum(h2_mass_cells * y) / total_density_mass)
    cz = float(np.sum(h2_mass_cells * z) / total_density_mass)
    centroid_shift = cx - leak_x
    if centroid_shift < args.min_centroid_shift:
        raise SystemExit(f'FAIL: plume centroid did not move downstream enough: {centroid_shift}')
    lateral_offset = math.hypot(cy - leak_y, cz - leak_z)
    if lateral_offset > args.max_lateral_offset:
        raise SystemExit(f'FAIL: plume centroid lateral/vertical offset too large: {lateral_offset}')

    downstream_mask = np.broadcast_to(x >= leak_x, h2_mass_cells.shape)
    downstream_fraction = float(np.sum(h2_mass_cells[downstream_mask]) / total_density_mass)
    if downstream_fraction < args.min_downstream_fraction:
        raise SystemExit(f'FAIL: downstream H2 mass fraction too small: {downstream_fraction}')

    ix = int(np.argmin(np.abs(np.asarray(pf['x'], dtype=float) - cx)))
    plane = h2_mass_cells[ix, :, :]
    plane_fraction = float(np.sum(plane) / total_density_mass)
    if plane_fraction < args.min_plane_mass_fraction:
        raise SystemExit(f'FAIL: centroid plane H2 fraction too small: {plane_fraction}')

    distance = max(float(pf['x'][ix]) - leak_x, float(pf['dx'][0]))
    sigma_y = max(0.10 * distance, 0.5 * leak_radius, float(pf['dx'][1]))
    sigma_z = max(0.05 * distance, 0.5 * leak_radius, float(pf['dx'][2]))

    y_profile = normalized_profile(np.sum(plane, axis=1), 'y')
    z_profile = normalized_profile(np.sum(plane, axis=0), 'z')
    y_ref = gaussian_profile(pf['y'], leak_y, sigma_y)
    z_ref = gaussian_profile(pf['z'], leak_z, sigma_z)
    y_l1 = float(np.sum(np.abs(y_profile - y_ref)))
    z_l1 = float(np.sum(np.abs(z_profile - z_ref)))
    if y_l1 > args.max_y_l1:
        raise SystemExit(f'FAIL: crosswind profile L1 too large: {y_l1}')
    if z_l1 > args.max_z_l1:
        raise SystemExit(f'FAIL: vertical profile L1 too large: {z_l1}')

    print('h2_leak_plume_profile_validation PASS ' +
          f'plot={args.plotfile} time={pf["time"]:.8g} h2_mass={h2_mass:.8e} ' +
          f'injected={injected:.8e} mass_ratio={mass_ratio:.8e} ' +
          f'centroid=({cx:.8e},{cy:.8e},{cz:.8e}) ' +
          f'centroid_shift={centroid_shift:.8e} downstream_fraction={downstream_fraction:.8e} ' +
          f'plane_x={float(pf["x"][ix]):.8e} plane_fraction={plane_fraction:.8e} ' +
          f'sigma_y={sigma_y:.8e} sigma_z={sigma_z:.8e} y_l1={y_l1:.8e} z_l1={z_l1:.8e}')


if __name__ == '__main__':
    main()
