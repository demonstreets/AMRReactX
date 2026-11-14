#!/usr/bin/env python3
import argparse
import math
import os
import sys

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader

COMPARE_FIELDS = ['temp', 'Y(H2)', 'Y(O2)', 'Y(H2O)', 'I_R(H2)', 'I_R(O2)', 'I_R(H2O)', 'HeatRelease']


def require_field(fields, name):
    if name not in fields:
        raise SystemExit(f'FAIL: plotfile lacks required field {name}')
    arr = np.asarray(fields[name], dtype=float)
    if not np.all(np.isfinite(arr)):
        raise SystemExit(f'FAIL: non-finite values in {name}')
    return arr


def rel_linf(a, b):
    scale = max(float(np.max(np.abs(a))), float(np.max(np.abs(b))), 1.0)
    return float(np.max(np.abs(a - b)) / scale)


def abs_mean_diff(a, b):
    return float(abs(np.mean(a) - np.mean(b)))


def species_names(fields):
    names = sorted(name for name in fields if name.startswith('Y(') and name.endswith(')'))
    if not names:
        raise SystemExit('FAIL: plotfile has no mass-fraction Y(...) fields')
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sdc1-final', required=True)
    ap.add_argument('--sdc2-final', required=True)
    ap.add_argument('--expected-time', type=float, default=1.0e-7)
    ap.add_argument('--time-tolerance', type=float, default=1.0e-12)
    ap.add_argument('--max-temp-rel-linf', type=float, default=2.0e-3)
    ap.add_argument('--max-species-abs-mean', type=float, default=2.0e-9)
    ap.add_argument('--max-reaction-rel-linf', type=float, default=5.0e-2)
    ap.add_argument('--max-heat-release-rel-linf', type=float, default=5.0e-2)
    ap.add_argument('--min-h2o-mean', type=float, default=1.0e-10)
    args = ap.parse_args()

    p1 = amrex_reader.read_plotfile(args.sdc1_final)
    p2 = amrex_reader.read_plotfile(args.sdc2_final)
    f1 = p1['fields']
    f2 = p2['fields']

    for label, plot in [('sdc1', p1), ('sdc2', p2)]:
        if abs(plot['time'] - args.expected_time) > args.time_tolerance:
            raise SystemExit(f'FAIL: {label} final time {plot["time"]} differs from expected {args.expected_time}')
    if p1['grid']['nx'] != p2['grid']['nx'] or p1['grid']['ny'] != p2['grid']['ny']:
        raise SystemExit('FAIL: SDC comparison grids differ')
    if species_names(f1) != species_names(f2):
        raise SystemExit('FAIL: SDC comparison species lists differ')

    metrics = {}
    for name in COMPARE_FIELDS:
        a = require_field(f1, name)
        b = require_field(f2, name)
        metrics[name] = {
            'rel_linf': rel_linf(a, b),
            'abs_mean': abs_mean_diff(a, b),
            'mean1': float(np.mean(a)),
            'mean2': float(np.mean(b)),
            'max1': float(np.max(np.abs(a))),
            'max2': float(np.max(np.abs(b))),
        }

    if metrics['temp']['rel_linf'] > args.max_temp_rel_linf:
        raise SystemExit(f'FAIL: SDC1/SDC2 temperature relative Linf mismatch {metrics["temp"]["rel_linf"]}')
    for name in ['Y(H2)', 'Y(O2)', 'Y(H2O)']:
        if metrics[name]['abs_mean'] > args.max_species_abs_mean:
            raise SystemExit(f'FAIL: SDC1/SDC2 {name} mean mismatch {metrics[name]["abs_mean"]}')
    for name in ['I_R(H2)', 'I_R(O2)', 'I_R(H2O)']:
        if metrics[name]['rel_linf'] > args.max_reaction_rel_linf:
            raise SystemExit(f'FAIL: SDC1/SDC2 {name} relative Linf mismatch {metrics[name]["rel_linf"]}')
    if metrics['HeatRelease']['rel_linf'] > args.max_heat_release_rel_linf:
        raise SystemExit(f'FAIL: SDC1/SDC2 HeatRelease relative Linf mismatch {metrics["HeatRelease"]["rel_linf"]}')
    if min(metrics['Y(H2O)']['mean1'], metrics['Y(H2O)']['mean2']) <= args.min_h2o_mean:
        raise SystemExit('FAIL: SDC comparison did not produce enough H2O in both runs')

    print('h2_ignition_sdc_compare PASS ' +
          f'time={p1["time"]:.8g} nx={p1["grid"]["nx"]} ny={p1["grid"]["ny"]} ' +
          f'temp_rel_linf={metrics["temp"]["rel_linf"]:.8e} ' +
          f'h2_mean_abs={metrics["Y(H2)"]["abs_mean"]:.8e} ' +
          f'o2_mean_abs={metrics["Y(O2)"]["abs_mean"]:.8e} ' +
          f'h2o_mean_abs={metrics["Y(H2O)"]["abs_mean"]:.8e} ' +
          f'h2o_mean_sdc1={metrics["Y(H2O)"]["mean1"]:.8e} ' +
          f'h2o_mean_sdc2={metrics["Y(H2O)"]["mean2"]:.8e} ' +
          f'ir_h2_rel_linf={metrics["I_R(H2)"]["rel_linf"]:.8e} ' +
          f'ir_o2_rel_linf={metrics["I_R(O2)"]["rel_linf"]:.8e} ' +
          f'ir_h2o_rel_linf={metrics["I_R(H2O)"]["rel_linf"]:.8e} ' +
          f'heat_rel_linf={metrics["HeatRelease"]["rel_linf"]:.8e}')


if __name__ == '__main__':
    main()
