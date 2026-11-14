#!/usr/bin/env python3
"""Validate a short two-phase bubble-rise plotfile pair."""
from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import amrex_reader


def fail(message: str) -> None:
    raise SystemExit(f'academic_twophase_bubble_rise_validation FAIL {message}')


def field(data: dict, name: str) -> np.ndarray:
    fields = data.get('fields', {})
    if name not in fields:
        fail(f'missing field {name}')
    return np.asarray(fields[name], dtype=float)


def xy_mesh(data: dict) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(data.get('x', []), dtype=float)
    y = np.asarray(data.get('y', []), dtype=float)
    if x.size < 4 or y.size < 4:
        fail('plotfile grid is too small')
    return np.meshgrid(x, y, indexing='ij')


def cell_area(data: dict) -> float:
    x = np.asarray(data.get('x', []), dtype=float)
    y = np.asarray(data.get('y', []), dtype=float)
    if x.size < 2 or y.size < 2:
        fail('cannot compute cell area')
    return float(abs(x[1] - x[0]) * abs(y[1] - y[0]))


def metrics(plotfile: Path) -> dict[str, float | str]:
    data = amrex_reader.read_plotfile(str(plotfile))
    rho = field(data, 'density')
    adv = field(data, 'rho_adv_0')
    ymom = field(data, 'ymom')
    rho_e = field(data, 'rho_e')
    temp = field(data, 'Temp')
    xx, yy = xy_mesh(data)
    area = cell_area(data)
    for name, arr in (
        ('density', rho),
        ('rho_adv_0', adv),
        ('ymom', ymom),
        ('rho_e', rho_e),
        ('Temp', temp),
    ):
        if not np.isfinite(arr).all():
            fail(f'non-finite {name}')
    if float(rho.min()) <= 0.0 or float(rho_e.min()) <= 0.0:
        fail(f'nonphysical rho/rho_e minima rho={rho.min():.6g} rho_e={rho_e.min():.6g}')
    alpha = adv / np.maximum(rho, 1.0e-300)
    light = np.clip(1.0 - alpha, 0.0, 1.0)
    light_sum = float(light.sum())
    if light_sum <= 0.0:
        fail('no light phase detected')
    return {
        'plotfile': str(plotfile),
        'time': float(data.get('time', 0.0)),
        'nx': int(rho.shape[0]),
        'ny': int(rho.shape[1]),
        'rho_min': float(rho.min()),
        'rho_max': float(rho.max()),
        'rho_e_min': float(rho_e.min()),
        'rho_e_max': float(rho_e.max()),
        'temp_min': float(temp.min()),
        'temp_max': float(temp.max()),
        'alpha_min': float(alpha.min()),
        'alpha_max': float(alpha.max()),
        'total_mass': float(rho.sum() * area),
        'adv_mass': float(adv.sum() * area),
        'light_volume': float(light.sum() * area),
        'light_centroid_x': float((light * xx).sum() / light_sum),
        'light_centroid_y': float((light * yy).sum() / light_sum),
        'ymom_sum': float(ymom.sum() * area),
        'ymom_absmax': float(np.max(np.abs(ymom))),
    }


def rel_drift(final: float, initial: float) -> float:
    return abs(final - initial) / max(abs(initial), 1.0e-300)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--initial-plotfile', required=True)
    parser.add_argument('--final-plotfile', required=True)
    parser.add_argument('--min-final-time', type=float, default=1.0e-6)
    parser.add_argument('--min-centroid-rise', type=float, default=1.0e-5)
    parser.add_argument('--max-mass-rel-drift', type=float, default=1.0e-10)
    parser.add_argument('--max-adv-mass-rel-drift', type=float, default=1.0e-10)
    parser.add_argument('--alpha-tol', type=float, default=5.0e-2)
    parser.add_argument('--min-ymom-sum', type=float, default=0.0)
    args = parser.parse_args()

    initial = metrics(Path(args.initial_plotfile))
    final = metrics(Path(args.final_plotfile))
    if final['time'] < args.min_final_time:
        fail(f"final time too small: {final['time']:.12g}")
    if initial['nx'] != final['nx'] or initial['ny'] != final['ny']:
        fail('initial/final grid mismatch')
    if final['alpha_min'] < -args.alpha_tol or final['alpha_max'] > 1.0 + args.alpha_tol:
        fail(f"alpha out of bounds: {final['alpha_min']:.6g}:{final['alpha_max']:.6g}")
    mass_rel = rel_drift(final['total_mass'], initial['total_mass'])
    adv_rel = rel_drift(final['adv_mass'], initial['adv_mass'])
    if mass_rel > args.max_mass_rel_drift:
        fail(f'total mass drift too large: {mass_rel:.6g}')
    if adv_rel > args.max_adv_mass_rel_drift:
        fail(f'advected mass drift too large: {adv_rel:.6g}')
    centroid_rise = final['light_centroid_y'] - initial['light_centroid_y']
    if centroid_rise < args.min_centroid_rise:
        fail(f'light-phase centroid did not rise enough: {centroid_rise:.12g}')
    if final['ymom_sum'] < args.min_ymom_sum:
        fail(f"final integrated y momentum below threshold: {final['ymom_sum']:.12g} < {args.min_ymom_sum:.12g}")
    print(
        'academic_twophase_bubble_rise_validation PASS '
        f"time0={initial['time']:.12g} time1={final['time']:.12g} "
        f"grid={final['nx']}x{final['ny']} "
        f"rho_range={final['rho_min']:.8g}:{final['rho_max']:.8g} "
        f"alpha_range={final['alpha_min']:.8g}:{final['alpha_max']:.8g} "
        f"mass_rel_drift={mass_rel:.12g} adv_mass_rel_drift={adv_rel:.12g} "
        f"light_y0={initial['light_centroid_y']:.12g} "
        f"light_y1={final['light_centroid_y']:.12g} "
        f"centroid_rise={centroid_rise:.12g} "
        f"ymom_sum={final['ymom_sum']:.12g} ymom_absmax={final['ymom_absmax']:.12g}"
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
