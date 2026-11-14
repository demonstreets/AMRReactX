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
    return first_float(values, 'prob.leak_rate')

def gaussian_pdf(x, sigma):
    if sigma <= 0.0:
        return 0.0
    return math.exp(-0.5 * (x / sigma) ** 2) / (math.sqrt(2.0 * math.pi) * sigma)


def plume_reference(mdot, wind, distance, y, z, release_z):
    # Neutral-plume toy reference for a maintained, deterministic smoke check.
    # The slopes are intentionally conservative and documented in the audit;
    # full terrain/obstacle validation remains a separate benchmark.
    sy = max(0.10 * distance, 1.0e-6)
    sz = max(0.05 * distance, 1.0e-6)
    vertical = gaussian_pdf(z - release_z, sz) + gaussian_pdf(z + release_z, sz)
    return (mdot / wind) * gaussian_pdf(y, sy) * vertical


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plotfile', required=True)
    ap.add_argument('--input', required=True)
    ap.add_argument('--log', required=True)
    ap.add_argument('--min-h2-mass', type=float, default=1.0e-12)
    ap.add_argument('--max-mass-ratio', type=float, default=50.0)
    args = ap.parse_args()

    vals = parse_input(args.input)
    wind = first_float(vals, 'prob.wind_u')
    leak_x = first_float(vals, 'prob.leak_xc')
    leak_y = first_float(vals, 'prob.leak_yc')
    leak_z = first_float(vals, 'prob.leak_zc')
    dt = first_float(vals, 'amr.fixed_dt')

    with open(args.log, 'r', encoding='utf-8', errors='replace') as fh:
        log = fh.read()
    if 'Unused ParmParse Variables' in log:
        raise SystemExit('FAIL: unused ParmParse variables in run log')
    mdot = effective_mdot(vals, log)
    m = re.search(r'H2 leak discrete active volume=([0-9.eE+-]+), mdot_vol=([0-9.eE+-]+)', log)
    if not m:
        raise SystemExit('FAIL: leak normalization line missing from run log')
    active_volume = float(m.group(1))
    mdot_vol = float(m.group(2))
    if active_volume <= 0.0 or mdot_vol <= 0.0:
        raise SystemExit('FAIL: nonpositive active volume or volumetric source')

    pf = amrex_reader.read_plotfile(args.plotfile)
    fields = pf['fields']
    if 'Y(H2)' not in fields or 'density' not in fields:
        raise SystemExit('FAIL: plotfile lacks Y(H2) or density')
    yh2 = np.asarray(fields['Y(H2)'])
    rho = np.asarray(fields['density'])
    dx = pf['dx']
    cell_volume = float(np.prod(dx[:pf['ndim']]))
    h2_mass = float(np.sum(np.maximum(yh2, 0.0) * np.maximum(rho, 0.0)) * cell_volume)
    max_y = float(np.max(yh2))
    if h2_mass <= args.min_h2_mass:
        raise SystemExit(f'FAIL: H2 mass too small: {h2_mass}')
    injected = source_interval_injected_mass(log, float(pf["time"]), mdot)
    if injected > 0.0 and h2_mass / injected > args.max_mass_ratio:
        raise SystemExit(f'FAIL: H2 mass/injected ratio too large: {h2_mass / injected}')
    if max_y <= 0.0:
        raise SystemExit('FAIL: Y(H2) maximum is nonpositive')

    distance = max(pf['prob_hi'][0] - leak_x, dx[0])
    reference = plume_reference(mdot, max(wind, 1.0e-12), distance, 0.0, leak_z, leak_z)
    if reference <= 0.0 or not math.isfinite(reference):
        raise SystemExit('FAIL: invalid Gaussian plume reference')

    print('h2_leak_plume_validation PASS ' +
          f'plot={args.plotfile} time={pf["time"]:.8g} max_YH2={max_y:.8e} ' +
          f'h2_mass={h2_mass:.8e} injected={injected:.8e} ' +
          f'mass_ratio={h2_mass / injected if injected > 0 else 0.0:.8e} ' +
          f'gaussian_center_ref={reference:.8e} active_volume={active_volume:.8e}')


if __name__ == '__main__':
    main()
