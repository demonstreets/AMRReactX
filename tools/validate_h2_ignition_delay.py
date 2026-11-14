#!/usr/bin/env python3
import argparse
import os
import sys

import numpy as np


def load_history(path):
    if not os.path.exists(path):
        raise SystemExit(f'FAIL: missing temperature history {path}')
    arr = np.loadtxt(path)
    if arr.ndim != 2 or arr.shape[1] != 2 or arr.shape[0] < 10:
        raise SystemExit(f'FAIL: malformed temperature history {path}: shape={arr.shape}')
    if not np.all(np.isfinite(arr)):
        raise SystemExit(f'FAIL: non-finite values in {path}')
    times = arr[:, 0]
    temps = arr[:, 1]
    if not np.all(np.diff(times) > 0.0):
        raise SystemExit(f'FAIL: non-increasing time history in {path}')
    if np.min(temps) <= 0.0:
        raise SystemExit(f'FAIL: nonpositive temperature in {path}')
    return times, temps


def crossing_time(times, temps, rise):
    threshold = temps[0] + rise
    above = np.nonzero(temps >= threshold)[0]
    if len(above) == 0:
        raise SystemExit(
            f'FAIL: temperature never reaches T0+{rise:g}: T0={temps[0]:.8g} Tmax={np.max(temps):.8g}'
        )
    idx = int(above[0])
    if idx == 0:
        return float(times[0])
    t0, t1 = float(times[idx - 1]), float(times[idx])
    y0, y1 = float(temps[idx - 1]), float(temps[idx])
    if y1 == y0:
        return t1
    frac = (threshold - y0) / (y1 - y0)
    return t0 + frac * (t1 - t0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--case', action='append', nargs=2, metavar=('LABEL', 'HISTORY'), required=True)
    ap.add_argument('--threshold-rise', type=float, default=400.0)
    ap.add_argument('--expected-final-time', type=float, default=1.0e-2)
    ap.add_argument('--time-tolerance', type=float, default=1.0e-12)
    ap.add_argument('--min-final-temperature', type=float, default=2500.0)
    ap.add_argument('--max-final-temperature', type=float, default=3300.0)
    ap.add_argument('--max-mid-fine-rel-diff', type=float, default=0.025)
    ap.add_argument('--require-converging', action='store_true')
    args = ap.parse_args()

    if len(args.case) < 2:
        raise SystemExit('FAIL: need at least two ignition-delay cases')

    records = []
    for label, history in args.case:
        times, temps = load_history(history)
        if abs(float(times[-1]) - args.expected_final_time) > args.time_tolerance:
            raise SystemExit(f'FAIL: {label} final time {times[-1]} differs from expected {args.expected_final_time}')
        if not (args.min_final_temperature <= float(temps[-1]) <= args.max_final_temperature):
            raise SystemExit(f'FAIL: {label} final temperature {temps[-1]} outside expected bounds')
        tign = crossing_time(times, temps, args.threshold_rise)
        dt = float(np.min(np.diff(times)))
        records.append({
            'label': label,
            'history': history,
            'n': len(times) - 1,
            'dt': dt,
            'tign': tign,
            't0': float(temps[0]),
            'tfinal': float(temps[-1]),
            'tmax': float(np.max(temps)),
        })

    records.sort(key=lambda r: r['dt'], reverse=True)
    if args.require_converging and len(records) >= 3:
        d01 = abs(records[0]['tign'] - records[1]['tign'])
        d12 = abs(records[1]['tign'] - records[2]['tign'])
        if d12 > d01 + 1.0e-15:
            raise SystemExit(f'FAIL: ignition-delay estimate is not converging: coarse_mid={d01} mid_fine={d12}')
    mid = records[-2]
    fine = records[-1]
    rel = abs(mid['tign'] - fine['tign']) / max(abs(fine['tign']), 1.0e-300)
    if rel > args.max_mid_fine_rel_diff:
        raise SystemExit(f'FAIL: mid/fine ignition delay mismatch rel={rel}')

    detail = ' '.join(
        f'{r["label"]}:n={r["n"]}:dt={r["dt"]:.3e}:tign={r["tign"]:.8e}:Tfinal={r["tfinal"]:.4g}'
        for r in records
    )
    print('h2_ignition_delay_validation PASS ' +
          f'threshold_rise={args.threshold_rise:.8g} mid_fine_rel={rel:.8e} ' + detail)


if __name__ == '__main__':
    main()
