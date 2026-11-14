#!/usr/bin/env python3
import argparse
import os
import sys

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader

# Molecular weights [kg/kmol numerically equal to g/mol] for LiDryer species.
MOLECULAR_WEIGHTS = {
    'H': 1.00794,
    'H2': 2.01588,
    'O': 15.9994,
    'O2': 31.9988,
    'OH': 17.00734,
    'H2O': 18.01528,
    'HO2': 33.00674,
    'H2O2': 34.01468,
    'N2': 28.0134,
}


def field3(fields, name):
    if name not in fields:
        raise SystemExit(f'FAIL: plotfile lacks {name}')
    arr = np.asarray(fields[name], dtype=float)
    if arr.ndim != 3:
        raise SystemExit(f'FAIL: expected 3D field {name}, got shape {arr.shape}')
    if not np.all(np.isfinite(arr)):
        raise SystemExit(f'FAIL: non-finite values in {name}')
    return arr


def fluid_volume_fraction(fields, shape):
    if 'volFrac' not in fields:
        return np.ones(shape, dtype=float)
    vf = field3(fields, 'volFrac')
    if vf.shape != shape:
        raise SystemExit(f'FAIL: volFrac shape {vf.shape} does not match field shape {shape}')
    valid = (vf > 1.0e-12) & (vf <= 1.0 + 1.0e-8)
    weights = np.where(valid, np.clip(vf, 0.0, 1.0), 0.0)
    if float(np.sum(weights)) <= 0.0:
        raise SystemExit('FAIL: plotfile has no positive fluid volume fraction')
    return weights


def masked_field3(fields, name, volume_fraction, max_abs=None):
    arr = field3(fields, name)
    fluid = volume_fraction > 0.0
    if not np.all(np.isfinite(arr[fluid])):
        raise SystemExit(f'FAIL: non-finite fluid values in {name}')
    if max_abs is not None and np.any(np.abs(arr[fluid]) > max_abs):
        vmax = float(np.max(np.abs(arr[fluid])))
        raise SystemExit(f'FAIL: unphysical fluid values in {name}: max_abs={vmax}')
    return np.where(fluid, arr, 0.0)


def species_mole_fraction(fields, species, volume_fraction=None):
    denom = None
    numer = None
    fluid = None if volume_fraction is None else volume_fraction > 0.0
    for name, mw in MOLECULAR_WEIGHTS.items():
        field_name = f'Y({name})'
        if field_name not in fields:
            continue
        y_raw = field3(fields, field_name)
        if fluid is not None:
            y = np.where(fluid, np.maximum(y_raw, 0.0), 0.0)
        else:
            y = np.maximum(y_raw, 0.0)
        contrib = y / mw
        denom = contrib if denom is None else denom + contrib
        if name == species:
            numer = contrib
    if numer is None:
        raise SystemExit(f'FAIL: plotfile lacks Y({species})')
    if denom is None or not np.all(np.isfinite(denom)):
        raise SystemExit('FAIL: invalid mole-fraction denominator')
    x = np.zeros_like(numer, dtype=float)
    np.divide(numer, denom, out=x, where=denom > 0.0)
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plotfile', required=True)
    ap.add_argument('--species', default='H2')
    ap.add_argument('--lfl', type=float, default=0.04)
    ap.add_argument('--ufl', type=float, default=0.75)
    ap.add_argument('--warn-if-flammable', action='store_true')
    ap.add_argument('--min-cloud-cells', type=int, default=None)
    ap.add_argument('--min-cloud-volume', type=float, default=None)
    ap.add_argument('--max-cloud-volume', type=float, default=None)
    ap.add_argument('--min-max-x', type=float, default=None)
    ap.add_argument('--max-max-x', type=float, default=None)
    args = ap.parse_args()

    if not (0.0 <= args.lfl < args.ufl <= 1.0):
        raise SystemExit('FAIL: invalid LFL/UFL bounds')

    pf = amrex_reader.read_plotfile(args.plotfile)
    fields = pf['fields']
    raw_shape = field3(fields, 'density').shape
    volume_fraction = fluid_volume_fraction(fields, raw_shape)
    fluid = volume_fraction > 0.0
    rho = np.maximum(masked_field3(fields, 'density', volume_fraction, max_abs=1.0e6), 0.0)
    y_name = f'Y({args.species})'
    y_sp = np.maximum(masked_field3(fields, y_name, volume_fraction, max_abs=10.0), 0.0)
    x_sp = species_mole_fraction(fields, args.species, volume_fraction)
    if not np.all(np.isfinite(x_sp[fluid])):
        raise SystemExit(f'FAIL: non-finite fluid X({args.species})')

    cell_volume = float(np.prod(pf['dx'][:pf['ndim']]))
    species_mass_density = rho * y_sp
    cell_volumes = cell_volume * volume_fraction
    total_species_mass = float(np.sum(species_mass_density * cell_volumes))
    cloud_mask = (x_sp >= args.lfl) & (x_sp <= args.ufl) & fluid
    cloud_cells = int(np.count_nonzero(cloud_mask))
    cloud_volume = float(np.sum(cell_volumes[cloud_mask]))
    cloud_species_mass = float(np.sum(species_mass_density[cloud_mask] * cell_volumes[cloud_mask]))
    max_x = float(np.max(x_sp))
    max_y = float(np.max(y_sp))
    mean_x_active = float(np.mean(x_sp[x_sp > 0.0])) if np.any(x_sp > 0.0) else 0.0

    if args.min_cloud_cells is not None and cloud_cells < args.min_cloud_cells:
        raise SystemExit(f'FAIL: too few flammable cloud cells: {cloud_cells}')
    if args.min_cloud_volume is not None and cloud_volume < args.min_cloud_volume:
        raise SystemExit(f'FAIL: flammable cloud volume too small: {cloud_volume}')
    if args.max_cloud_volume is not None and cloud_volume > args.max_cloud_volume:
        raise SystemExit(f'FAIL: flammable cloud volume too large: {cloud_volume}')
    if args.min_max_x is not None and max_x < args.min_max_x:
        raise SystemExit(f'FAIL: max X({args.species}) too small: {max_x}')
    if args.max_max_x is not None and max_x > args.max_max_x:
        raise SystemExit(f'FAIL: max X({args.species}) too large: {max_x}')
    if args.warn_if_flammable and cloud_volume > 0.0:
        raise SystemExit(f'FAIL: flammable cloud detected: volume={cloud_volume}')

    status = 'flammable_cloud_detected' if cloud_volume > 0.0 else 'no_flammable_cloud'
    print('h2_leak_hazard_summary PASS ' +
          f'plot={args.plotfile} time={pf["time"]:.8g} species={args.species} ' +
          f'lfl={args.lfl:.8e} ufl={args.ufl:.8e} status={status} ' +
          f'cloud_cells={cloud_cells} cloud_volume={cloud_volume:.8e} ' +
          f'cloud_species_mass={cloud_species_mass:.8e} total_species_mass={total_species_mass:.8e} ' +
          f'max_X={max_x:.8e} max_Y={max_y:.8e} mean_X_active={mean_x_active:.8e}')


if __name__ == '__main__':
    main()
