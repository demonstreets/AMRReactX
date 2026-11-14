#!/usr/bin/env python3
import argparse
import csv
import os
import sys

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader
from validate_h2_leak_hazard_summary import field3, fluid_volume_fraction, masked_field3, species_mole_fraction


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plotfile', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--species', default='H2')
    ap.add_argument('--lfl', type=float, default=0.04)
    ap.add_argument('--ufl', type=float, default=0.75)
    ap.add_argument('--min-x', type=float, default=None,
                    help='Only planes with x >= min-x count toward plane gates.')
    ap.add_argument('--min-active-x', type=float, default=1.0e-6,
                    help='Plane is active when max mole fraction is at least this value.')
    ap.add_argument('--min-active-planes', type=int, default=None)
    ap.add_argument('--min-flammable-planes', type=int, default=None)
    ap.add_argument('--min-total-cloud-volume', type=float, default=None)
    ap.add_argument('--max-total-cloud-volume', type=float, default=None)
    ap.add_argument('--min-peak-x', type=float, default=None)
    ap.add_argument('--max-peak-x', type=float, default=None)
    args = ap.parse_args()

    if not (0.0 <= args.lfl < args.ufl <= 1.0):
        raise SystemExit('FAIL: invalid LFL/UFL bounds')

    pf = amrex_reader.read_plotfile(args.plotfile)
    if pf['ndim'] != 3:
        raise SystemExit(f'FAIL: expected 3D plotfile, got ndim={pf["ndim"]}')
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

    dx = np.asarray(pf['dx'][:3], dtype=float)
    cell_volume = float(np.prod(dx))
    plane_area_cell = float(dx[1] * dx[2])
    cell_volumes = cell_volume * volume_fraction
    plane_area_cells = plane_area_cell * volume_fraction
    species_mass_density = rho * y_sp
    cloud_mask = (x_sp >= args.lfl) & (x_sp <= args.ufl) & fluid

    rows = []
    total_cloud_volume = 0.0
    total_cloud_species_mass = 0.0
    total_species_mass = 0.0
    peak_x = 0.0
    active_planes = 0
    flammable_planes = 0

    for ix, x in enumerate(np.asarray(pf['x'], dtype=float)):
        plane_x = x_sp[ix, :, :]
        plane_y = y_sp[ix, :, :]
        plane_mass_density = species_mass_density[ix, :, :]
        plane_cell_volumes = cell_volumes[ix, :, :]
        plane_area_weights = plane_area_cells[ix, :, :]
        plane_cloud = cloud_mask[ix, :, :]
        plane_species_mass = float(np.sum(plane_mass_density * plane_cell_volumes))
        plane_cloud_species_mass = float(np.sum(plane_mass_density[plane_cloud] * plane_cell_volumes[plane_cloud]))
        cloud_cells = int(np.count_nonzero(plane_cloud))
        cloud_area = float(np.sum(plane_area_weights[plane_cloud]))
        cloud_volume = float(np.sum(plane_cell_volumes[plane_cloud]))
        max_x = float(np.max(plane_x))
        max_y = float(np.max(plane_y))
        active_count = int(np.count_nonzero(plane_x >= args.min_active_x))
        mean_x_active = float(np.mean(plane_x[plane_x >= args.min_active_x])) if active_count else 0.0
        gate_plane = args.min_x is None or float(x) >= args.min_x
        if gate_plane and active_count > 0:
            active_planes += 1
        if gate_plane and cloud_cells > 0:
            flammable_planes += 1
        total_cloud_volume += cloud_volume
        total_cloud_species_mass += plane_cloud_species_mass
        total_species_mass += plane_species_mass
        peak_x = max(peak_x, max_x)
        rows.append({
            'time': f'{pf["time"]:.8g}',
            'species': args.species,
            'plane_index': ix,
            'x': f'{float(x):.12e}',
            'max_X': f'{max_x:.12e}',
            'max_Y': f'{max_y:.12e}',
            'active_cells': active_count,
            'cloud_cells': cloud_cells,
            'cloud_area': f'{cloud_area:.12e}',
            'cloud_volume': f'{cloud_volume:.12e}',
            'plane_species_mass': f'{plane_species_mass:.12e}',
            'cloud_species_mass': f'{plane_cloud_species_mass:.12e}',
            'mean_X_active': f'{mean_x_active:.12e}',
        })

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    if args.min_active_planes is not None and active_planes < args.min_active_planes:
        raise SystemExit(f'FAIL: too few active planes: {active_planes}')
    if args.min_flammable_planes is not None and flammable_planes < args.min_flammable_planes:
        raise SystemExit(f'FAIL: too few flammable planes: {flammable_planes}')
    if args.min_total_cloud_volume is not None and total_cloud_volume < args.min_total_cloud_volume:
        raise SystemExit(f'FAIL: total cloud volume too small: {total_cloud_volume}')
    if args.max_total_cloud_volume is not None and total_cloud_volume > args.max_total_cloud_volume:
        raise SystemExit(f'FAIL: total cloud volume too large: {total_cloud_volume}')
    if args.min_peak_x is not None and peak_x < args.min_peak_x:
        raise SystemExit(f'FAIL: peak X({args.species}) too small: {peak_x}')
    if args.max_peak_x is not None and peak_x > args.max_peak_x:
        raise SystemExit(f'FAIL: peak X({args.species}) too large: {peak_x}')

    print('h2_leak_hazard_planes PASS ' +
          f'plot={args.plotfile} output={args.output} time={pf["time"]:.8g} species={args.species} ' +
          f'lfl={args.lfl:.8e} ufl={args.ufl:.8e} min_x={args.min_x} ' +
          f'planes={len(rows)} active_planes={active_planes} flammable_planes={flammable_planes} ' +
          f'total_cloud_volume={total_cloud_volume:.8e} ' +
          f'total_cloud_species_mass={total_cloud_species_mass:.8e} ' +
          f'total_species_mass={total_species_mass:.8e} peak_X={peak_x:.8e}')


if __name__ == '__main__':
    main()
