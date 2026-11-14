#!/usr/bin/env python3
import argparse
import csv
import os
import re
import sys

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader
from validate_h2_leak_hazard_summary import field3, fluid_volume_fraction, masked_field3, species_mole_fraction


def step_number(path):
    match = re.search(r'plt(\d+)$', os.path.basename(path.rstrip('/')))
    return int(match.group(1)) if match else -1


def discover_plotfiles(run_dir):
    paths = []
    for name in os.listdir(run_dir):
        path = os.path.join(run_dir, name)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, 'Header')) and re.match(r'plt\d+$', name):
            paths.append(path)
    return sorted(paths, key=step_number)


def plane_metrics(pf, species, lfl, ufl, min_x, min_active_x):
    fields = pf['fields']
    raw_shape = field3(fields, 'density').shape
    volume_fraction = fluid_volume_fraction(fields, raw_shape)
    fluid = volume_fraction > 0.0
    rho = np.maximum(masked_field3(fields, 'density', volume_fraction, max_abs=1.0e6), 0.0)
    y_sp = np.maximum(masked_field3(fields, f'Y({species})', volume_fraction, max_abs=10.0), 0.0)
    x_sp = species_mole_fraction(fields, species, volume_fraction)
    if not np.all(np.isfinite(x_sp[fluid])):
        raise SystemExit(f'FAIL: non-finite fluid X({species})')

    dx = np.asarray(pf['dx'][:3], dtype=float)
    cell_volume = float(np.prod(dx))
    cell_volumes = cell_volume * volume_fraction
    species_mass_density = rho * y_sp
    cloud_mask = (x_sp >= lfl) & (x_sp <= ufl) & fluid
    total_species_mass = float(np.sum(species_mass_density * cell_volumes))
    total_cloud_species_mass = float(np.sum(species_mass_density[cloud_mask] * cell_volumes[cloud_mask]))
    total_cloud_volume = float(np.sum(cell_volumes[cloud_mask]))
    peak_x = float(np.max(x_sp))
    peak_y = float(np.max(y_sp))

    active_planes = 0
    flammable_planes = 0
    max_plane_cloud_cells = 0
    max_plane_cloud_volume = 0.0
    for ix, x in enumerate(np.asarray(pf['x'], dtype=float)):
        if min_x is not None and float(x) < min_x:
            continue
        plane_x = x_sp[ix, :, :]
        plane_cloud = cloud_mask[ix, :, :]
        if int(np.count_nonzero(plane_x >= min_active_x)) > 0:
            active_planes += 1
        cloud_cells = int(np.count_nonzero(plane_cloud))
        if cloud_cells > 0:
            flammable_planes += 1
        max_plane_cloud_cells = max(max_plane_cloud_cells, cloud_cells)
        max_plane_cloud_volume = max(max_plane_cloud_volume, float(cloud_cells * cell_volume))

    return {
        'time': float(pf['time']),
        'step': None,
        'total_species_mass': total_species_mass,
        'total_cloud_species_mass': total_cloud_species_mass,
        'total_cloud_volume': total_cloud_volume,
        'peak_X': peak_x,
        'peak_Y': peak_y,
        'active_planes': active_planes,
        'flammable_planes': flammable_planes,
        'max_plane_cloud_cells': max_plane_cloud_cells,
        'max_plane_cloud_volume': max_plane_cloud_volume,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-dir', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--species', default='H2')
    ap.add_argument('--lfl', type=float, default=0.04)
    ap.add_argument('--ufl', type=float, default=0.75)
    ap.add_argument('--min-x', type=float, default=None)
    ap.add_argument('--min-active-x', type=float, default=1.0e-6)
    ap.add_argument('--min-plotfiles', type=int, default=2)
    ap.add_argument('--require-monotone-mass', action='store_true')
    ap.add_argument('--max-mass-drop-ratio', type=float, default=1.0e-6)
    ap.add_argument('--max-initial-cloud-volume', type=float, default=None)
    ap.add_argument('--min-final-active-planes', type=int, default=None)
    ap.add_argument('--min-final-flammable-planes', type=int, default=None)
    ap.add_argument('--min-max-flammable-planes', type=int, default=None)
    ap.add_argument('--min-final-cloud-volume', type=float, default=None)
    ap.add_argument('--max-final-cloud-volume', type=float, default=None)
    ap.add_argument('--min-final-peak-x', type=float, default=None)
    ap.add_argument('--max-final-peak-x', type=float, default=None)
    args = ap.parse_args()

    if not (0.0 <= args.lfl < args.ufl <= 1.0):
        raise SystemExit('FAIL: invalid LFL/UFL bounds')

    plotfiles = discover_plotfiles(args.run_dir)
    if len(plotfiles) < args.min_plotfiles:
        raise SystemExit(f'FAIL: expected at least {args.min_plotfiles} plotfiles, found {len(plotfiles)}')

    rows = []
    for path in plotfiles:
        pf = amrex_reader.read_plotfile(path)
        if pf['ndim'] != 3:
            raise SystemExit(f'FAIL: expected 3D plotfile, got ndim={pf["ndim"]}')
        row = plane_metrics(pf, args.species, args.lfl, args.ufl, args.min_x, args.min_active_x)
        row['step'] = step_number(path)
        row['plotfile'] = os.path.basename(path.rstrip('/'))
        rows.append(row)

    times = np.asarray([row['time'] for row in rows], dtype=float)
    if not np.all(np.diff(times) > 0.0):
        raise SystemExit(f'FAIL: plotfile times are not strictly increasing: {times.tolist()}')

    masses = np.asarray([row['total_species_mass'] for row in rows], dtype=float)
    if args.require_monotone_mass:
        max_drop = float(np.max(-np.diff(masses))) if len(masses) > 1 else 0.0
        allowed_drop = max(1.0e-14, args.max_mass_drop_ratio * float(np.max(masses)))
        if max_drop > allowed_drop:
            raise SystemExit(
                f'FAIL: species mass is not monotone enough: max_drop={max_drop} ' +
                f'max_mass_drop_ratio={args.max_mass_drop_ratio}'
            )

    initial_cloud_volume = rows[0]['total_cloud_volume']
    final = rows[-1]
    max_flammable_planes = max(row['flammable_planes'] for row in rows)
    max_cloud_volume = max(row['total_cloud_volume'] for row in rows)
    max_peak_x = max(row['peak_X'] for row in rows)

    if args.max_initial_cloud_volume is not None and initial_cloud_volume > args.max_initial_cloud_volume:
        raise SystemExit(f'FAIL: initial cloud volume too large: {initial_cloud_volume}')
    if args.min_final_active_planes is not None and final['active_planes'] < args.min_final_active_planes:
        raise SystemExit(f'FAIL: final active planes too few: {final["active_planes"]}')
    if args.min_final_flammable_planes is not None and final['flammable_planes'] < args.min_final_flammable_planes:
        raise SystemExit(f'FAIL: final flammable planes too few: {final["flammable_planes"]}')
    if args.min_max_flammable_planes is not None and max_flammable_planes < args.min_max_flammable_planes:
        raise SystemExit(f'FAIL: max flammable planes too few: {max_flammable_planes}')
    if args.min_final_cloud_volume is not None and final['total_cloud_volume'] < args.min_final_cloud_volume:
        raise SystemExit(f'FAIL: final cloud volume too small: {final["total_cloud_volume"]}')
    if args.max_final_cloud_volume is not None and final['total_cloud_volume'] > args.max_final_cloud_volume:
        raise SystemExit(f'FAIL: final cloud volume too large: {final["total_cloud_volume"]}')
    if args.min_final_peak_x is not None and final['peak_X'] < args.min_final_peak_x:
        raise SystemExit(f'FAIL: final peak X({args.species}) too small: {final["peak_X"]}')
    if args.max_final_peak_x is not None and final['peak_X'] > args.max_final_peak_x:
        raise SystemExit(f'FAIL: final peak X({args.species}) too large: {final["peak_X"]}')

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    fieldnames = [
        'step', 'plotfile', 'time', 'species', 'total_species_mass',
        'total_cloud_species_mass', 'total_cloud_volume', 'peak_X', 'peak_Y',
        'active_planes', 'flammable_planes', 'max_plane_cloud_cells',
        'max_plane_cloud_volume',
    ]
    with open(args.output, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = {key: row[key] for key in fieldnames if key in row}
            out['species'] = args.species
            for key in ('time', 'total_species_mass', 'total_cloud_species_mass',
                        'total_cloud_volume', 'peak_X', 'peak_Y',
                        'max_plane_cloud_volume'):
                out[key] = f'{float(out[key]):.12e}'
            writer.writerow(out)

    print('h2_leak_hazard_timeseries PASS ' +
          f'run_dir={args.run_dir} output={args.output} species={args.species} ' +
          f'plotfiles={len(rows)} time0={times[0]:.8g} timeN={times[-1]:.8g} ' +
          f'mass0={masses[0]:.8e} massN={masses[-1]:.8e} ' +
          f'initial_cloud_volume={initial_cloud_volume:.8e} ' +
          f'final_cloud_volume={final["total_cloud_volume"]:.8e} ' +
          f'max_cloud_volume={max_cloud_volume:.8e} ' +
          f'final_active_planes={final["active_planes"]} ' +
          f'final_flammable_planes={final["flammable_planes"]} ' +
          f'max_flammable_planes={max_flammable_planes} ' +
          f'final_peak_X={final["peak_X"]:.8e} max_peak_X={max_peak_x:.8e}')


if __name__ == '__main__':
    main()
