#!/usr/bin/env python3
import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import amrex_reader


def expected_states(mach, gamma, rho_pre, p_pre):
    a_pre = math.sqrt(gamma * p_pre / rho_pre)
    m2 = mach * mach
    rho_ratio = (gamma + 1.0) * m2 / ((gamma - 1.0) * m2 + 2.0)
    p_ratio = 1.0 + 2.0 * gamma / (gamma + 1.0) * (m2 - 1.0)
    vn_post = a_pre * 2.0 * (m2 - 1.0) / ((gamma + 1.0) * mach)
    shock_nx = math.cos(math.pi / 6.0)
    shock_ny = -math.sin(math.pi / 6.0)
    shock_speed_x = mach * a_pre / shock_nx
    return {
        'rho_pre': rho_pre,
        'p_pre': p_pre,
        'rho_post': rho_pre * rho_ratio,
        'p_post': p_pre * p_ratio,
        'u_post': vn_post * shock_nx,
        'v_post': vn_post * shock_ny,
        'shock_speed_x': shock_speed_x,
        'shock_tan': math.tan(math.pi / 3.0),
    }


def as_2d(arr):
    arr = np.asarray(arr)
    if arr.ndim == 3:
        return arr.mean(axis=2)
    if arr.ndim == 2:
        return arr
    raise SystemExit(f'FAIL: unsupported field rank {arr.ndim}')


def weighted_front_x(mask, x):
    cols = np.where(mask.any(axis=1))[0]
    if cols.size == 0:
        return None
    return float(x[cols.max()])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plotfile', required=True)
    ap.add_argument('--mach', type=float, default=10.0)
    ap.add_argument('--gamma', type=float, default=1.4)
    ap.add_argument('--rho-pre', type=float, default=1.4)
    ap.add_argument('--p-pre', type=float, default=1.0)
    ap.add_argument('--shock-x0', type=float, default=0.16666667)
    ap.add_argument('--min-time', type=float, default=1.0e-5)
    ap.add_argument('--state-rtol', type=float, default=0.12)
    ap.add_argument('--min-front-advance-frac', type=float, default=0.35)
    args = ap.parse_args()

    pf = amrex_reader.read_plotfile(args.plotfile)
    fields = pf['fields']
    for name in ('density', 'pressure', 'x_velocity', 'y_velocity'):
        if name not in fields:
            raise SystemExit(f'FAIL: missing plotfile field {name}')

    rho = as_2d(fields['density'])
    p = as_2d(fields['pressure'])
    u = as_2d(fields['x_velocity'])
    v = as_2d(fields['y_velocity'])
    t = float(pf['time'])
    x = np.asarray(pf['x'])
    y = np.asarray(pf['y'])

    for name, arr in (('density', rho), ('pressure', p), ('x_velocity', u), ('y_velocity', v)):
        if not np.isfinite(arr).all():
            raise SystemExit(f'FAIL: non-finite {name}')
    if rho.min() <= 0.0 or p.min() <= 0.0:
        raise SystemExit(f'FAIL: nonphysical state rho_min={rho.min():.6g} p_min={p.min():.6g}')
    if t < args.min_time:
        raise SystemExit(f'FAIL: plotfile time too small time={t:.12g}')

    exp = expected_states(args.mach, args.gamma, args.rho_pre, args.p_pre)
    xx, yy = np.meshgrid(x, y, indexing='ij')
    initial_line = args.shock_x0 + yy / exp['shock_tan']
    expected_line = initial_line + exp['shock_speed_x'] * t

    low_band = yy < 0.20
    high_band = yy > 0.80
    post_mask = low_band & (xx < args.shock_x0 - 0.03)
    pre_mask = high_band & (xx > expected_line + 0.10)
    if post_mask.sum() < 3 or pre_mask.sum() < 3:
        raise SystemExit('FAIL: insufficient plateau samples for Double Mach validation')

    rho_post = float(np.mean(rho[post_mask]))
    p_post = float(np.mean(p[post_mask]))
    u_post = float(np.mean(u[post_mask]))
    v_post = float(np.mean(v[post_mask]))
    rho_pre = float(np.mean(rho[pre_mask]))
    p_pre = float(np.mean(p[pre_mask]))

    checks = [
        ('rho_post', rho_post, exp['rho_post']),
        ('p_post', p_post, exp['p_post']),
        ('u_post', u_post, exp['u_post']),
        ('v_post', v_post, exp['v_post']),
        ('rho_pre', rho_pre, exp['rho_pre']),
        ('p_pre', p_pre, exp['p_pre']),
    ]
    bad = []
    for name, val, ref in checks:
        scale = max(abs(ref), 1.0)
        if abs(val - ref) / scale > args.state_rtol:
            bad.append(f'{name}={val:.6g} ref={ref:.6g}')
    if bad:
        raise SystemExit('FAIL: plateau state mismatch ' + '; '.join(bad))

    shock_rho_threshold = 0.5 * (exp['rho_pre'] + exp['rho_post'])
    observed_front = weighted_front_x(rho > shock_rho_threshold, x)
    if observed_front is None:
        raise SystemExit('FAIL: no high-density shock region detected')
    initial_front = float(np.max(initial_line[low_band]))
    min_advance = args.min_front_advance_frac * exp['shock_speed_x'] * t
    if observed_front < initial_front + min_advance:
        raise SystemExit(
            f'FAIL: shock front did not advance enough observed={observed_front:.6g} '
            f'initial={initial_front:.6g} min_advance={min_advance:.6g} time={t:.6g}')

    print(
        'double_mach_plotfile_validation PASS '
        f'time={t:.12g} grid={rho.shape[0]}x{rho.shape[1]} '
        f'rho_range={rho.min():.6g}:{rho.max():.6g} '
        f'p_range={p.min():.6g}:{p.max():.6g} '
        f'post=rho:{rho_post:.6g},p:{p_post:.6g},u:{u_post:.6g},v:{v_post:.6g} '
        f'pre=rho:{rho_pre:.6g},p:{p_pre:.6g} '
        f'front_x={observed_front:.6g} min_expected_front={initial_front + min_advance:.6g}')


if __name__ == '__main__':
    main()
