#!/usr/bin/env python3
import argparse
import os
import re
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


def step_number(path):
    match = re.search(r'plt(\d+)$', os.path.basename(path.rstrip('/')))
    if not match:
        return -1
    return int(match.group(1))


def discover_plotfiles(run_dir):
    entries = []
    for name in os.listdir(run_dir):
        path = os.path.join(run_dir, name)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, 'Header')) and re.match(r'plt\d+$', name):
            entries.append(path)
    return sorted(entries, key=step_number)


def cell_center(data, i, j):
    return float(data['x'][i]), float(data['y'][j])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-dir', required=True)
    ap.add_argument('--min-plotfiles', type=int, default=11)
    ap.add_argument('--expected-final-time', type=float, default=1.0e-7)
    ap.add_argument('--time-tolerance', type=float, default=1.0e-12)
    ap.add_argument('--min-h2-consumption', type=float, default=1.0e-9)
    ap.add_argument('--min-o2-consumption', type=float, default=1.0e-8)
    ap.add_argument('--min-h2o-production', type=float, default=1.0e-10)
    ap.add_argument('--min-active-reaction-slices', type=int, default=8)
    ap.add_argument('--min-reaction-rate', type=float, default=1.0e-4)
    ap.add_argument('--max-species-sum-error', type=float, default=2.0e-10)
    ap.add_argument('--max-mean-trend-reversal', type=float, default=5.0e-12)
    ap.add_argument('--max-hotspot-radius', type=float, default=2.0e-3)
    ap.add_argument('--min-peak-temperature', type=float, default=1900.0)
    args = ap.parse_args()

    plotfiles = discover_plotfiles(args.run_dir)
    if len(plotfiles) < args.min_plotfiles:
        raise SystemExit(f'FAIL: expected at least {args.min_plotfiles} plotfiles, found {len(plotfiles)}')

    times = []
    h2_mean = []
    o2_mean = []
    h2o_mean = []
    temp_max = []
    temp_mean = []
    reaction_max = []
    species_err = []
    hotspot_radius = []
    base_grid = None
    base_species = None

    for path in plotfiles:
        data = amrex_reader.read_plotfile(path)
        fields = data['fields']
        grid = (data['grid']['nx'], data['grid']['ny'])
        if base_grid is None:
            base_grid = grid
        elif grid != base_grid:
            raise SystemExit(f'FAIL: plotfile grid changed from {base_grid} to {grid} at {path}')

        names = species_names(fields)
        if base_species is None:
            base_species = names
        elif names != base_species:
            raise SystemExit(f'FAIL: species field list changed at {path}')

        total = species_sum(fields, names)
        species_err.append(float(np.max(np.abs(total - 1.0))))

        temp = require_field(fields, 'temp')
        if float(np.min(temp)) <= 0.0:
            raise SystemExit(f'FAIL: nonpositive temperature at {path}')
        peak_index = np.unravel_index(np.argmax(temp), temp.shape)
        x, y = cell_center(data, peak_index[0], peak_index[1])
        hotspot_radius.append(float((x * x + y * y) ** 0.5))
        temp_max.append(float(np.max(temp)))
        temp_mean.append(float(np.mean(temp)))

        h2_mean.append(float(np.mean(require_field(fields, 'Y(H2)'))))
        o2_mean.append(float(np.mean(require_field(fields, 'Y(O2)'))))
        h2o_mean.append(float(np.mean(require_field(fields, 'Y(H2O)'))))

        local_max = 0.0
        for name in REACTION_FIELDS:
            local_max = max(local_max, float(np.max(np.abs(require_field(fields, name)))))
        reaction_max.append(local_max)
        times.append(float(data['time']))

    if max(species_err) > args.max_species_sum_error:
        raise SystemExit(f'FAIL: species mass fractions do not sum to one: max_err={max(species_err)}')
    if max(hotspot_radius) > args.max_hotspot_radius:
        raise SystemExit(f'FAIL: hot spot drifted too far from bubble center: max_radius={max(hotspot_radius)}')
    if max(temp_max) < args.min_peak_temperature:
        raise SystemExit(f'FAIL: hot-bubble peak temperature too low: max_temp={max(temp_max)}')

    dt = np.diff(np.asarray(times))
    if not np.all(dt > 0.0):
        raise SystemExit(f'FAIL: plotfile times are not strictly increasing: {times}')
    if abs(times[-1] - args.expected_final_time) > args.time_tolerance:
        raise SystemExit(f'FAIL: final time {times[-1]} differs from expected {args.expected_final_time}')

    h2_consumed = h2_mean[0] - h2_mean[-1]
    o2_consumed = o2_mean[0] - o2_mean[-1]
    h2o_produced = h2o_mean[-1] - h2o_mean[0]
    if h2_consumed <= args.min_h2_consumption:
        raise SystemExit(f'FAIL: H2 consumption too small: {h2_consumed}')
    if o2_consumed <= args.min_o2_consumption:
        raise SystemExit(f'FAIL: O2 consumption too small: {o2_consumed}')
    if h2o_produced <= args.min_h2o_production:
        raise SystemExit(f'FAIL: H2O production too small: {h2o_produced}')

    h2_reversal = float(np.max(np.diff(h2_mean)))
    o2_reversal = float(np.max(np.diff(o2_mean)))
    h2o_reversal = float(np.max(-np.diff(h2o_mean)))
    if h2_reversal > args.max_mean_trend_reversal:
        raise SystemExit(f'FAIL: mean H2 increased during history: max_reversal={h2_reversal}')
    if o2_reversal > args.max_mean_trend_reversal:
        raise SystemExit(f'FAIL: mean O2 increased during history: max_reversal={o2_reversal}')
    if h2o_reversal > args.max_mean_trend_reversal:
        raise SystemExit(f'FAIL: mean H2O decreased during history: max_reversal={h2o_reversal}')

    active_slices = sum(1 for value in reaction_max if value > args.min_reaction_rate)
    if active_slices < args.min_active_reaction_slices:
        raise SystemExit(f'FAIL: reaction fields active in only {active_slices} plotfiles')

    print('h2_ignition_history_validation PASS ' +
          f'nplot={len(plotfiles)} time0={times[0]:.8g} timeN={times[-1]:.8g} ' +
          f'dt_min={float(np.min(dt)):.8e} dt_max={float(np.max(dt)):.8e} ' +
          f'h2_consumed_mean={h2_consumed:.8e} o2_consumed_mean={o2_consumed:.8e} ' +
          f'h2o_produced_mean={h2o_produced:.8e} temp_peak_min={min(temp_max):.8e} ' +
          f'temp_peak_max={max(temp_max):.8e} temp_mean_change={temp_mean[-1] - temp_mean[0]:.8e} ' +
          f'max_hotspot_radius={max(hotspot_radius):.8e} species_sum_err={max(species_err):.8e} ' +
          f'active_reaction_slices={active_slices} max_reaction_rate={max(reaction_max):.8e}')


if __name__ == '__main__':
    main()
