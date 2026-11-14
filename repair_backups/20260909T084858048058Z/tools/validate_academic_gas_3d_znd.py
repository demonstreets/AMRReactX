#!/usr/bin/env python3
"""Validate a 3D ZND-style gas detonation plotfile pair."""
from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import amrex_reader

SPECIES = ['H2', 'O2', 'H2O', 'H', 'O', 'OH', 'HO2', 'H2O2', 'N2']


def fail(message: str) -> None:
    raise SystemExit(f'FAIL: {message}')


def require_field(fields: dict[str, object], name: str) -> np.ndarray:
    if name not in fields:
        fail(f'plotfile lacks required field {name}')
    arr = np.asarray(fields[name], dtype=float)
    if not np.all(np.isfinite(arr)):
        fail(f'non-finite values in {name}')
    return arr


def species_density(fields: dict[str, object], rho: np.ndarray, species: str) -> np.ndarray:
    rho_name = f'rho_{species}'
    y_name = f'Y({species})'
    if rho_name in fields:
        return require_field(fields, rho_name)
    if y_name in fields:
        return rho * require_field(fields, y_name)
    fail(f'plotfile lacks {rho_name} or {y_name}')


def species_fraction(fields: dict[str, object], rho: np.ndarray, species: str) -> np.ndarray:
    y_name = f'Y({species})'
    if y_name in fields:
        return require_field(fields, y_name)
    return species_density(fields, rho, species) / np.maximum(rho, 1.0e-300)


def mean_abs_delta(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(b) - np.asarray(a))))


def argmax_x(arr: np.ndarray, x: np.ndarray) -> float:
    idx = np.unravel_index(int(np.argmax(arr)), arr.shape)[0]
    return float(x[idx])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--initial', required=True)
    parser.add_argument('--final', required=True)
    parser.add_argument('--min-front-shift', type=float, default=0.01)
    parser.add_argument('--min-front-shift-cells', type=float, default=3.0)
    parser.add_argument('--min-temp-l1-change', type=float, default=1.0)
    parser.add_argument('--min-h2o-l1-change', type=float, default=1.0e-8)
    parser.add_argument('--min-front-speed', type=float, default=1.0e4)
    parser.add_argument('--max-front-speed', type=float, default=1.0e8)
    parser.add_argument('--max-mass-rel', type=float, default=5.0e-11)
    parser.add_argument('--max-species-closure-rel', type=float, default=1.0e-10)
    parser.add_argument('--allow-small-negative-y', type=float, default=1.0e-3)
    args = parser.parse_args()

    p0 = amrex_reader.read_plotfile(args.initial)
    p1 = amrex_reader.read_plotfile(args.final)
    if int(p0['ndim']) != 3 or int(p1['ndim']) != 3:
        fail(f'expected 3D plotfiles, got ndim={p0["ndim"]}/{p1["ndim"]}')
    if p1['time'] <= p0['time']:
        fail(f'final time {p1["time"]} is not after initial time {p0["time"]}')
    for axis in ['nx', 'ny', 'nz']:
        if p0['grid'][axis] != p1['grid'][axis]:
            fail(f'initial/final grids do not match on {axis}')

    f0, f1 = p0['fields'], p1['fields']
    rho0 = require_field(f0, 'density')
    rho1 = require_field(f1, 'density')
    temp0 = require_field(f0, 'Temp')
    temp1 = require_field(f1, 'Temp')
    if float(np.min(rho1)) <= 0.0:
        fail('final density is nonpositive')
    if float(np.min(temp1)) <= 0.0:
        fail('final temperature is nonpositive')

    x = np.asarray(p1['x'], dtype=float)
    temp_front0 = argmax_x(temp0, x)
    temp_front1 = argmax_x(temp1, x)
    front_shift = temp_front1 - temp_front0
    dx = float(p1['dx'][0])
    front_shift_cells = front_shift / dx
    if front_shift <= args.min_front_shift:
        fail(f'thermal front did not move right enough: {front_shift}')
    if front_shift_cells < args.min_front_shift_cells:
        fail(f'thermal front shift too small in cells: {front_shift_cells}')
    front_speed = front_shift / (float(p1['time']) - float(p0['time']))
    if not (args.min_front_speed <= front_speed <= args.max_front_speed):
        fail(f'thermal front speed {front_speed} outside [{args.min_front_speed}, {args.max_front_speed}]')

    temp_l1 = mean_abs_delta(temp0, temp1)
    if temp_l1 <= args.min_temp_l1_change:
        fail(f'temperature field changed too little: {temp_l1}')

    species0 = {name: species_density(f0, rho0, name) for name in SPECIES}
    species1 = {name: species_density(f1, rho1, name) for name in SPECIES}
    y_min = min(float(np.min(species_fraction(f1, rho1, name))) for name in SPECIES)
    if y_min < -abs(args.allow_small_negative_y):
        fail(f'final species mass fraction is too negative: {y_min}')
    y_sum = sum(species_fraction(f1, rho1, name) for name in SPECIES)
    species_closure_rel = float(np.max(np.abs(y_sum - 1.0)))
    if species_closure_rel > args.max_species_closure_rel:
        fail(f'species mass-fraction closure error too large: {species_closure_rel}')

    h2o_l1 = mean_abs_delta(species0['H2O'], species1['H2O'])
    if h2o_l1 <= args.min_h2o_l1_change:
        fail(f'H2O density field changed too little: {h2o_l1}')

    cell_volume = float(np.prod(p1['dx'][:p1['ndim']]))
    total_mass0 = float(np.sum(rho0) * cell_volume)
    total_mass1 = float(np.sum(rho1) * cell_volume)
    mass_rel = abs(total_mass1 - total_mass0) / max(abs(total_mass0), 1.0e-300)
    if mass_rel > args.max_mass_rel:
        fail(f'total mass changed unexpectedly: {mass_rel}')
    h2_mass0 = float(np.sum(species0['H2']) * cell_volume)
    h2_mass1 = float(np.sum(species1['H2']) * cell_volume)
    h2o_mass0 = float(np.sum(species0['H2O']) * cell_volume)
    h2o_mass1 = float(np.sum(species1['H2O']) * cell_volume)

    print(
        'academic_gas_3d_znd_validation PASS '
        f'time0={p0["time"]:.8g} time1={p1["time"]:.8g} '
        f'grid_nx={p1["grid"]["nx"]} grid_ny={p1["grid"]["ny"]} grid_nz={p1["grid"]["nz"]} '
        f'temp_front0={temp_front0:.8g} temp_front1={temp_front1:.8g} '
        f'front_shift={front_shift:.8g} front_shift_cells={front_shift_cells:.8g} '
        f'front_speed={front_speed:.8e} '
        f'temp_max0={float(np.max(temp0)):.8g} temp_max1={float(np.max(temp1)):.8g} '
        f'temp_l1={temp_l1:.8e} h2o_l1={h2o_l1:.8e} '
        f'species_y_min={y_min:.8e} species_closure_rel={species_closure_rel:.8e} '
        f'mass_rel={mass_rel:.8e} '
        f'h2_mass0={h2_mass0:.8e} h2_mass1={h2_mass1:.8e} '
        f'h2o_mass0={h2o_mass0:.8e} h2o_mass1={h2o_mass1:.8e}'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
