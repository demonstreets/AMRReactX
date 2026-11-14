#!/usr/bin/env python3
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import amrex_reader

GAMMA = 1.4


def sound_speed(rho, p):
    return np.sqrt(GAMMA * p / rho)


def pressure_function(p, rho_k, p_k):
    a_k = sound_speed(rho_k, p_k)
    if p > p_k:
        A = 2.0 / ((GAMMA + 1.0) * rho_k)
        B = (GAMMA - 1.0) / (GAMMA + 1.0) * p_k
        return (p - p_k) * np.sqrt(A / (p + B))
    return 2.0 * a_k / (GAMMA - 1.0) * ((p / p_k) ** ((GAMMA - 1.0) / (2.0 * GAMMA)) - 1.0)


def pressure_derivative(p, rho_k, p_k):
    a_k = sound_speed(rho_k, p_k)
    if p > p_k:
        A = 2.0 / ((GAMMA + 1.0) * rho_k)
        B = (GAMMA - 1.0) / (GAMMA + 1.0) * p_k
        root = np.sqrt(A / (p + B))
        return root * (1.0 - 0.5 * (p - p_k) / (p + B))
    return (1.0 / (rho_k * a_k)) * (p / p_k) ** (-(GAMMA + 1.0) / (2.0 * GAMMA))


def star_state(rho_l, p_l, rho_r, p_r):
    a_l = sound_speed(rho_l, p_l)
    a_r = sound_speed(rho_r, p_r)
    p = max(1.0e-14, 0.5 * (p_l + p_r) - 0.125 * (rho_l + rho_r) * (a_l + a_r) * 0.0)
    for _ in range(50):
        f = pressure_function(p, rho_l, p_l) + pressure_function(p, rho_r, p_r)
        df = pressure_derivative(p, rho_l, p_l) + pressure_derivative(p, rho_r, p_r)
        p_next = max(1.0e-14, p - f / df)
        if abs(p_next - p) <= 1.0e-13 * max(1.0, p_next):
            p = p_next
            break
        p = p_next
    u = 0.5 * (pressure_function(p, rho_r, p_r) - pressure_function(p, rho_l, p_l))
    return p, u


def sample_exact(x, t, x0, rho_l, p_l, rho_r, p_r):
    if t <= 0.0:
        rho = np.where(x < x0, rho_l, rho_r)
        p = np.where(x < x0, p_l, p_r)
        u = np.zeros_like(x)
        return rho, u, p
    p_star, u_star = star_state(rho_l, p_l, rho_r, p_r)
    xi = (x - x0) / t
    a_l = sound_speed(rho_l, p_l)
    a_r = sound_speed(rho_r, p_r)
    rho = np.empty_like(x)
    u = np.empty_like(x)
    p = np.empty_like(x)

    left_mask = xi <= u_star
    p_ratio_l = p_star / p_l
    a_star_l = a_l * p_ratio_l ** ((GAMMA - 1.0) / (2.0 * GAMMA))
    head = -a_l
    tail = u_star - a_star_l

    m = left_mask & (xi <= head)
    rho[m] = rho_l; u[m] = 0.0; p[m] = p_l
    m = left_mask & (xi > head) & (xi < tail)
    u[m] = 2.0 / (GAMMA + 1.0) * (a_l + xi[m])
    a = 2.0 / (GAMMA + 1.0) * (a_l - 0.5 * (GAMMA - 1.0) * xi[m])
    rho[m] = rho_l * (a / a_l) ** (2.0 / (GAMMA - 1.0))
    p[m] = p_l * (a / a_l) ** (2.0 * GAMMA / (GAMMA - 1.0))
    m = left_mask & (xi >= tail)
    rho[m] = rho_l * p_ratio_l ** (1.0 / GAMMA)
    u[m] = u_star; p[m] = p_star

    p_ratio_r = p_star / p_r
    rho_star_r = rho_r * ((p_ratio_r + (GAMMA - 1.0) / (GAMMA + 1.0)) / ((GAMMA - 1.0) / (GAMMA + 1.0) * p_ratio_r + 1.0))
    shock_speed = a_r * np.sqrt((GAMMA + 1.0) / (2.0 * GAMMA) * p_ratio_r + (GAMMA - 1.0) / (2.0 * GAMMA))
    m = (~left_mask) & (xi < shock_speed)
    rho[m] = rho_star_r; u[m] = u_star; p[m] = p_star
    m = (~left_mask) & (xi >= shock_speed)
    rho[m] = rho_r; u[m] = 0.0; p[m] = p_r
    return rho, u, p


