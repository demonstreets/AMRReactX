#!/usr/bin/env python3
import argparse
import os
import sys

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader

REQUIRED_FIELDS = [
    'density', 'Temp', 'pressure', 'rho_NC7H16', 'rho_O2', 'rho_N2',
    'spray_mass', 'spray_density', 'spray_num', 'spray_vol', 'spray_temp',
    'num_parcels', 'spray_x_vel', 'spray_y_vel'
]


def field(fields, name):
    if name not in fields:
        raise SystemExit(f'FAIL: plotfile lacks required field {name}')
    arr = np.asarray(fields[name], dtype=float)
    if not np.all(np.isfinite(arr)):
        raise SystemExit(f'FAIL: non-finite values in {name}')
    return arr


def require_min(name, value, threshold):
    if value <= threshold:
        raise SystemExit(f'FAIL: {name}={value} <= {threshold}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plotfile', required=True)
    ap.add_argument('--min-time', type=float, default=0.0)
    ap.add_argument('--min-total-spray-mass', type=float, default=1.0e-16)
    ap.add_argument('--min-total-parcels', type=float, default=0.5)
    ap.add_argument('--min-pressure-ratio', type=float, default=1.5)
    args = ap.parse_args()

    plot = amrex_reader.read_plotfile(args.plotfile)
    if plot['time'] <= args.min_time:
        raise SystemExit(f'FAIL: plot time {plot["time"]} <= {args.min_time}')

    fields = plot['fields']
    for name in REQUIRED_FIELDS:
        field(fields, name)

    rho = field(fields, 'density')
    temp = field(fields, 'Temp')
    pressure = field(fields, 'pressure')
    if float(np.min(rho)) <= 0.0:
        raise SystemExit('FAIL: nonpositive gas density')
    if float(np.min(temp)) <= 0.0:
        raise SystemExit('FAIL: nonpositive gas temperature')
    if float(np.min(pressure)) <= 0.0:
        raise SystemExit('FAIL: nonpositive gas pressure')

    for name in ['rho_NC7H16', 'rho_O2', 'rho_N2', 'spray_mass', 'spray_density',
                 'spray_num', 'spray_vol', 'num_parcels']:
        min_value = float(np.min(field(fields, name)))
        if min_value < -1.0e-14:
            raise SystemExit(f'FAIL: negative {name}: {min_value}')

    total_spray_mass = float(np.sum(field(fields, 'spray_mass')))
    total_parcels = float(np.sum(field(fields, 'num_parcels')))
    spray_temp = field(fields, 'spray_temp')
    active = field(fields, 'num_parcels') > 0.0
    if not np.any(active):
        raise SystemExit('FAIL: no active parcel cells in plotfile')
    active_spray_temp_min = float(np.min(spray_temp[active]))
    active_spray_temp_max = float(np.max(spray_temp[active]))
    require_min('total_spray_mass', total_spray_mass, args.min_total_spray_mass)
    require_min('total_parcels', total_parcels, args.min_total_parcels)
    if active_spray_temp_min <= 0.0:
        raise SystemExit('FAIL: active spray temperature is nonpositive')

    pressure_ratio = float(np.max(pressure) / max(np.min(pressure), 1.0e-300))
    require_min('pressure_ratio', pressure_ratio, args.min_pressure_ratio)

    print('shock_droplet_spray_validation PASS ' +
          f'time={plot["time"]:.8g} nx={plot["grid"]["nx"]} ny={plot["grid"]["ny"]} ' +
          f'rho_min={float(np.min(rho)):.8e} rho_max={float(np.max(rho)):.8e} ' +
          f'temp_min={float(np.min(temp)):.8e} temp_max={float(np.max(temp)):.8e} ' +
          f'pressure_ratio={pressure_ratio:.8e} total_spray_mass={total_spray_mass:.8e} ' +
          f'total_parcels={total_parcels:.8e} active_spray_temp_min={active_spray_temp_min:.8e} ' +
          f'active_spray_temp_max={active_spray_temp_max:.8e}')


if __name__ == '__main__':
    main()
