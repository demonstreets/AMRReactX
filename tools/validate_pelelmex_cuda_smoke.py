#!/usr/bin/env python3
import argparse
import os
import sys

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader

REQUIRED_FIELDS = [
    'x_velocity', 'y_velocity', 'z_velocity', 'density', 'rhoh', 'temp',
    'RhoRT', 'divu', 'k', 'epsilon', 'volFrac', 'avg_pressure', 'mag_vort',
    'Y(N2)', 'Y(O2)', 'Y(C3H8)',
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
    ap.add_argument('--expected-nx', type=int, default=16)
    ap.add_argument('--expected-ny', type=int, default=10)
    ap.add_argument('--expected-nz', type=int, default=8)
    ap.add_argument('--min-time', type=float, default=0.0)
    ap.add_argument('--min-c3h8-max', type=float, default=1.0e-12)
    ap.add_argument('--max-species-sum-error', type=float, default=5.0e-12)
    args = ap.parse_args()

    data = amrex_reader.read_plotfile(args.plotfile)
    grid = data['grid']
    if data['ndim'] != 3:
        raise SystemExit(f'FAIL: expected 3D plotfile, got ndim={data["ndim"]}')
    if (grid.get('nx'), grid.get('ny'), grid.get('nz')) != (args.expected_nx, args.expected_ny, args.expected_nz):
        raise SystemExit(
            f'FAIL: unexpected grid {grid.get("nx")}x{grid.get("ny")}x{grid.get("nz")}')
    if data['time'] <= args.min_time:
        raise SystemExit(f'FAIL: plotfile time {data["time"]} <= {args.min_time}')

    fields = data['fields']
    for name in REQUIRED_FIELDS:
        require_field(fields, name)

    rho = require_field(fields, 'density')
    temp = require_field(fields, 'temp')
    rhoh = require_field(fields, 'rhoh')
    k = require_field(fields, 'k')
    eps = require_field(fields, 'epsilon')
    vfrac = require_field(fields, 'volFrac')
    yn2 = require_field(fields, 'Y(N2)')
    yo2 = require_field(fields, 'Y(O2)')
    yc3h8 = require_field(fields, 'Y(C3H8)')

    if float(np.min(rho)) <= 0.0:
        raise SystemExit('FAIL: nonpositive density')
    if float(np.min(temp)) <= 0.0:
        raise SystemExit('FAIL: nonpositive temperature')
    if float(np.min(rhoh)) <= 0.0:
        raise SystemExit('FAIL: nonpositive rhoh')
    if float(np.min(k)) < 0.0 or float(np.min(eps)) < 0.0:
        raise SystemExit('FAIL: negative k-epsilon field')
    if float(np.min(vfrac)) < -1.0e-14 or float(np.max(vfrac)) > 1.0 + 1.0e-14:
        raise SystemExit('FAIL: volume fraction outside [0,1]')

    species_min = min(float(np.min(yn2)), float(np.min(yo2)), float(np.min(yc3h8)))
    if species_min < -1.0e-14:
        raise SystemExit(f'FAIL: negative mass fraction {species_min}')
    species_sum_error = float(np.max(np.abs(yn2 + yo2 + yc3h8 - 1.0)))
    if species_sum_error > args.max_species_sum_error:
        raise SystemExit(f'FAIL: mass fraction sum error too large: {species_sum_error}')

    c3h8_max = float(np.max(yc3h8))
    if c3h8_max <= args.min_c3h8_max:
        raise SystemExit(f'FAIL: C3H8 source did not appear: {c3h8_max}')

    velocity_linf = max(
        float(np.max(np.abs(require_field(fields, 'x_velocity')))),
        float(np.max(np.abs(require_field(fields, 'y_velocity')))),
        float(np.max(np.abs(require_field(fields, 'z_velocity')))),
    )
    if velocity_linf <= 0.0:
        raise SystemExit('FAIL: velocity field is zero')

    print('pelelmex_cuda_smoke_validation PASS ' +
          f'time={data["time"]:.8e} nx={grid["nx"]} ny={grid["ny"]} nz={grid["nz"]} ' +
          f'rho_min={float(np.min(rho)):.8e} rho_max={float(np.max(rho)):.8e} ' +
          f'temp_min={float(np.min(temp)):.8e} temp_max={float(np.max(temp)):.8e} ' +
          f'k_min={float(np.min(k)):.8e} k_max={float(np.max(k)):.8e} ' +
          f'epsilon_min={float(np.min(eps)):.8e} epsilon_max={float(np.max(eps)):.8e} ' +
          f'volfrac_min={float(np.min(vfrac)):.8e} volfrac_max={float(np.max(vfrac)):.8e} ' +
          f'c3h8_max={c3h8_max:.8e} species_sum_error={species_sum_error:.8e} ' +
          f'velocity_linf={velocity_linf:.8e}')


if __name__ == '__main__':
    main()
