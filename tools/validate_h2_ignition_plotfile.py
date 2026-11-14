#!/usr/bin/env python3
import argparse
import math
import os
import sys

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader


REACTION_FIELDS = ['I_R(H2)', 'I_R(O2)', 'I_R(H2O)', 'HeatRelease']


def require_field(fields, name):
    if name not in fields:
        raise SystemExit(f'FAIL: plotfile lacks required field {name}')
    arr = np.asarray(fields[name], dtype=float)
    if not np.all(np.isfinite(arr)):
        raise SystemExit(f'FAIL: non-finite values in {name}')
    return arr


def species_names(fields):
    names = sorted(name for name in fields if name.startswith('Y(') and name.endswith(')'))
    if not names:
        raise SystemExit('FAIL: plotfile has no mass-fraction Y(...) fields')
    return names


def species_sum(fields, names):
    total = None
    for name in names:
        arr = require_field(fields, name)
        total = arr.copy() if total is None else total + arr
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--initial', required=True)
    ap.add_argument('--final', required=True)
    ap.add_argument('--min-h2-consumption', type=float, default=1.0e-9)
    ap.add_argument('--min-o2-consumption', type=float, default=1.0e-8)
    ap.add_argument('--min-h2o-production', type=float, default=1.0e-10)
    ap.add_argument('--min-reaction-rate', type=float, default=1.0e-4)
    ap.add_argument('--max-species-sum-error', type=float, default=2.0e-10)
    ap.add_argument('--max-temperature-drop', type=float, default=10.0)
    args = ap.parse_args()

    p0 = amrex_reader.read_plotfile(args.initial)
    p1 = amrex_reader.read_plotfile(args.final)
    f0 = p0['fields']
    f1 = p1['fields']

    if p1['time'] <= p0['time']:
        raise SystemExit(f'FAIL: final time {p1["time"]} is not after initial time {p0["time"]}')
    if p0['grid']['nx'] != p1['grid']['nx'] or p0['grid']['ny'] != p1['grid']['ny']:
        raise SystemExit('FAIL: initial/final grids do not match')

    temp0 = require_field(f0, 'temp')
    temp1 = require_field(f1, 'temp')
    if float(np.min(temp1)) <= 0.0:
        raise SystemExit('FAIL: final temperature is nonpositive')
    temp_drop = float(np.max(temp0 - temp1))
    if temp_drop > args.max_temperature_drop:
        raise SystemExit(f'FAIL: temperature drop too large for short smoke: {temp_drop}')

    y_names0 = species_names(f0)
    y_names1 = species_names(f1)
    if y_names0 != y_names1:
        raise SystemExit(f'FAIL: initial/final species fields differ: {y_names0} vs {y_names1}')
    y0_sum = species_sum(f0, y_names0)
    y1_sum = species_sum(f1, y_names1)
    sum_err0 = float(np.max(np.abs(y0_sum - 1.0)))
    sum_err1 = float(np.max(np.abs(y1_sum - 1.0)))
    if max(sum_err0, sum_err1) > args.max_species_sum_error:
        raise SystemExit(f'FAIL: species mass fractions do not sum to one: initial={sum_err0} final={sum_err1}')

    yh2_0 = require_field(f0, 'Y(H2)')
    yh2_1 = require_field(f1, 'Y(H2)')
    yo2_0 = require_field(f0, 'Y(O2)')
    yo2_1 = require_field(f1, 'Y(O2)')
    yh2o_0 = require_field(f0, 'Y(H2O)')
    yh2o_1 = require_field(f1, 'Y(H2O)')

    h2_consumed = float(np.mean(yh2_0 - yh2_1))
    o2_consumed = float(np.mean(yo2_0 - yo2_1))
    h2o_produced = float(np.mean(yh2o_1 - yh2o_0))
    if h2_consumed <= args.min_h2_consumption:
        raise SystemExit(f'FAIL: H2 consumption too small: {h2_consumed}')
    if o2_consumed <= args.min_o2_consumption:
        raise SystemExit(f'FAIL: O2 consumption too small: {o2_consumed}')
    if h2o_produced <= args.min_h2o_production:
        raise SystemExit(f'FAIL: H2O production too small: {h2o_produced}')

    max_rate = 0.0
    for name in REACTION_FIELDS:
        arr = require_field(f1, name)
        max_rate = max(max_rate, float(np.max(np.abs(arr))))
    if max_rate <= args.min_reaction_rate:
        raise SystemExit(f'FAIL: reaction-rate fields are too small: {max_rate}')

    max_h2o = float(np.max(yh2o_1))
    temp_mean_change = float(np.mean(temp1 - temp0))
    print('h2_ignition_plotfile_validation PASS ' +
          f'time0={p0["time"]:.8g} time1={p1["time"]:.8g} ' +
          f'h2_consumed_mean={h2_consumed:.8e} o2_consumed_mean={o2_consumed:.8e} ' +
          f'h2o_produced_mean={h2o_produced:.8e} max_h2o={max_h2o:.8e} ' +
          f'temp_mean_change={temp_mean_change:.8e} temp_drop_max={temp_drop:.8e} ' +
          f'species_sum_err={max(sum_err0, sum_err1):.8e} nspecies={len(y_names0)} max_reaction_rate={max_rate:.8e}')


if __name__ == '__main__':
    main()
