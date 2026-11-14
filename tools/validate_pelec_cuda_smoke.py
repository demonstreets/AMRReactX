#!/usr/bin/env python3
import argparse
import os
import sys

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader

REQUIRED_FIELDS = [
    'density', 'Temp', 'rho_H2', 'rho_O2', 'rho_H2O', 'rho_H', 'rho_O', 'rho_OH',
    'rho_HO2', 'rho_H2O2', 'rho_N2', 'x_velocity', 'y_velocity', 'z_velocity',
]


def require_field(fields, name):
    if name not in fields:
        raise SystemExit(f'FAIL: plotfile lacks required field {name}')
    arr = np.asarray(fields[name], dtype=float)
    if not np.all(np.isfinite(arr)):
        raise SystemExit(f'FAIL: non-finite values in {name}')
    return arr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plotfile', required=True)
    ap.add_argument('--min-time', type=float, default=0.0)
    ap.add_argument('--expected-nx', type=int, default=24)
    ap.add_argument('--expected-ny', type=int, default=16)
    ap.add_argument('--expected-nz', type=int, default=4)
    ap.add_argument('--min-temp-ratio', type=float, default=2.0)
    ap.add_argument('--max-species-closure-rel', type=float, default=1.0e-3)
    args = ap.parse_args()

    data = amrex_reader.read_plotfile(args.plotfile)
    grid = data['grid']
    if data['ndim'] != 3:
        raise SystemExit(f'FAIL: expected 3D plotfile, got ndim={data["ndim"]}')
    if (grid.get('nx'), grid.get('ny'), grid.get('nz')) != (args.expected_nx, args.expected_ny, args.expected_nz):
        raise SystemExit(
            'FAIL: unexpected grid '
            f'{grid.get("nx")}x{grid.get("ny")}x{grid.get("nz")}')
    if data['time'] <= args.min_time:
        raise SystemExit(f'FAIL: plotfile time {data["time"]} <= {args.min_time}')

    fields = data['fields']
    for name in REQUIRED_FIELDS:
        require_field(fields, name)

    rho = require_field(fields, 'density')
    temp = require_field(fields, 'Temp')
    h2 = require_field(fields, 'rho_H2')
    o2 = require_field(fields, 'rho_O2')
    h2o = require_field(fields, 'rho_H2O')

    if float(np.min(rho)) <= 0.0:
        raise SystemExit('FAIL: nonpositive density')
    if float(np.min(temp)) <= 0.0:
        raise SystemExit('FAIL: nonpositive temperature')
    species_min = min(float(np.min(h2)), float(np.min(o2)), float(np.min(h2o)))
    if species_min < -1.0e-14:
        raise SystemExit(f'FAIL: negative species density {species_min}')

    species_sum = sum(require_field(fields, name) for name in ['rho_H2', 'rho_O2', 'rho_H2O', 'rho_H', 'rho_O', 'rho_OH', 'rho_HO2', 'rho_H2O2', 'rho_N2'])
    species_closure_rel = float(np.max(np.abs(species_sum - rho) / np.maximum(np.abs(rho), 1.0e-300)))
    if species_closure_rel > args.max_species_closure_rel:
        raise SystemExit(f'FAIL: species closure relative error too large: {species_closure_rel}')

    temp_ratio = float(np.max(temp) / np.min(temp))
    if temp_ratio < args.min_temp_ratio:
        raise SystemExit(f'FAIL: temperature ratio too small: {temp_ratio}')

    h2o_max = float(np.max(h2o))
    if h2o_max <= 0.0:
        raise SystemExit('FAIL: hotspot H2O density did not appear')

    velocity_linf = max(
        float(np.max(np.abs(require_field(fields, 'x_velocity')))),
        float(np.max(np.abs(require_field(fields, 'y_velocity')))),
        float(np.max(np.abs(require_field(fields, 'z_velocity')))),
    )

    print('pelec_cuda_smoke_validation PASS ' +
          f'time={data["time"]:.8e} nx={grid["nx"]} ny={grid["ny"]} nz={grid["nz"]} ' +
          f'rho_min={float(np.min(rho)):.8e} rho_max={float(np.max(rho)):.8e} ' +
          f'temp_min={float(np.min(temp)):.8e} temp_max={float(np.max(temp)):.8e} temp_ratio={temp_ratio:.8e} ' +
          f'h2o_max={h2o_max:.8e} ' +
          f'species_min={species_min:.8e} species_closure_rel={species_closure_rel:.8e} ' +
          f'velocity_linf={velocity_linf:.8e}')


if __name__ == '__main__':
    main()