def l1(actual, exact):
    return float(np.mean(np.abs(actual - exact)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plotfile', required=True)
    ap.add_argument('--x0', type=float, default=0.5)
    ap.add_argument('--rho-l', type=float)
    ap.add_argument('--rho-r', type=float)
    ap.add_argument('--p-l', type=float)
    ap.add_argument('--p-r', type=float)
    ap.add_argument('--plateau-cells', type=int, default=12)
    ap.add_argument('--max-rho-l1', type=float, default=0.08)
    ap.add_argument('--max-p-l1', type=float, default=0.08)
    ap.add_argument('--max-u-l1', type=float, default=0.08)
    args = ap.parse_args()

    pf = amrex_reader.read_plotfile(args.plotfile)
    fields = pf['fields']
    for name in ('density', 'x_velocity', 'pressure'):
        if name not in fields:
            raise SystemExit(f'FAIL: missing plotfile field {name}')
    rho = np.asarray(fields['density']).mean(axis=1)
    u = np.asarray(fields['x_velocity']).mean(axis=1)
    p = np.asarray(fields['pressure']).mean(axis=1)
    x = np.asarray(pf['x'])
    t = float(pf['time'])

    nedge = min(args.plateau_cells, max(2, rho.size // 8))
    rho_l = args.rho_l if args.rho_l is not None else float(np.mean(rho[:nedge]))
    rho_r = args.rho_r if args.rho_r is not None else float(np.mean(rho[-nedge:]))
    p_l = args.p_l if args.p_l is not None else float(np.mean(p[:nedge]))
    p_r = args.p_r if args.p_r is not None else float(np.mean(p[-nedge:]))
    rho_scale = rho_l
    p_scale = p_l
    u_scale = sound_speed(rho_l, p_l)
    rho_n = rho / rho_scale
    p_n = p / p_scale
    u_n = u / u_scale
    rho_e, u_e, p_e = sample_exact(x, t * u_scale, args.x0, rho_l / rho_scale, p_l / p_scale, rho_r / rho_scale, p_r / p_scale)

    rho_l1 = l1(rho_n, rho_e)
    p_l1 = l1(p_n, p_e)
    u_l1 = l1(u_n, u_e)
    if rho_l1 > args.max_rho_l1 or p_l1 > args.max_p_l1 or u_l1 > args.max_u_l1:
        raise SystemExit(f'FAIL: Sod L1 too large rho={rho_l1:.6g} p={p_l1:.6g} u={u_l1:.6g}')
    if not (rho_n.min() > 0.0 and p_n.min() > 0.0 and np.isfinite(u_n).all()):
        raise SystemExit('FAIL: nonphysical normalized Sod plotfile state')

    print('sod_plotfile_validation PASS ' +
          f'time={t:.12g} nx={rho.size} rho_l1={rho_l1:.6g} p_l1={p_l1:.6g} u_l1={u_l1:.6g} ' +
          f'rho_lr={rho_l:.6g}:{rho_r:.6g} p_lr={p_l:.6g}:{p_r:.6g} ' +
          f'rho_range={rho_n.min():.6g}:{rho_n.max():.6g} p_range={p_n.min():.6g}:{p_n.max():.6g} ' +
          f'u_range={u_n.min():.6g}:{u_n.max():.6g}')


if __name__ == '__main__':
    main()
