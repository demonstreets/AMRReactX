#!/usr/bin/env python3
import argparse
import glob
import math
import os


def read_particle(path):
    lines = [ln.strip() for ln in open(path, encoding='utf-8') if ln.strip()]
    vals = lines[-1].split()
    if len(vals) < 12:
        raise SystemExit(f'FAIL: bad particle line in {path}')
    temp = float(vals[4])
    mass_fraction = float(vals[11])
    if not (temp > 0.0 and 0.0 < mass_fraction <= 1.000001):
        raise SystemExit(f'FAIL: invalid T/Y in {path}: {temp} {mass_fraction}')
    return temp, mass_fraction


def linfit(xs, ys):
    n = len(xs)
    sx = sum(xs); sy = sum(ys)
    sxx = sum(x*x for x in xs); sxy = sum(x*y for x, y in zip(xs, ys))
    den = n * sxx - sx * sx
    if den == 0.0:
        raise SystemExit('FAIL: degenerate fit')
    slope = (n * sxy - sx * sy) / den
    intercept = (sy - slope * sx) / n
    mean = sy / n
    ss_tot = sum((y - mean) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 if ss_tot == 0.0 else 1.0 - ss_res / ss_tot
    return slope, intercept, r2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-dir', required=True)
    ap.add_argument('--expected-step', type=int, required=True)
    ap.add_argument('--min-snapshots', type=int, default=6)
    ap.add_argument('--min-r2', type=float, default=0.999)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.run_dir, 'spray*.p3d')))
    if len(files) < args.min_snapshots:
        raise SystemExit(f'FAIL: only {len(files)} spray snapshots')
    final_name = os.path.basename(files[-1])
    expected = f'spray{args.expected_step:05d}.p3d'
    if final_name != expected:
        raise SystemExit(f'FAIL: final snapshot {final_name} != {expected}')

    temps = []
    yvals = []
    steps = []
    for path in files:
        step = int(os.path.basename(path)[5:10])
        temp, y = read_particle(path)
        steps.append(float(step))
        temps.append(temp)
        yvals.append(y)
    d2 = [y ** (2.0 / 3.0) for y in yvals]
    slope, intercept, r2 = linfit(steps, d2)
    if not (slope < 0.0):
        raise SystemExit(f'FAIL: nonnegative D2 slope {slope}')
    if r2 < args.min_r2:
        raise SystemExit(f'FAIL: D2 fit R2 {r2} < {args.min_r2}')
    if not (temps[-1] > temps[0] and yvals[-1] < yvals[0] and d2[-1] < d2[0]):
        raise SystemExit('FAIL: expected heating/evaporation/D2 decrease')

    print('d2_fresh_history_validation PASS ' +
          f'snapshots={len(files)} first_step={int(steps[0])} final_step={int(steps[-1])} ' +
          f'slope={slope:.16e} intercept={intercept:.16e} r2={r2:.12f} ' +
          f'T={temps[0]:.12g}->{temps[-1]:.12g} Y={yvals[0]:.12g}->{yvals[-1]:.12g} ' +
          f'D2={d2[0]:.12g}->{d2[-1]:.12g}')


if __name__ == '__main__':
    main()
