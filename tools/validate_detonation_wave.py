#!/usr/bin/env python3
import argparse
import os
import sys

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader
from cfd_evidence_checks import pressure_front_x, reacting_pair_metrics


REQUIRED_FIELDS = ['density', 'Temp', 'pressure', 'rho_H2', 'rho_O2', 'rho_H2O', 'rho_N2']


def require_field(fields, name):
    if name not in fields:
        raise SystemExit(f'FAIL: plotfile lacks required field {name}')
    arr = np.asarray(fields[name], dtype=float)
    if not np.all(np.isfinite(arr)):
        raise SystemExit(f'FAIL: non-finite values in {name}')
    return arr


def argmax_x(arr, x):
    idx = np.unravel_index(int(np.argmax(arr)), arr.shape)[0]
    return float(x[idx])


def mean_abs_delta(a, b):
    return float(np.mean(np.abs(np.asarray(b) - np.asarray(a))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--initial', required=True)
    ap.add_argument('--final', required=True)
    ap.add_argument('--min-front-shift', type=float, default=0.20)
    ap.add_argument('--min-temp-rise', type=float, default=5.0)
    ap.add_argument('--min-temp-l1-change', type=float, default=0.5)
    ap.add_argument('--min-pressure-l1-change', type=float, default=10.0)
    ap.add_argument('--min-front-speed', type=float, default=1.0e5)
    ap.add_argument('--max-front-speed', type=float, default=1.0e6)
    ap.add_argument('--max-species-closure-rel', type=float, default=1.0e-10)
    ap.add_argument('--min-h2o-l1-change', type=float, default=1.0e-8)
    args = ap.parse_args()

    p0 = amrex_reader.read_plotfile(args.initial)
    p1 = amrex_reader.read_plotfile(args.final)
    if p1['time'] <= p0['time']:
        raise SystemExit(f'FAIL: final time {p1["time"]} is not after initial time {p0["time"]}')
    if p0['grid']['nx'] != p1['grid']['nx'] or p0['grid']['ny'] != p1['grid']['ny']:
        raise SystemExit('FAIL: initial/final grids do not match')

    f0, f1 = p0['fields'], p1['fields']
    for name in REQUIRED_FIELDS:
        require_field(f0, name)
        require_field(f1, name)

    rho1 = require_field(f1, 'density')
    temp0 = require_field(f0, 'Temp')
    temp1 = require_field(f1, 'Temp')
    p_init = require_field(f0, 'pressure')
    p_final = require_field(f1, 'pressure')

    if float(np.min(rho1)) <= 0.0:
        raise SystemExit('FAIL: final density is nonpositive')
    if float(np.min(temp1)) <= 0.0:
        raise SystemExit('FAIL: final temperature is nonpositive')
    if float(np.min(p_final)) <= 0.0:
        raise SystemExit('FAIL: final pressure is nonpositive')

    x = np.asarray(p1['x'], dtype=float)
    temp_front0 = pressure_front_x(require_field(f0, 'pressure'), x)
    temp_front1 = pressure_front_x(require_field(f1, 'pressure'), x)
    front_shift = temp_front1 - temp_front0
    if front_shift <= args.min_front_shift:
        raise SystemExit(f'FAIL: pressure front did not move right enough: {front_shift}')
    front_speed = front_shift / (p1['time'] - p0['time'])
    if front_speed < args.min_front_speed or front_speed > args.max_front_speed:
        raise SystemExit(
            f'FAIL: pressure front speed {front_speed} outside '
            f'[{args.min_front_speed}, {args.max_front_speed}]')

    temp_rise = float(np.max(temp1) - np.max(temp0))
    if temp_rise <= args.min_temp_rise:
        raise SystemExit(f'FAIL: temperature peak rise too small: {temp_rise}')

    temp_l1 = mean_abs_delta(temp0, temp1)
    pressure_l1 = mean_abs_delta(p_init, p_final)
    if temp_l1 <= args.min_temp_l1_change:
        raise SystemExit(f'FAIL: temperature field changed too little: {temp_l1}')
    if pressure_l1 <= args.min_pressure_l1_change:
        raise SystemExit(f'FAIL: pressure field changed too little: {pressure_l1}')

    species_names = [name for name in f1 if name.startswith('rho_') and name not in ('rho_E', 'rho_e')]
    if not all(name in species_names for name in REQUIRED_FIELDS if name.startswith('rho_')):
        raise SystemExit('FAIL: incomplete species data')
    final_species = [require_field(f1, name) for name in species_names]
    min_species = min(float(np.min(arr)) for arr in final_species)
    min_y = min(float(np.min(arr/rho1)) for arr in final_species)
    if min_y < -1.0e-12:
        raise SystemExit(f'FAIL: final species mass fraction is negative: {min_y}')

    species_sum = np.sum(final_species, axis=0)
    species_closure_rel = float(
        np.max(np.abs(species_sum - rho1) / np.maximum(np.abs(rho1), 1.0e-300)))
    if species_closure_rel > args.max_species_closure_rel:
        raise SystemExit(
            f'FAIL: species density closure relative error too large: {species_closure_rel}')

    h2o_l1 = mean_abs_delta(require_field(f0, 'rho_H2O'), require_field(f1, 'rho_H2O'))
    if h2o_l1 <= args.min_h2o_l1_change:
        raise SystemExit(f'FAIL: H2O field changed too little: {h2o_l1}')

    dx = p1['dx'][:p1['ndim']]
    cell_volume = float(np.prod(dx))
    h2_mass0 = float(np.sum(require_field(f0, 'rho_H2')) * cell_volume)
    h2_mass1 = float(np.sum(require_field(f1, 'rho_H2')) * cell_volume)
    h2o_mass0 = float(np.sum(require_field(f0, 'rho_H2O')) * cell_volume)
    h2o_mass1 = float(np.sum(require_field(f1, 'rho_H2O')) * cell_volume)
    total_mass0 = float(np.sum(require_field(f0, 'density')) * cell_volume)
    total_mass1 = float(np.sum(rho1) * cell_volume)
    mass_rel = abs(total_mass1 - total_mass0) / max(total_mass0, 1.0e-300)
    if mass_rel > 1.0e-12:
        raise SystemExit(f'FAIL: total mass changed unexpectedly: {mass_rel}')

    reacting_pair_metrics(args.initial, args.final)

    print('detonation_wave_validation PASS ' +
          'scope=reacting_wave_smoke self_sustained_detonation_verified=0 ' +
          f'time0={p0["time"]:.8g} time1={p1["time"]:.8g} ' +
          f'pressure_front0={temp_front0:.8g} pressure_front1={temp_front1:.8g} ' +
          f'front_shift={front_shift:.8g} front_speed={front_speed:.8e} ' +
          f'temp_max0={float(np.max(temp0)):.8g} ' +
          f'temp_max1={float(np.max(temp1)):.8g} temp_l1={temp_l1:.8e} ' +
          f'pressure_l1={pressure_l1:.8e} h2o_l1={h2o_l1:.8e} ' +
          f'species_min={min_species:.8e} species_closure_rel={species_closure_rel:.8e} ' +
          f'mass_rel={mass_rel:.8e} ' +
          f'h2_mass0={h2_mass0:.8e} h2_mass1={h2_mass1:.8e} ' +
          f'h2o_mass0={h2o_mass0:.8e} h2o_mass1={h2o_mass1:.8e}')


if __name__ == '__main__':
    main()
